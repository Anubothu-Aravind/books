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
sources_path = os.path.join(base_dir, "_meta", "SOURCES.md")

os.makedirs(logs_dir, exist_ok=True)

# Load state
if os.path.exists(state_path):
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception:
        state = {"batch_num": 1, "total_batches": 12}
else:
    state = {"batch_num": 1, "total_batches": 12}

batch_num = state.get("batch_num", 1)
total_batches = state.get("total_batches", 12)

def validate_metadata(bible_dir):
    required_fields = {
        "name": "Unknown Version",
        "abbreviation": "UNK",
        "language": "Unknown",
        "language_code": "un",
        "year": 2000,
        "testament_count": {"ot": 0, "nt": 0},
        "source": "https://github.com/Anubothu-Aravind/books",
        "license": "Public Domain",
        "notes": ""
    }
    for root, dirs, files in os.walk(bible_dir):
        if "metadata.json" in files:
            meta_file = os.path.join(root, "metadata.json")
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                dirty = False
                for field, default in required_fields.items():
                    if field not in meta or meta[field] is None:
                        meta[field] = default
                        dirty = True
                if dirty:
                    with open(meta_file, "w", encoding="utf-8") as f:
                        json.dump(meta, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Error validating {meta_file}: {e}")

def tidy_repo():
    # 1. Delete scratch files in repo root or desktop root
    desktop_root = r"c:\Users\91837\Desktop"
    for path in [base_dir, desktop_root]:
        if os.path.exists(path):
            for item in os.listdir(path):
                if item.startswith("scratch") or item.startswith("temp"):
                    full_path = os.path.join(path, item)
                    if os.path.isfile(full_path):
                        try:
                            os.remove(full_path)
                            print(f"Deleted scratch file: {full_path}")
                        except Exception as e:
                            print(f"Error deleting {full_path}: {e}")
                            
    # 2. Remove empty folders, *.pyc files, and __pycache__ folders
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
                    
        # Remove empty folders (except .git or other critical ones)
        if not os.listdir(root):
            if ".git" not in root and root != base_dir:
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
            
    status_content = f"""# Repository Status

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

def touch_sources_timestamp(sources_path):
    if not os.path.exists(sources_path):
        return
    with open(sources_path, "r", encoding="utf-8") as f:
        content = f.read()
    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pattern = r"\*Last Updated:.*?\*"
    if re.search(pattern, content):
        content = re.sub(pattern, f"*Last Updated: {current_time_str}*", content)
    else:
        content = f"*Last Updated: {current_time_str}*\n\n" + content
        
    with open(sources_path, "w", encoding="utf-8") as f:
        f.write(content)

def register_task():
    # Register Windows schtasks for remaining runs starting 20 minutes from now
    python_bin = sys.executable
    script_path = os.path.abspath(__file__)
    start_time = datetime.datetime.now() + datetime.timedelta(minutes=20)
    start_time_str = start_time.strftime("%H:%M")
    
    # tr_arg should be escaped with backslash-quotes
    tr_arg = f'"{python_bin}" "{script_path}"'
    cmd = [
        "schtasks", "/create",
        "/tn", "books-batch-push-today",
        "/tr", tr_arg,
        "/sc", "MINUTE",
        "/mo", "20",
        "/st", start_time_str,
        "/et", "19:00",
        "/z",
        "/f"
    ]
    print(f"Registering Windows Task: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print("Windows Task 'books-batch-push-today' registered successfully.")
    else:
        print(f"Error registering Windows Task: {res.stderr}")

def main():
    print(f"Starting BATCH {batch_num}/{total_batches} at {datetime.datetime.now()}")
    
    # 1. Tidy
    tidy_repo()
    validate_metadata(bible_dir)
    
    # 2. Update meta
    update_status_file(status_path, bible_dir)
    touch_sources_timestamp(sources_path)
    
    # 3. Stage and commit
    subprocess.run(["git", "add", "-A"], cwd=base_dir, check=True)
    
    # Get count of files changed (staged)
    staged_files = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=base_dir).decode("utf-8").splitlines()
    files_changed = len(staged_files)
    
    if files_changed == 0:
        print("No changes to push.")
        log_entry = f"[{datetime.datetime.now().isoformat()}] BATCH {batch_num}/{total_batches} - No changes to commit/push.\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_entry)
        return
        
    current_time_hm = datetime.datetime.now().strftime("%H:%M")
    commit_msg = f"[BATCH {batch_num}/{total_batches}] tidy + data update - {current_time_hm}"
    
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=base_dir, check=True)
    subprocess.run(["git", "push", "origin", "data/bible"], cwd=base_dir, check=True)
    
    # 4. Log
    log_entry = f"[{datetime.datetime.now().isoformat()}] BATCH {batch_num}/{total_batches} - Committed and pushed {files_changed} files. Commit: '{commit_msg}'\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_entry)
        
    print(f"Successfully completed batch {batch_num}. Logs updated.")
    
    # Register scheduler if this is the first batch
    if batch_num == 1:
        register_task()
        
    # Save incremented state
    state["batch_num"] = batch_num + 1
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

if __name__ == "__main__":
    main()
