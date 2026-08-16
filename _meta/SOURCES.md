*Last Updated: 2026-08-16 15:12:44*

# Sources & Licenses

This document tracks all external source URLs, licensing information, and collection statuses for texts included in this repository.

## Confirmed & Collected Sources

| Version Code | Language | Version Name | Source / URL | License | Notes |
|---|---|---|---|---|---|
| **kjv** | English | King James Version (CPB) | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/eng-engkjvcpb.txt) | Public Domain | Cambridge Paragraph Bible edition of KJV |
| **asv** | English | American Standard Version | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/eng-engasvbt.txt) | Public Domain | 1901 translation |
| **web** | English | World English Bible | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/eng-engwebu.txt) | Public Domain / CC0 | Modern English update of ASV |
| **ylt** | English | Young's Literal Translation | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/eng-engylt.txt) | Public Domain | 1862/1898 literal translation |
| **darby** | English | Darby Bible | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/eng-engDBY.txt) | Public Domain | J.N. Darby translation |
| **bbe** | English | Bible in Basic English | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/eng-engBBE.txt) | Public Domain | 1949 edition |
| **dra** | English | Douay-Rheims Bible | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/eng-engDRA.txt) | Public Domain | Challoner revision |
| **oeb** | English | Open English Bible | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/eng-engoebcw.txt) | Creative Commons Zero (CC0) | Modern English translation |
| **irv** | Telugu | Indian Revised Version | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/tel-tel2017.txt) | CC BY-SA 4.0 | Bridge Connectivity Solutions |
| **irv** | Hindi | Indian Revised Version | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/hin-hin2017.txt) | CC BY-SA 4.0 | Bridge Connectivity Solutions |
| **irv** | Tamil | Indian Revised Version | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/tam-tam2017.txt) | CC BY-SA 4.0 | Bridge Connectivity Solutions |
| **irv** | Kannada | Indian Revised Version | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/kan-kan2017.txt) | CC BY-SA 4.0 | Bridge Connectivity Solutions |
| **irv** | Malayalam | Indian Revised Version | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/mal-mal2015.txt) | CC BY-SA 4.0 | Bridge Connectivity Solutions |
| **irv** | Bengali | Indian Revised Version | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/ben-benirv.txt) | CC BY-SA 4.0 | Bridge Connectivity Solutions |
| **irv** | Marathi | Indian Revised Version | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/mar-mar.txt) | CC BY-SA 4.0 | Bridge Connectivity Solutions |
| **irv** | Gujarati | Indian Revised Version | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/guj-guj2017.txt) | CC BY-SA 4.0 | Bridge Connectivity Solutions |
| **irv** | Punjabi | Indian Revised Version | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/pan-pan.txt) | CC BY-SA 4.0 | Bridge Connectivity Solutions |
| **irv** | Urdu | Indian Revised Version | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/urd-urd.txt) | CC BY-SA 4.0 | Bridge Connectivity Solutions |
| **wlc** | Hebrew | Westminster Leningrad Codex | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/hbo-hboWLC.txt) | Public Domain | Codex Leningradensis transcription |
| **sblgnt** | Greek | SBL Greek New Testament | [Faithlife SBLGNT Repo](https://raw.githubusercontent.com/Faithlife/SBLGNT/master/data/sblgnt/text/) | SBLGNT License | Society of Biblical Literature Greek NT |
| **lxx** | Greek | Septuagint | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/grc-grcbrent.txt) | Public Domain | Brenton Greek Old Testament |
| **vandyke** | Arabic | Smith & Van Dyke (NAV Fallback) | [eBible Corpus](https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/arb-arbnav.txt) | Copyright © Biblica, Inc. | Loaded New Arabic Version as a working fallback |

---

## Pending / Unconfirmed

The following targeted versions are pending source verification or licensing checks:

- **tr** (Greek - Textus Receptus)
  - *Status*: Pending — license unconfirmed.
  - *Notes*: Digital transcriptions of Textus Receptus (e.g., Stephanus 1550 or Scrivener 1894) require review to ensure no copyright claims exist on the electronic parsing/tagging.
- **tsi** (Telugu - Telugu Study Bible)
  - *Status*: Pending — licensing check & source location.
- **hhbd** (Hindi - Hindi Holy Bible Deluxe)
  - *Status*: Pending — licensing check & source location.

---

## Known Canon & Versification Differences

The test suite flags the following variations. These are not errors but expected textual variations across translations:

- **[KNOWN DIFFERENCE — CANON VARIANT] DRA Psalms (1741 vs 2461 expected)**: The Douay-Rheims Bible (Challoner Revision) is translated from the Catholic Vulgate, which groups and numbers the Psalms differently (combining/splitting several psalms), resulting in a different total verse structure.
- **[KNOWN DIFFERENCE — CANON VARIANT] LXX Psalms (1740 vs 2461 expected)**: The Brenton Greek Septuagint (LXX) follows the Alexandrian canon's psalm numbering system, resulting in variations and different verse counts from the Protestant Masoretic text.
- **[KNOWN DIFFERENCE — CANON VARIANT] WLC Psalms (2527 vs 2461 expected)**: The Hebrew Westminster Leningrad Codex (WLC) counts introductory psalm superscriptions (e.g. "A Psalm of David...") as verse 1, increasing the total verse count relative to English translations which do not count titles as verses.
