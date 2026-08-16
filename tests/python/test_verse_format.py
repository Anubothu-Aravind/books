import os
import re

def run_test(bible_dir):
    failures = []
    passes = 0
    fails = 0
    
    if not os.path.exists(bible_dir):
        return 0, 0, []
        
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

    nt_books = [
        "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", 
        "PHP", "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS", 
        "1PE", "2PE", "1JN", "2JN", "3JN", "JUD", "REV"
    ]
    
    ot_books = [
        "GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT", "1SA", "2SA",
        "1KI", "2KI", "1CH", "2CH", "EZR", "NEH", "EST", "JOB", "PSA", "PRO",
        "ECC", "SNG", "ISA", "JER", "LAM", "EZK", "DAN", "HOS", "JOL", "AMO",
        "OBA", "JON", "MIC", "NAM", "HAB", "ZEP", "HAG", "ZEC", "MAL",
        # Apocrypha
        "TOB", "JDT", "ESG", "WIS", "SIR", "BAR", "LJE", "S3Y", "SUS", "BEL",
        "1MA", "2MA", "3MA", "4MA", "1ES", "2ES", "MAN", "PS2", "ODA", "PSS",
        "EZA", "JUB", "ENO"
    ]

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

    pattern = re.compile(r"^\[([A-Z0-9_]+) \| ([A-Z]{2}) \| (OT|NT) \| ([^|]+) \| Chapter (\d+) \| Verse (\d+)\] (.*)$")
    
    for lang in os.listdir(bible_dir):
        lang_path = os.path.join(bible_dir, lang)
        if not os.path.isdir(lang_path):
            continue
            
        lang_code = lang_codes.get(lang, "unknown").upper()
            
        for ver in os.listdir(lang_path):
            ver_path = os.path.join(lang_path, ver)
            if not os.path.isdir(ver_path):
                continue
                
            version_label = ver.upper()
                
            for testament in ["ot", "nt"]:
                test_path = os.path.join(ver_path, testament)
                if not os.path.exists(test_path):
                    continue
                    
                canonical_books = nt_books if testament == "nt" else ot_books
                    
                for book in os.listdir(test_path):
                    book_path = os.path.join(test_path, book)
                    if not os.path.isdir(book_path):
                        continue
                        
                    # Extract book pretty name dynamically from folder index
                    book_folder_match = re.match(r"^(\d{2})_(\w+)$", book)
                    if not book_folder_match:
                        continue
                    prefix_val = int(book_folder_match.group(1))
                    
                    expected_abbr = canonical_books[prefix_val - 1] if (prefix_val - 1) < len(canonical_books) else None
                    expected_pretty_book = pretty_book_names.get(expected_abbr, "").lower()
                    
                    for chapter in os.listdir(book_path):
                        chapter_file = os.path.join(book_path, chapter)
                        if not os.path.isfile(chapter_file) or not chapter.endswith(".txt"):
                            continue
                            
                        # Extract chapter number from file name
                        ch_match = re.match(r"^chapter_(\d{3})\.txt$", chapter)
                        if not ch_match:
                            continue
                        expected_chapter_num = int(ch_match.group(1))
                            
                        try:
                            with open(chapter_file, "r", encoding="utf-8") as f:
                                lines = f.readlines()
                                
                            if not lines:
                                failures.append(f"[{lang}/{ver}] Chapter file is empty: {testament}/{book}/{chapter}")
                                fails += 1
                                continue
                                
                            last_verse = 0
                            for line_idx, line in enumerate(lines):
                                line_str = line.strip()
                                if not line_str:
                                    failures.append(f"[{lang}/{ver}] Blank line found in {testament}/{book}/{chapter} at line {line_idx+1}")
                                    fails += 1
                                    continue
                                    
                                match = pattern.match(line_str)
                                if not match:
                                    failures.append(f"[{lang}/{ver}] Invalid verse format in {testament}/{book}/{chapter} at line {line_idx+1}: {line_str}")
                                    fails += 1
                                else:
                                    label_ver, label_lang, label_testament, label_book, label_chapter, label_verse, label_text = match.groups()
                                    
                                    # 1. Complete Tuple Validations against Folder Path
                                    
                                    # Version check
                                    # Note: SBL Greek New Testament abbreviation is SBLGNT, folder is sblgnt, matches ver.upper()
                                    # Smith & Van Dyke Arabic version is VANDYKE or NAV on disk, folder is vandyke.
                                    # Let's check matching upper vs upper.
                                    if label_ver.upper() != version_label:
                                        failures.append(f"[{lang}/{ver}] Version label mismatch in {testament}/{book}/{chapter} at line {line_idx+1}: bracket '{label_ver}', path '{version_label}'")
                                        fails += 1
                                    else:
                                        passes += 1
                                        
                                    # Language check
                                    if label_lang.upper() != lang_code:
                                        failures.append(f"[{lang}/{ver}] Language label mismatch in {testament}/{book}/{chapter} at line {line_idx+1}: bracket '{label_lang}', expected '{lang_code}'")
                                        fails += 1
                                    else:
                                        passes += 1
                                        
                                    # Testament check
                                    if label_testament.upper() != testament.upper():
                                        failures.append(f"[{lang}/{ver}] Testament label mismatch in {testament}/{book}/{chapter} at line {line_idx+1}: bracket '{label_testament}', expected '{testament.upper()}'")
                                        fails += 1
                                    else:
                                        passes += 1
                                        
                                    # Book name check (case-insensitive)
                                    if label_book.strip().lower() != expected_pretty_book:
                                        failures.append(f"[{lang}/{ver}] Book label mismatch in {testament}/{book}/{chapter} at line {line_idx+1}: bracket '{label_book}', expected pretty name '{expected_pretty_book}'")
                                        fails += 1
                                    else:
                                        passes += 1
                                        
                                    # Chapter check
                                    if int(label_chapter) != expected_chapter_num:
                                        failures.append(f"[{lang}/{ver}] Chapter label mismatch in {testament}/{book}/{chapter} at line {line_idx+1}: bracket '{label_chapter}', expected '{expected_chapter_num}'")
                                        fails += 1
                                    else:
                                        passes += 1
                                        
                                    # 2. Verse Contiguity Check (must be strictly increasing)
                                    verse_num = int(label_verse)
                                    if verse_num <= last_verse:
                                        failures.append(f"[{lang}/{ver}] Verse number not strictly increasing in {testament}/{book}/{chapter} at line {line_idx+1}: current {verse_num}, last {last_verse}")
                                        fails += 1
                                    else:
                                        passes += 1
                                    last_verse = verse_num
                                    
                        except Exception as e:
                            failures.append(f"[{lang}/{ver}] Failed to read chapter file {testament}/{book}/{chapter}: {e}")
                            fails += 1
                            
    return passes, fails, failures
