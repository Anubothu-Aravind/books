import os
import re

def run_test(bible_dir):
    failures = []
    passes = 0
    fails = 0
    
    if not os.path.exists(bible_dir):
        failures.append("bible/ directory does not exist")
        return 0, 1, failures
        
    for lang in os.listdir(bible_dir):
        lang_path = os.path.join(bible_dir, lang)
        if not os.path.isdir(lang_path):
            continue
            
        for ver in os.listdir(lang_path):
            ver_path = os.path.join(lang_path, ver)
            if not os.path.isdir(ver_path):
                continue
                
            # Check metadata.json
            meta_file = os.path.join(ver_path, "metadata.json")
            if not os.path.exists(meta_file):
                failures.append(f"[{lang}/{ver}] Missing metadata.json")
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
                    
                for book in os.listdir(test_path):
                    book_path = os.path.join(test_path, book)
                    if not os.path.isdir(book_path):
                        continue
                        
                    # Book folders follow NN_bookname format
                    if not re.match(r"^\d{2}_\w+$", book):
                        failures.append(f"[{lang}/{ver}] Book folder '{testament}/{book}' does not match format 'NN_bookname'")
                        fails += 1
                    else:
                        passes += 1
                        
                    # Chapter files follow chapter_NN.txt format (allow 2 or 3 digits for books like Psalms)
                    for chapter in os.listdir(book_path):
                        chapter_path = os.path.join(book_path, chapter)
                        if not os.path.isfile(chapter_path):
                            continue
                        if not re.match(r"^chapter_\d{3}\.txt$", chapter):
                            failures.append(f"[{lang}/{ver}] Chapter file '{testament}/{book}/{chapter}' does not match format 'chapter_NNN.txt'")
                            fails += 1
                        else:
                            passes += 1
                            
    return passes, fails, failures
