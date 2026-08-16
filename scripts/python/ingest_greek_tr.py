"""
ingest_greek_tr.py

Ingests the Greek Textus Receptus New Testament (eBible edition with annotations by Adam Boyd).
Source: https://ebible.org/Scriptures/grctr_usfm.zip
License: Public Domain
"""

import os
import re
import json
import zipfile
import io
import urllib.request
import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(script_dir))
bible_dir = os.path.join(base_dir, "bible")

SOURCE_URL = "https://ebible.org/Scriptures/grctr_usfm.zip"
LANG = "greek"
VERSION = "tr/ebible"
VERSION_LABEL = "GRCGTR"
LANG_LABEL = "EL"

NT_BOOKS = [
    "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH",
    "PHP", "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS",
    "1PE", "2PE", "1JN", "2JN", "3JN", "JUD", "REV"
]

BOOK_FOLDER = {
    "MAT": "01_matthew", "MRK": "02_mark", "LUK": "03_luke", "JHN": "04_john", "ACT": "05_acts",
    "ROM": "06_romans", "1CO": "07_1corinthians", "2CO": "08_2corinthians", "GAL": "09_galatians", "EPH": "10_ephesians",
    "PHP": "11_philippians", "COL": "12_colossians", "1TH": "13_1thessalonians", "2TH": "14_2thessalonians", "1TI": "15_1timothy",
    "2TI": "16_2timothy", "TIT": "17_titus", "PHM": "18_philemon", "HEB": "19_hebrews", "JAS": "20_james",
    "1PE": "21_1peter", "2PE": "22_2peter", "1JN": "23_1john", "2JN": "24_2john", "3JN": "25_3john",
    "JUD": "26_jude", "REV": "27_revelation",
}

PRETTY_NAME = {
    "MAT": "Matthew", "MRK": "Mark", "LUK": "Luke", "JHN": "John", "ACT": "Acts",
    "ROM": "Romans", "1CO": "1 Corinthians", "2CO": "2 Corinthians", "GAL": "Galatians", "EPH": "Ephesians",
    "PHP": "Philippians", "COL": "Colossians", "1TH": "1 Thessalonians", "2TH": "2 Thessalonians", "1TI": "1 Timothy",
    "2TI": "2 Timothy", "TIT": "Titus", "PHM": "Philemon", "HEB": "Hebrews", "JAS": "James",
    "1PE": "1 Peter", "2PE": "2 Peter", "1JN": "1 John", "2JN": "2 John", "3JN": "3 John",
    "JUD": "Jude", "REV": "Revelation",
}


def clean_usfm_text(text):
    # Remove inline Word-level strongs annotations: word|strong="..."
    text = re.sub(r'\|strong="[^"]*"', "", text)
    # Remove character-level markers: \wj ...\wj*, \add ...\add*, etc.
    text = re.sub(r"\\[a-z]+\*", "", text)
    text = re.sub(r"\\[a-z]+[0-9]?\s", " ", text)
    text = re.sub(r"\\[a-z]+\*?", "", text)
    # Remove footnote / manuscript annotations spans: \f ... \f* and \x ... \x*
    # This cleanly strips Adam Boyd's manuscript annotations, leaving only clean Greek text!
    text = re.sub(r"\\f\s.*?\\f\*", "", text, flags=re.DOTALL)
    text = re.sub(r"\\x\s.*?\\x\*", "", text, flags=re.DOTALL)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_usfm(usfm_text):
    chapters = {}
    current_chapter = None
    current_verse = None
    verse_buffer = []

    def flush_verse():
        if current_chapter and current_verse is not None and verse_buffer:
            raw = " ".join(verse_buffer)
            cleaned = clean_usfm_text(raw)
            if cleaned:
                if current_chapter not in chapters:
                    chapters[current_chapter] = []
                chapters[current_chapter].append((current_verse, cleaned))

    for line in usfm_text.splitlines():
        line = line.strip()
        if not line:
            continue

        c_match = re.match(r"^\\c\s+(\d+)", line)
        if c_match:
            flush_verse()
            current_chapter = int(c_match.group(1))
            current_verse = None
            verse_buffer = []
            continue

        v_match = re.match(r"^\\v\s+(\d+)\s*(.*)", line)
        if v_match:
            flush_verse()
            current_verse = int(v_match.group(1))
            verse_buffer = [v_match.group(2)] if v_match.group(2).strip() else []
            continue

        if current_verse is not None and line.startswith("\\"):
            remainder = re.sub(r"^\\[a-z]+[0-9]?\s*", "", line).strip()
            if remainder:
                verse_buffer.append(remainder)
            continue

        if current_verse is not None:
            verse_buffer.append(line)

    flush_verse()
    return chapters


def main():
    version_dir = os.path.join(bible_dir, LANG, VERSION)

    if os.path.exists(version_dir):
        print(f"Directory {version_dir} already exists. Cleaning up...")
        import shutil
        shutil.rmtree(version_dir)

    print(f"=== INGESTING GREEK TEXTUS RECEPTUS ===")
    print(f"Source: {SOURCE_URL}")

    # Download zip
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        zip_data = r.read()
    print(f"Downloaded {len(zip_data):,} bytes.")

    z = zipfile.ZipFile(io.BytesIO(zip_data))
    usfm_files = [f for f in z.namelist() if f.endswith(".usfm")]
    print(f"Found {len(usfm_files)} USFM files.")

    os.makedirs(version_dir, exist_ok=True)
    total_chapters = 0
    total_verses = 0

    for usfm_name in sorted(usfm_files):
        # Extract book code: e.g. "46-MATgrctr.usfm" -> "MAT"
        fname_match = re.search(r"\d{2}-([A-Z0-9]{3})", usfm_name)
        if not fname_match:
            continue

        book_abbr = fname_match.group(1)
        if book_abbr not in BOOK_FOLDER:
            continue

        book_folder = BOOK_FOLDER[book_abbr]
        pretty_name = PRETTY_NAME[book_abbr]
        book_dir = os.path.join(version_dir, "nt", book_folder)
        os.makedirs(book_dir, exist_ok=True)

        usfm_text = z.read(usfm_name).decode("utf-8", errors="replace")
        chapters = parse_usfm(usfm_text)

        for ch_num in sorted(chapters.keys()):
            verses = sorted(chapters[ch_num], key=lambda x: x[0])
            chapter_file = os.path.join(book_dir, f"chapter_{ch_num:03d}.txt")
            with open(chapter_file, "w", encoding="utf-8") as f:
                for v_num, text in verses:
                    label = f"[{VERSION_LABEL} | {LANG_LABEL} | NT | {pretty_name} | Chapter {ch_num} | Verse {v_num}]"
                    f.write(f"{label} {text}\n")
            total_chapters += 1
            total_verses += len(verses)

        print(f"  {book_abbr}: {len(chapters)} chapters, {sum(len(v) for v in chapters.values())} verses")

    # Write metadata
    meta = {
        "version": "Textus Receptus",
        "abbreviation": "GRCGTR",
        "language": "Ancient Greek",
        "testament": "NT",
        "edition": "eBible Textus Receptus",
        "source": "eBible.org",
        "source_id": "grctr",
        "license": "Public Domain",
        "text_type": "Textus Receptus",
        "annotations": True,
        "annotation_author": "Adam Boyd",
        "source_format": "USFM",
        "download_date": datetime.date.today().isoformat()
    }
    with open(os.path.join(version_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {total_chapters} chapters, {total_verses} verses written to {version_dir}")


if __name__ == "__main__":
    main()
