import os
import re

def run_test(bible_dir):
    failures = []
    passes = 0
    fails = 0
    
    # We will use the canonical book lists to check book folder names
    nt_books = [
        "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", 
        "PHP", "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS", 
        "1PE", "2PE", "1JN", "2JN", "3JN", "JUD", "REV"
    ]
    
    # Standard Protestant OT books in order of appearance in vref.txt
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

    # Known allowed missing chapters due to canon/translation variants
    allowed_missing_chapters = {
        "english/asv": {"42_esther_greek": {2, 6, 7, 9}},
        "english/kjv": {"42_esther_greek": {2, 6, 7, 9}},
        "greek/lxx": {"20_proverbs": {30}}
    }

    if not os.path.exists(bible_dir):
        failures.append("bible/ directory does not exist")
        return 0, 1, failures

    for lang in os.listdir(bible_dir):
        lang_path = os.path.join(bible_dir, lang)
        if not os.path.isdir(lang_path):
            continue
            
        # Recursively find all directories containing metadata.json
        version_paths = []
        for root, dirs, files in os.walk(lang_path):
            if "metadata.json" in files:
                version_paths.append(root)

        for ver_path in sorted(version_paths):
            ver = os.path.relpath(ver_path, lang_path).replace("\\", "/")
            version_key = f"{lang}/{ver}"
            
            # Check metadata.json exists
            meta_file = os.path.join(ver_path, "metadata.json")
            if not os.path.exists(meta_file):
                failures.append(f"[{lang}/{ver}] Missing metadata.json")
                fails += 1
            else:
                passes += 1
                
            # Check that only allowed files/folders exist under the version directory
            allowed_version_items = {"ot", "nt", "metadata.json"}
            for item in os.listdir(ver_path):
                if item not in allowed_version_items:
                    failures.append(f"[{lang}/{ver}] Unexpected item in version directory: {item}")
                    fails += 1
                else:
                    passes += 1
                    
            # Check ot and nt folders
            ot_path = os.path.join(ver_path, "ot")
            nt_path = os.path.join(ver_path, "nt")
            if not os.path.exists(ot_path) and not os.path.exists(nt_path):
                failures.append(f"[{lang}/{ver}] Neither ot/ nor nt/ folders exist")
                fails += 1
            else:
                passes += 1
                
            # Check book and chapter structures
            for testament in ["ot", "nt"]:
                test_path = os.path.join(ver_path, testament)
                if not os.path.exists(test_path):
                    continue
                    
                book_folders = []
                for book in os.listdir(test_path):
                    book_path = os.path.join(test_path, book)
                    if os.path.isdir(book_path):
                        book_folders.append(book)
                    else:
                        failures.append(f"[{lang}/{ver}] Non-directory item found in testament folder: {testament}/{book}")
                        fails += 1
                        
                # Verify book folder prefixes and sorting
                last_prefix = 0
                canonical_books = nt_books if testament == "nt" else ot_books
                
                for book in sorted(book_folders):
                    book_path = os.path.join(test_path, book)
                    match = re.match(r"^(\d{2})_(\w+)$", book)
                    if not match:
                        failures.append(f"[{lang}/{ver}] Book folder '{testament}/{book}' does not match format 'NN_bookname'")
                        fails += 1
                        continue
                    else:
                        passes += 1
                        
                    prefix_str, book_name = match.groups()
                    prefix_val = int(prefix_str)
                    
                    # Prefixes must be strictly increasing
                    if prefix_val <= last_prefix:
                        failures.append(f"[{lang}/{ver}] Book folder '{testament}/{book}' prefix is not strictly increasing (last: {last_prefix}, current: {prefix_val})")
                        fails += 1
                    else:
                        passes += 1
                    last_prefix = prefix_val
                    
                    # Verify book_name matches the canonical book name for this prefix index
                    expected_idx = prefix_val - 1
                    if expected_idx < len(canonical_books):
                        canonical_abbr = canonical_books[expected_idx]
                        expected_name = book_mapping.get(canonical_abbr)
                        if book_name != expected_name:
                            failures.append(f"[{lang}/{ver}] Book folder '{testament}/{book}' has name mismatch: Expected '{expected_name}', got '{book_name}'")
                            fails += 1
                        else:
                            passes += 1
                    else:
                        failures.append(f"[{lang}/{ver}] Book folder '{testament}/{book}' has prefix index out of bounds: {prefix_val}")
                        fails += 1
                        
                    # Check chapter files inside the book folder
                    chapters = []
                    unexpected_files = []
                    for item in os.listdir(book_path):
                        item_path = os.path.join(book_path, item)
                        if os.path.isfile(item_path):
                            ch_match = re.match(r"^chapter_(\d{3})\.txt$", item)
                            if ch_match:
                                ch_num = int(ch_match.group(1))
                                chapters.append(ch_num)
                                
                                # Verify no empty files
                                if os.path.getsize(item_path) == 0:
                                    failures.append(f"[{lang}/{ver}] Chapter file is empty: {testament}/{book}/{item}")
                                    fails += 1
                                else:
                                    passes += 1
                            else:
                                unexpected_files.append(item)
                                failures.append(f"[{lang}/{ver}] Chapter file '{testament}/{book}/{item}' does not match format 'chapter_NNN.txt'")
                                fails += 1
                        else:
                            failures.append(f"[{lang}/{ver}] Non-file item found in book folder: {testament}/{book}/{item}")
                            fails += 1
                            
                    if unexpected_files:
                        failures.append(f"[{lang}/{ver}] Unexpected files in {testament}/{book}: {unexpected_files}")
                        fails += 1
                        
                    # Verify contiguous chapter files (from 1 to max_chapter)
                    if chapters:
                        max_chapter = max(chapters)
                        expected_chapters = set(range(1, max_chapter + 1))
                        actual_chapters = set(chapters)
                        missing_chapters = expected_chapters - actual_chapters
                        
                        # Apply version-specific allowed missing chapters
                        version_allowed_gaps = allowed_missing_chapters.get(version_key, {}).get(book, set())
                        missing_chapters = missing_chapters - version_allowed_gaps
                        
                        if missing_chapters:
                            failures.append(f"[{lang}/{ver}] Book '{testament}/{book}' has missing chapters: {sorted(list(missing_chapters))}")
                            fails += 1
                        else:
                            passes += 1
                            
    return passes, fails, failures
