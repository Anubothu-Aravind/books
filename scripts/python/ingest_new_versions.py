"""
ingest_new_versions.py

Non-destructive ingestion script. Downloads and ingests only the specified
new versions into the existing bible/ folder structure without wiping
any already-collected versions.

Usage:
    python scripts/python/ingest_new_versions.py

After ingestion, run:
    python scripts/python/update_metadata.py
    python scripts/python/generate_status.py
    python tests/python/run_tests.py
"""

import os
import json
import urllib.request
import re
import subprocess

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(script_dir))
bible_dir = os.path.join(base_dir, "bible")

# -----------------------------------------------------------------------
# New versions to ingest. Each entry must have a confirmed, non-empty
# eBible corpus file before being added here.
# -----------------------------------------------------------------------
NEW_VERSIONS = [
    {
        "lang": "english", "version": "webster",
        "filename": "eng-engwebster.txt",
        "name": "Webster's Bible Translation", "year": 1833,
        "license": "Public Domain",
        "publisher_source": "eBible Corpus (BibleNLP/ebible)",
        "source_url": "https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/eng-engwebster.txt",
    },
    {
        "lang": "english", "version": "bsb",
        "filename": "eng-engbsb.txt",
        "name": "Berean Standard Bible", "year": 2020,
        "license": "CC BY 4.0",
        "publisher_source": "eBible Corpus (BibleNLP/ebible)",
        "source_url": "https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/eng-engbsb.txt",
    },
    {
        "lang": "english", "version": "gnv",
        "filename": "eng-enggnv.txt",
        "name": "Geneva Bible (1599)", "year": 1599,
        "license": "Public Domain",
        "publisher_source": "eBible Corpus (BibleNLP/ebible)",
        "source_url": "https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/eng-enggnv.txt",
    },
    {
        "lang": "english", "version": "jps",
        "filename": "eng-engjps.txt",
        "name": "Jewish Publication Society Tanakh (1917)", "year": 1917,
        "license": "Public Domain",
        "publisher_source": "eBible Corpus (BibleNLP/ebible)",
        "source_url": "https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/eng-engjps.txt",
    },
]

# -----------------------------------------------------------------------
# Canonical book lists and mappings (duplicated from download_bibles.py
# so this script is standalone)
# -----------------------------------------------------------------------
vref_url = "https://raw.githubusercontent.com/BibleNLP/ebible/main/metadata/vref.txt"

nt_books = [
    "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH",
    "PHP", "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS",
    "1PE", "2PE", "1JN", "2JN", "3JN", "JUD", "REV"
]

book_mapping = {
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
    "TOB": "tobit", "JDT": "judith", "ESG": "esther_greek", "WIS": "wisdom",
    "SIR": "sirach", "BAR": "baruch", "LJE": "letter_of_jeremiah", "S3Y": "song_of_three_children",
    "SUS": "susanna", "BEL": "bel_and_the_dragon", "1MA": "1maccabees", "2MA": "2maccabees",
    "3MA": "3maccabees", "4MA": "4maccabees", "1ES": "1esdras", "2ES": "2esdras",
    "MAN": "prayer_of_manasseh", "PS2": "psalm_151", "ODA": "odes", "PSS": "psalms_of_solomon",
    "EZA": "ezra_apocalypse", "JUB": "jubilees", "ENO": "enoch"
}

pretty_book_names = {
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
    "TOB": "Tobit", "JDT": "Judith", "ESG": "Esther (Greek)", "WIS": "Wisdom of Solomon",
    "SIR": "Sirach", "BAR": "Baruch", "LJE": "Letter of Jeremiah", "S3Y": "Song of the Three Holy Children",
    "SUS": "Susanna", "BEL": "Bel and the Dragon", "1MA": "1 Maccabees", "2MA": "2 Maccabees",
    "3MA": "3 Maccabees", "4MA": "4 Maccabees", "1ES": "1 Esdras", "2ES": "2 Esdras",
    "MAN": "Prayer of Manasseh", "PS2": "Psalm 151", "ODA": "Odes", "PSS": "Psalms of Solomon",
    "EZA": "Apocalypse of Ezra", "JUB": "Jubilees", "ENO": "Enoch"
}

lang_codes = {
    "english": "en", "telugu": "te", "hindi": "hi", "tamil": "ta", "kannada": "kn",
    "malayalam": "ml", "bengali": "bn", "marathi": "mr", "gujarati": "gu",
    "punjabi": "pa", "urdu": "ur", "hebrew": "he", "greek": "el", "arabic": "ar"
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        return r.read().decode("utf-8")


def main():
    print("=== FETCHING VREF ===")
    vref_lines = fetch(vref_url).splitlines()
    print(f"Loaded {len(vref_lines)} vref references.")

    ot_books = []
    for ref in vref_lines:
        m = re.match(r"^([\w\d]+)\s+", ref.strip())
        if m:
            b = m.group(1)
            if b not in nt_books and b not in ot_books:
                ot_books.append(b)

    for dl in NEW_VERSIONS:
        lang = dl["lang"]
        version = dl["version"]
        url = dl["source_url"]
        name = dl["name"]

        version_dir = os.path.join(bible_dir, lang, version)

        print(f"\n=== INGESTING {lang}/{version} ({name}) ===")
        print(f"    Source: {url}")

        # Skip if already present and populated
        if os.path.exists(version_dir):
            existing = sum(
                1 for root, _, files in os.walk(version_dir)
                for f in files if f.endswith(".txt") and f != "metadata.json"
            )
            if existing > 0:
                print(f"    Already ingested ({existing} chapter files). Skipping.")
                continue

        # Download
        content = fetch(url)
        lines = content.splitlines()
        filled = sum(1 for l in lines if l.strip())
        print(f"    Downloaded: {len(lines)} lines, {filled} non-empty.")

        if filled == 0:
            print(f"    ERROR: Source file is empty. Skipping {lang}/{version}.")
            continue

        # Parse and group by book/chapter
        version_label = version.upper()
        lang_label = lang_codes.get(lang, "xx").upper()
        grouped = {}
        max_idx = min(len(lines), len(vref_lines))

        for i in range(max_idx):
            verse_text = lines[i].strip()
            if not verse_text:
                continue
            ref = vref_lines[i].strip()
            m = re.match(r"^(\w+)\s+(\d+):(\d+)$", ref)
            if not m:
                continue
            book_abbr, ch_str, v_str = m.group(1), m.group(2), m.group(3)
            ch_num, v_num = int(ch_str), int(v_str)
            if book_abbr not in grouped:
                grouped[book_abbr] = {}
            if ch_num not in grouped[book_abbr]:
                grouped[book_abbr][ch_num] = []
            grouped[book_abbr][ch_num].append((v_num, verse_text))

        os.makedirs(version_dir, exist_ok=True)
        total_chapters = 0

        for book_abbr, chapters in grouped.items():
            is_nt = book_abbr in nt_books
            testament_folder = "nt" if is_nt else "ot"
            book_name_lower = book_mapping.get(book_abbr, book_abbr.lower())
            pretty_name = pretty_book_names.get(book_abbr, book_abbr.title())

            if is_nt:
                prefix_idx = nt_books.index(book_abbr) + 1
            else:
                prefix_idx = ot_books.index(book_abbr) + 1 if book_abbr in ot_books else 99

            book_folder_name = f"{prefix_idx:02d}_{book_name_lower}"
            book_dir = os.path.join(version_dir, testament_folder, book_folder_name)
            os.makedirs(book_dir, exist_ok=True)

            for chapter_num, verses in chapters.items():
                verses.sort(key=lambda x: x[0])
                chapter_file = os.path.join(book_dir, f"chapter_{chapter_num:03d}.txt")
                with open(chapter_file, "w", encoding="utf-8") as f:
                    for verse_num, text in verses:
                        label = f"[{version_label} | {lang_label} | {testament_folder.upper()} | {pretty_name} | Chapter {chapter_num} | Verse {verse_num}]"
                        f.write(f"{label} {text}\n")
                total_chapters += 1

        # Write initial metadata.json
        import datetime
        meta = {
            "version": version.upper(),
            "name": name,
            "language": lang,
            "edition_year": dl.get("year"),
            "license": dl.get("license"),
            "publisher_source": dl.get("publisher_source", "eBible Corpus"),
            "source_url": url,
            "download_date": datetime.date.today().isoformat(),
        }
        with open(os.path.join(version_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        print(f"    Written: {total_chapters} chapters.")

    # Post-processors
    print("\n=== RUNNING POST-PROCESSORS ===")
    for script in ["update_metadata.py", "generate_status.py"]:
        path = os.path.join(script_dir, script)
        if os.path.exists(path):
            print(f"Running {script}...")
            subprocess.run(["python", path], cwd=base_dir, check=True)
        else:
            print(f"WARNING: {script} not found at {path}")

    print("\nDone. Run the test suite next:")
    print("    python tests/python/run_tests.py")


if __name__ == "__main__":
    main()
