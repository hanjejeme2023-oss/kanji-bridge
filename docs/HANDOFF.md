# HANDOFF

Read `PROMPT.md` first, then this file. Do only the assignment for your role. Update this file, `CHANGELOG.md`, `DECISIONS.md` when done; `git commit`; stop with one line `Next: <agent> — <task>`.

## Current status
- Stage 0 (setup) — **DONE** by Claude, 2026-11-04.
- Contract files: `docs/SCHEMA.md` (columns, IDs, `data.js` shape, view mappings), `config/rules.json`, `docs/DECISIONS.md` (D1–D20), `docs/final-data-spec.md` (+ Addenda).
- Folder layout exists. `raw/` is git-ignored. Git identity is set in repo-local config.
- Prototype: `prototype/index.html` (frozen). `prototype/PUT_INDEX_HTML_HERE.txt` is a leftover placeholder; ignore it.
- Git identity changed 2026-11-04 to `Hanje Unesaki <311183901+hanjejeme2023-oss@users.noreply.github.com>` (D19); Stage 0 commit rewritten. Check `git config user.email` before committing.
- Environment: Python 3.12.10, Git 2.56 available on Windows. pandas etc. not checked; Codex installs what it needs (ask the user to approve installs).

## NEXT ASSIGNMENT
**Agent: Codex — Stage 1: sources and licenses** (PROMPT "STAGE 1", steps 1–4)

1. Write `pipeline/download.py`. For each source in `docs/SOURCES.md` it downloads into `raw/<source>/`, with the source's own license file, and writes `raw/MANIFEST.csv` (source, url, date, sha256, bytes). Also recreate from recorded URLs + checksums on a second run (idempotent; verify checksum, don't re-download if it matches).
   - URL hints (verify, they are not guaranteed): Unihan `https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip` (license: `https://www.unicode.org/license.txt`); KANJIDIC2 and JMdict from `https://www.edrdg.org/` (`kanjidic2.xml.gz`, `JMdict_e.gz`; licence page on edrdg.org); CC-CEDICT from `https://www.mdbg.net/chinese/export/cedict/` (zip); `github.com/ivankra/hsk30`; libhangul `hanja/hanja.txt`; chinese-hanviet-cognates (GitHub URL unknown — search; if you cannot find it, **ask the user**, do not substitute silently).
   - Source #8 (shinjitai ↔ traditional mapping): do NOT decide a method. Download candidate material (e.g. KANJIDIC2 variants, Unihan variant fields, OpenCC `JPVariants*` tables) and describe each in SOURCE_PROFILES; Claude chooses.
2. Fill `docs/SOURCES.md` section 1 from each source's **own license file** (quote the license name/version and the attribution wording). Copy each license file to `licenses/` (commit it). Mark anything unclear as 要確認; do not guess.
3. Write `docs/SOURCE_PROFILES.md`: per source — format, encoding, row count, key columns, 10 sample rows, quality problems.
4. Use the standard for loading in PROMPT "DATA RULES" (utf-8, NFC, `keep_default_na=False`) for any profiling code; profiling scripts go in `pipeline/` (e.g. `profile_sources.py`) so they can be rerun.
5. Commit as `[Codex] Stage 1: download + profiles`.

Things to flag for Claude's review (write them in a "Review questions" list at the end of SOURCE_PROFILES.md):
- License of libhangul `hanja.txt` (libhangul is LGPL; check the data file's own header) and whether combining with CC BY-SA sources is a problem.
- Whether the HSK 3.0 character list in ivankra/hsk30 has per-character levels (SCHEMA `chars.level`).
- Which columns the Sino-Vietnamese source has (frequency? word-level?) and its license.
- Unihan `kVietnamese` coverage vs. the Sino-Vietnamese source (Claude will cross-check 200 chars).

Then hand off to **Claude: Stage 1 review** (license confirmation, 200-char kVietnamese cross-check, shinjitai mapping method, source priority per column).

## Notes for later stages
- **Stage 5 (Codex), user-approved addition — DECISIONS D20:** daily limit of 20 new (never-seen) cards in カード; reviews unlimited; no visible UI change except smaller counters. State in localStorage `kb_newtoday`. Add a test. List it in the Stage 5 side-by-side difference list.

## Rules to keep in mind (from PROMPT)
- No agent fills a missing reading/fact from its own knowledge. Missing stays empty and is reported.
- Do not edit `prototype/index.html`. Do not edit `SCHEMA.md`/spec/DECISIONS decisions; raise questions here in HANDOFF instead.
- If a source has no license or non-commercial-only terms: do not use it; stop and ask the user.

## Open problems / notes
- None yet.

## Log
- 2026-11-04 Claude — applied user decisions: new-card limit approved (D20); git email changed, Stage 0 commit author rewritten (D19). Next assignment unchanged.
- 2026-11-04 Claude — Stage 0 done (see CHANGELOG).
