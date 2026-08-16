# Bible Verification Test Suite

This directory contains the automated test suite used to validate the folder structure, line format compliance, canon verse counts, spot checks, and translation fingerprints for the `books` repository.

## Directory Structure

```text
tests/
├── README.md                ← this documentation
├── reports/                 ← generated test run reports (report_YYYY-MM-DD.txt)
├── bible_fingerprints/
│   └── kjv_asv_fingerprints.json   ← JSON metadata of 100 translation fingerprint checks
└── python/
    ├── run_tests.py         ← main orchestrator/runner script
    ├── test_structure.py    ← structural and file placement checks
    ├── test_verse_format.py ← metadata label compliance checks on lines
    ├── test_verse_count.py  ← checks verse counts for standard books against canon
    ├── test_spot_checks.py  ← exact verse text matches for key references (Genesis 1:1, John 3:16)
    └── test_fingerprints.py ← verifies 100 fingerprint substring checks against local texts
```

## Running the Test Suite

To run all checks and generate a comprehensive verification report:

### Requirements
- **Python 3.x** (Standard library only; no external dependencies required).

### Execution
Run the orchestrator script from the repository root:
```bash
python tests/python/run_tests.py
```

Upon completion, a detailed report is written to:
`tests/reports/report_YYYY-MM-DD.txt`
indicating overall score, failures list, and status counts.
