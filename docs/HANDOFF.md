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
- Stage 2 (character table): Codex built loaders and tests; the build stopped at the `着`/`著` key collision. **Resolved: D37 (two rows, `key_char`, 3,000 rows)**; the first version of D37 (merge on `trad`) was wrong for the Korean/Japanese side and was revised at the user's request. Codex resumes and finishes Stage 2.
- **PROMPT Rule 11 (stage gates) is in force.** Gate results are logged in `docs/GATES.md`. Stage 1 gate: PASS (2026-11-04). Stage 2 gate comes after Codex finishes; it checks the Stage 2 Done-when criteria, then the `rules_report.csv` review.

## Stage 1 review: outcome in brief (details in STAGE1_REVIEW.md)
- **Licences:** all accepted. hsk30 accepted with a recorded provenance risk (confirmed by the user, D35). Dataset will be **CC BY-SA 4.0**.
- **Vietnamese:** Kaikki (reading + Han form) and FrequencyWords (frequency proxy) selected. Unihan `kVietnamese` mixes Nôm readings (200-sample check: 31 covered, 29 agree; whole overlap 88%), so it is used only with verification flags. **Measured ceiling: about 35% of HSK words (3,832 / 11,092) and 61% of HSK characters (1,835 / 3,000) get a Vietnamese reading with evidence.** Cards in the Chinese target are unaffected (pinyin always exists); Vietnamese-target decks will be smaller than the HSK list. This is a source limit, not a bug; report it in `coverage_report.csv`.
- **Shinjitai:** inverted OpenCC `JPShinjitaiCharacters` (16/16 on the prototype's glyph pairs), KANJIDIC2 tie-break.

## NEXT ASSIGNMENT
**Agent: Codex — finish Stage 2: character table** (resume from commit `8ac5d66`; PROMPT "STAGE 2" and its **Done when** criteria)

**Decision (DECISIONS D37, revised by the user's request; read it fully):** `着` and `著` stay **two rows** (3,000 rows, not 2,999). `trad` is not unique in `chars` (both are `著`); the unique key is `char_id`, and the new column `key_char` (source `Hanzi`; `着` for the first row, `著` for the second) is what readings are looked up by and what `id_map.csv` uses as the chars key. Everything in the previous Stage 2 assignment still applies except these changes:

1. **Row key and lookups.** `id_map` key for chars = `key_char`. Look up Unihan, KANJIDIC2, libhangul single-character and Kaikki readings by `key_char`, not `trad`. `simp` = source `Hanzi`. `jp` = `key_char` if it is a KANJIDIC2 literal with no D28 inverse-map target, else D28 from `key_char` (for all other rows `key_char = trad`, so D28/D33 behave as before). Implement it generically (rule: `key_char` = source `Hanzi`; no special case for 着).
2. **Tests (replace the earlier collision tests):** `chars` has 3,000 rows; `char_id` and `key_char` are unique; `trad` duplicates exist only in `char_key_collisions.csv` (expect exactly the pair 着/著); row `着`: `trad=著, key_char=着, simp=着, jp=着, ko=착, level=1`, `ja_on_all` contains ちゃく; row `著`: `trad=著, key_char=著, simp=著, jp=著, ko=저, level=4`, `ja_on_all` contains ちょ. Keep the other tests (normalizer, Hangul finals, 6 shinjitai tie-breaks, 16 glyph pairs, fixed test characters 學 國 茶 行 生 樂, NFC, rebuild-twice identical).
3. **Reports:** `char_key_collisions.csv` (`trad, key_char, source_level`), plus everything from the previous assignment (`rules_report.csv`, `no_jp_form.csv`, coverage, `_merge` counts).
4. Expected sanity numbers: 3,000 rows; `jp` empty about 45; verified Vietnamese primary about 1,835 (may differ by a few because `着` is now looked up separately; report the exact value).
5. Stage 2 **Done when** (the gate checks each with evidence; put the evidence in your hand-off note): `chars` covers all 3,000 HSK characters (missing values reported, not guessed); no duplicate `char_id`/`key_char` and every `trad` collision resolved by D37; all text NFC; the test characters among the 20 test words correct in every language; `rules_report.csv` exists; tests in `tests/` pass; rebuilding twice gives identical output (give the two hashes). Include: row counts per stage, `_merge` counts, isna counts per language column, test run output.

Stage 3 note (not now): D37 items (5) and (6) define how `word_chars` picks between 着 and 著 and how Korean/Japanese matching uses the `key_char` form (接著 → 接着). Build them in Stage 3.

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
- Resolved: hsk30 `着`/`著` collision → separate rows with `key_char` (D37, revised).
- Vietnamese coverage ceiling (about 35% of HSK words) with the current licensed sources; the search for further licensed sources runs after Stage 3, before Stage 4 (D36).
- Source #7 stays excluded (D21).
- EDRDG data impose an update-procedure requirement; `download.py --refresh` exists; release documentation must explain updates.
- hsk30 provenance risk: **accepted by the user** (D35, personal non-commercial project; revisit if ever published commercially).

## Log
- 2026-11-04 Claude — user challenged D37: 着/著 are distinct Korean/Japanese characters (着 is HSK 1). Verified in Unihan (착 vs 저), KANJIDIC2, libhangul (接着→접착). D37 rewritten: two rows, `key_char`, link words by simp then pinyin. Next: Codex finish Stage 2.
- 2026-11-04 Claude — PROMPT Rule 11 (gates) adopted and committed with this session; `docs/GATES.md` created; Stage 1 gate PASS logged; `着`/`著` collision resolved (D37). Next: Codex finish Stage 2.
- 2026-11-04 Codex — Stage 2 implementation written but build stopped at the `着`/`著` canonical-key conflict. No improvised data rule; next: Claude decision, then Codex resumes Stage 2.
- 2026-11-04 Claude — applied user decisions: hsk30 accepted (D35); Vietnamese source search moved to after Stage 3 / before Stage 4 (D36). Next assignment unchanged: Codex Stage 2.
- 2026-11-04 Claude — Stage 1 review done: licences accepted, Vietnamese sources selected with verification rules, shinjitai method chosen, priorities set (D23–D34). Next: Codex Stage 2.
- 2026-11-04 Codex — Stage 1 done: downloader + checksums, all licensed-source profiles, licences copied, unlicensed Hán-Việt source excluded by user, two licensed Vietnamese replacements profiled, reproducibility verified. Next: Claude Stage 1 review.
- 2026-11-04 Claude — applied user decisions: new-card limit approved (D20); git email changed, Stage 0 commit author rewritten (D19). Next assignment unchanged.
- 2026-11-04 Claude — Stage 0 done (see CHANGELOG).
