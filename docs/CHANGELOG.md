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
