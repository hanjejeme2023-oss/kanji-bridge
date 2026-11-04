# SOURCES: data source & license log

Rule: **check the license when downloading (before using), write the attribution at the end.**
Each row is completed when the source is first downloaded (Stage 1), from the source's own license file. "要確認" = not verified yet.

Last updated: 2026-11-04 (Stage 1 download and profiling)

---

## 1. License check (fill in at download time)

| # | Source | URL | Version / date downloaded | License | Can we use it? | Share-alike? | Attribution text required | Checked on |
|---|---|---|---|---|---|---|---|---|
| 1 | Unihan database | https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip | UCD `latest` snapshot downloaded 2026-11-04; exact SHA-256 in `pipeline/source_manifest.csv` | Unicode License v3 / SPDX `Unicode-3.0`; own text in `licenses/UNICODE-LICENSE.txt` | Yes | No | Preserve the Unicode copyright and permission notice with copies/substantial portions; identify the Unicode Consortium and Unihan/UCD as source. | 2026-11-04 |
| 2 | KANJIDIC2 | https://www.edrdg.org/pub/Nihongo/kanjidic2.xml.gz | Rolling EDRDG snapshot downloaded 2026-11-04; exact SHA-256 in manifest | EDRDG General Dictionary Licence: CC BY-SA 4.0; own statement in `licenses/KANJIDIC2-EDRDG-LICENSE.html` | Yes; Claude to confirm field-specific notices | **Yes** | Clearly acknowledge use of KANJIDIC2 and EDRDG; provide local or upstream documentation/licence links; derived published data stay under a compatible share-alike licence. Maintain an update procedure. | 2026-11-04 |
| 3 | ivankra/hsk30 | https://github.com/ivankra/hsk30 | `master` snapshot downloaded 2026-11-04; 11,092 words / 3,000 chars; exact SHA-256 in manifest | MIT, Copyright Ivan Krasilnikov / Shawky / Pleco; `licenses/HSK30-MIT-LICENSE.txt` | **要確認** — repository grants MIT, but its README flags uncertainty around the PRC Ministry of Education source | No | Retain the MIT copyright and permission notice; credit `ivankra/hsk30` and document its upstream HSK provenance. | 2026-11-04 |
| 4 | CC-CEDICT | https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz | Rolling export downloaded 2026-11-04; 125,365 entries; exact SHA-256 in manifest | CC BY-SA 4.0; source statement in `licenses/CC-CEDICT-LICENSE.html`, legal code in `licenses/CC-BY-SA-4.0.txt` | Yes | **Yes** | Credit CC-CEDICT and its contributors/editor team, link the source and CC BY-SA 4.0, indicate modifications, and distribute adapted data under the same/compatible licence. | 2026-11-04 |
| 5 | JMdict (English subset) | https://www.edrdg.org/pub/Nihongo/JMdict_e.gz | Rolling EDRDG snapshot downloaded 2026-11-04; 219,015 entries; exact SHA-256 in manifest | EDRDG General Dictionary Licence: CC BY-SA 4.0; `licenses/JMDICT-EDRDG-LICENSE.html` | Yes | **Yes** | Clearly acknowledge use of JMdict and EDRDG; provide local or upstream documentation/licence links; derived published data stay under a compatible share-alike licence. Maintain an update procedure. | 2026-11-04 |
| 6 | libhangul `hanja.txt` | https://github.com/libhangul/libhangul/blob/master/data/hanja/hanja.txt | `master` snapshot downloaded 2026-11-04; 303,495 records; exact SHA-256 in manifest | File-specific BSD 3-Clause header, Copyright (c) 2005,2006 Choe Hwanjin; extracted verbatim to `licenses/LIBHANGUL-HANJA-BSD-3-CLAUSE.txt` (repository code is LGPL-2.1) | **要確認** — header is a usable grant; Claude must confirm it governs this data file | No | Retain the copyright notice, three conditions, and disclaimer in source redistributions and documentation/materials for binary redistribution. | 2026-11-04 |
| 7 | `ryanphung/chinese-hanviet-cognates` | https://github.com/ryanphung/chinese-hanviet-cognates | **Not downloaded** | **No licence; README also identifies an input as `source missing`** | **No — excluded by user 2026-11-04** | N/A | N/A. No data or sample rows may be copied into this project. | 2026-11-04 |
| 7A | Kaikki / Vietnamese Wiktionary raw Wiktextract data (replacement candidate) | https://kaikki.org/viwiktionary/rawdata.html | Extract produced 2026-11-03 from viwiktionary dump 2026-10-02; downloaded 2026-11-04; exact SHA-256 in manifest | Same licences as Wiktionary: CC BY-SA and GFDL; source statement in `licenses/KAIKKI-VIWIKTIONARY-LICENSE.html` | Yes as a candidate; not selected | **Yes** | Credit Vietnamese Wiktionary contributors and Kaikki/Wiktextract (Tatu Ylonen), link the source and applicable Wiktionary licences, and preserve share-alike terms. | 2026-11-04 |
| 7B | FrequencyWords Vietnamese OpenSubtitles 2018 list (replacement candidate) | https://github.com/hermitdave/FrequencyWords/blob/master/content/2018/vi/vi_50k.txt | 2018 corpus list; downloaded 2026-11-04; 50,000 rows; exact SHA-256 in manifest | Upstream README declares **content** CC BY-SA 4.0 (`licenses/FREQUENCYWORDS-CONTENT-LICENSE.md`; legal code already copied) | Yes as a candidate; not selected | **Yes** | Credit Hermit Dave / FrequencyWords and the OpenSubtitles 2018-derived list; link CC BY-SA 4.0, indicate modifications, and preserve share-alike terms. | 2026-11-04 |
| 8 | OpenCC Japanese shinjitai candidate tables | https://github.com/BYVoid/OpenCC/tree/master/data/dictionary | `master` snapshot downloaded 2026-11-04; 403 character + 235 phrase mappings; exact SHA-256 in manifest | Apache License 2.0; `licenses/OPENCC-APACHE-2.0-LICENSE.txt` | Yes as candidate material; method not selected | No | Include the Apache 2.0 licence, retain applicable copyright/attribution notices, and mark modified files. | 2026-11-04 |

## 2. Usage log (fill in during work)

| Source # | Used in table | Columns | Notes |
|---|---|---|---|
| 1 | `chars` (planned) | `trad`, `simp`, `ko`, `ko_all`, `pinyin`, `pinyin_all`, `vi`, `vi_all`, `gloss_en`; variant evidence | Character-level source; primary-reading priority and Vietnamese cross-check remain for Claude. |
| 2 | `chars` (planned) | `jp`, `ja_on`, `ja_on_all`; variant evidence | Japanese on-reading source required by D9. |
| 3 | `words`, `chars` (planned, licence review pending) | HSK backbone; `trad`, `simp`, `pinyin`, `level`, HSK-character membership/level | Do not use until Claude accepts provenance/licence. |
| 4 | `words` (planned) | Chinese dictionary pinyin and `gloss_en` | Word key includes reading; source priority pending. |
| 5 | `words`, false-friend candidate generation (planned) | `jp`, `ja`, `ja_alt`, Japanese gloss/commonness | Written-form mapping method pending. |
| 6 | `words`, false-friend candidate generation (planned, licence review pending) | `ko`, `ko_alt`, Korean word inventory | Input-method table requires filtering; do not use until Claude confirms per-file licence. |
| 7 | None | None | Excluded: no licence and incomplete input provenance. |
| 7A | Candidate for `words` / validation only | Vietnamese word reading, explicit Han form, Vietnamese gloss | Downloaded/profiled but not selected; Claude decides. No frequency column. |
| 7B | Candidate for `words` frequency only | Vietnamese token count/rank evidence | Downloaded/profiled but not selected; syllable-token list does not directly rank compounds. |
| 8 | Candidate for `chars.jp` mapping | shinjitai ↔ old/traditional-form evidence | Claude chooses among OpenCC, KANJIDIC2 variants and Unihan variants. |

## 3. Implications to track

- If any share-alike (CC BY-SA) source is used, the **published dataset** (`data/final/*`) must be released under CC BY-SA too. App code can still use a different license (e.g. MIT).
- Sources with no license or "non-commercial only" terms: do not use without permission.
- AI-generated content (`content/`): record which model generated it and that it was human/auditor-verified.
- Keep each source's license file in `raw/<source>/` and copy it to `licenses/` (committed; `raw/` itself is not committed).

## 4. Final attribution (written at the end)

Generated from sections 1–2 into the repo's README "Data sources" section and LICENSE files.
