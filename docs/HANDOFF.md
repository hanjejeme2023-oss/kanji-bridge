# HANDOFF

Read `PROMPT.md` first, then this file. Do only the assignment for your role. Update this file, `CHANGELOG.md`, `DECISIONS.md` when done; `git commit`; stop with one line `Next: <agent> — <task>`.

## Current status
- Stage 0 (setup) — **DONE** by Claude, 2026-11-04.
- Stage 1 (sources and licences) — **DONE** by Codex; **Claude review DONE** 2026-11-04. All blocking source/licence decisions are closed (DECISIONS D23–D34). Evidence: `docs/STAGE1_REVIEW.md`; reference scripts (evidence, not pipeline): `docs/review_scripts/`.
- Contract files: `docs/SCHEMA.md` (updated: level 1–7, source tags, new reports), `config/rules.json`, `docs/DECISIONS.md` (D1–D38), `docs/final-data-spec.md` (+ Addenda), `docs/SOURCES.md` (all rows now decided).
- `raw/` is git-ignored and recreated by `pipeline/download.py` (checksums in committed `pipeline/source_manifest.csv`). Licence copies are in `licenses/`.
- Git identity: `Hanje Unesaki <311183901+hanjejeme2023-oss@users.noreply.github.com>` (D19). Check `git config user.email` before committing.
- Environment: Python 3.12.10 + pandas 3.1.1 (`pipeline/requirements.txt`). On this machine the Python with pandas is `<user folder>\AppData\Local\Programs\Python\Python312\python.exe`; the `python` on the bash PATH may be a Store stub without pandas.
- Prototype: `prototype/index.html` (frozen).
- Stage 2 (character table) — **DONE** by Codex, 2026-11-04. Revised D37 is implemented as two rows with unique `key_char`; 3,000 rows and all Stage 2 reports are committed. Stage 2 gate: PASS (Claude, 2026-11-04).
- **PROMPT Rule 11 (stage gates) is in force.** Gate results are logged in `docs/GATES.md`. Stage 1 gate: PASS (2026-11-04). Stage 2 gate comes after Codex finishes; it checks the Stage 2 Done-when criteria, then the `rules_report.csv` review.

## Stage 1 review: outcome in brief (details in STAGE1_REVIEW.md)
- **Licences:** all accepted. hsk30 accepted with a recorded provenance risk (confirmed by the user, D35). Dataset will be **CC BY-SA 4.0**.
- **Vietnamese:** Kaikki (reading + Han form) and FrequencyWords (frequency proxy) selected. Unihan `kVietnamese` mixes Nôm readings (200-sample check: 31 covered, 29 agree; whole overlap 88%), so it is used only with verification flags. **Measured ceiling: about 35% of HSK words (3,832 / 11,092) and 61% of HSK characters (1,835 / 3,000) get a Vietnamese reading with evidence.** Cards in the Chinese target are unaffected (pinyin always exists); Vietnamese-target decks will be smaller than the HSK list. This is a source limit, not a bug; report it in `coverage_report.csv`.
- **Shinjitai:** inverted OpenCC `JPShinjitaiCharacters` (16/16 on the prototype's glyph pairs), KANJIDIC2 tie-break.

## NEXT ASSIGNMENT
**Agent: Codex — Stage 3: word table** (PROMPT Stage 3). Stage 2 gate: **PASS** (attempt 1, 2026-11-04; evidence in `docs/GATES.md`).

Stage 3 must apply D24, D26-D32, D37 items 5-6, D38 and **D39 (new, user decision: primary character readings from word evidence)**. Additional points from the Stage 2 gate:
- Align `word_chars` with the word-level Korean reading (libhangul) and `chars.ko_all`; do not use `chars.ko` (first Unihan value, e.g. 行 = 항, 茶 = 다, 樂 = 낙; valid but not the common reading).
- **D39 (after `word_chars`):** set each `chars` primary (`ko`, `vi`, `ja_on`, `pinyin`, hence `ko_final`/`vi_final`) to the reading most used across aligned words; ties keep current order; `*_all` unchanged. Write `data/final/char_primary_changes.csv` and `data/final/char_primary_no_evidence.csv` (characters with no word evidence keep the current value). Add a test: 行→행, 茶→차 (or 다 if the words say so), 樂→락 or 악 as the words say. Then rebuild `rules_report.csv`. This replaces the earlier instruction to avoid `chars.ko`: align `word_chars` first with the word reading and `ko_all`, then update the primaries.
- Rebuild `rules_report.csv` from verified readings only (`kaikki_aligned`, `unihan_hvsyl`; never `unihan_unverified`), as in Stage 2. Gate-verified: 0 unverified readings in the Stage 2 report.
- Create the 88 missing C2 traditional-variant rows in `chars`; at the end, 0 unlinked word characters. Hand-off note must show C1/C2 evidence (row counts before/after growth, `char_simp_mismatch.csv`, `char_ambiguous.csv`).
- **Added to the Stage 3 Done-when (D39):** every `chars` primary reading equals the most frequent reading in aligned words (ties: previous order); `char_primary_changes.csv` and `char_primary_no_evidence.csv` exist with row counts reported; the test passes (行→행, 茶→차 or 다 per words, 樂→락 or 악 per words); `*_all` columns unchanged; `rules_report.csv` rebuilt after the change and still uses verified Vietnamese readings only; rebuild twice is identical.
- At the end, hand off to **Claude (Stage 3 gate, then Vietnamese source search, D36)**, not to Gemini.

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
- **At the end of Stage 3, hand off to Claude (Stage 3 gate, then the Vietnamese source search), not to Gemini** (D36, Rule 11). The Stage 3 Done-when criteria are in PROMPT; the C1/C2 collision checks (D38) are rerun at that gate after `chars` has grown: produce the evidence (row counts before/after growth, `char_simp_mismatch.csv`, `char_ambiguous.csv`) in your hand-off note.

## Notes for later stages
- **Stage 5 (Codex), user-approved addition — DECISIONS D20:** daily limit of 20 new (never-seen) cards in カード; reviews unlimited; no visible UI change except smaller counters. State in localStorage `kb_newtoday`. Add a test. List it in the Stage 5 side-by-side difference list.

## Rules to keep in mind (from PROMPT)
- No agent fills a missing reading/fact from its own knowledge. Missing stays empty and is reported.
- Do not edit `prototype/index.html`. Do not edit `SCHEMA.md`/spec/DECISIONS decisions; raise questions here in HANDOFF instead.
- If a source has no license or non-commercial-only terms: do not use it; stop and ask the user.

## Open problems / notes
- Stage 2 gate notes (non-blocking): (1) `chars.ko` primary is the first Unihan value (行 항, 茶 다, 樂 낙); use word-level readings and `ko_all` in Stage 3. (2) Suspect Vietnamese readings for loop 1 accuracy: 怎 chẩn (expected chẩm; `unihan_hvsyl`), 幻 ảo (usual Hán-Việt huyễn). (3) `unihan_hvsyl` (300 chars) is a weaker check than `kaikki_aligned`.
- Resolved: hsk30 `着`/`著` collision → separate rows with `key_char` (D37, revised).
- Vietnamese coverage ceiling (about 35% of HSK words) with the current licensed sources; the search for further licensed sources runs after Stage 3, before Stage 4 (D36).
- Source #7 stays excluded (D21).
- EDRDG data impose an update-procedure requirement; `download.py --refresh` exists; release documentation must explain updates.
- hsk30 provenance risk: **accepted by the user** (D35, personal non-commercial project; revisit if ever published commercially).

## Log
- 2026-11-04 Claude — user decision D39 recorded (primary readings from word evidence); added to the Stage 3 task. Next: Codex Stage 3.
- 2026-11-04 Claude — Stage 2 gate PASS: all Done-when criteria re-verified (16 tests rerun OK); `rules_report.csv` uses only verified readings (0 unihan_unverified, 主 = chủ); 7 off-pattern characters reviewed (5 real exceptions, 2 flagged). Next: Codex Stage 3.
- 2026-11-04 Codex — Stage 2 completed: 3,000-character table, D37 `key_char` collision handling, C1/C2 tests, reports, and reproducible outputs; 16 tests pass and consecutive hashes match. Next: Claude Stage 2 gate.
- 2026-11-04 Claude — user asked for the one→many check. Measured: 83 HSK rows / 89 variants / 88 need new rows; solved by linking words through their own `trad` (D38). Found and fixed an error in D37/HANDOFF: `key_char` must be `trad` (not source Hanzi) except for 着/著. Added standing checks C1/C2 to GATES.md. Next: Codex finish Stage 2.
- 2026-11-04 Claude — user challenged D37: 着/著 are distinct Korean/Japanese characters (着 is HSK 1). Verified in Unihan (착 vs 저), KANJIDIC2, libhangul (接着→접착). D37 rewritten: two rows, `key_char`, link words by simp then pinyin. Next: Codex finish Stage 2.
- 2026-11-04 Claude — PROMPT Rule 11 (gates) adopted and committed with this session; `docs/GATES.md` created; Stage 1 gate PASS logged; `着`/`著` collision resolved (D37). Next: Codex finish Stage 2.
- 2026-11-04 Codex — Stage 2 implementation written but build stopped at the `着`/`著` canonical-key conflict. No improvised data rule; next: Claude decision, then Codex resumes Stage 2.
- 2026-11-04 Claude — applied user decisions: hsk30 accepted (D35); Vietnamese source search moved to after Stage 3 / before Stage 4 (D36). Next assignment unchanged: Codex Stage 2.
- 2026-11-04 Claude — Stage 1 review done: licences accepted, Vietnamese sources selected with verification rules, shinjitai method chosen, priorities set (D23–D34). Next: Codex Stage 2.
- 2026-11-04 Codex — Stage 1 done: downloader + checksums, all licensed-source profiles, licences copied, unlicensed Hán-Việt source excluded by user, two licensed Vietnamese replacements profiled, reproducibility verified. Next: Claude Stage 1 review.
- 2026-11-04 Claude — applied user decisions: new-card limit approved (D20); git email changed, Stage 0 commit author rewritten (D19). Next assignment unchanged.
- 2026-11-04 Claude — Stage 0 done (see CHANGELOG).
