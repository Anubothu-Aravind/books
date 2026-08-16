import os
import sys
import json
import datetime
import subprocess
import re

# Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(script_dir))
bible_dir = os.path.join(base_dir, "bible")
logs_dir = os.path.join(base_dir, "scripts", "logs")
state_path = os.path.join(logs_dir, "batch_state.json")
log_path = os.path.join(logs_dir, "batch_push.log")
status_path = os.path.join(base_dir, "_meta", "STATUS.md")

os.makedirs(logs_dir, exist_ok=True)

# Load state
if os.path.exists(state_path):
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception:
        state = {"batch_num": 1}
else:
    state = {"batch_num": 1}

batch_num = state.get("batch_num", 1)

def tidy_repo():
    # 1. Remove empty folders, *.pyc files, and __pycache__ folders
    for root, dirs, files in os.walk(base_dir, topdown=False):
        # Remove *.pyc files
        for f in files:
            if f.endswith(".pyc"):
                full_path = os.path.join(root, f)
                try:
                    os.remove(full_path)
                except Exception as e:
                    print(f"Error removing {full_path}: {e}")
                    
        # Remove __pycache__ folders
        for d in dirs:
            if d == "__pycache__":
                full_path = os.path.join(root, d)
                try:
                    import shutil
                    shutil.rmtree(full_path)
                except Exception as e:
                    print(f"Error removing cache {full_path}: {e}")
                    
        # Remove empty folders (except .git, logs, or other critical ones)
        if not os.listdir(root):
            if ".git" not in root and "logs" not in root and root != base_dir:
                try:
                    os.rmdir(root)
                    print(f"Removed empty folder: {root}")
                except Exception as e:
                    pass

def update_status_file(status_path, bible_dir):
    languages = [d for d in os.listdir(bible_dir) if os.path.isdir(os.path.join(bible_dir, d))]
    versions_count = 0
    chapters_count = 0
    detailed_lines = []
    
    for lang in sorted(languages):
        lang_dir = os.path.join(bible_dir, lang)
        vers = [v for v in os.listdir(lang_dir) if os.path.isdir(os.path.join(lang_dir, v))]
        versions_count += len(vers)
        detailed_lines.append(f"### {lang.capitalize()}")
        
        for v in sorted(vers):
            ver_dir = os.path.join(lang_dir, v)
            v_chapters = 0
            v_books = 0
            for testament in ["ot", "nt"]:
                test_path = os.path.join(ver_dir, testament)
                if os.path.exists(test_path):
                    books = [b for b in os.listdir(test_path) if os.path.isdir(os.path.join(test_path, b))]
                    v_books += len(books)
                    for b in books:
                        b_path = os.path.join(test_path, b)
                        v_chapters += len([f for f in os.listdir(b_path) if f.startswith("chapter_") and f.endswith(".txt")])
                        
            chapters_count += v_chapters
            detailed_lines.append(f"- [x] **{v.upper()}** — *Collected & Split ({v_chapters} chapters across {v_books} books)*")
            
    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    status_content = f"""# Repository Status

*Last Updated: {current_time_str}*

This file tracks the current state of the multilingual sacred text & teaching archive dataset, showcasing what is collected, split, or pending.

## Collection Overview

- **Total Languages**: {len(languages)}
- **Total Bible Versions**: {versions_count}
- **Total Chapters**: {chapters_count}

| Category | Target Languages / Versions | Status | Notes |
|---|---|---|---|
| **Bible (Phase 1)** | English (8 versions), Telugu (IRV), Hindi (IRV) | ✅ Complete | 8 English versions + Telugu IRV + Hindi IRV are fully downloaded and split into book/chapter structure. (23 known test variations documented in `kjv_asv_fingerprints.json` and `SOURCES.md` — not errors) |
| **Bible (Phase 2)** | Tamil, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi, Urdu (IRV each) | Completed & Split | All 8 Indian languages (IRV) are fully downloaded and split into book/chapter structure. |
| **Bible (Originals & Arabic)**| Hebrew (WLC), Greek (SBLGNT, LXX), Arabic (VanDyke/NAV) | Completed & Split | Hebrew WLC, Greek SBLGNT, Greek LXX, and Arabic NAV are fully downloaded and split. |
| **Bible (Pending)**| Greek (TR), Telugu (TSI), Hindi (HHBD) | Pending | Greek TR (License check pending), Telugu TSI, and Hindi HHBD are pending. |
| **Teachings (Phase 3)**| Pastor transcripts and profiles | Pending | Real collections to begin in Phase 3. |

---

## Detailed Version Status

{"\n".join(detailed_lines)}

---

## Teachings / Sermons
- [ ] **Speaker Collections** — *No real speaker data collected yet*
"""
    with open(status_path, "w", encoding="utf-8") as f:
        f.write(status_content)

def main():
    print(f"Starting BATCH {batch_num} at {datetime.datetime.now()}")
    
    # 1. Tidy
    tidy_repo()
    
    # 2. Update status timestamp
    update_status_file(status_path, bible_dir)
    
    # 3. Stage and commit check
    subprocess.run(["git", "add", "-A"], cwd=base_dir, check=True)
    
    # Get staged files list
    staged_files = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=base_dir).decode("utf-8").splitlines()
    files_changed = len(staged_files)
    
    if files_changed == 0:
        log_msg = f"[{datetime.datetime.now().isoformat()}] BATCH {batch_num} - nothing to push\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_msg)
        print("Nothing to commit/push.")
        return
        
    current_time_hm = datetime.datetime.now().strftime("%H:%M")
    commit_msg = f"[BATCH {batch_num}] tidy + update - {current_time_hm}"
    
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=base_dir, check=True)
    subprocess.run(["git", "push", "origin", "data/bible"], cwd=base_dir, check=True)
    
    # 4. Log
    log_msg = f"[{datetime.datetime.now().isoformat()}] BATCH {batch_num} - pushed {files_changed} files. Commit: '{commit_msg}'\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_msg)
        
    print(f"Batch {batch_num} push complete.")
    
    # Save incremented state
    state["batch_num"] = batch_num + 1
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

if __name__ == "__main__":
    main()
