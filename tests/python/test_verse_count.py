import os
import re

def run_test(bible_dir):
    failures = []
    passes = 0
    fails = 0
    
    if not os.path.exists(bible_dir):
        return 0, 0, []
        
    # Standard Protestant Bible book counts:
    # Genesis: 1533 verses
    # Psalms: 2461 verses
    # Matthew: 1071 verses
    # Revelation: 404 verses
    target_counts = {
        "genesis": 1533,
        "psalms": 2461,
        "matthew": 1071,
        "revelation": 404
    }
    
    for lang in os.listdir(bible_dir):
        lang_path = os.path.join(bible_dir, lang)
        if not os.path.isdir(lang_path):
            continue
            
        for ver in os.listdir(lang_path):
            ver_path = os.path.join(lang_path, ver)
            if not os.path.isdir(ver_path):
                continue
                
            # Read metadata to check how many books it lists. SBLGNT has only NT, Hebrew WLC only OT.
            # Greek LXX has apocrypha books that might change OT counts, but we target book-level counts.
            for testament in ["ot", "nt"]:
                test_path = os.path.join(ver_path, testament)
                if not os.path.exists(test_path):
                    continue
                    
                for book in os.listdir(test_path):
                    book_path = os.path.join(test_path, book)
                    if not os.path.isdir(book_path):
                        continue
                        
                    # Extract book name from folder (e.g., 01_genesis -> genesis)
                    book_name = book.split("_", 1)[1] if "_" in book else book
                    if book_name not in target_counts:
                        continue
                        
                    expected_verses = target_counts[book_name]
                    actual_verses = 0
                    
                    for chapter in os.listdir(book_path):
                        chapter_file = os.path.join(book_path, chapter)
                        if not os.path.isfile(chapter_file) or not chapter.endswith(".txt"):
                            continue
                            
                        try:
                            with open(chapter_file, "r", encoding="utf-8") as f:
                                actual_verses += len(f.readlines())
                        except Exception as e:
                            failures.append(f"[{lang}/{ver}] Failed to read {testament}/{book}/{chapter} for verse counting: {e}")
                            
                    # SBLGNT (New Testament only) or WLC (Hebrew Old Testament only) can be checked safely.
                    # Note: YLT, KJV, DRA might have slightly different versification (e.g. Psalms numbering differences).
                    # We flag deviations as failures/warnings.
                    if abs(actual_verses - expected_verses) > 5:
                        failures.append(f"[{lang}/{ver}] {book_name.capitalize()} verse count deviation: Expected {expected_verses}, got {actual_verses} (outside tolerance ±5)")
                        fails += 1
                    else:
                        passes += 1
                        
    return passes, fails, failures
