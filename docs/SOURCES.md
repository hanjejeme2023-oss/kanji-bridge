# SOURCES: data source & license log

Rule: **check the license when downloading (before using), write the attribution at the end.**
Each row is completed when the source is first downloaded (Stage 1), from the source's own license file. "要確認" = not verified yet.

Last updated: 2026-11-04 (Stage 1 review by Claude; evidence in `docs/STAGE1_REVIEW.md`, decisions D23–D34)

---

## 1. License check (fill in at download time)

| # | Source | URL | Version / date downloaded | License | Can we use it? | Share-alike? | Attribution text required | Checked on |
|---|---|---|---|---|---|---|---|---|
| 1 | Unihan database | https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip | UCD `latest` snapshot downloaded 2026-11-04; exact SHA-256 in `pipeline/source_manifest.csv` | Unicode License v3 / SPDX `Unicode-3.0`; own text in `licenses/UNICODE-LICENSE.txt` | Yes | No | Preserve the Unicode copyright and permission notice with copies/substantial portions; identify the Unicode Consortium and Unihan/UCD as source. | 2026-11-04 |
| 2 | KANJIDIC2 | https://www.edrdg.org/pub/Nihongo/kanjidic2.xml.gz | Rolling EDRDG snapshot downloaded 2026-11-04; exact SHA-256 in manifest | EDRDG General Dictionary Licence: CC BY-SA 4.0; own statement in `licenses/KANJIDIC2-EDRDG-LICENSE.html` | Yes; Claude to confirm field-specific notices | **Yes** | Clearly acknowledge use of KANJIDIC2 and EDRDG; provide local or upstream documentation/licence links; derived published data stay under a compatible share-alike licence. Maintain an update procedure. | 2026-11-04 |
| 3 | ivankra/hsk30 | https://github.com/ivankra/hsk30 | `master` snapshot downloaded 2026-11-04; 11,092 words / 3,000 chars; exact SHA-256 in manifest | MIT, Copyright Ivan Krasilnikov / Shawky / Pleco; `licenses/HSK30-MIT-LICENSE.txt` | **Yes — accepted with recorded risk (D23); confirmed by the user, personal non-commercial project, D35**: MIT grant is clear; README says the underlying PRC Ministry of Education list's copyright is questionable/possibly public domain. Content used = word list, pinyin, levels. | No | Retain the MIT copyright and permission notice; credit `ivankra/hsk30` and document its upstream HSK provenance. | 2026-11-04 |
| 4 | CC-CEDICT | https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz | Rolling export downloaded 2026-11-04; 125,365 entries; exact SHA-256 in manifest | CC BY-SA 4.0; source statement in `licenses/CC-CEDICT-LICENSE.html`, legal code in `licenses/CC-BY-SA-4.0.txt` | Yes | **Yes** | Credit CC-CEDICT and its contributors/editor team, link the source and CC BY-SA 4.0, indicate modifications, and distribute adapted data under the same/compatible licence. | 2026-11-04 |
| 5 | JMdict (English subset) | https://www.edrdg.org/pub/Nihongo/JMdict_e.gz | Rolling EDRDG snapshot downloaded 2026-11-04; 219,015 entries; exact SHA-256 in manifest | EDRDG General Dictionary Licence: CC BY-SA 4.0; `licenses/JMDICT-EDRDG-LICENSE.html` | Yes | **Yes** | Clearly acknowledge use of JMdict and EDRDG; provide local or upstream documentation/licence links; derived published data stay under a compatible share-alike licence. Maintain an update procedure. | 2026-11-04 |
| 6 | libhangul `hanja.txt` | https://github.com/libhangul/libhangul/blob/master/data/hanja/hanja.txt | `master` snapshot downloaded 2026-11-04; 303,495 records; exact SHA-256 in manifest | File-specific BSD 3-Clause header, Copyright (c) 2005,2006 Choe Hwanjin; extracted verbatim to `licenses/LIBHANGUL-HANJA-BSD-3-CLAUSE.txt` (repository code is LGPL-2.1) | **Yes (D23)** — the file's own BSD-3 header governs the data; LGPL-2.1 is the library code's licence. Compatible with a CC BY-SA 4.0 dataset | No | Retain the copyright notice, three conditions, and disclaimer in source redistributions and documentation/materials for binary redistribution. | 2026-11-04 |
| 7 | `ryanphung/chinese-hanviet-cognates` | https://github.com/ryanphung/chinese-hanviet-cognates | **Not downloaded** | **No licence; README also identifies an input as `source missing`** | **No — excluded by user 2026-11-04** | N/A | N/A. No data or sample rows may be copied into this project. | 2026-11-04 |
| 7A | Kaikki / Vietnamese Wiktionary raw Wiktextract data (replacement candidate) | https://kaikki.org/viwiktionary/rawdata.html | Extract produced 2026-11-03 from viwiktionary dump 2026-10-02; downloaded 2026-11-04; exact SHA-256 in manifest | Same licences as Wiktionary: CC BY-SA and GFDL; source statement in `licenses/KAIKKI-VIWIKTIONARY-LICENSE.html` | **Yes, SELECTED (D24)** — used under CC BY-SA 4.0 (saved page says CC BY-SA and GFDL; version not stated, Wikimedia text is CC BY-SA 4.0) | **Yes** | Credit Vietnamese Wiktionary contributors and Kaikki/Wiktextract (Tatu Ylonen), link the source and applicable Wiktionary licences, and preserve share-alike terms. | 2026-11-04 |
| 7B | FrequencyWords Vietnamese OpenSubtitles 2018 list (replacement candidate) | https://github.com/hermitdave/FrequencyWords/blob/master/content/2018/vi/vi_50k.txt | 2018 corpus list; downloaded 2026-11-04; 50,000 rows; exact SHA-256 in manifest | Upstream README declares **content** CC BY-SA 4.0 (`licenses/FREQUENCYWORDS-CONTENT-LICENSE.md`; legal code already copied) | **Yes, SELECTED for frequency (D24, D26)** | **Yes** | Credit Hermit Dave / FrequencyWords and the OpenSubtitles 2018-derived list; link CC BY-SA 4.0, indicate modifications, and preserve share-alike terms. | 2026-11-04 |
| 8 | OpenCC Japanese shinjitai candidate tables | https://github.com/BYVoid/OpenCC/tree/master/data/dictionary | `master` snapshot downloaded 2026-11-04; 403 character + 235 phrase mappings; exact SHA-256 in manifest | Apache License 2.0; `licenses/OPENCC-APACHE-2.0-LICENSE.txt` | **Yes, SELECTED (D28)**: inverted `JPShinjitaiCharacters.txt` | No | Include the Apache 2.0 licence, retain applicable copyright/attribution notices, and mark modified files. | 2026-11-04 |

## 2. Usage log (fill in during work)

| Source # | Used in table | Columns | Notes |
|---|---|---|---|
| 1 | `chars`, `words` matching | `trad`, `simp`, `ko`, `ko_all`, `pinyin`, `pinyin_all`, `vi`, `vi_all`, `gloss_en`; compatibility/semantic variant evidence | Stage 3 loads all D43 variant fields. Character primaries follow D39; unverified Vietnamese readings are excluded from words/rules. |
| 2 | `chars`, `words` matching | `jp`, `ja_on`, `ja_on_all`; single-character Japanese fallback | KANJIDIC2 first on-reading is preserved; JMdict supplies word readings. |
| 3 | `words`, `chars` | HSK backbone; `trad`, `simp`, `pinyin`, `level`; `chars.level`, `in_hsk_chars` | Accepted (D23). Loading rules D30. |
| 4 | `words`, false-friend candidates | `simp`, dictionary pinyin boundaries, `gloss_en` | D41 exact key plus same-form/readings fallback; HSK pinyin remains authoritative. |
| 5 | `words`, false-friend candidates | `jp`, `ja`, `ja_alt`, `ja_common`, `gloss_ja_en` | D42 restrictions/ranking; entity tag names retained by the loader. |
| 6 | `words`, `chars`, false-friend candidates | `ko`, `ko_alt`, `gloss_ko`, `chars.ko_all`, Korean word inventory | Full aligned records and comments loaded; D43 variants/alignment/두음법칙 rules applied. |
| 7 | None | None | Excluded: no licence and incomplete input provenance. |
| 7A | `words`, `chars` | `words.vi` (rule A/B), `chars.vi`/`vi_all` (aligned readings), Hán-Việt syllable set, VI-only additions | Selected (D24, D27). Parsing rule in D24. |
| 7B | `words` | `freq_vi` (proxy `syllable_min`) | Selected (D26). |
| 8 | `chars` (`jp`), `words` (JMdict match) | shinjitai ↔ traditional character and phrase mappings | OpenCC chosen (D28); KANJIDIC2 validates/tie-breaks; phrase mappings are match candidates only. |

## 3. Implications to track

- If any share-alike (CC BY-SA) source is used, the **published dataset** (`data/final/*`) must be released under CC BY-SA too. App code can still use a different license (e.g. MIT). **Confirmed in Stage 1 review (D23): the dataset is CC BY-SA 4.0**; EDRDG ×2, CC-CEDICT, Kaikki and FrequencyWords are all CC BY-SA 4.0; BSD-3 (libhangul), MIT (hsk30), Unicode v3 and Apache 2.0 (OpenCC) notices must be reproduced at Final Delivery.
- Sources with no license or "non-commercial only" terms: do not use without permission.
- AI-generated content (`content/`): record which model generated it and that it was human/auditor-verified.
- Keep each source's license file in `raw/<source>/` and copy it to `licenses/` (committed; `raw/` itself is not committed).

## 4. Final attribution (written at the end)

Generated from sections 1–2 into the repo's README "Data sources" section and LICENSE files.
