# HANDOFF

Read `PROMPT.md` first, then this file. Do only the assignment for your role. Update this file, `CHANGELOG.md`, `DECISIONS.md` when done; `git commit`; stop with one line `Next: <agent> — <task>`.

## Current status
- Stage 0 (setup) — **DONE** by Claude, 2026-11-04.
- Stage 1 (sources and licences) — **DONE** by Codex; **Claude review DONE** 2026-11-04. All blocking source/licence decisions are closed (DECISIONS D23–D34). Evidence: `docs/STAGE1_REVIEW.md`; reference scripts (evidence, not pipeline): `docs/review_scripts/`.
- Contract files: `docs/SCHEMA.md` (updated: level 1–7, source tags, new reports), `config/rules.json`, `docs/DECISIONS.md` (D1–D50), `docs/final-data-spec.md` (+ Addenda), `docs/SOURCES.md` (all rows now decided).
- `raw/` is git-ignored and recreated by `pipeline/download.py` (checksums in committed `pipeline/source_manifest.csv`). Licence copies are in `licenses/`.
- Git identity: `Hanje Unesaki <311183901+hanjejeme2023-oss@users.noreply.github.com>` (D19). Check `git config user.email` before committing.
- Environment: Python 3.12.10 + pandas 3.1.1 (`pipeline/requirements.txt`). On this machine the Python with pandas is `<user folder>\AppData\Local\Programs\Python\Python312\python.exe`; the `python` on the bash PATH may be a Store stub without pandas.
- Prototype: `prototype/index.html` (frozen).
- Stage 2 (character table) — **DONE** by Codex, 2026-11-04. Revised D37 is implemented as two rows with unique `key_char`; 3,000 rows and all Stage 2 reports are committed. Stage 2 gate: PASS (Claude, 2026-11-04).
- **PROMPT Rule 11 (stage gates) is in force.** Gate results are logged in `docs/GATES.md`. Stage 1 gate: PASS. Stage 2 gate: PASS (both 2026-11-04).
- Pre-Stage-3 readiness review: **DONE** by Claude, 2026-11-04 (three passes, CHANGELOG; decisions D39-D50).
- Stage 3 (word table) — **DONE** by Codex, 2026-11-04; awaiting the Claude gate. Full pipeline and outputs are committed; 22 tests pass, including two-build byte-for-byte determinism.

## Stage 1 review: outcome in brief (details in STAGE1_REVIEW.md)
- **Licences:** all accepted. hsk30 accepted with a recorded provenance risk (confirmed by the user, D35). Dataset will be **CC BY-SA 4.0**.
- **Vietnamese:** Kaikki (reading + Han form) and FrequencyWords (frequency proxy) selected. Unihan `kVietnamese` mixes Nôm readings (200-sample check: 31 covered, 29 agree; whole overlap 88%), so it is used only with verification flags. **Measured ceiling: about 35% of HSK words (3,832 / 11,092) and 61% of HSK characters (1,835 / 3,000) get a Vietnamese reading with evidence.** Cards in the Chinese target are unaffected (pinyin always exists); Vietnamese-target decks will be smaller than the HSK list. This is a source limit, not a bug; report it in `coverage_report.csv`.
- **Shinjitai:** inverted OpenCC `JPShinjitaiCharacters` (16/16 on the prototype's glyph pairs), KANJIDIC2 tie-break.

## NEXT ASSIGNMENT
**Agent: Claude — Stage 3 gate.** Run the checklist in `docs/GATES.md`, including the 30-word source sample and the review short list. Per D50, propose picks (including 茶→차 because the evidence build leaves `chars.ko=다`) and stop for user confirmation before writing `pipeline/overrides.csv`. Do not start the D36 Vietnamese source search until the gate flow is complete.

## Stage 3 Codex completion evidence (2026-11-04)
- Final tables: 11,028 HSK rows + 1,201 `vi_freq` rows (including 越南) = 12,229 words; 24,458 `word_chars` rows; 3,178 characters. HSK coverage: Japanese 5,732 (51.98%), Korean 7,110 (64.47%), Vietnamese 3,882 (35.20%), all four 3,114 (28.24%); 7,354 HSK cards eligible.
- D41/merges: 10,974 exact CC-CEDICT keys, 19 fallbacks, 35 unmatched. All SCHEMA §1.8 merges are in `merge_report.csv` with their validation cardinality; match tables are one row per word key.
- VI-only: 1,200 ranked rows plus the 越南 seed; `vi_only_report.csv` has 3,367 candidate/audit rows. IDs use `x|trad`; HSK IDs use `trad|pinyin`.
- C1/C2: `chars` grew 3,000 → 3,178. HSK words require exactly 82 new characters. VI-only words use 119 non-base characters, 23 shared with the HSK additions, so they add 96 more after HSK (the pre-build estimate was about 108). `char_ambiguous.csv`: 0 rows. `char_simp_mismatch.csv`: 12 rows (10 HSK, 2 VI-only), including the expected 反覆/答覆 rows; all are explicit for gate review. `char_key_collisions.csv` remains the two 著 rows (`着`, `著`).
- Reports (rows): `cedict_unmatched` 35; `ja_multi_candidates` 154; `ko_multi_candidates` 136; `ko_unresolved` 53; `vi_ambiguous` 12; `alignment_mismatches` 50; `char_primary_changes` 95; `char_primary_no_evidence` 1,819; `rules_examples` 2,080; `rules_report` 7; `coverage_report` 41; `ff_candidates` 2,944. `rules_examples.csv` has 0 `unihan_unverified` rows.
- Fixed words match the Stage 3 table. Single-character fallback tests pass for 國 こく, 電 でん, 海 かい, 手 しゅ with the JMdict readings in `ja_alt`. 手紙 and 大丈夫 are in `ff_candidates.csv`; 手紙 is not in `words`. 新聞 has empty Vietnamese as expected.
- D39 first build: 樂=락, 歷=력, 怒=노, 行=행. 茶 remains **다** with 차 in its dictionary candidates; this is the expected gate short-list item, not a Codex override. `ja_on`/`pinyin` ordering is unchanged from KANJIDIC2/Unihan.
- Validation: `python -m unittest discover -s tests -p 'test_*.py'` → 22 tests OK (393.898 s). `test_rebuild` ran `run_all.py` twice and compared every final file plus `pipeline/id_map.csv`: identical.

## COMPLETED ASSIGNMENT — Codex Stage 3 reference
**Agent: Codex — Stage 3: word table** (PROMPT Stage 3, as completed by DECISIONS D39-D50 and the spec addenda; **where PROMPT's wording differs, those win**). Stage 2 gate: **PASS** (attempt 1, 2026-11-04). A pre-Stage-3 readiness review (Claude, 2026-11-04, three passes) simulated the matching rules below on the raw files; expected counts are estimates, not yet from a real build. Do not improvise a data rule; if one is missing, stop and raise it here.

**Before starting:** read D39-D50. **D50 records the user's answers to the four open points; apply them.**

### Task, in build order (D40)
1. **HSK rows (D41):** 11,110 → 11,028 rows, one per `(trad, pinyin)`; minimum level; `pos`, `hsk_ids`; pinyin without spaces. Attach CC-CEDICT by `cedict_key`, then the D41 fallback; write `cedict_unmatched.csv`.
2. **Loaders:** add Unihan `kCompatibilityVariant`, `kZVariant`, `kSemanticVariant`, `kSpecializedSemanticVariant` (D43); a JMdict loader keeping tag names, not entity expansions; a CC-CEDICT loader; full libhangul records with comments; Kaikki first gloss (D48). Update `SOURCES.md` section 2.
3. **Reading lookup** for any character, without adding rows.
4. **VI-only words (D46)** with the current sources, plus the seed 越南; write `vi_only_report.csv`. IDs: `trad|pinyin` for HSK, `x|trad` otherwise.
5. **Grow `chars` (D38, D48):** about 82 + 108 rows, `in_hsk_chars=false`. Rescope the Stage 2 checks that assume 3,000 rows (D40). Link word characters to `char_id` (D37 item 5, D38); write `char_ambiguous.csv`, `char_simp_mismatch.csv`.
6. **Match tables:** JMdict (D42, including the single-character KANJIDIC2 fallback, `source_ja=kanjidic2_on`), libhangul (D43), Vietnamese (D44), one row per word key, merged left `1:1`. Create `pipeline/overrides.csv` (header only). Write `ja_multi_candidates.csv`, `ko_multi_candidates.csv`, `ko_unresolved.csv`, `vi_ambiguous.csv`.
7. **`word_chars` (D45)** with `pinyin_syllable`, `ko_syllable`, `ko_base`, `vi_syllable`, `syl_aligned`; write `alignment_mismatches.csv`.
8. **D39:** update primaries for `ko` and `vi` only (`ja_on` keeps KANJIDIC2 order, `pinyin` keeps `kMandarin` order), `ko_final`, `vi_final`, source tags, `ko_base_all`; write `char_primary_changes.csv`, `char_primary_no_evidence.csv`. Then apply `table=chars` overrides and recompute those same columns.
9. **Rebuild `rules_report.csv`, `rules_examples.csv` (D45):** verified readings only.
10. **`freq_vi` (D44), `origin`, `chars.level`, `card_eligible` (D48), `verified=false`, glosses (D48).**
11. **`data/staging/ff_candidates.csv` (D47).**
12. **Validate and export:** `words`, `word_chars`, extended `chars` as CSV + JSON, `merge_report.csv`, `coverage_report.csv` (per level: all 4 languages, per language, `freq_vi_basis=syllable_min`). `run_all.py` runs everything.

### Done when
PROMPT's criteria, measured by the checklist and the test-word table in `docs/GATES.md`, and specifically:
- 11,028 HSK rows, `word_id` unique; every merge in SCHEMA §1.8 logged with `validate=`; every report above exists with its row count in your hand-off note.
- Test words match the table in `GATES.md` (18 HSK words; 越南 as `vi_freq`; 手紙 in `ff_candidates.csv`, not in `words`). Single-character fallback tests: 國 こく, 電 でん, 海 かい, 手 しゅ, with the JMdict reading in `ja_alt`.
- D39: every `ko` and `vi` primary equals the most frequent reading in evidence words after normalization (ties: previous order), unless a `table=chars` override applies; `*_all` sets unchanged, primary first; every `ja_on` is the KANJIDIC2 first value; every `pinyin` is the first `kMandarin` value; tests 樂 (락 or 악, never 낙), 歷 (력, never 역), 怒 (노), 行 (행), 茶 (차 if `overrides.csv` has it, otherwise 차 or 다). 다 at your build is expected, not a failure: state it in your hand-off note. The user wants 차, and the gate handles it.
- `rules_report.csv` rebuilt after D39, 0 unverified readings.
- `ff_candidates.csv` has 2,500-3,300 rows.
- Tests added: `tests/test_words.py` for D41-D46, `tests/test_char_collisions.py` rescoped; all pass; rebuilding twice is identical including `id_map.csv`.
- Hand-off note shows C1/C2 evidence: `chars` rows before and after growth, `char_simp_mismatch.csv`, `char_ambiguous.csv`.

**At the end, hand off to Claude (Stage 3 gate), not to Gemini.**

## Planned sequence after Stage 3 (user-approved, DECISIONS D36; order made explicit in D46)
1. **Codex: Stage 3**, VI-only words included, with the current sources.
2. **Claude: Stage 3 gate** (checklist in `GATES.md`, 30-word sample). Claude proposes picks for the review short list, including 茶 차 if needed, and **stops for the user to confirm** (D50 item 4); then writes the confirmed overrides, rebuilds and rechecks before recording the gate.
3. **Claude: Vietnamese source search (D36).** Reads `coverage_report.csv` and `vi_ambiguous.csv`, then:
   - searches for additional **licensed** Vietnamese resources: a Hán-Việt character dictionary (to verify/replace Unihan's Nôm-contaminated readings), a Chinese-Vietnamese or Sino-Vietnamese word list, a Vietnamese frequency list of words (not syllables); candidates to check include Wikimedia/Wiktionary-derived data other than Kaikki, open Vietnamese dictionaries, and Chinese-Vietnamese resources on GitHub/Hugging Face/academic sites;
   - records each candidate's licence from its own licence file in `docs/SOURCES.md` before anything is used; anything unlicensed, non-commercial-only, or of unclear provenance is rejected (the user is asked only for a licence judgment call);
   - measures each licensed candidate on the same yardsticks as Stage 1 (HSK words gained, agreement with existing readings on a seeded sample, precision of new readings) and records accepted sources and rules in DECISIONS.
4. **If a source is accepted:** Codex integrates it and **reruns all of Stage 3, including VI-only selection**; Claude repeats the Stage 3 gate. **If nothing is accepted:** Claude records the ceiling.
5. **The word list freezes here (D46). Gemini: Stage 4** only after this point, sized from the final coverage.

## Notes for later stages
- **Stage 4 (Gemini), sizes:** about 8,500 eligible words for task 1 and about 2,900 `ff_candidates` rows for task 2 before the D36 round. Words now carry `gloss_ja_en`, `gloss_ko`, `gloss_vi` (D48); a Korean reading that is a rare or archaic dictionary entry is marked `confidence: low` (D49). `ff_only` words get IDs `x|trad`.
- **Stage 5 (Codex):** glyph Korean readings use `ko_base_all`; a rule example uses only pairs equal to the primaries, and `ex[0]` = `key_char` (SCHEMA §3.2, §3.5, D45).
- **Stage 5 (Codex), user-approved addition — DECISIONS D20:** daily limit of 20 new (never-seen) cards in カード; reviews unlimited; no visible UI change except smaller counters. State in localStorage `kb_newtoday`. Add a test. List it in the Stage 5 side-by-side difference list.

## Rules to keep in mind (from PROMPT)
- No agent fills a missing reading/fact from its own knowledge. Missing stays empty and is reported.
- Do not edit `prototype/index.html`. Do not edit `SCHEMA.md`/spec/DECISIONS decisions; raise questions here in HANDOFF instead.
- If a source has no license or non-commercial-only terms: do not use it; stop and ask the user.

## Open problems / notes
- Known limits to report, not fix, in Stage 3: `hanja.txt` has no frequency, so a Korean reading may be a rare entry; `freq_vi` is a syllable proxy, so VI-only levels are rough until D36 finds a word list.
- Stage 2 gate notes (non-blocking): (1) resolved by D39 and D43. (2) Suspect Vietnamese readings for loop 1 accuracy: 怎 chẩn (expected chẩm; `unihan_hvsyl`), 幻 ảo (usual Hán-Việt huyễn). (3) `unihan_hvsyl` (300 chars) is a weaker check than `kaikki_aligned`.
- Resolved: hsk30 `着`/`著` collision → separate rows with `key_char` (D37, revised).
- Vietnamese coverage ceiling (about 35% of HSK words) with the current licensed sources; the search for further licensed sources runs after Stage 3, before Stage 4 (D36).
- Source #7 stays excluded (D21).
- EDRDG data impose an update-procedure requirement; `download.py --refresh` exists; release documentation must explain updates.
- hsk30 provenance risk: **accepted by the user** (D35, personal non-commercial project; revisit if ever published commercially).

## Log
- 2026-11-04 Codex — Stage 3 complete: 11,028 HSK + 1,201 VI-only words, 3,178 chars, all reports, fixed-word tests, and deterministic rebuild verified. Next: Claude Stage 3 gate.
- 2026-11-04 Claude — user chose the KANJIDIC2 fallback for single-character words with no on'yomi in JMdict (D42, D50); 國 is now こく in the test table. No open user questions. Next: Codex Stage 3.
- 2026-11-04 Claude — applied the user's D50 answers: pinyin out of D39; on'yomi first; Korean base form; user confirms the review short list; 茶 `chars.ko` to end as 차. 國 くに explained. Next: Codex Stage 3.
- 2026-11-04 Claude — pre-Stage-3 readiness review, three passes; D39 refined by the user; D40-D50 added; SCHEMA, spec addenda, GATES checklist and this task updated; four user questions recorded in D50. Next: Codex Stage 3.
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
