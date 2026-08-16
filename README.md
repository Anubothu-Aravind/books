# Multilingual Sacred Text & Teaching Archive

Welcome to the **Multilingual Sacred Text & Teaching Archive** (the `books` repository) — a structured, open-source dataset of canonical scripture texts and teachings. It is designed to be clean, standardized, and immediately useful for AI/NLP applications, morphological research, or dataset analysis.

---

## Current Status

*   **Bibles**: 
    *   **Phase 1**: ✅ English (8 versions) + Telugu (IRV) + Hindi (IRV) are fully collected, split, and verified.
    *   **Phase 2**: ✅ Tamil, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi, and Urdu (IRV each) are fully collected, split, and verified.
    *   **Originals / Classic**: ✅ Hebrew (WLC), Greek (LXX), Greek (SBLGNT), and Arabic (NAV fallback) are fully collected, split, and verified.
    *   **Total Bible Versions**: **22 versions** are successfully structured on disk.
*   **Teachings / Sermons**: *Pending* (Phase 3 collection will start separately when verified transcript data is ready).

---

## Folder Structure Overview

Each Bible version is split into its respective testament (`ot` / `nt`) and organized under zero-padded canonical book prefixes. Every verse text file line is labeled with full context parameters.

```text
books/
├── bible/
│   ├── english/
│   │   ├── kjv/
│   │   │   ├── metadata.json
│   │   │   ├── ot/
│   │   │   │   ├── 01_genesis/
│   │   │   │   │   ├── chapter_001.txt
│   │   │   │   │   └── ...
│   │   │   │   └── ...
│   │   │   └── nt/
│   │   │       ├── 01_matthew/
│   │   │       │   ├── chapter_001.txt
│   │   │       │   └── ...
│   │   │       └── ...
│   │   ├── asv/
│   │   └── ...
│   ├── telugu/
│   ├── hindi/
│   ├── greek/
│   ├── hebrew/
│   ├── arabic/
│   └── ...
├── teachings/        ← reserved for pastor transcript collections (currently empty)
├── tests/
│   ├── README.md
│   ├── bible_fingerprints/
│   │   └── kjv_asv_fingerprints.json   ← 100-case translation fingerprint database (with notes)
│   ├── reports/                        ← execution report logs (.txt)
│   └── python/                         ← test suite modules & runner
├── scripts/
│   ├── README.md
│   ├── python/
│   │   └── download_bibles.py
│   └── js/
└── _meta/
    ├── SOURCES.md    ← detailed download URLs, licenses, and notes
    ├── STATUS.md     ← comprehensive matrix of book/chapter collection statuses
    └── schemas/      ← JSON schemas validating metadata formats
```

### Verse Formatting

Verses inside each `chapter_XX.txt` file are formatted to contain complete metadata on every line:
```text
[VERSION | LANG_CODE | OT/NT | Book Name | Chapter N | Verse N] Verse Text
```
*Example line from `bible/english/asv/nt/22_2peter/chapter_01.txt`:*
```text
[ASV | EN | NT | 2 Peter | Chapter 1 | Verse 17] For he received from God the Father honor and glory, when there was borne such a voice to him by the Majestic Glory, This is my beloved Son, in whom I am well pleased:
```

---

## Setup & Running Scripts

To download, parse, and rebuild the entire database structure, run the Python script from the repository root.

### Requirements
- **Python 3.x** (Standard library only; no pip dependencies required).

### Running the Script
Run the download utility using:
```bash
python scripts/python/download_bibles.py
```
*Note: This script dynamically handles cleaning target paths, fetching the canonical alignment index (`vref.txt`), downloading the 22 translation source texts from eBible/Faithlife repos, grouping chapters into `ot`/`nt` subfolders, and compiling standard `metadata.json` descriptors for each translation.*

---

## Test Suite & Verification

The repository includes an automated validation suite that checks repository structure, verse formats, canonical book verse counts, spot checks, and translation fingerprints.

### Current Baseline (v1 Verification Status)
* **Passed**: 3,921,237 assertions
* **Skipped**: 2 fingerprint checks (explicitly skipped due to documented source-corpus versification limitations)
* **Failed**: 0
* **Applicable pass rate**: 100.00% (3,921,237 / 3,921,237 applicable assertions passed)

### Validation Rules
1. **Structure Validation**: Verifies book folder name sorting and contiguous chapter ranges (1 to max_chapter) for all canonical books on disk, accounting for known translation-specific variations.
2. **Verse Format Validation**: Verifies that every verse line in every chapter file is correctly labeled with version, language, testament, pretty book name, and chapter number matching the filesystem path. It also enforces that verse numbers are strictly increasing (allowing for manuscript gaps).
3. **Verse Count Validation**: Compares actual verse counts against Protestant canonical standards for Genesis, Psalms, Matthew, and Revelation, accounting for known Vulgate (DRA), Septuagint (LXX), and Hebrew (WLC) numbering overrides.
4. **Translation Fingerprint Validation**: Runs 100 translation fingerprint tests to catch version mixing. It handles documented omissions as skips using fingerprint case notes.

### Running Tests
Execute the verification runner from the repository root:
```bash
python tests/python/run_tests.py
```

### Test Reports
The runner compiles execution results and saves dated report logs to:
`tests/reports/report_YYYY-MM-DD.txt`

If multiple runs are performed on the same day, versioned suffixes are dynamically appended (e.g. `report_YYYY-MM-DD_v2.txt`, `report_YYYY-MM-DD_v3.txt`, etc.) to prevent overwriting historical verification logs.


