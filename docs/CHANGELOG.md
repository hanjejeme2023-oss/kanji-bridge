# CHANGELOG

## 2026-11-04 — Stage 0: setup [Claude]
- Created folder layout (`raw/ pipeline/ config/ content/accepted/ data/staging/ data/final/ app/ tests/ licenses/`), `.gitignore`, `git init`.
- `docs/SCHEMA.md`: exact columns, ID rules, `data.js` shape, and field-by-field mapping from `WORDS`/`RULES`/`FF`/`PASSAGES`/`GLYPHS` to tables.
- `config/rules.json`: the 6 rules' text copied verbatim from the prototype.
- `docs/DECISIONS.md` (D1–D11 + new D12–D19), `docs/HANDOFF.md`, spec Addenda section.
- Why: PROMPT Stage 0. D12–D19 fill gaps that real data forces (stable word ids, multiple readings, large passage list) without touching UI/UX.

## 2026-11-04 — User decisions applied [Claude]
- DECISIONS D20: daily new-card limit (20/day) approved for Stage 5; D18 superseded; UX_BACKLOG #1 marked approved.
- D19: repo-local git email changed to 311183901+hanjejeme2023-oss@users.noreply.github.com; Stage 0 commit author rewritten (unpushed).

## 2026-11-04 — Stage 1: sources and licences [Codex]
- Added `pipeline/download.py`: standard-library downloader with atomic writes, retries, committed `pipeline/source_manifest.csv` URL/date/SHA-256/byte locks (mirrored to `raw/MANIFEST.csv`), idempotent verification, explicit `--refresh`, and synchronization of source licence files into committed `licenses/`.
- Downloaded and profiled Unihan, KANJIDIC2, hsk30, CC-CEDICT, JMdict, libhangul `hanja.txt`, and OpenCC Japanese mapping candidates. Raw files remain git-ignored.
- Excluded `ryanphung/chinese-hanviet-cognates` by user decision (D21): no licence grant and an input with missing provenance. No content from it was downloaded or copied.
- Downloaded and profiled two licensed Vietnamese replacement candidates without selecting either (D22): Kaikki/Vietnamese Wiktionary (6,878 Hán-Việt-marked Vietnamese entries; 4,653 with CJK strings in etymology text) and FrequencyWords/OpenSubtitles 2018 (50,000 token-frequency rows).
- Added reproducible `pipeline/profile_sources.py`, `pipeline/requirements.txt`, and generated `docs/SOURCE_PROFILES.md` with formats, encodings, counts, keys, ten-row samples, quality risks, mapping candidates, and review questions.
- Completed `docs/SOURCES.md` licence and planned-usage logs. Ambiguous hsk30 provenance and libhangul per-file licence remain marked `要確認` for Claude; all share-alike effects are called out.

## 2026-11-04 — Stage 2: implementation started, blocked on canonical key [Codex]
- Implemented the Stage 2 pipeline structure: shared NFC/Vietnamese/pinyin/phonology/ID helpers; per-source loaders for Unihan, KANJIDIC2, hsk30, OpenCC, libhangul, Kaikki, and FrequencyWords; the character builder/reports; `run_all.py`; and Stage 2 unit/rebuild tests.
- First build correctly detected a contract conflict in the raw HSK character list: source rows `着 → 著` (level 1) and `著 → 著` (level 4) both produce canonical `trad=著` under D33. This conflicts with the simultaneous requirements for 3,000 rows and a unique `trad` key. No row was dropped, renamed, or overridden because HANDOFF explicitly forbids improvising a rule.
- Pipeline stopped at the hsk30 loader validation. Claude must decide whether to merge to 2,999 canonical rows, introduce a documented `着` exception to keep 3,000 unique rows, or revise another contract requirement. No Stage 2 final tables are claimed complete.

## 2026-11-04 — Stage 1 review [Claude]
- Confirmed licences (D23): all sources usable; dataset will be CC BY-SA 4.0; hsk30 provenance risk accepted and recorded.
- Selected Vietnamese inputs (D24-D27): Kaikki for readings/Han forms, FrequencyWords for a frequency proxy; Unihan `kVietnamese` gated by verification flags after the 200-character cross-check (`docs/STAGE1_REVIEW.md`).
- Chose the shinjitai method (D28: inverted OpenCC + KANJIDIC2 tie-break, 16/16 on the prototype glyphs); fixed level semantics (D29); hsk30/JMdict/libhangul rules (D30-D32); source priority per column (D33).
- Updated SCHEMA (levels 1-7, source tags, new reports) and SOURCES (all rows decided). Saved reference scripts in `docs/review_scripts/`.
- Why: the review closes every blocking decision so Stage 2 can build `chars` without improvisation. The measured Vietnamese ceiling (about 35% of HSK words) is recorded as a source limit.

## 2026-11-04 — User decisions applied [Claude]
- D35: hsk30 provenance risk accepted by the user (personal, non-commercial; revisit if published commercially).
- D36: search for additional licensed Vietnamese sources moved to after Stage 3, before Stage 4; new Claude task recorded in HANDOFF.md. Next assignment unchanged (Codex, Stage 2).

## 2026-11-04 — Stage gates and Stage 2 key collision [Claude]
- PROMPT updated by the user (Rule 11: stage gates, Done-when criteria); committed together with this change. Created `docs/GATES.md`; logged the Stage 1 gate (PASS, evidence: 23/23 checksums, download rerun, licences, profiles).
- (SUPERSEDED by the entry below) D37: canonical-key collisions in `chars` are merged on `trad` (hsk30 `着`/`著` -> `trad=著`, `simp=着`, `level=1`); `chars` has 2,999 rows for 3,000 source characters, plus `char_key_collisions.csv`. SCHEMA updated. Why: words use the traditional form `著`; duplicate or exception keys would break IDs, merges and tests.

## 2026-11-04 — D37 revised [Claude, at the user's request]
- The earlier D37 merged 着/著 into one row keyed `著` and would have taken every reading from `著`, losing 着's Korean 착 and Japanese ちゃく. Replaced by: one row per source character (3,000 rows), `trad` non-unique, new unique column `key_char` (readings lookup + id_map key), word-to-character linking by simp then pinyin, Korean/Japanese word matching also on the `key_char` form (接著 -> 接着), glyph view uses `key_char`. Updated DECISIONS, SCHEMA, spec addenda, Stage 2 task.

## 2026-11-04 — One-to-many collision check [Claude, at the user's request]
- Measured the one simplified -> several traditional case: 83/3,000 HSK rows (89 variant characters, 88 without a row yet). D38: link words through their own `trad` string, extend `chars` in Stage 3 for every word character lacking a row, simp rule for added rows, position check against the word's `simp`.
- Corrected D37: `key_char = trad` for all rows except shared-`trad` rows (using the simplified Hanzi everywhere would find Korean readings for only 145 of 1,088 differing rows instead of 1,036).
- Added the standing C1 (many->one) and C2 (one->many) checks to `docs/GATES.md`, Stage 2 and Stage 3 tasks; reference script `docs/review_scripts/char_collision_reference.py`.
