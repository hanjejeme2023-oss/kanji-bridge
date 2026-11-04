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
- Stage 2 (character table) — **DONE** by Codex, 2026-11-04. Revised D37 is implemented as two rows with unique `key_char`; 3,000 rows and all Stage 2 reports are committed. Awaiting Claude's Stage 2 gate.
- **PROMPT Rule 11 (stage gates) is in force.** Gate results are logged in `docs/GATES.md`. Stage 1 gate: PASS (2026-11-04). Stage 2 gate comes after Codex finishes; it checks the Stage 2 Done-when criteria, then the `rules_report.csv` review.

## Stage 1 review: outcome in brief (details in STAGE1_REVIEW.md)
- **Licences:** all accepted. hsk30 accepted with a recorded provenance risk (confirmed by the user, D35). Dataset will be **CC BY-SA 4.0**.
- **Vietnamese:** Kaikki (reading + Han form) and FrequencyWords (frequency proxy) selected. Unihan `kVietnamese` mixes Nôm readings (200-sample check: 31 covered, 29 agree; whole overlap 88%), so it is used only with verification flags. **Measured ceiling: about 35% of HSK words (3,832 / 11,092) and 61% of HSK characters (1,835 / 3,000) get a Vietnamese reading with evidence.** Cards in the Chinese target are unaffected (pinyin always exists); Vietnamese-target decks will be smaller than the HSK list. This is a source limit, not a bug; report it in `coverage_report.csv`.
- **Shinjitai:** inverted OpenCC `JPShinjitaiCharacters` (16/16 on the prototype's glyph pairs), KANJIDIC2 tie-break.

## NEXT ASSIGNMENT
**Agent: Claude — Stage 2 gate** (PROMPT Rule 11: check every Done-when criterion, then review `rules_report.csv` against `config/rules.json`; log the result in `docs/GATES.md`)

### Stage 2 evidence for the gate
- **Build row counts:** Unihan 50,934; KANJIDIC2 13,033; hsk30 3,000 characters and 11,110 expanded word variants (word output is ancillary until Stage 3); OpenCC 414 character / 235 phrase pairs; libhangul 28,460 distinct single-character readings; Kaikki 3,373 explicit pairs / 1,743 aligned characters / 1,227 Hán-Việt syllables / 41,444 Vietnamese headwords; FrequencyWords 50,000 input rows → 47,362 normalized tokens; final `chars` 3,000.
- **Keys/collisions:** `char_id` and `key_char` duplicates = 0; empty `trad` = 0. `char_key_collisions.csv` contains exactly `著 → 着 (level 1), 著 (level 4)`. The two rows have the D37-mandated forms/readings (`着`: `simp/jp=着`, `ko=착`, `ja_on_all` includes ちゃく; `著`: `simp/jp=著`, `ko=저`, `ja_on_all` includes ちょ). `pipeline/id_map.csv` has 3,000 character IDs keyed by `key_char`.
- **C2:** 83 HSK-list rows have multiple traditional variants (78 with 2; 5 with ≥3); 89 distinct non-first variants; 1 already exists as `trad` (`覆`), leaving 88 to add in Stage 3. Rows where `simp != trad`: 1,088; all 1,088 have non-empty `ko` (threshold ≥1,000). These counts are regression-tested in `tests/test_char_collisions.py`.
- **Coverage/missing:** `jp` 2,955 present / 45 missing; `ja_on` 2,951 / 49; `ko` 3,000 / 0; `pinyin` 3,000 / 0; `vi` 2,291 / 709. Vietnamese primary provenance: 1,535 `kaikki_aligned`, 300 `unihan_hvsyl` (**1,835 verified total**), 456 `unihan_unverified`, 709 missing. Missing values remain empty and are reported, never guessed.
- **Merge counts (`left_only / both`):** Unihan 0 / 3,000; OpenCC 2,696 / 304; libhangul 0 / 3,000; Kaikki 1,465 / 1,535; KANJIDIC2 45 / 2,955. Every merge uses `how="left"` and explicit `validate=`; `merge_report.csv` records these plus zero `right_only` indicator rows.
- **Quality/tests:** all exported text passes NFC and missing-sentinel checks. Source suffixes such as Unihan `:0N` are removed in the loader. Tests cover the six fixed characters 學 國 茶 行 生 樂 in all five character fields, 6 shinjitai tie-breaks, 16 prototype glyph pairs, phonology/normalizers, C1/C2, and IDs. `rules_report.csv` and `rules_examples.csv` exist.
- **Test command/result:** `<user folder>\AppData\Local\Programs\Python\Python312\python.exe -X utf8 -m unittest discover -s tests -p 'test_*.py'` → **16 tests, OK** (65.728 s), including two rebuilds.
- **Determinism:** consecutive pre/post rebuild SHA-256 for `data/final/chars.csv` = `b6bffbc97b3d7eef0df4f77c389a8acd6091333473afeebe33e1076e99c08102` and `b6bffbc97b3d7eef0df4f77c389a8acd6091333473afeebe33e1076e99c08102`. The test compares every file in `data/final/` plus `pipeline/id_map.csv` across two rebuilds.

If the gate passes, assign **Codex — Stage 3: word table**. Stage 3 must apply D24, D26–D32, D37 items 5–6, and D38, then return to Claude for the Stage 3 gate and D36 Vietnamese source search.

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
- Resolved: hsk30 `着`/`著` collision → separate rows with `key_char` (D37, revised).
- Vietnamese coverage ceiling (about 35% of HSK words) with the current licensed sources; the search for further licensed sources runs after Stage 3, before Stage 4 (D36).
- Source #7 stays excluded (D21).
- EDRDG data impose an update-procedure requirement; `download.py --refresh` exists; release documentation must explain updates.
- hsk30 provenance risk: **accepted by the user** (D35, personal non-commercial project; revisit if ever published commercially).

## Log
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
