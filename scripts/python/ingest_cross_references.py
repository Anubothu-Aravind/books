"""
ingest_cross_references.py

Downloads and processes the OpenBible.info cross-references dataset.
Source: https://a.openbible.info/data/cross-references.zip
License: Creative Commons Attribution (CC BY 4.0)

Outputs:
  - cross_references/cross_references.json (verse-to-verse mapping)
  - cross_references/book_matrix.csv (66x66 book cross-reference counts)
  - cross_references/metadata.json (schema metadata and checksums)
"""

import os
import json
import urllib.request
import zipfile
import io
import hashlib
import csv

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
xref_dir = os.path.join(base_dir, "cross_references")
os.makedirs(xref_dir, exist_ok=True)

SOURCE_URL = "https://a.openbible.info/data/cross-references.zip"

# Canon books in order
CANON_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
    "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah",
    "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah",
    "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
    "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians",
    "Galatians", "Ephesians", "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James", "1 Peter", "2 Peter",
    "1 John", "2 John", "3 John", "Jude", "Revelation"
]

# Map OSIS abbreviations used in the raw file to pretty book names
OSIS_MAP = {
    "Gen": "Genesis", "Exod": "Exodus", "Lev": "Leviticus", "Num": "Numbers", "Deut": "Deuteronomy",
    "Josh": "Joshua", "Judg": "Judges", "Ruth": "Ruth", "1Sam": "1 Samuel", "2Sam": "2 Samuel",
    "1Kings": "1 Kings", "2Kings": "2 Kings", "1Chr": "1 Chronicles", "2Chr": "2 Chronicles",
    "Ezra": "Ezra", "Neh": "Nehemiah", "Esth": "Esther", "Job": "Job", "Ps": "Psalms", "Prov": "Proverbs",
    "Eccl": "Ecclesiastes", "Song": "Song of Solomon", "Isa": "Isaiah", "Jer": "Jeremiah",
    "Lam": "Lamentations", "Ezek": "Ezekiel", "Dan": "Daniel", "Hos": "Hosea", "Joel": "Joel",
    "Amos": "Amos", "Obad": "Obadiah", "Jonah": "Jonah", "Mic": "Micah", "Nah": "Nahum",
    "Hab": "Habakkuk", "Zeph": "Zephaniah", "Hag": "Haggai", "Zech": "Zechariah", "Mal": "Malachi",
    "Matt": "Matthew", "Mark": "Mark", "Luke": "Luke", "John": "John", "Acts": "Acts", "Rom": "Romans",
    "1Cor": "1 Corinthians", "2Cor": "2 Corinthians", "Gal": "Galatians", "Eph": "Ephesians",
    "Phil": "Philippians", "Col": "Colossians", "1Thess": "1 Thessalonians", "2Thess": "2 Thessalonians",
    "1Tim": "1 Timothy", "2Tim": "2 Timothy", "Titus": "Titus", "Phlm": "Philemon", "Heb": "Hebrews",
    "Jas": "James", "1Pet": "1 Peter", "2Pet": "2 Peter", "1John": "1 John", "2John": "2 John",
    "3John": "3 John", "Jude": "Jude", "Rev": "Revelation"
}


def parse_verse_ref(raw_ref):
    """
    Parses a reference like 'Gen.1.1' or '1John.1.1' and returns (book_name, chapter, verse).
    Handles verse ranges (e.g. Rom.12.19-Rom.12.21) by taking the starting verse.
    """
    # Split hyphen if it represents a range
    raw_ref = raw_ref.split("-")[0]
    parts = raw_ref.split(".")
    if len(parts) >= 3:
        osis_book = parts[0]
        chapter = parts[1]
        verse = parts[2]
        pretty_book = OSIS_MAP.get(osis_book)
        if pretty_book:
            try:
                return pretty_book, int(chapter), int(verse)
            except ValueError:
                pass
    return None


def main():
    print("=== INGESTING BIBLE CROSS-REFERENCES ===")
    print(f"Downloading dataset from: {SOURCE_URL}")

    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        zip_data = r.read()
    print(f"Downloaded {len(zip_data):,} bytes.")

    z = zipfile.ZipFile(io.BytesIO(zip_data))
    content = z.read("cross_references.txt").decode("utf-8")
    lines = content.splitlines()

    print(f"Loaded {len(lines)} records.")

    # Dictionary for verse-to-verse mapping
    xref_map = {}
    
    # 66x66 Matrix initialized to 0
    matrix = {b: {other: 0 for other in CANON_BOOKS} for b in CANON_BOOKS}

    skipped_count = 0
    valid_count = 0

    # Line 0 is header: "From Verse \t To Verse \t Votes"
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        
        raw_from = parts[0].strip()
        raw_to = parts[1].strip()
        votes_str = parts[2].strip()

        try:
            votes = int(votes_str)
        except Exception:
            votes = 1

        from_parsed = parse_verse_ref(raw_from)
        to_parsed = parse_verse_ref(raw_to)

        if not from_parsed or not to_parsed:
            skipped_count += 1
            continue

        valid_count += 1

        from_book, from_ch, from_v = from_parsed
        to_book, to_ch, to_v = to_parsed

        # standard key structure: e.g. "Genesis 1:1"
        from_key = f"{from_book} {from_ch}:{from_v}"
        to_key = f"{to_book} {to_ch}:{to_v}"

        if from_key not in xref_map:
            xref_map[from_key] = []
        xref_map[from_key].append({
            "target": to_key,
            "votes": votes
        })

        # Add to the matrix
        matrix[from_book][to_book] += 1

    print(f"Ingested {valid_count} connections. Skipped {skipped_count} invalid records.")

    # Save cross-references map to JSON
    xref_json_file = os.path.join(xref_dir, "cross_references.json")
    with open(xref_json_file, "w", encoding="utf-8") as f:
        json.dump(xref_map, f, indent=2, ensure_ascii=False)
    print(f"Saved connections map to {xref_json_file}")

    # Save 66x66 book matrix to CSV
    matrix_csv_file = os.path.join(xref_dir, "book_matrix.csv")
    with open(matrix_csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        # Header: empty top-left, then book names
        writer.writerow([""] + CANON_BOOKS)
        for b in CANON_BOOKS:
            row = [b]
            for other in CANON_BOOKS:
                row.append(matrix[b][other])
            writer.writerow(row)
    print(f"Saved book matrix to {matrix_csv_file}")

    # Generate metadata
    metadata_file = os.path.join(xref_dir, "metadata.json")

    def get_sha256(filepath):
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    meta = {
        "dataset_name": "Bible Cross-References",
        "description": "Comprehensive map of cross-references between verses of the Bible, with votes indicating significance.",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "source": "OpenBible.info Cross References (openbible.info/labs/cross-references)",
        "source_urls": [SOURCE_URL],
        "download_date": urllib.request.urlopen(urllib.request.Request(SOURCE_URL, method="HEAD")).info().get("Date") or "2026-08-16",
        "files": {
            "cross_references.json": {
                "records_count": len(xref_map),
                "sha256": get_sha256(xref_json_file)
            },
            "book_matrix.csv": {
                "records_count": 66,
                "sha256": get_sha256(matrix_csv_file)
            }
        }
    }

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"Saved cross-references metadata to {metadata_file}")

    print("Cross-references ingestion complete!\n")


if __name__ == "__main__":
    main()
