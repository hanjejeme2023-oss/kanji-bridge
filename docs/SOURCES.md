# SOURCES: data source & license log

Rule: **check the license when downloading (before using), write the attribution at the end.**
Each row is completed when the source is first downloaded (Stage 1), from the source's own license file. "要確認" = not verified yet.

Last updated: 2026-11-04

---

## 1. License check (fill in at download time)

| # | Source | URL | Version / date downloaded | License | Can we use it? | Share-alike? | Attribution text required | Checked on |
|---|---|---|---|---|---|---|---|---|
| 1 | Unihan database | unicode.org (Unihan.zip) | | Unicode License (要確認) | 要確認 | 要確認 | 要確認 | |
| 2 | KANJIDIC2 | EDRDG | | CC BY-SA (要確認) | 要確認 | ⚠️ likely yes | 要確認 | |
| 3 | ivankra/hsk30 | github.com/ivankra/hsk30 | | MIT per README (data derived from other MIT repos; 要確認) | 要確認 | | | |
| 4 | CC-CEDICT | mdbg.net | | CC BY-SA 4.0 (要確認) | 要確認 | ⚠️ likely yes | | |
| 5 | JMdict | EDRDG | | CC BY-SA (要確認) | 要確認 | ⚠️ likely yes | | |
| 6 | libhangul hanja.txt | github.com/choehwanjin/libhangul | | 要確認 | 要確認 | | | |
| 7 | chinese-hanviet-cognates | GitHub (URL 要確認) | | 要確認 | 要確認 | | | |
| 8 | Shinjitai ↔ traditional mapping | TBD in Stage 1 | | 要確認 | 要確認 | | | |

## 2. Usage log (fill in during work)

| Source # | Used in table | Columns | Notes |
|---|---|---|---|
| | | | |

## 3. Implications to track

- If any share-alike (CC BY-SA) source is used, the **published dataset** (`data/final/*`) must be released under CC BY-SA too. App code can still use a different license (e.g. MIT).
- Sources with no license or "non-commercial only" terms: do not use without permission.
- AI-generated content (`content/`): record which model generated it and that it was human/auditor-verified.
- Keep each source's license file in `raw/<source>/` and copy it to `licenses/` (committed; `raw/` itself is not committed).

## 4. Final attribution (written at the end)

Generated from sections 1–2 into the repo's README "Data sources" section and LICENSE files.
