import os
import re

def run_test(bible_dir):
    failures = []
    passes = 0
    fails = 0
    
    if not os.path.exists(bible_dir):
        return 0, 0, []
        
    pattern = re.compile(r"^\[([A-Z0-9_]+) \| ([A-Z]{2}) \| (OT|NT) \| ([^|]+) \| Chapter (\d+) \| Verse (\d+)\] (.*)$")
    
    for lang in os.listdir(bible_dir):
        lang_path = os.path.join(bible_dir, lang)
        if not os.path.isdir(lang_path):
            continue
            
        for ver in os.listdir(lang_path):
            ver_path = os.path.join(lang_path, ver)
            if not os.path.isdir(ver_path):
                continue
                
            for testament in ["ot", "nt"]:
                test_path = os.path.join(ver_path, testament)
                if not os.path.exists(test_path):
                    continue
                    
                for book in os.listdir(test_path):
                    book_path = os.path.join(test_path, book)
                    if not os.path.isdir(book_path):
                        continue
                        
                    for chapter in os.listdir(book_path):
                        chapter_file = os.path.join(book_path, chapter)
                        if not os.path.isfile(chapter_file) or not chapter.endswith(".txt"):
                            continue
                            
                        try:
                            with open(chapter_file, "r", encoding="utf-8") as f:
                                lines = f.readlines()
                                
                            if not lines:
                                failures.append(f"[{lang}/{ver}] Chapter file is empty: {testament}/{book}/{chapter}")
                                fails += 1
                                continue
                                
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
                                    passes += 1
                        except Exception as e:
                            failures.append(f"[{lang}/{ver}] Failed to read chapter file {testament}/{book}/{chapter}: {e}")
                            fails += 1
                            
    return passes, fails, failures
