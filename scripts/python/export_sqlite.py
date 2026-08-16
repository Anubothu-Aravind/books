"""
export_sqlite.py

Parses all ingested Bible translations, geography places, and cross-references,
and exports them into a single optimized SQLite database file (bible_database.db).
"""

import os
import re
import json
import sqlite3
import hashlib

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
bible_dir = os.path.join(base_dir, "bible")
geography_dir = os.path.join(base_dir, "geography")
xref_dir = os.path.join(base_dir, "cross_references")
db_path = os.path.join(base_dir, "bible_database.db")

# Regex to parse the standard verse label: [VERSION | LANG | TESTAMENT | Book | Chapter X | Verse Y] Text
verse_pattern = re.compile(
    r"^\[\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*Chapter\s+(\d+)\s*\|\s*Verse\s+(\d+)\s*\]\s*(.*)$"
)


def create_schema(conn):
    cursor = conn.cursor()
    
    # 1. Versions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS versions (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        language TEXT NOT NULL,
        year INTEGER,
        license TEXT,
        checksum_hash TEXT
    )""")

    # 2. Verses Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS verses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version TEXT NOT NULL,
        testament TEXT NOT NULL,
        book_name TEXT NOT NULL,
        chapter INTEGER NOT NULL,
        verse INTEGER NOT NULL,
        text TEXT NOT NULL,
        label TEXT NOT NULL,
        FOREIGN KEY (version) REFERENCES versions(code)
    )""")

    # 3. Geography Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS geography (
        place_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        lat REAL,
        lon REAL,
        wikidata_id TEXT,
        confidence TEXT,
        verses_list TEXT
    )""")

    # 4. Cross References Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cross_references (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_verse TEXT NOT NULL,
        target_verse TEXT NOT NULL,
        votes INTEGER NOT NULL
    )""")

    conn.commit()


def create_indexes(conn):
    cursor = conn.cursor()
    print("Creating database indexes for query optimization...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_verses_lookup ON verses (version, book_name, chapter, verse)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_verses_book ON verses (version, book_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_xref_source ON cross_references (source_verse)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_geography_type ON geography (type)")
    conn.commit()


def main():
    print("=== EXPORTING BIBLE CORPUS TO SQLITE ===")

    # Delete existing database file if present
    if os.path.exists(db_path):
        print(f"Removing existing database at {db_path}...")
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    create_schema(conn)

    cursor = conn.cursor()

    # 1. Ingest Versions and Verses
    print("\n--- Ingesting Bible Versions and Verses ---")
    if os.path.exists(bible_dir):
        for lang in sorted(os.listdir(bible_dir)):
            lang_path = os.path.join(bible_dir, lang)
            if not os.path.isdir(lang_path):
                continue
            
            for ver in sorted(os.listdir(lang_path)):
                ver_path = os.path.join(lang_path, ver)
                if not os.path.isdir(ver_path):
                    continue

                print(f"Processing version: {lang}/{ver}...")

                # Generate a globally unique version code (e.g., BENGALI_IRV, ENGLISH_KJV)
                ver_code = f"{lang}_{ver}".upper()

                # Read metadata.json
                meta_file = os.path.join(ver_path, "metadata.json")
                name = ver.upper()
                year = None
                lic = "Unknown"
                checksum = ""

                if os.path.exists(meta_file):
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            name = meta.get("name", name)
                            year = meta.get("edition_year")
                            lic = meta.get("license", lic)
                            checksum = meta.get("checksum_hash", "")
                    except Exception as e:
                        print(f"  Warning parsing metadata for {ver}: {e}")

                # Insert Version
                cursor.execute(
                    "INSERT INTO versions (code, name, language, year, license, checksum_hash) VALUES (?, ?, ?, ?, ?, ?)",
                    (ver_code, name, lang, year, lic, checksum)
                )

                # Read chapter files
                verse_buffer = []
                for test in ["ot", "nt"]:
                    test_path = os.path.join(ver_path, test)
                    if not os.path.exists(test_path):
                        continue
                    
                    for book_folder in sorted(os.listdir(test_path)):
                        book_path = os.path.join(test_path, book_folder)
                        if not os.path.isdir(book_path):
                            continue
                        
                        for ch_file in sorted(os.listdir(book_path)):
                            if not ch_file.endswith(".txt"):
                                continue
                            
                            ch_path = os.path.join(book_path, ch_file)
                            try:
                                with open(ch_path, "r", encoding="utf-8") as f:
                                    for line in f:
                                        line = line.strip()
                                        if not line:
                                            continue
                                        
                                        match = verse_pattern.match(line)
                                        if match:
                                            v_code, lang_code, testament, b_name, ch_num, v_num, v_text = match.groups()
                                            
                                            # Add to insertion buffer
                                            verse_buffer.append((
                                                ver_code,
                                                testament.lower(),
                                                b_name,
                                                int(ch_num),
                                                int(v_num),
                                                v_text,
                                                line[:line.index("]")+1]
                                            ))
                            except Exception as e:
                                print(f"  Error reading {ch_path}: {e}")

                # Batch insert verses
                if verse_buffer:
                    cursor.executemany(
                        "INSERT INTO verses (version, testament, book_name, chapter, verse, text, label) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        verse_buffer
                    )
                    print(f"  Ingested {len(verse_buffer)} verses.")
    
    # 2. Ingest Geography Places
    print("\n--- Ingesting Geography Places ---")
    places_injected = 0
    
    # Places
    places_file = os.path.join(geography_dir, "places.json")
    if os.path.exists(places_file):
        try:
            with open(places_file, "r", encoding="utf-8") as f:
                places = json.load(f)
                for p in places:
                    cursor.execute(
                        "INSERT INTO geography (place_id, name, type, lat, lon, wikidata_id, confidence, verses_list) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            p["id"],
                            p["name"],
                            p["type"],
                            p.get("lat"),
                            p.get("lon"),
                            p.get("wikidata_id"),
                            p.get("confidence"),
                            json.dumps(p.get("verses", []))
                        )
                    )
                places_injected += len(places)
        except Exception as e:
            print(f"  Error ingesting places: {e}")

    # Regions/Water
    regions_file = os.path.join(geography_dir, "regions_water.json")
    if os.path.exists(regions_file):
        try:
            with open(regions_file, "r", encoding="utf-8") as f:
                regions = json.load(f)
                for r in regions:
                    cursor.execute(
                        "INSERT INTO geography (place_id, name, type, lat, lon, wikidata_id, confidence, verses_list) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            r["id"],
                            r["name"],
                            r["type"],
                            r.get("lat"),
                            r.get("lon"),
                            r.get("wikidata_id"),
                            r.get("confidence"),
                            json.dumps(r.get("verses", []))
                        )
                    )
                places_injected += len(regions)
        except Exception as e:
            print(f"  Error ingesting regions_water: {e}")
            
    print(f"Ingested {places_injected} geography records.")

    # 3. Ingest Cross References
    print("\n--- Ingesting Cross References ---")
    xref_file = os.path.join(xref_dir, "cross_references.json")
    if os.path.exists(xref_file):
        try:
            with open(xref_file, "r", encoding="utf-8") as f:
                xrefs = json.load(f)
                xref_buffer = []
                for src_verse, targets in xrefs.items():
                    for target in targets:
                        xref_buffer.append((
                            src_verse,
                            target["target"],
                            target["votes"]
                        ))
                
                if xref_buffer:
                    cursor.executemany(
                        "INSERT INTO cross_references (source_verse, target_verse, votes) VALUES (?, ?, ?)",
                        xref_buffer
                    )
                    print(f"Ingested {len(xref_buffer)} cross-reference connections.")
        except Exception as e:
            print(f"  Error ingesting cross-references: {e}")
    else:
        print("  Cross-references file not found.")

    # Commit insertions
    conn.commit()

    # Create optimized indexes
    create_indexes(conn)

    # Print summary database statistics
    print("\nDatabase Generation Complete!")
    cursor.execute("SELECT COUNT(*) FROM versions")
    print(f"Total Versions: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM verses")
    print(f"Total Verses  : {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM geography")
    print(f"Total Places  : {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM cross_references")
    print(f"Total CrossRefs: {cursor.fetchone()[0]}")

    conn.close()


if __name__ == "__main__":
    main()
