# HANDOFF

Read `PROMPT.md` first, then this file. Do only the assignment for your role. Update this file, `CHANGELOG.md`, `DECISIONS.md` when done; `git commit`; stop with one line `Next: <agent> — <task>`.

## Current status
- Stage 0 (setup) — **DONE** by Claude, 2026-11-04.
- Stage 1 (sources and licences) — **DONE** by Codex; **Claude review DONE** 2026-11-04. All blocking source/licence decisions are closed (DECISIONS D23–D34). Evidence: `docs/STAGE1_REVIEW.md`; reference scripts (evidence, not pipeline): `docs/review_scripts/`.
- Contract files: `docs/SCHEMA.md` (updated: level 1–7, source tags, new reports), `config/rules.json`, `docs/DECISIONS.md` (D1–D34), `docs/final-data-spec.md` (+ Addenda), `docs/SOURCES.md` (all rows now decided).
- `raw/` is git-ignored and recreated by `pipeline/download.py` (checksums in committed `pipeline/source_manifest.csv`). Licence copies are in `licenses/`.
- Git identity: `Hanje Unesaki <311183901+hanjejeme2023-oss@users.noreply.github.com>` (D19). Check `git config user.email` before committing.
- Environment: Python 3.12.10 + pandas 3.1.1 (`pipeline/requirements.txt`). On this machine the Python with pandas is `<user folder>\AppData\Local\Programs\Python\Python312\python.exe`; the `python` on the bash PATH may be a Store stub without pandas.
- Prototype: `prototype/index.html` (frozen).
- Stage 2 implementation is **BLOCKED pending one Claude decision**: the HSK character rows `着 → 著` and `著 → 著` collide under canonical `trad=著`. See Open problems and the next assignment below. Codex did not invent an exception.

## Stage 1 review: outcome in brief (details in STAGE1_REVIEW.md)
- **Licences:** all accepted. hsk30 accepted with a recorded provenance risk (confirmed by the user, D35). Dataset will be **CC BY-SA 4.0**.
- **Vietnamese:** Kaikki (reading + Han form) and FrequencyWords (frequency proxy) selected. Unihan `kVietnamese` mixes Nôm readings (200-sample check: 31 covered, 29 agree; whole overlap 88%), so it is used only with verification flags. **Measured ceiling: about 35% of HSK words (3,832 / 11,092) and 61% of HSK characters (1,835 / 3,000) get a Vietnamese reading with evidence.** Cards in the Chinese target are unaffected (pinyin always exists); Vietnamese-target decks will be smaller than the HSK list. This is a source limit, not a bug; report it in `coverage_report.csv`.
- **Shinjitai:** inverted OpenCC `JPShinjitaiCharacters` (16/16 on the prototype's glyph pairs), KANJIDIC2 tie-break.

## NEXT ASSIGNMENT
**Agent: Claude — resolve the Stage 2 `着` / `著` canonical-key conflict**

Evidence from checksum-locked `raw/hsk30/hsk30-chars.csv`:

- `着,1,1,著,36,...`
- `著,4,3,著,5,...`

D33 says `chars.trad = hsk30-chars Traditional (first value)`, so both become `trad=著`. SCHEMA §1.1 and the required tests say `trad` is unique; HANDOFF also expects exactly 3,000 character rows. These requirements cannot all hold simultaneously:

1. **Merge the two source rows at canonical `著`** → correct traditional-key normalization, but 2,999 rows and two HSK levels/source simplified forms need an explicit resolution rule.
2. **Keep `着` as canonical `trad=着` for its source row** → 3,000 unique rows and preserves both simplified-source characters, but creates a documented exception to D33/global traditional-key policy.
3. **Allow duplicate `trad=著`** → preserves 3,000 rows but breaks the schema, stable ID key, merge validation, and duplicate-key tests; not recommended.

Claude must choose and record the exact rule in `DECISIONS.md`/`SCHEMA.md`, update the expected Stage 2 row count if needed, then hand back to **Codex — finish Stage 2 character table**. The partial implementation is committed and ready to resume; do not perform the Stage 2 sound-rule review yet because final tables do not exist.

Validation completed before stopping: all Python files compile; the Vietnamese normalizer, Hangul-final, and numbered-pinyin tests pass; every non-HSK loader ran successfully (Unihan 50,934 NFC keys; KANJIDIC2 13,033 NFC keys after compatibility-form aggregation; OpenCC 414 non-identity character pairs; libhangul 28,460 single-character readings; Kaikki 3,373 explicit pairs / 1,743 aligned characters; FrequencyWords 47,362 normalized tokens). The full build intentionally fails at the HSK duplicate-key assertion.

## Planned sequence after Stage 2 (user-approved change, DECISIONS D36)
1. Claude: Stage 2 review → Codex: Stage 3 (words; word rules D24, D26, D27, D30-D32; VI-only additions top 1,200, bands in D27; report counts).
2. **Claude: Vietnamese source search (new task, before Stage 4).** After Codex's Stage 3, Claude reads `coverage_report.csv` and `vi_ambiguous.csv`, then:
   - searches for additional **licensed** Vietnamese resources: a Hán-Việt character dictionary (to verify/replace Unihan's Nôm-contaminated readings), a Chinese-Vietnamese or Sino-Vietnamese word list, a Vietnamese frequency list of words (not syllables); candidates to check include Wikimedia/Wiktionary-derived data other than Kaikki, open Vietnamese dictionaries, and Chinese-Vietnamese resources on GitHub/Hugging Face/academic sites;
   - records each candidate's licence from its own licence file in `docs/SOURCES.md` before anything is used; anything unlicensed, non-commercial-only, or of unclear provenance is rejected (the user is asked only for a licence judgment call);
   - measures each licensed candidate on the same yardsticks as Stage 1 (HSK words gained, agreement with existing readings on a seeded sample, precision of new readings) and records accepted sources and rules in DECISIONS;
   - hands off to Codex (integration + rebuild of `words`, `word_chars`, rules report) or, if nothing usable is found, to Gemini (Stage 4) with the ceiling recorded.
3. Codex: integrate accepted sources, rebuild Stage 3 outputs, report new coverage.
4. Gemini: Stage 4 (sized from the post-integration coverage).

## Heads-up for Stage 3 (not for this session)
- Word rules are fixed in D24, D26, D27, D30, D31, D32. VI-only additions: top 1,200, bands in D27. Report counts when built.
- **At the end of Stage 3, hand off to Claude (Vietnamese source search), not to Gemini** (D36).

## Notes for later stages
- **Stage 5 (Codex), user-approved addition — DECISIONS D20:** daily limit of 20 new (never-seen) cards in カード; reviews unlimited; no visible UI change except smaller counters. State in localStorage `kb_newtoday`. Add a test. List it in the Stage 5 side-by-side difference list.

## Rules to keep in mind (from PROMPT)
- No agent fills a missing reading/fact from its own knowledge. Missing stays empty and is reported.
- Do not edit `prototype/index.html`. Do not edit `SCHEMA.md`/spec/DECISIONS decisions; raise questions here in HANDOFF instead.
- If a source has no license or non-commercial-only terms: do not use it; stop and ask the user.

## Open problems / notes
- **BLOCKING:** hsk30 character canonical collision: `着 → 著` and `著 → 著`. D33 yields duplicate `trad=著`; merging yields 2,999 rows, while keeping 3,000 requires an explicit exception. Claude must decide; Codex stopped at loader validation as instructed.
- Vietnamese coverage ceiling (about 35% of HSK words) with the current licensed sources; the search for further licensed sources runs after Stage 3, before Stage 4 (D36).
- Source #7 stays excluded (D21).
- EDRDG data impose an update-procedure requirement; `download.py --refresh` exists; release documentation must explain updates.
- hsk30 provenance risk: **accepted by the user** (D35, personal non-commercial project; revisit if ever published commercially).

## Log
- 2026-11-04 Codex — Stage 2 implementation written but build stopped at the `着`/`著` canonical-key conflict. No improvised data rule; next: Claude decision, then Codex resumes Stage 2.
- 2026-11-04 Claude — applied user decisions: hsk30 accepted (D35); Vietnamese source search moved to after Stage 3 / before Stage 4 (D36). Next assignment unchanged: Codex Stage 2.
- 2026-11-04 Claude — Stage 1 review done: licences accepted, Vietnamese sources selected with verification rules, shinjitai method chosen, priorities set (D23–D34). Next: Codex Stage 2.
- 2026-11-04 Codex — Stage 1 done: downloader + checksums, all licensed-source profiles, licences copied, unlicensed Hán-Việt source excluded by user, two licensed Vietnamese replacements profiled, reproducibility verified. Next: Claude Stage 1 review.
- 2026-11-04 Claude — applied user decisions: new-card limit approved (D20); git email changed, Stage 0 commit author rewritten (D19). Next assignment unchanged.
- 2026-11-04 Claude — Stage 0 done (see CHANGELOG).
