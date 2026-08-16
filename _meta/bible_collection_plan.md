# Bible Collection Plan

*Last Updated: 2026-08-16*

This is the master checklist for building the multilingual Bible corpus.
Every new addition follows the same ingestion workflow (documented below) and must pass the frozen verification pipeline before being considered complete.

---

## Ingestion Workflow (Frozen)

For every new Bible version:

`
1.  Find authoritative source
2.  Verify redistribution / license
3.  Record curated metadata
4.  Download raw source
5.  Ingest into existing folder structure
6.  Run scripts/python/update_metadata.py
7.  Run scripts/python/generate_status.py
8.  Run python tests/python/run_tests.py
9.  Inspect PASS / SKIP / FAIL
10. Commit
`

If a test fails: investigate the source or data. Fix ingestion. Rerun.
Do NOT modify the frozen tests unless the difference is a genuinely documented canon, versification, manuscript, or source-specific exception.

---

## English

| Version | Full Name | Source | License | eBible Corpus File | Status |
|---------|-----------|--------|---------|-------------------|--------|
| KJV | King James Version (Cambridge Paragraph Bible) | eBible | Public Domain | eng-engkjvcpb.txt | Complete |
| ASV | American Standard Version (1901) | eBible | Public Domain | eng-engasvbt.txt | Complete |
| WEB | World English Bible | eBible | Public Domain / CC0 | eng-engwebu.txt | Complete |
| YLT | Young's Literal Translation (1898) | eBible | Public Domain | eng-engylt.txt | Complete |
| DARBY | Darby Bible (1890) | eBible | Public Domain | eng-engDBY.txt | Complete |
| BBE | Bible in Basic English (1949) | eBible | Public Domain | eng-engBBE.txt | Complete |
| DRA | Douay-Rheims Bible -- Challoner Revision (1752) | eBible | Public Domain | eng-engDRA.txt | Complete |
| OEB | Open English Bible | eBible | CC0 | eng-engoebcw.txt | Complete |
| ERV | English Revised Version (1885) | eBible.org | Public Domain | eng-rv_usfm.zip | Complete |
| WEBSTER | Webster's Bible Translation (1833) | eBible | Public Domain | eng-engwebster.txt | Complete |
| BSB | Berean Standard Bible | eBible | CC BY 4.0 | eng-engbsb.txt | Complete |
| GNV | Geneva Bible (1599) | eBible | Public Domain | eng-enggnv.txt | Complete |
| JPS | Jewish Publication Society Tanakh (1917) | eBible | Public Domain | eng-engjps.txt | Complete |

### Notes -- ERV 1885
The eBible corpus file eng-eng_rv.txt exists but is entirely empty (0 non-empty lines out of 41,899).
The English Revised Version (1885) must be sourced from an alternative location.

Candidate sources:
- https://ebible.org/find/details.php?id=engrv (eBible.org USFM download)
- https://www.sacred-texts.com/bib/rv/ (sacred-texts.com HTML edition)
- Project Gutenberg (public domain text edition)

License: The ERV 1885 is definitively Public Domain.

---

## Indian Languages

| Language | Version | Full Name | Source | License | eBible Corpus File | Status |
|----------|---------|-----------|--------|---------|-------------------|--------|
| Telugu | IRV | Indian Revised Version | eBible | CC BY-SA 4.0 | tel-tel2017.txt | Complete |
| Hindi | IRV | Indian Revised Version | eBible | CC BY-SA 4.0 | hin-hin2017.txt | Complete |
| Tamil | IRV | Indian Revised Version | eBible | CC BY-SA 4.0 | tam-tam2017.txt | Complete |
| Kannada | IRV | Indian Revised Version | eBible | CC BY-SA 4.0 | kan-kan2017.txt | Complete |
| Malayalam | IRV | Indian Revised Version | eBible | CC BY-SA 4.0 | mal-mal2015.txt | Complete |
| Bengali | IRV | Indian Revised Version | eBible | CC BY-SA 4.0 | ben-benirv.txt | Complete |
| Marathi | IRV | Indian Revised Version | eBible | CC BY-SA 4.0 | mar-mar.txt | Complete |
| Gujarati | IRV | Indian Revised Version | eBible | CC BY-SA 4.0 | guj-guj2017.txt | Complete |
| Punjabi | IRV | Indian Revised Version | eBible | CC BY-SA 4.0 | pan-pan.txt | Complete |
| Urdu | IRV | Indian Revised Version | eBible | CC BY-SA 4.0 | urd-urd.txt | Complete |

---

## Originals and Classical Languages

| Language | Version | Full Name | Source | License | eBible Corpus File | Status |
|----------|---------|-----------|--------|---------|-------------------|--------|
| Hebrew | WLC | Westminster Leningrad Codex | eBible | Public Domain | hbo-hboWLC.txt | Complete |
| Greek | LXX | Septuagint -- Brenton (1851) | eBible | Public Domain | grc-grcbrent.txt | Complete |
| Greek | SBLGNT | SBL Greek New Testament | Faithlife | SBLGNT License | (per-book files) | Complete |
| Arabic | VANDYKE | Smith and Van Dyke / NAV fallback | eBible | Copyright Biblica | arb-arbnav.txt | Complete (NAV fallback; true Van Dyke sourcing pending) |
| Greek | TR | Textus Receptus (Stephanus 1550 or Scrivener 1894) | TBD | License under review | -- | Pending |

### Notes -- Arabic Van Dyke
The current corpus entry uses the NAV (New Arabic Version, Biblica copyright) as a fallback.
A true public-domain Van Dyke source should be located and used to replace this entry in a future pass.

---

## Priority Order

### Immediate Next (English completion)

1. ERV 1885 -- highest priority. Source from eBible.org USFM or Project Gutenberg.
2. WEBSTER -- eBible corpus file confirmed populated (30,966 non-empty lines). Ready to ingest.
3. BSB -- CC BY 4.0 license (attribution required). eBible file confirmed (30,950 lines). Ready to ingest.
4. GNV -- Geneva Bible 1599. eBible file confirmed (30,957 lines). Ready to ingest.
5. JPS -- Jewish Publication Society OT only. eBible file confirmed (23,011 lines). Ready to ingest.

### After English

All 10 Indian language IRV versions are already complete.

Pending originals:
- Arabic Van Dyke: resolve true public-domain source
- Greek TR: resolve licensing

---

## Summary

| Region | Versions Complete | Versions Pending |
|--------|-------------------|-----------------|
| English | 13 | 0 |
| Indian Languages | 10 | 0 |
| Originals | 3 | Arabic Van Dyke (true source), Greek TR |
