import os
import re
import json

def run_test(bible_dir, test_dir):
    failures = []
    passes = 0
    fails = 0
    skips = 0
    fingerprint_log = []
    
    # Load reverse mappings
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
    
    # Reverse mapping of book names to abbreviation
    reverse_pretty = {v: k for k, v in pretty_book_names.items()}
    # Spacing overrides
    reverse_pretty["Esther Greek"] = "ESG"
    reverse_pretty["Wisdom"] = "WIS"
    reverse_pretty["Song of the Three Children"] = "S3Y"
    reverse_pretty["Apocalypse of Ezra"] = "EZA"
    reverse_pretty["Ekeziel"] = "EZK"
    
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
    
    nt_books = [
        "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", 
        "PHP", "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS", 
        "1PE", "2PE", "1JN", "2JN", "3JN", "JUD", "REV"
    ]
    
    all_books = list(pretty_book_names.keys())
    ot_books = [b for b in all_books if b not in nt_books]
    
    # Load fingerprints file
    json_path = os.path.join(test_dir, "bible_fingerprints", "kjv_asv_fingerprints.json")
    if not os.path.exists(json_path):
        failures.append(f"Fingerprint file not found: {json_path}")
        return 0, 1, failures
        
    with open(json_path, "r", encoding="utf-8") as f:
        cases = json.load(f)
        
    def check_match(expected, actual):
        has_god_lord = any(w in expected.lower() for w in ["lord", "god", "jehovah", "jah"])
        if has_god_lord:
            exp_search = expected.lower()
            act_search = actual.lower()
        else:
            exp_search = expected
            act_search = actual
            
        if "..." in exp_search:
            parts = [p.strip() for p in exp_search.split("...")]
            current_idx = 0
            for part in parts:
                idx = act_search.find(part, current_idx)
                if idx == -1:
                    return False
                current_idx = idx + len(part)
            return True
        else:
            return exp_search in act_search
            
    for case in cases:
        case_id = case.get("id")
        ref = case.get("reference")
        translations = case.get("translations", {})
        note = case.get("note", "")
        
        match = re.match(r"^(.+)\s+(\d+):(\d+)$", ref.strip())
        if not match:
            failures.append(f"Failed to parse reference: {ref}")
            fails += 1
            continue
            
        book_name, chapter_str, verse_str = match.groups()
        chapter_num = int(chapter_str)
        verse_num = int(verse_str)
        
        book_abbr = reverse_pretty.get(book_name)
        if not book_abbr:
            book_abbr = book_name[:3].upper()
            
        book_name_lower = book_mapping.get(book_abbr, book_name.lower())
        
        is_nt = book_abbr in nt_books
        testament = "nt" if is_nt else "ot"
        
        if is_nt:
            idx = nt_books.index(book_abbr) + 1
        else:
            idx = ot_books.index(book_abbr) + 1
            
        book_folder = f"{idx:02d}_{book_name_lower}"
        
        for trans, expected_info in translations.items():
            expected_contains = expected_info.get("expected_contains")
            trans_lower = trans.lower()
            trans_path = os.path.join(bible_dir, "english", trans_lower)
            
            if not os.path.exists(trans_path):
                continue
                
            chapter_file = os.path.join(trans_path, testament, book_folder, f"chapter_{chapter_num:03d}.txt")
            
            is_annotated_skip = False
            if note:
                note_lower = note.lower()
                if any(w in note_lower for w in ["omitted", "shifted", "missing", "limitation"]):
                    is_annotated_skip = True
                    
            if not os.path.exists(chapter_file):
                if is_annotated_skip:
                    log_line = f"[SKIP] #{case_id:<3} {ref:<18} {trans:<4} → Omitted/shifted in source (documented in case note): {note}"
                    fingerprint_log.append(log_line)
                    skips += 1
                else:
                    log_line = f"[FAIL] #{case_id:<3} {ref:<18} {trans:<4} → expected \"{expected_contains}\" — chapter not found"
                    failures.append(log_line)
                    fingerprint_log.append(log_line)
                    fails += 1
                continue
                
            try:
                with open(chapter_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                # Find the verse line
                verse_line = None
                for line in lines:
                    if f"Verse {verse_num}]" in line:
                        verse_line = line.strip()
                        break
                        
                if not verse_line:
                    if is_annotated_skip:
                        log_line = f"[SKIP] #{case_id:<3} {ref:<18} {trans:<4} → Omitted/shifted in source (documented in case note): {note}"
                        fingerprint_log.append(log_line)
                        skips += 1
                    else:
                        log_line = f"[FAIL] #{case_id:<3} {ref:<18} {trans:<4} → expected \"{expected_contains}\" — verse not found"
                        failures.append(log_line)
                        fingerprint_log.append(log_line)
                        fails += 1
                    continue
                    
                # Extract verse text
                match_text = re.match(r"^\[.*?\]\s*(.*)$", verse_line)
                verse_text = match_text.group(1).strip() if match_text else verse_line
                
                if check_match(expected_contains, verse_text):
                    log_line = f"[PASS] #{case_id:<3} {ref:<18} {trans:<4} → contains \"{expected_contains}\""
                    fingerprint_log.append(log_line)
                    passes += 1
                else:
                    log_line = f"[FAIL] #{case_id:<3} {ref:<18} {trans:<4} → expected \"{expected_contains}\" — not found"
                    failures.append(log_line)
                    fingerprint_log.append(log_line)
                    fails += 1
            except Exception as e:
                log_line = f"[FAIL] #{case_id:<3} {ref:<18} {trans:<4} → exception: {e}"
                failures.append(log_line)
                fingerprint_log.append(log_line)
                fails += 1
                
    return passes, fails, skips, failures, fingerprint_log
