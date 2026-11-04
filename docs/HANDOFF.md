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
- Stage 2 (character table): Codex built loaders and tests; the build stopped at the `着`/`著` key collision. **Resolved by Claude: D37 (merge on `trad`; 2,999 rows).** Codex resumes and finishes Stage 2.
- **PROMPT Rule 11 (stage gates) is in force.** Gate results are logged in `docs/GATES.md`. Stage 1 gate: PASS (2026-11-04). Stage 2 gate comes after Codex finishes; it checks the Stage 2 Done-when criteria, then the `rules_report.csv` review.

## Stage 1 review: outcome in brief (details in STAGE1_REVIEW.md)
- **Licences:** all accepted. hsk30 accepted with a recorded provenance risk (confirmed by the user, D35). Dataset will be **CC BY-SA 4.0**.
- **Vietnamese:** Kaikki (reading + Han form) and FrequencyWords (frequency proxy) selected. Unihan `kVietnamese` mixes Nôm readings (200-sample check: 31 covered, 29 agree; whole overlap 88%), so it is used only with verification flags. **Measured ceiling: about 35% of HSK words (3,832 / 11,092) and 61% of HSK characters (1,835 / 3,000) get a Vietnamese reading with evidence.** Cards in the Chinese target are unaffected (pinyin always exists); Vietnamese-target decks will be smaller than the HSK list. This is a source limit, not a bug; report it in `coverage_report.csv`.
- **Shinjitai:** inverted OpenCC `JPShinjitaiCharacters` (16/16 on the prototype's glyph pairs), KANJIDIC2 tie-break.

## NEXT ASSIGNMENT
**Agent: Codex — finish Stage 2: character table** (resume from commit `8ac5d66`; PROMPT "STAGE 2" and its **Done when** criteria)

Decision (DECISIONS D37, SCHEMA §1.1): characters that share one canonical `trad` are merged into one `chars` row. For the only known case, `着` and `著` in `hsk30-chars.csv`, the result is `trad=著`, `simp=着`, `level=1`, `in_hsk_chars=true`, readings from the normal sources keyed by `著`. **Expected `chars` size: 2,999 rows for the 3,000 HSK source characters.** Implement it generically (merge on `trad` with the D37 rules, not a special case for 著) and write `data/final/char_key_collisions.csv` (`trad, source_hanzi, source_level, source_row`). Do not touch anything else in the decisions; if another rule is unworkable, write it under Open problems and stop.

Finish everything in the previous Stage 2 assignment (loaders are done; remaining: `chars`, derived columns, reports, tests, `run_all.py` skeleton, validation). Replace the "3,000 rows" expectation with **2,999 rows + collision report** in the tests. Add a test that `著` has `simp=着`, `level=1`, and that the key `着` does not exist as a `trad` value.

Stage 2 **Done when** (the gate will check each with evidence, so produce the evidence in your hand-off note): `chars` covers all 3,000 HSK characters (each source character maps to one row; missing values reported, not guessed); no duplicate `char_id` or `trad`; all text NFC; the test characters among the 20 test words (學 國 茶 行 生 樂) correct in every language; `rules_report.csv` exists; tests in `tests/` pass; rebuilding twice gives identical output (give the two hashes).

Hand-off note must include: row counts per stage, `_merge` counts, coverage numbers per language column (isna counts), `jp` empty count (about 45 expected), number of characters with verified Vietnamese primary (about 1,835 expected), the 6 shinjitai tie-break outcomes, and the test run output.

When done: hand off to **Claude: Stage 2 gate** (Done-when check + `rules_report.csv` against `config/rules.json`: ㄱ→c/ch, ㅂ→p, ㄹ→t, ㄴ→n, ㅁ→m, ㅇ→ng/nh).

## Planned sequence after Stage 2 (user-approved change, DECISIONS D36)
1. Claude: Stage 2 gate → Codex: Stage 3 (words; word rules D24, D26, D27, D30-D32; VI-only additions top 1,200, bands in D27; report counts).
2. **Claude: Stage 3 gate (Done-when + 30-word sample, PROMPT Rule 11) and Vietnamese source search (D36), before Stage 4.** After Codex's Stage 3, Claude reads `coverage_report.csv` and `vi_ambiguous.csv`, then:
   - searches for additional **licensed** Vietnamese resources: a Hán-Việt character dictionary (to verify/replace Unihan's Nôm-contaminated readings), a Chinese-Vietnamese or Sino-Vietnamese word list, a Vietnamese frequency list of words (not syllables); candidates to check include Wikimedia/Wiktionary-derived data other than Kaikki, open Vietnamese dictionaries, and Chinese-Vietnamese resources on GitHub/Hugging Face/academic sites;
   - records each candidate's licence from its own licence file in `docs/SOURCES.md` before anything is used; anything unlicensed, non-commercial-only, or of unclear provenance is rejected (the user is asked only for a licence judgment call);
   - measures each licensed candidate on the same yardsticks as Stage 1 (HSK words gained, agreement with existing readings on a seeded sample, precision of new readings) and records accepted sources and rules in DECISIONS;
   - hands off to Codex (integration + rebuild of `words`, `word_chars`, rules report) or, if nothing usable is found, to Gemini (Stage 4) with the ceiling recorded.
3. Codex: integrate accepted sources, rebuild Stage 3 outputs, report new coverage.
4. Gemini: Stage 4 (sized from the post-integration coverage).

## Heads-up for Stage 3 (not for this session)
- Word rules are fixed in D24, D26, D27, D30, D31, D32. VI-only additions: top 1,200, bands in D27. Report counts when built.
- **At the end of Stage 3, hand off to Claude (Stage 3 gate, then the Vietnamese source search), not to Gemini** (D36, Rule 11). The Stage 3 Done-when criteria are in PROMPT; produce the evidence in your hand-off note.

## Notes for later stages
- **Stage 5 (Codex), user-approved addition — DECISIONS D20:** daily limit of 20 new (never-seen) cards in カード; reviews unlimited; no visible UI change except smaller counters. State in localStorage `kb_newtoday`. Add a test. List it in the Stage 5 side-by-side difference list.

## Rules to keep in mind (from PROMPT)
- No agent fills a missing reading/fact from its own knowledge. Missing stays empty and is reported.
- Do not edit `prototype/index.html`. Do not edit `SCHEMA.md`/spec/DECISIONS decisions; raise questions here in HANDOFF instead.
- If a source has no license or non-commercial-only terms: do not use it; stop and ask the user.

## Open problems / notes
- Resolved: hsk30 `着`/`著` collision → merge on `trad` (D37).
- Vietnamese coverage ceiling (about 35% of HSK words) with the current licensed sources; the search for further licensed sources runs after Stage 3, before Stage 4 (D36).
- Source #7 stays excluded (D21).
- EDRDG data impose an update-procedure requirement; `download.py --refresh` exists; release documentation must explain updates.
- hsk30 provenance risk: **accepted by the user** (D35, personal non-commercial project; revisit if ever published commercially).

## Log
- 2026-11-04 Claude — PROMPT Rule 11 (gates) adopted and committed with this session; `docs/GATES.md` created; Stage 1 gate PASS logged; `着`/`著` collision resolved (D37). Next: Codex finish Stage 2.
- 2026-11-04 Codex — Stage 2 implementation written but build stopped at the `着`/`著` canonical-key conflict. No improvised data rule; next: Claude decision, then Codex resumes Stage 2.
- 2026-11-04 Claude — applied user decisions: hsk30 accepted (D35); Vietnamese source search moved to after Stage 3 / before Stage 4 (D36). Next assignment unchanged: Codex Stage 2.
- 2026-11-04 Claude — Stage 1 review done: licences accepted, Vietnamese sources selected with verification rules, shinjitai method chosen, priorities set (D23–D34). Next: Codex Stage 2.
- 2026-11-04 Codex — Stage 1 done: downloader + checksums, all licensed-source profiles, licences copied, unlicensed Hán-Việt source excluded by user, two licensed Vietnamese replacements profiled, reproducibility verified. Next: Claude Stage 1 review.
- 2026-11-04 Claude — applied user decisions: new-card limit approved (D20); git email changed, Stage 0 commit author rewritten (D19). Next assignment unchanged.
- 2026-11-04 Claude — Stage 0 done (see CHANGELOG).
