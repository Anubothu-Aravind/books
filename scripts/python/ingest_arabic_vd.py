"""
ingest_arabic_vd.py

Ingests the true public domain Arabic Van Dyke Bible from eBible.org.
Source: https://ebible.org/Scriptures/arb-vd_usfm.zip
License: Public Domain
"""

import os
import re
import json
import zipfile
import io
import urllib.request
import datetime
import subprocess

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(script_dir))
bible_dir = os.path.join(base_dir, "bible")

SOURCE_URL = "https://ebible.org/Scriptures/arb-vd_usfm.zip"
LANG = "arabic"
VERSION = "vandyke"
VERSION_LABEL = "VANDYKE"
LANG_LABEL = "AR"

NT_BOOKS = [
    "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH",
    "PHP", "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS",
    "1PE", "2PE", "1JN", "2JN", "3JN", "JUD", "REV"
]

OT_BOOKS = [
    "GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT", "1SA", "2SA",
    "1KI", "2KI", "1CH", "2CH", "EZR", "NEH", "EST", "JOB", "PSA", "PRO",
    "ECC", "SNG", "ISA", "JER", "LAM", "EZK", "DAN", "HOS", "JOL", "AMO",
    "OBA", "JON", "MIC", "NAM", "HAB", "ZEP", "HAG", "ZEC", "MAL"
]

BOOK_FOLDER = {
    "GEN": "genesis", "EXO": "exodus", "LEV": "leviticus", "NUM": "numbers", "DEU": "deuteronomy",
    "JOS": "joshua", "JDG": "judges", "RUT": "ruth", "1SA": "1samuel", "2SA": "2samuel",
    "1KI": "1kings", "2KI": "2kings", "1CH": "1chronicles", "2CH": "2chronicles", "EZR": "ezra",
    "NEH": "nehemiah", "EST": "esther", "JOB": "job", "PSA": "psalms", "PRO": "proverbs",
    "ECC": "ecclesiastes", "SNG": "songofsolomon", "ISA": "isaiah", "JER": "jeremiah", "LAM": "lamentations",
    "EZK": "ekeziel", "DAN": "daniel", "HOS": "hosea", "JOL": "joel", "AMO": "amos",
    "OBA": "obadiah", "JON": "jonah", "MIC": "micah", "NAM": "nahum", "HAB": "habakkuk",
    "ZEP": "zephaniah", "HAG": "haggai", "ZEC": "zechariah", "MAL": "malachi",
    "MAT": "matthew", "MRK": "mark", "LUK": "luke", "JHN": "john", "ACT": "acts",
    "ROM": "romans", "1CO": "1corinthians", "2CO": "2corinthians", "GAL": "galatians", "EPH": "ephesians",
    "PHP": "philippians", "COL": "colossians", "1TH": "1thessalonians", "2TH": "2thessalonians", "1TI": "1timothy",
    "2TI": "2timothy", "TIT": "titus", "PHM": "philemon", "HEB": "hebrews", "JAS": "james",
    "1PE": "1peter", "2PE": "2peter", "1JN": "1john", "2JN": "2john", "3JN": "3john",
    "JUD": "jude", "REV": "revelation",
}

PRETTY_NAME = {
    "GEN": "Genesis", "EXO": "Exodus", "LEV": "Leviticus", "NUM": "Numbers", "DEU": "Deuteronomy",
    "JOS": "Joshua", "JDG": "Judges", "RUT": "Ruth", "1SA": "1 Samuel", "2SA": "2 Samuel",
    "1KI": "1 Kings", "2KI": "2 Kings", "1CH": "1 Chronicles", "2CH": "2 Chronicles", "EZR": "Ezra",
    "NEH": "Nehemiah", "EST": "Esther", "JOB": "Job", "PSA": "Psalms", "PRO": "Proverbs",
    "ECC": "Ecclesiastes", "SNG": "Song of Solomon", "ISA": "Isaiah", "JER": "Jeremiah", "LAM": "Lamentations",
    "EZK": "Ezekiel", "DAN": "Daniel", "HOS": "Hosea", "JOL": "Joel", "AMO": "Amos",
    "OBA": "Obadiah", "JON": "Jonah", "MIC": "Micah", "NAM": "Nahum", "HAB": "Habakkuk",
    "ZEP": "Zephaniah", "HAG": "Haggai", "ZEC": "Zechariah", "MAL": "Malachi",
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
    # Remove footnote / cross-ref spans: \f ... \f* and \x ... \x*
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

    # Delete existing folder to ensure clean overwrite
    if os.path.exists(version_dir):
        print(f"Removing old fallback at {version_dir}...")
        import shutil
        shutil.rmtree(version_dir)

    print(f"=== INGESTING ARABIC VAN DYKE ===")
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
        fname_match = re.search(r"\d{2}-([A-Z0-9]{3})", usfm_name)
        if not fname_match:
            continue

        book_abbr = fname_match.group(1)
        if book_abbr not in BOOK_FOLDER:
            continue

        is_nt = book_abbr in NT_BOOKS
        testament = "nt" if is_nt else "ot"
        book_folder_name_lower = BOOK_FOLDER[book_abbr]
        pretty_name = PRETTY_NAME[book_abbr]

        if is_nt:
            prefix_idx = NT_BOOKS.index(book_abbr) + 1
        else:
            prefix_idx = OT_BOOKS.index(book_abbr) + 1

        book_folder = f"{prefix_idx:02d}_{book_folder_name_lower}"
        book_dir = os.path.join(version_dir, testament, book_folder)
        os.makedirs(book_dir, exist_ok=True)

        usfm_text = z.read(usfm_name).decode("utf-8", errors="replace")
        chapters = parse_usfm(usfm_text)

        for ch_num in sorted(chapters.keys()):
            verses = sorted(chapters[ch_num], key=lambda x: x[0])
            chapter_file = os.path.join(book_dir, f"chapter_{ch_num:03d}.txt")
            with open(chapter_file, "w", encoding="utf-8") as f:
                for v_num, text in verses:
                    label = f"[{VERSION_LABEL} | {LANG_LABEL} | {testament.upper()} | {pretty_name} | Chapter {ch_num} | Verse {v_num}]"
                    f.write(f"{label} {text}\n")
            total_chapters += 1
            total_verses += len(verses)

        print(f"  {book_abbr}: {len(chapters)} chapters, {sum(len(v) for v in chapters.values())} verses")

    # Write metadata
    meta = {
        "version": "Arabic Van Dyke",
        "abbreviation": "AVD",
        "language": "Arabic",
        "source": "eBible.org",
        "source_id": "arb-vd",
        "license": "Public Domain",
        "translator": "Syrian Mission",
        "contributor": "American Bible Society",
        "source_format": "USFM",
        "testament": "OT+NT",
        "download_date": datetime.date.today().isoformat()
    }
    with open(os.path.join(version_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {total_chapters} chapters, {total_verses} verses written to {version_dir}")


if __name__ == "__main__":
    main()
