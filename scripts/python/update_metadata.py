import os
import json
import hashlib
import datetime

# Resolve paths
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(script_dir))
bible_dir = os.path.join(base_dir, "bible")

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

def get_publisher_from_url(url):
    if not url:
        return "Unknown Publisher"
    if "ebible" in url:
        return "eBible Corpus"
    if "sblgnt" in url or "faithlife" in url:
        return "Society of Biblical Literature / Faithlife"
    return "Unknown Publisher"

def update_version_metadata(lang, version, version_path):
    metadata_file = os.path.join(version_path, "metadata.json")
    
    # 1. Read existing metadata if available
    existing = {}
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception as e:
            print(f"[{lang}/{version}] Warning reading metadata.json: {e}")
            
    # 2. Count books, chapters, and verses
    books_count = 0
    chapters_count = 0
    verses_count = 0
    testaments = []
    
    # We will also gather files for checksum calculation
    chapter_files_relative = []
    
    for testament in ["ot", "nt"]:
        testament_path = os.path.join(version_path, testament)
        if not os.path.exists(testament_path):
            continue
            
        testament_has_books = False
        for book in sorted(os.listdir(testament_path)):
            book_path = os.path.join(testament_path, book)
            if not os.path.isdir(book_path):
                continue
                
            books_count += 1
            testament_has_books = True
            
            for ch in sorted(os.listdir(book_path)):
                ch_path = os.path.join(book_path, ch)
                if not os.path.isfile(ch_path) or not ch.endswith(".txt"):
                    continue
                    
                chapters_count += 1
                rel_path = f"{testament}/{book}/{ch}"
                chapter_files_relative.append((rel_path, ch_path))
                
                try:
                    with open(ch_path, "r", encoding="utf-8") as f:
                        verses_count += len(f.readlines())
                except Exception as e:
                    print(f"[{lang}/{version}] Error reading {rel_path}: {e}")
                    
        if testament_has_books:
            testaments.append(testament)
            
    # 3. Calculate snapshot checksum fingerprint
    # SHA256 of: relative_path + "\0" + file_bytes + "\0" for every chapter in deterministic order
    chapter_files_relative.sort(key=lambda x: x[0])
    
    sha256 = hashlib.sha256()
    for rel_path, abs_path in chapter_files_relative:
        try:
            with open(abs_path, "rb") as f:
                file_bytes = f.read()
            # Normalize line endings to LF before hashing to ensure cross-platform reproducibility
            normalized_bytes = file_bytes.replace(b"\r\n", b"\n")
            
            sha256.update(rel_path.encode("utf-8"))
            sha256.update(b"\x00")
            sha256.update(normalized_bytes)
            sha256.update(b"\x00")
        except Exception as e:
            print(f"[{lang}/{version}] Error hashing {rel_path}: {e}")
            
    checksum = sha256.hexdigest()
    
    # 4. Construct updated metadata safely, preserving existing curation
    name = existing.get("name", version.upper())
    abbrev = existing.get("abbreviation", existing.get("version", version.upper()))
    lang_name = existing.get("language", lang.capitalize())
    lang_code = existing.get("language_code", lang_codes.get(lang, "unknown"))
    
    # edition_year handles both 'year' and 'edition_year'
    edition_year = existing.get("edition_year", existing.get("year", "Unknown"))
    
    # source_url handles both 'source' and 'source_url'
    source_url = existing.get("source_url", existing.get("source", ""))
    
    publisher = existing.get("publisher_source", get_publisher_from_url(source_url))
    license_info = existing.get("license", "Unknown License")
    download_date = existing.get("download_date", datetime.date.today().strftime("%Y-%m-%d"))
    notes = existing.get("notes", "")
    
    new_metadata = {
        "name": name,
        "version": abbrev,
        "language": lang_name,
        "language_code": lang_code,
        "edition_year": edition_year,
        "publisher_source": publisher,
        "license": license_info,
        "source_url": source_url,
        "download_date": download_date,
        "checksum_hash": checksum,
        "coverage": {
            "books_count": books_count,
            "chapters_count": chapters_count,
            "verses_count": verses_count,
            "testaments": sorted(testaments)
        }
    }
    
    if notes:
        new_metadata["notes"] = notes
        
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(new_metadata, f, indent=2, ensure_ascii=False)
        
    print(f"[{lang}/{version}] Updated metadata.json (Hash: {checksum[:8]}..., Verses: {verses_count})")

def main():
    print("=== UPDATING BIBLE VERSION METADATA ===")
    if not os.path.exists(bible_dir):
        print("Error: bible/ directory does not exist.")
        return
        
    for lang in sorted(os.listdir(bible_dir)):
        lang_path = os.path.join(bible_dir, lang)
        if not os.path.isdir(lang_path):
            continue
            
        for version in sorted(os.listdir(lang_path)):
            version_path = os.path.join(lang_path, version)
            if not os.path.isdir(version_path):
                continue
                
            update_version_metadata(lang, version, version_path)
            
    print("\nMetadata update finished successfully!")

if __name__ == "__main__":
    main()
