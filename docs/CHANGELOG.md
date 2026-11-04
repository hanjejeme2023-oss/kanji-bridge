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

## 2026-11-04 — Stage 1 review [Claude]
- Confirmed licences (D23): all sources usable; dataset will be CC BY-SA 4.0; hsk30 provenance risk accepted and recorded.
- Selected Vietnamese inputs (D24-D27): Kaikki for readings/Han forms, FrequencyWords for a frequency proxy; Unihan `kVietnamese` gated by verification flags after the 200-character cross-check (`docs/STAGE1_REVIEW.md`).
- Chose the shinjitai method (D28: inverted OpenCC + KANJIDIC2 tie-break, 16/16 on the prototype glyphs); fixed level semantics (D29); hsk30/JMdict/libhangul rules (D30-D32); source priority per column (D33).
- Updated SCHEMA (levels 1-7, source tags, new reports) and SOURCES (all rows decided). Saved reference scripts in `docs/review_scripts/`.
- Why: the review closes every blocking decision so Stage 2 can build `chars` without improvisation. The measured Vietnamese ceiling (about 35% of HSK words) is recorded as a source limit.

## 2026-11-04 — User decisions applied [Claude]
- D35: hsk30 provenance risk accepted by the user (personal, non-commercial; revisit if published commercially).
- D36: search for additional licensed Vietnamese sources moved to after Stage 3, before Stage 4; new Claude task recorded in HANDOFF.md. Next assignment unchanged (Codex, Stage 2).
