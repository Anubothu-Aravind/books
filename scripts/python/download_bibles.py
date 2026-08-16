import os
import shutil
import urllib.request
import json
import re
import datetime

# Resolve the repository root dynamically (two levels up from scripts/python/)
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(script_dir))
bible_dir = os.path.join(base_dir, "bible")

# 1. Clean up existing directories as requested
print("--- CLEANING UP DIRECTORIES ---")

# Delete teachings/sample-pastor/
sample_pastor_dir = os.path.join(base_dir, "teachings", "sample-pastor")
if os.path.exists(sample_pastor_dir):
    print(f"Deleting sample pastor directory: {sample_pastor_dir}")
    shutil.rmtree(sample_pastor_dir)

# Delete version folders under bible/<lang>/*
if os.path.exists(bible_dir):
    for lang in os.listdir(bible_dir):
        lang_path = os.path.join(bible_dir, lang)
        if os.path.isdir(lang_path):
            print(f"Cleaning subfolders in language folder: {lang_path}")
            for item in os.listdir(lang_path):
                item_path = os.path.join(lang_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                elif os.path.isfile(item_path):
                    os.remove(item_path)

print("Cleanup finished!")

# 2. Download and parse vref.txt
vref_url = "https://raw.githubusercontent.com/BibleNLP/ebible/main/metadata/vref.txt"
print(f"Downloading vref.txt from: {vref_url}")
req = urllib.request.Request(
    vref_url, 
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
)
with urllib.request.urlopen(req) as response:
    vref_content = response.read().decode('utf-8')
vref_lines = vref_content.splitlines()
print(f"Loaded vref.txt with {len(vref_lines)} references.")

# Standard lists for categorization and ordering
nt_books = [
    "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", 
    "PHP", "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS", 
    "1PE", "2PE", "1JN", "2JN", "3JN", "JUD", "REV"
]

# Build ot_books dynamically based on the exact order of appearance in vref.txt
ot_books = []
for ref in vref_lines:
    match = re.match(r"^([\w\d]+)\s+", ref.strip())
    if match:
        b = match.group(1)
        if b not in nt_books and b not in ot_books:
            ot_books.append(b)

# Book mappings
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
    # Apocrypha
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
    # Apocrypha
    "TOB": "Tobit", "JDT": "Judith", "ESG": "Esther (Greek)", "WIS": "Wisdom of Solomon",
    "SIR": "Sirach", "BAR": "Baruch", "LJE": "Letter of Jeremiah", "S3Y": "Song of the Three Holy Children",
    "SUS": "Susanna", "BEL": "Bel and the Dragon", "1MA": "1 Maccabees", "2MA": "2 Maccabees",
    "3MA": "3 Maccabees", "4MA": "4 Maccabees", "1ES": "1 Esdras", "2ES": "2 Esdras",
    "MAN": "Prayer of Manasseh", "PS2": "Psalm 151", "ODA": "Odes", "PSS": "Psalms of Solomon",
    "EZA": "Apocalypse of Ezra", "JUB": "Jubilees", "ENO": "Enoch"
}

lang_codes = {
    "english": "en",
    "telugu": "te",
    "hindi": "hi",
    "tamil": "ta",
    "kannada": "kn",
    "malayalam": "ml",
    "bengali": "bn",
    "marathi": "mr",
    "gujarati": "gu",
    "punjabi": "pa",
    "urdu": "ur",
    "hebrew": "he",
    "greek": "el",
    "arabic": "ar"
}

# Define target downloads with correct eBible corpus filenames
downloads = [
    {"lang": "english", "version": "kjv", "filename": "eng-engkjvcpb.txt", "name": "King James Version", "year": 1611, "ot": 39, "nt": 27, "license": "Public Domain"},
    {"lang": "english", "version": "asv", "filename": "eng-engasvbt.txt", "name": "American Standard Version", "year": 1901, "ot": 39, "nt": 27, "license": "Public Domain"},
    {"lang": "english", "version": "web", "filename": "eng-engwebu.txt", "name": "World English Bible", "year": 2000, "ot": 39, "nt": 27, "license": "Public Domain / CC0"},
    {"lang": "english", "version": "ylt", "filename": "eng-engylt.txt", "name": "Young's Literal Translation", "year": 1862, "ot": 39, "nt": 27, "license": "Public Domain"},
    {"lang": "english", "version": "darby", "filename": "eng-engDBY.txt", "name": "Darby Bible", "year": 1890, "ot": 39, "nt": 27, "license": "Public Domain"},
    {"lang": "english", "version": "bbe", "filename": "eng-engBBE.txt", "name": "Bible in Basic English", "year": 1949, "ot": 39, "nt": 27, "license": "Public Domain"},
    {"lang": "english", "version": "dra", "filename": "eng-engDRA.txt", "name": "Douay-Rheims Bible", "year": 1899, "ot": 39, "nt": 27, "license": "Public Domain"},
    {"lang": "english", "version": "oeb", "filename": "eng-engoebcw.txt", "name": "Open English Bible", "year": 2010, "ot": 39, "nt": 27, "license": "Creative Commons Zero (CC0)"},
    {"lang": "telugu", "version": "irv", "filename": "tel-tel2017.txt", "name": "Indian Revised Version - Telugu", "year": 2019, "ot": 39, "nt": 27, "license": "CC BY-SA 4.0"},
    {"lang": "hindi", "version": "irv", "filename": "hin-hin2017.txt", "name": "Indian Revised Version - Hindi", "year": 2019, "ot": 39, "nt": 27, "license": "CC BY-SA 4.0"},
    {"lang": "tamil", "version": "irv", "filename": "tam-tam2017.txt", "name": "Indian Revised Version - Tamil", "year": 2019, "ot": 39, "nt": 27, "license": "CC BY-SA 4.0"},
    {"lang": "kannada", "version": "irv", "filename": "kan-kan2017.txt", "name": "Indian Revised Version - Kannada", "year": 2019, "ot": 39, "nt": 27, "license": "CC BY-SA 4.0"},
    {"lang": "malayalam", "version": "irv", "filename": "mal-mal2015.txt", "name": "Indian Revised Version - Malayalam", "year": 2019, "ot": 39, "nt": 27, "license": "CC BY-SA 4.0"},
    {"lang": "bengali", "version": "irv", "filename": "ben-benirv.txt", "name": "Indian Revised Version - Bengali", "year": 2019, "ot": 39, "nt": 27, "license": "CC BY-SA 4.0"},
    {"lang": "marathi", "version": "irv", "filename": "mar-mar.txt", "name": "Indian Revised Version - Marathi", "year": 2019, "ot": 39, "nt": 27, "license": "CC BY-SA 4.0"},
    {"lang": "gujarati", "version": "irv", "filename": "guj-guj2017.txt", "name": "Indian Revised Version - Gujarati", "year": 2019, "ot": 39, "nt": 27, "license": "CC BY-SA 4.0"},
    {"lang": "punjabi", "version": "irv", "filename": "pan-pan.txt", "name": "Indian Revised Version - Punjabi", "year": 2019, "ot": 39, "nt": 27, "license": "CC BY-SA 4.0"},
    {"lang": "urdu", "version": "irv", "filename": "urd-urd.txt", "name": "Indian Revised Version - Urdu", "year": 2019, "ot": 39, "nt": 27, "license": "CC BY-SA 4.0"},
    {"lang": "hebrew", "version": "wlc", "filename": "hbo-hboWLC.txt", "name": "Westminster Leningrad Codex", "year": 1008, "ot": 39, "nt": 0, "license": "Public Domain"},
    {"lang": "greek", "version": "lxx", "filename": "grc-grcbrent.txt", "name": "Septuagint", "year": -200, "ot": 46, "nt": 0, "license": "Public Domain"}
]

results = []

def write_chapters_and_metadata(lang, version, grouped, metadata_info):
    version_dir = os.path.join(bible_dir, lang, version)
    os.makedirs(version_dir, exist_ok=True)
    
    version_label = version.upper()
    lang_label = lang_codes.get(lang, "unknown").upper()
    
    total_chapters = 0
    
    for book_abbr, chapters in grouped.items():
        is_nt = book_abbr in nt_books
        testament_folder = "nt" if is_nt else "ot"
        
        book_name_lower = book_mapping.get(book_abbr, book_abbr.lower())
        pretty_name = pretty_book_names.get(book_abbr, book_abbr.title())
        
        # Determine zero-padded prefix based on canonical list index
        if is_nt:
            prefix_idx = nt_books.index(book_abbr) + 1
        else:
            prefix_idx = ot_books.index(book_abbr) + 1
            
        book_folder_name = f"{prefix_idx:02d}_{book_name_lower}"
        book_dir = os.path.join(version_dir, testament_folder, book_folder_name)
        os.makedirs(book_dir, exist_ok=True)
        
        for chapter_num, verses in chapters.items():
            verses.sort(key=lambda x: x[0])
            chapter_file = os.path.join(book_dir, f"chapter_{chapter_num:03d}.txt")
            
            with open(chapter_file, "w", encoding="utf-8") as f:
                for verse_num, text in verses:
                    # Label format: [VERSION | LANG_CODE | OT/NT | Book Name | Chapter N | Verse N] Verse Text
                    label = f"[{version_label} | {lang_label} | {testament_folder.upper()} | {pretty_name} | Chapter {chapter_num} | Verse {verse_num}]"
                    f.write(f"{label} {text}\n")
            total_chapters += 1
            
    # Write metadata.json
    meta_path = os.path.join(version_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata_info, f, indent=2, ensure_ascii=False)
        
    return total_chapters

print("\n--- STARTING SEQUENTIAL BIBLE DOWNLOADS & SPLITS (NEW FORMAT) ---")

# Process the standard 20 eBible versions
for dl in downloads:
    lang = dl["lang"]
    version = dl["version"]
    filename = dl["filename"]
    url = f"https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/{filename}"
    
    print(f"\nProcessing {lang}/{version} from URL: {url}")
    
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            
        lines = content.splitlines()
        has_data = any(line.strip() for line in lines)
        if not has_data:
            raise ValueError("Downloaded file is empty or contains no verse data")
            
        grouped = {}
        max_idx = min(len(lines), len(vref_lines))
        
        for i in range(max_idx):
            verse_text = lines[i].strip()
            if not verse_text:
                continue
                
            ref = vref_lines[i].strip()
            match = re.match(r"^([\w\d]+)\s+(\d+):(\d+)$", ref)
            if not match:
                continue
                
            book_abbr, chapter_str, verse_str = match.groups()
            chapter_num = int(chapter_str)
            verse_num = int(verse_str)
            
            if book_abbr not in grouped:
                grouped[book_abbr] = {}
            if chapter_num not in grouped[book_abbr]:
                grouped[book_abbr][chapter_num] = []
                
            grouped[book_abbr][chapter_num].append((verse_num, verse_text))
            
        if not grouped:
            raise ValueError("No valid verses parsed from file")
            
        metadata = {
            "name": dl["name"],
            "version": version.upper(),
            "language": lang.capitalize(),
            "language_code": lang_codes.get(lang, "unknown"),
            "edition_year": dl["year"],
            "publisher_source": "eBible Corpus",
            "license": dl["license"],
            "source_url": url,
            "download_date": datetime.date.today().strftime("%Y-%m-%d"),
            "notes": "Collected and split canonically into ot/nt folders with labeled verses."
        }
        
        total_ch = write_chapters_and_metadata(lang, version, grouped, metadata)
        print(f"SUCCESS: Saved {lang}/{version} -> {total_ch} chapters across {len(grouped)} books")
        results.append({"lang": lang, "version": version, "status": "Success", "chapters": total_ch})
        
    except Exception as e:
        print(f"FAILED: {lang}/{version} -> {str(e)}")
        results.append({"lang": lang, "version": version, "status": "Failed", "error": str(e)})


# --- PROCESS GREEK SBLGNT ---
print("\n--- PROCESSING GREEK SBLGNT ---")
sblgnt_files = [
    "Matt.txt", "Mark.txt", "Luke.txt", "John.txt", "Acts.txt",
    "Rom.txt", "1Cor.txt", "2Cor.txt", "Gal.txt", "Eph.txt",
    "Phil.txt", "Col.txt", "1Thess.txt", "2Thess.txt", "1Tim.txt",
    "2Tim.txt", "Titus.txt", "Phlm.txt", "Heb.txt", "Jas.txt",
    "1Pet.txt", "2Pet.txt", "1John.txt", "2John.txt", "3John.txt",
    "Jude.txt", "Rev.txt"
]

sblgnt_mapping_reverse = {
    "Matt": "MAT", "Mark": "MRK", "Luke": "LUK", "John": "JHN", "Acts": "ACT",
    "Rom": "ROM", "1Cor": "1CO", "2Cor": "2CO", "Gal": "GAL", "Eph": "EPH",
    "Phil": "PHP", "Col": "COL", "1Thess": "1TH", "2Thess": "2TH", "1Tim": "1TI",
    "2Tim": "2TI", "Titus": "TIT", "Phlm": "PHM", "Heb": "HEB", "Jas": "JAS",
    "1Pet": "1PE", "2Pet": "2PE", "1John": "1JN", "2John": "2JN", "3John": "3JN",
    "Jude": "JUD", "Rev": "REV"
}

sblgnt_grouped = {}
sbl_success = True

for sfile in sblgnt_files:
    url = f"https://raw.githubusercontent.com/Faithlife/SBLGNT/master/data/sblgnt/text/{sfile}"
    print(f"Fetching {sfile} from SBLGNT repo...")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            
        lines = content.splitlines()
        for line in lines:
            line = line.strip()
            match = re.match(r"^([\w\d]+)\s+(\d+):(\d+)\t(.*)$", line)
            if not match:
                continue
                
            book_abbr_sbl, chapter_str, verse_str, verse_text = match.groups()
            chapter_num = int(chapter_str)
            verse_num = int(verse_str)
            
            book_abbr = sblgnt_mapping_reverse.get(book_abbr_sbl, book_abbr_sbl)
            
            if book_abbr not in sblgnt_grouped:
                sblgnt_grouped[book_abbr] = {}
            if chapter_num not in sblgnt_grouped[book_abbr]:
                sblgnt_grouped[book_abbr][chapter_num] = []
                
            sblgnt_grouped[book_abbr][chapter_num].append((verse_num, verse_text))
            
    except Exception as e:
        print(f"Error fetching {sfile}: {e}")
        sbl_success = False
        break

if sbl_success and sblgnt_grouped:
    metadata = {
        "name": "SBL Greek New Testament",
        "version": "SBLGNT",
        "language": "Greek",
        "language_code": "el",
        "edition_year": 2010,
        "publisher_source": "Society of Biblical Literature / Faithlife",
        "license": "SBLGNT License",
        "source_url": "https://raw.githubusercontent.com/Faithlife/SBLGNT/master/data/sblgnt/text/",
        "download_date": datetime.date.today().strftime("%Y-%m-%d"),
        "notes": "SBLGNT text fetched book-by-book from Faithlife GitHub repository."
    }
    total_ch = write_chapters_and_metadata("greek", "sblgnt", sblgnt_grouped, metadata)
    print(f"SUCCESS: Saved greek/sblgnt -> {total_ch} chapters across {len(sblgnt_grouped)} books")
    results.append({"lang": "greek", "version": "sblgnt", "status": "Success", "chapters": total_ch})
else:
    print("FAILED to process Greek SBLGNT.")
    results.append({"lang": "greek", "version": "sblgnt", "status": "Failed", "error": "Download/parsing error"})


# --- PROCESS ARABIC VANDYKE/NAV ---
print("\n--- PROCESSING ARABIC VANDYKE ---")
urls = [
    "https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/arb-arb.txt",
    "https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/arb-arbnav.txt"
]

arabic_content = ""
selected_url = ""
name = "Smith & Van Dyke Arabic Bible"
license_info = "Public Domain"

for url in urls:
    print(f"Trying to fetch Arabic Bible from: {url}")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            
        lines = content.splitlines()
        has_data = any(line.strip() for line in lines)
        if has_data:
            arabic_content = content
            selected_url = url
            if "arbnav" in url:
                name = "New Arabic Version (Book of Life)"
                license_info = "Copyright © 1988, 1997, 2012 Biblica, Inc."
            print(f"SUCCESS: Fetched non-empty text from {url}")
            break
    except Exception as e:
        print(f"Failed to fetch from {url}: {e}")

if arabic_content:
    lines = arabic_content.splitlines()
    grouped = {}
    max_idx = min(len(lines), len(vref_lines))
    
    for i in range(max_idx):
        verse_text = lines[i].strip()
        if not verse_text:
            continue
            
        ref = vref_lines[i].strip()
        match = re.match(r"^([\w\d]+)\s+(\d+):(\d+)$", ref)
        if not match:
            continue
            
        book_abbr, chapter_str, verse_str = match.groups()
        chapter_num = int(chapter_str)
        verse_num = int(verse_str)
        
        if book_abbr not in grouped:
            grouped[book_abbr] = {}
        if chapter_num not in grouped[book_abbr]:
            grouped[book_abbr][chapter_num] = []
            
        grouped[book_abbr][chapter_num].append((verse_num, verse_text))
        
    metadata = {
        "name": name,
        "version": "VANDYKE" if "arb-arb.txt" in selected_url else "NAV",
        "language": "Arabic",
        "language_code": "ar",
        "edition_year": 1865 if "arb-arb.txt" in selected_url else 2012,
        "publisher_source": "eBible Corpus",
        "license": license_info,
        "source_url": selected_url,
        "download_date": datetime.date.today().strftime("%Y-%m-%d"),
        "notes": f"Arabic translation split canonically. Source: {selected_url}"
    }
    
    total_ch = write_chapters_and_metadata("arabic", "vandyke", grouped, metadata)
    print(f"SUCCESS: Saved arabic/vandyke -> {total_ch} chapters across {len(grouped)} books")
    results.append({"lang": "arabic", "version": "vandyke", "status": "Success", "chapters": total_ch})
else:
    print("FAILED to process Arabic.")
    results.append({"lang": "arabic", "version": "vandyke", "status": "Failed", "error": "No non-empty source found"})

# Print summary
print("\n--- DOWNLOAD AND SPLIT SUMMARY ---")
for res in results:
    status_str = f"{res['status']}"
    if res['status'] == "Success":
        status_str += f" ({res.get('chapters')} chapters)"
    else:
        status_str += f" ({res.get('error')})"
    print(f"  {res['lang']}/{res['version']} -> {status_str}")

# Save status to a json for reporting
summary_path = os.path.join(base_dir, "_meta", "download_summary.json")
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

# Run post-processing to generate complete metadata and fingerprint checksums
try:
    print("\n--- RUNNING POST-PROCESS METADATA AND SNAPSHOT CHECKSUMS ---")
    import update_metadata
    update_metadata.main()
except Exception as e:
    print(f"Error running metadata update post-processor: {e}")

print("\nProcessing complete!")
