# Bible Version Fingerprint Test Suite

This directory contains the verification metadata used to distinguish and fingerprint English Bible versions (**KJV, ERV, and ASV**) to prevent source mixture or incorrect transcription sourcing.

> [!WARNING]
> The fingerprint cases in this directory are designed to detect translation/version mix-ups. They are not, by themselves, authoritative representations of the complete verse text. Exact-text validation must use a pinned source edition and documented normalization rules.

## Files

- **[`kjv_erv_asv.json`](file:///c:/Users/91837/Desktop/books/tests/bible_fingerprints/kjv_erv_asv.json)**: A 100-case fingerprint suite verifying wording, capitalization, sentence restructuring, and distinct translation features.
- **`README.md`**: This documentation.

## Test Case Structure

Each fingerprint case is mapped as follows:
```json
{
  "id": 81,
  "reference": "Matthew 1:18",
  "language": "en",
  "translations": {
    "KJV": {
      "expected_contains": "Holy Ghost"
    },
    "ERV": {
      "expected_contains": "Holy Spirit"
    },
    "ASV": {
      "expected_contains": "Holy Spirit"
    }
  },
  "fingerprint": "holy_ghost_vs_holy_spirit"
}
```

## Validation Strategy

1. **Level 1 — Fingerprint Validation**:
   Checks only the distinctive phrase (e.g., KJV/ERV `heaven` vs ASV `heavens`) against the target corpus files to detect version mix-ups.
   
2. **Level 2 — Exact-Text Validation (Future)**:
   Once authoritative source editions are selected and frozen for each translation, character-for-character comparisons should be added utilizing pinned source strings and defined normalization rules:
   ```json
   {
     "reference": "Genesis 1:1",
     "exact": {
       "KJV": "...complete canonical verse...",
       "ERV": "...complete canonical verse...",
       "ASV": "...complete canonical verse..."
     }
   }
   ```
