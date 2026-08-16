import os
import re

def run_test(bible_dir):
    failures = []
    passes = 0
    fails = 0
    
    # We will test KJV and ASV if they are present on disk
    # Checks:
    # 1. KJV Genesis 1:1
    # 2. KJV John 3:16
    # 3. ASV Genesis 1:1
    
    # helper function to parse verse text from line
    def extract_text(line):
        match = re.match(r"^\[.*?\]\s*(.*)$", line.strip())
        if match:
            return match.group(1).strip()
        return line.strip()

    # KJV Checks
    kjv_path = os.path.join(bible_dir, "english", "kjv")
    if os.path.exists(kjv_path):
        # Genesis 1:1 (OT)
        gen_1_1 = os.path.join(kjv_path, "ot", "01_genesis", "chapter_001.txt")
        if os.path.exists(gen_1_1):
            try:
                with open(gen_1_1, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                if lines:
                    txt = extract_text(lines[0])
                    expected = "In the beginning God created the heaven and the earth."
                    if txt != expected:
                        failures.append(f"[english/kjv] Genesis 1:1 text mismatch: Expected '{expected}', got '{txt}'")
                        fails += 1
                    else:
                        passes += 1
                else:
                    failures.append("[english/kjv] Genesis 1:1 file is empty")
                    fails += 1
            except Exception as e:
                failures.append(f"[english/kjv] Failed to read Genesis 1:1: {e}")
                fails += 1
        else:
            failures.append("[english/kjv] Genesis 1:1 file not found")
            fails += 1

        # John 3:16 (NT)
        john_3_16 = os.path.join(kjv_path, "nt", "04_john", "chapter_003.txt")
        if os.path.exists(john_3_16):
            try:
                with open(john_3_16, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                # John 3:16 is line 16 (0-indexed 15)
                if len(lines) >= 16:
                    txt = extract_text(lines[15])
                    expected = "For God so loved the world"
                    if expected not in txt:
                        failures.append(f"[english/kjv] John 3:16 text mismatch: Expected to contain '{expected}', got '{txt}'")
                        fails += 1
                    else:
                        passes += 1
                else:
                    failures.append(f"[english/kjv] John 3:16 not found (chapter has only {len(lines)} lines)")
                    fails += 1
            except Exception as e:
                failures.append(f"[english/kjv] Failed to read John 3:16: {e}")
                fails += 1
        else:
            failures.append("[english/kjv] John 3:16 file not found")
            fails += 1

    # ASV Checks
    asv_path = os.path.join(bible_dir, "english", "asv")
    if os.path.exists(asv_path):
        # Genesis 1:1 (OT)
        gen_1_1 = os.path.join(asv_path, "ot", "01_genesis", "chapter_001.txt")
        if os.path.exists(gen_1_1):
            try:
                with open(gen_1_1, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                if lines:
                    txt = extract_text(lines[0])
                    expected = "In the beginning God created the heavens and the earth."
                    if txt != expected:
                        failures.append(f"[english/asv] Genesis 1:1 text mismatch: Expected '{expected}', got '{txt}'")
                        fails += 1
                    else:
                        passes += 1
                else:
                    failures.append("[english/asv] Genesis 1:1 file is empty")
                    fails += 1
            except Exception as e:
                failures.append(f"[english/asv] Failed to read Genesis 1:1: {e}")
                fails += 1
        else:
            failures.append("[english/asv] Genesis 1:1 file not found")
            fails += 1

    return passes, fails, failures
