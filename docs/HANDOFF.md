# HANDOFF

Read `PROMPT.md` first, then this file. Do only the assignment for your role. Update this file, `CHANGELOG.md`, `DECISIONS.md` when done; `git commit`; stop with one line `Next: <agent> — <task>`.

## Current status
- Stage 0 (setup) — **DONE** by Claude, 2026-11-04.
- Stage 1 (sources and licences) — **DONE** by Codex, 2026-11-04.
- Contract files: `docs/SCHEMA.md` (columns, IDs, `data.js` shape, view mappings), `config/rules.json`, `docs/DECISIONS.md` (D1–D22), `docs/final-data-spec.md` (+ Addenda).
- Folder layout exists. `raw/` is git-ignored. Git identity is set in repo-local config.
- Prototype: `prototype/index.html` (frozen). `prototype/PUT_INDEX_HTML_HERE.txt` is a leftover placeholder; ignore it.
- Git identity changed 2026-11-04 to `Hanje Unesaki <311183901+hanjejeme2023-oss@users.noreply.github.com>` (D19); Stage 0 commit rewritten. Check `git config user.email` before committing.
- Environment: Python 3.12.10, Git 2.56, pandas 3.1.1 installed. Pinned in `pipeline/requirements.txt`.
- Stage 1 reproducibility: `pipeline/download.py` downloaded and SHA-256-locked all approved files in committed `pipeline/source_manifest.csv` (mirrored to ignored `raw/MANIFEST.csv`); a second run verified every file without re-downloading. `pipeline/profile_sources.py` regenerated `docs/SOURCE_PROFILES.md` byte-identically after compile validation.
- Committed licence copies are in `licenses/`; `docs/SOURCES.md` sections 1–2 are populated.

## NEXT ASSIGNMENT
**Agent: Claude — Stage 1 review** (PROMPT "STAGE 1", Claude review)

Read `docs/SOURCES.md`, `docs/SOURCE_PROFILES.md`, committed files in `licenses/`, and exact raw checksums from `pipeline/source_manifest.csv` (local files are under ignored `raw/`).

1. Confirm every licence judgment, especially:
   - hsk30: repository MIT, but README flags uncertain PRC Ministry of Education provenance (`要確認`).
   - libhangul: repository LGPL-2.1, but `hanja.txt` carries its own BSD 3-Clause header (`要確認`). Confirm that header governs the data and its combination with CC BY-SA output.
   - Share-alike impact of EDRDG, CC-CEDICT, and whichever Vietnamese candidates are selected.
2. Select or reject the Vietnamese replacement candidates (D22; do not use excluded D21 source):
   - **Kaikki/Vietnamese Wiktionary:** 6,878 Hán-Việt-marked Vietnamese entries; 4,653 include CJK strings in etymology text; word-oriented, no frequency.
   - **FrequencyWords/OpenSubtitles 2018:** 50,000 token-count rows; usable CC BY-SA licence, but syllable-token frequency does not directly rank multi-syllable words.
   Record the chosen input(s), join/frequency rule, and source priority. If neither is sufficient, assign a new licensed-source search rather than relaxing licence rules.
3. Cross-check a fixed/reproducible sample of 200 Unihan `kVietnamese` readings against the selected licensed Vietnamese data. Kaikki may not supply enough character-level pairs; document the measurable coverage and decide whether a separate licensed character source is required.
4. Choose the Japanese shinjitai ↔ traditional mapping method among:
   - OpenCC: 403 character + 235 phrase mappings, Apache 2.0, explicit but sometimes multi-target.
   - KANJIDIC2 variants: 4,675 variant values, not a direct preferred-form map.
   - Unihan `kTraditionalVariant` / `kSimplifiedVariant`: broad many-to-many CJK mappings.
   Record tie-breaks and ambiguity handling.
5. Confirm hsk30 `chars.level`: the source has 3,000 characters with per-character first-appearance levels (300 each at 1–6, 1,200 at 7–9).
6. Set source priority per output column in `DECISIONS.md`.
7. Update HANDOFF and commit, then hand off to **Codex — Stage 2: character table** only after all blocking source/licence decisions are closed.

## Notes for later stages
- **Stage 5 (Codex), user-approved addition — DECISIONS D20:** daily limit of 20 new (never-seen) cards in カード; reviews unlimited; no visible UI change except smaller counters. State in localStorage `kb_newtoday`. Add a test. List it in the Stage 5 side-by-side difference list.

## Rules to keep in mind (from PROMPT)
- No agent fills a missing reading/fact from its own knowledge. Missing stays empty and is reported.
- Do not edit `prototype/index.html`. Do not edit `SCHEMA.md`/spec/DECISIONS decisions; raise questions here in HANDOFF instead.
- If a source has no license or non-commercial-only terms: do not use it; stop and ask the user.

## Open problems / notes
- Source #7 is permanently excluded (D21): no licence and missing input provenance. No file/sample was copied.
- hsk30 and libhangul remain `要確認` pending Claude's licence review.
- The two Vietnamese candidates are profiled but intentionally not selected. Kaikki lacks corpus frequency; FrequencyWords lacks multi-syllable word ranks.
- A licensed character-level Vietnamese comparison source may still be needed if Kaikki cannot support the required 200-character cross-check.
- EDRDG data impose an update-procedure requirement; the checksum-locked downloader supports deliberate `--refresh`, but release documentation must explain updates.

## Log
- 2026-11-04 Codex — Stage 1 done: downloader + checksums, all licensed-source profiles, licences copied, unlicensed Hán-Việt source excluded by user, two licensed Vietnamese replacements profiled, reproducibility verified. Next: Claude Stage 1 review.
- 2026-11-04 Claude — applied user decisions: new-card limit approved (D20); git email changed, Stage 0 commit author rewritten (D19). Next assignment unchanged.
- 2026-11-04 Claude — Stage 0 done (see CHANGELOG).
