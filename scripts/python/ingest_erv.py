"""
ingest_erv.py

Ingests the English Revised Version (1885) from the eBible.org USFM package.
Source: https://ebible.org/Scriptures/eng-rv_usfm.zip
License: Public Domain

USFM markers used:
  \\id   - Book identifier
  \\c    - Chapter number
  \\v    - Verse number + text
  \\p \\q \\m etc - Paragraph/poetry markers (ignored, text extracted)

After ingestion, run:
    python scripts/python/update_metadata.py
    python scripts/python/generate_status.py
    python tests/python/run_tests.py
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

SOURCE_URL = "https://ebible.org/Scriptures/eng-rv_usfm.zip"
LANG = "english"
VERSION = "erv"
VERSION_LABEL = "ERV"
LANG_LABEL = "EN"

# Canonical NT book list (for testament assignment)
NT_BOOKS = [
    "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH",
    "PHP", "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS",
    "1PE", "2PE", "1JN", "2JN", "3JN", "JUD", "REV"
]

# OT canonical order (Protestant 39 books)
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

# USFM filename prefix to book code map (eBible uses numeric prefix + 3-letter code)
USFM_ID_MAP = {
    "GEN": "GEN", "EXO": "EXO", "LEV": "LEV", "NUM": "NUM", "DEU": "DEU",
    "JOS": "JOS", "JDG": "JDG", "RUT": "RUT", "1SA": "1SA", "2SA": "2SA",
    "1KI": "1KI", "2KI": "2KI", "1CH": "1CH", "2CH": "2CH", "EZR": "EZR",
    "NEH": "NEH", "EST": "EST", "JOB": "JOB", "PSA": "PSA", "PRO": "PRO",
    "ECC": "ECC", "SNG": "SNG", "ISA": "ISA", "JER": "JER", "LAM": "LAM",
    "EZK": "EZK", "DAN": "DAN", "HOS": "HOS", "JOL": "JOL", "AMO": "AMO",
    "OBA": "OBA", "JON": "JON", "MIC": "MIC", "NAM": "NAM", "HAB": "HAB",
    "ZEP": "ZEP", "HAG": "HAG", "ZEC": "ZEC", "MAL": "MAL",
    "MAT": "MAT", "MRK": "MRK", "LUK": "LUK", "JHN": "JHN", "ACT": "ACT",
    "ROM": "ROM", "1CO": "1CO", "2CO": "2CO", "GAL": "GAL", "EPH": "EPH",
    "PHP": "PHP", "COL": "COL", "1TH": "1TH", "2TH": "2TH", "1TI": "1TI",
    "2TI": "2TI", "TIT": "TIT", "PHM": "PHM", "HEB": "HEB", "JAS": "JAS",
    "1PE": "1PE", "2PE": "2PE", "1JN": "1JN", "2JN": "2JN", "3JN": "3JN",
    "JUD": "JUD", "REV": "REV",
}


def clean_usfm_text(text):
    """Remove inline USFM markers and return clean verse text."""
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
    """Parse a USFM file and return {chapter_num: [(verse_num, text), ...]}."""
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

        # Chapter marker
        c_match = re.match(r"^\\c\s+(\d+)", line)
        if c_match:
            flush_verse()
            current_chapter = int(c_match.group(1))
            current_verse = None
            verse_buffer = []
            continue

        # Verse marker — may have text on the same line
        v_match = re.match(r"^\\v\s+(\d+)\s*(.*)", line)
        if v_match:
            flush_verse()
            current_verse = int(v_match.group(1))
            verse_buffer = [v_match.group(2)] if v_match.group(2).strip() else []
            continue

        # Paragraph/poetry markers at the start of a line — continuation of current verse
        if current_verse is not None and line.startswith("\\"):
            # Strip the marker tag, keep the text after it
            remainder = re.sub(r"^\\[a-z]+[0-9]?\s*", "", line).strip()
            if remainder:
                verse_buffer.append(remainder)
            continue

        # Plain text continuation
        if current_verse is not None:
            verse_buffer.append(line)

    flush_verse()
    return chapters


def main():
    version_dir = os.path.join(bible_dir, LANG, VERSION)

    # Check if already ingested
    if os.path.exists(version_dir):
        existing = sum(
            1 for root, _, files in os.walk(version_dir)
            for f in files if f.endswith(".txt") and f != "metadata.json"
        )
        if existing > 0:
            print(f"ERV already ingested ({existing} chapter files). Delete {version_dir} to re-ingest.")
            return

    print(f"=== INGESTING ERV 1885 ===")
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
        # Extract book abbreviation from filename: e.g. "02-GENeng-rv.usfm" -> "GEN"
        fname_match = re.search(r"\d{2}-([A-Z0-9]{3})", usfm_name)
        if not fname_match:
            print(f"  Skipping unrecognized file: {usfm_name}")
            continue

        book_abbr = fname_match.group(1)

        # Map SNG variants
        if book_abbr == "SNG":
            book_abbr = "SNG"

        if book_abbr not in BOOK_FOLDER:
            print(f"  Skipping non-canonical book: {book_abbr} ({usfm_name})")
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
        "version": VERSION_LABEL,
        "name": "English Revised Version (1885)",
        "language": LANG,
        "edition_year": 1885,
        "license": "Public Domain",
        "publisher_source": "eBible.org USFM Package",
        "source_url": SOURCE_URL,
        "download_date": datetime.date.today().isoformat(),
    }
    with open(os.path.join(version_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {total_chapters} chapters, {total_verses} verses written to {version_dir}")

    # Post-processors
    print("\n=== RUNNING POST-PROCESSORS ===")
    for script in ["update_metadata.py", "generate_status.py"]:
        path = os.path.join(script_dir, script)
        if os.path.exists(path):
            print(f"Running {script}...")
            subprocess.run(["python", path], cwd=base_dir, check=True)

    print("\nRun the test suite next:")
    print("    python tests/python/run_tests.py")


if __name__ == "__main__":
    main()
