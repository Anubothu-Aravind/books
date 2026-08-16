# Repository Tooling & Scripts

This directory contains command-line utilities and automation tools used to build, maintain, and validate the multilingual sacred text & teaching archive dataset.

## Structure

```text
scripts/
├── README.md
├── python/
│   └── download_bibles.py     ← fetches and splits Bible versions from eBible/BibleNLP
└── js/                        ← reserved for future JavaScript tooling
```

## Python Utilities

### `python/download_bibles.py`
This script automates the download and chapter-splitting of target Bible versions.

- **Source**: Fetches raw data from the `BibleNLP/ebible` parallel corpus.
- **Processing**:
  - Validates and parses the verses against `vref.txt`.
  - Splits each translation into a structured book-and-chapter directory layout (e.g. `bible/english/kjv/genesis/chapter_01.txt`).
  - Cleans up temporary raw text files.
  - Automatically generates valid `metadata.json` files matching the schema definitions for each successfully fetched version.
- **Execution**: Run with standard Python (no external dependencies required):
  ```bash
  python scripts/python/download_bibles.py
  ```

## JS Utilities

### `js/`
Reserved for future JavaScript-based tooling and schemas validation.
