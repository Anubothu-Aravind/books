"""
export_sqlite.py

Parses all ingested Bible translations, geography places, cross-references,
and early Christian/council/patristic tradition texts, exporting them into
a single optimized SQLite database file (scriptural_tradition.db).
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
tradition_dir = os.path.join(base_dir, "tradition")
db_path = os.path.join(base_dir, "scriptural_tradition.db")

# Regex to parse the standard verse label: [VERSION | LANG | TESTAMENT | Book | Chapter X | Verse Y] Text
verse_pattern = re.compile(
    r"^\[\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*Chapter\s+(\d+)\s*\|\s*Verse\s+(\d+)\s*\]\s*(.*)$"
)


def create_schema(conn):
    cursor = conn.cursor()
    
    # 1. Bible Versions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS versions (
        code TEXT PRIMARY KEY,
        abbreviation TEXT,
        name TEXT NOT NULL,
        language TEXT NOT NULL,
        year INTEGER,
        license TEXT,
        checksum_hash TEXT
    )""")

    # 2. Bible Verses Table
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

    # 5. Tradition Works Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tradition_works (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        author TEXT,
        date TEXT,
        date_confidence TEXT,
        language TEXT,
        translator TEXT,
        license TEXT,
        source TEXT,
        source_url TEXT,
        source_id TEXT
    )""")

    # 6. Tradition Passages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tradition_passages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_id INTEGER NOT NULL,
        section_label TEXT NOT NULL,
        section_number INTEGER NOT NULL,
        text TEXT NOT NULL,
        FOREIGN KEY(work_id) REFERENCES tradition_works(id),
        UNIQUE(work_id, section_label, section_number)
    )""")

    conn.commit()


def create_indexes(conn):
    cursor = conn.cursor()
    print("Creating database indexes for query optimization...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_verses_lookup ON verses (version, book_name, chapter, verse)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_verses_book ON verses (version, book_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_xref_source ON cross_references (source_verse)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_geography_type ON geography (type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trad_passage ON tradition_passages (work_id, section_number)")
    conn.commit()


def parse_digits(s):
    match = re.search(r"\d+", s)
    return int(match.group(0)) if match else 0


def main():
    print("=== EXPORTING CORPUS TO SQLITE (scriptural_tradition.db) ===")

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
            
            # Walk and find all folders containing metadata.json (supports nesting like greek/tr/ebible)
            version_folders = []
            for root, dirs, files in os.walk(lang_path):
                if "metadata.json" in files:
                    version_folders.append(root)

            for ver_path in sorted(version_folders):
                # Relative path from lang_path gives the version subfolder(s)
                ver = os.path.relpath(ver_path, lang_path).replace("\\", "/")
                print(f"Processing version: {lang}/{ver}...")

                ver_code = f"{lang}_{ver}".upper().replace("/", "_")

                # Read metadata.json
                meta_file = os.path.join(ver_path, "metadata.json")
                name = ver.upper()
                abbreviation = ver.upper()
                year = None
                lic = "Unknown"
                checksum = ""

                if os.path.exists(meta_file):
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            name = meta.get("name", name)
                            abbreviation = meta.get("abbreviation", abbreviation)
                            year = meta.get("edition_year")
                            lic = meta.get("license", lic)
                            checksum = meta.get("checksum_hash", "")
                    except Exception as e:
                        print(f"  Warning parsing metadata for {ver}: {e}")

                # Insert Version
                cursor.execute(
                    "INSERT INTO versions (code, abbreviation, name, language, year, license, checksum_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (ver_code, abbreviation, name, lang, year, lic, checksum)
                )

                # Read chapter files
                verse_buffer = []
                for test in ["ot", "nt"]:
                    test_path = os.path.join(ver_path, test)
                    if not os.path.exists(test_path):
                        continue
                    
                    for root_dir, sub_dirs, files in os.walk(test_path):
                        for file in sorted(files):
                            if not file.endswith(".txt"):
                                continue
                            
                            ch_path = os.path.join(root_dir, file)
                            try:
                                with open(ch_path, "r", encoding="utf-8") as f:
                                    for line in f:
                                        line = line.strip()
                                        if not line:
                                            continue
                                        
                                        match = verse_pattern.match(line)
                                        if match:
                                            v_code, lang_code, testament, b_name, ch_num, v_num, v_text = match.groups()
                                            
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

    # 4. Ingest Tradition Corpus
    print("\n--- Ingesting Tradition Corpus ---")
    tradition_works_count = 0
    tradition_passages_count = 0
    
    if os.path.exists(tradition_dir):
        for category in ["early_christian", "councils", "patristics"]:
            cat_path = os.path.join(tradition_dir, category)
            if not os.path.exists(cat_path):
                continue
            
            # Recursively find any folder containing a metadata.json (supports nesting like patristics/augustine/de_trinitate)
            work_folders = []
            for root, dirs, files in os.walk(cat_path):
                if "metadata.json" in files:
                    work_folders.append(root)

            for work_path in sorted(work_folders):
                # Read metadata
                meta_file = os.path.join(work_path, "metadata.json")
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception as e:
                    print(f"  Error reading metadata in {work_path}: {e}")
                    continue

                work_dir_name = os.path.basename(work_path)
                title = meta.get("work", work_dir_name)
                author = meta.get("author")
                date = meta.get("date") or meta.get("date_range")
                date_conf = meta.get("date_confidence")
                lang = meta.get("language")
                translator = meta.get("translator")
                license_str = meta.get("license") or meta.get("source_license")
                source = meta.get("source")
                source_url = meta.get("source_url")
                source_id = meta.get("source_id")

                # Insert into tradition_works
                cursor.execute("""
                    INSERT INTO tradition_works (
                        category, title, author, date, date_confidence, language, translator, license, source, source_url, source_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (category, title, author, date, date_conf, lang, translator, license_str, source, source_url, source_id))
                
                work_id = cursor.lastrowid
                tradition_works_count += 1

                # Parse text files under this work
                text_files = []
                for root, _, files in os.walk(work_path):
                    for file in files:
                        if file.endswith(".txt"):
                            text_files.append(os.path.join(root, file))

                work_passages_count = 0
                for txt_file in sorted(text_files):
                    try:
                        with open(txt_file, "r", encoding="utf-8") as f:
                            for line in f:
                                line = line.strip()
                                if not line:
                                    continue
                                
                                # Parse custom label format, e.g. [Didache | EN | Liturgy | Chapter 14 | Verse 1] Text
                                match = re.match(r"^\[\s*(.*?)\s*\]\s*(.*)$", line)
                                if match:
                                    label_content = match.group(1)
                                    text_content = match.group(2)
                                    
                                    parts = [p.strip() for p in label_content.split("|")]
                                    
                                    # Extract section label (e.g. "Chapter 14" or "Canon 29")
                                    section_label = "Section"
                                    if len(parts) >= 4:
                                        # Usually parts[3] is the chapter/canon, e.g. "Chapter 14"
                                        section_label = parts[3]
                                    
                                    # Extract section number and verse number
                                    section_number = parse_digits(section_label)
                                    verse_number = 0
                                    if len(parts) >= 5:
                                        verse_number = parse_digits(parts[4])
                                    
                                    cursor.execute("""
                                        INSERT OR IGNORE INTO tradition_passages (
                                            work_id, section_label, section_number, text
                                        ) VALUES (?, ?, ?, ?)
                                    """, (work_id, section_label, verse_number, text_content))
                                    if cursor.rowcount > 0:
                                        work_passages_count += 1
                                        tradition_passages_count += 1
                    except Exception as e:
                        print(f"  Error parsing tradition text {txt_file}: {e}")

                print(f"  Ingested tradition work: {title} ({work_passages_count} passages).")

    # Commit all
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
    cursor.execute("SELECT COUNT(*) FROM tradition_works")
    print(f"Total Trad Works: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM tradition_passages")
    print(f"Total Trad Passages: {cursor.fetchone()[0]}")

    conn.close()


if __name__ == "__main__":
    main()
