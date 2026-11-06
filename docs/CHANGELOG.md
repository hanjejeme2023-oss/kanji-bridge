# CHANGELOG

## 2026-11-06 — Stage 4b-fix: D60 and Argon re-pilot [Codex]

- Pinned Argon and v2 prompts; added response property ordering, D60 validators, the 243-item task-4 filter, the UTC deadline guard, and a 600-second per-request timeout.
- Added resumable `--task N` batch validation/skip behavior and a test; explicit `--batch N` remains a forced rerun.
- Added `total_token_count` and conservative unreported-token billing at the output rate to the ledger, measured averages and $100 ceiling calculation.
- Argon check and all five `pilot_v2` requests passed on the first attempt. Re-pilot: 28,350 input, 18,750 output, 0 thinking, 47,100 total, 0 unreported tokens, $0.244200; request wall times and full-run projections are in `docs/STAGE4B_FIX_REPORT.md`.
- 63 non-rebuild tests pass; canonical rebuild completed with no frozen-data diff. No full run started. Next: Claude Stage 4b re-check.

## 2026-11-06 — Stage 4b pilot review [Claude]
- Verified the frozen build after Codex's override-backup restore: `pipeline/overrides.csv` byte-identical to `03b3bf9` (121 rows); no file under `data/` differs; `pipeline/id_map.csv` differs in line endings only.
- Reviewed both models' task-1/task-2 pilot outputs on identical inputs, all Flash task-3/task-4 outputs, all low-confidence and non-`same_word` items, retry causes and costs: `docs/STAGE4B_REVIEW.md` (10 side-by-side examples), script `docs/review_scripts/stage4b_compare.py`.
- D60: Gemini 4 Argon for all tasks, full run by 2026-11-30; prompts `task1_v2.md`, `task2_v2.md`, `task3_v2.md` added (v1 kept); schema `propertyOrdering`, two validator rules, task-4 input filter and a date guard assigned to Codex with an Argon re-pilot. No pipeline code or data changed. Next: Codex Stage 4b-fix.

## 2026-11-06 — Stage 4a Vertex generation script and pilot [Codex]
- Added `pipeline/stage4_generate.py` and `pipeline/stage4/`: deterministic builders for four tasks, strict local validators, Vertex-only ADC client, API-key guard, structured schemas, retries/backoff, token accounting, date-aware Flash/Argon prices, and a shared $100 hard ceiling. Pinned `google-genai==2.34.0` separately; `run_all.py` remains isolated.
- Added versioned English prompts, exact pilot JSONL inputs, per-request outputs/logs, and `content/cost_log.csv`. No readings are emitted by model outputs. Final saved pilot output passed every local validator.
- Fixed check handling after the first 32-token check returned empty text: check budget 1,024; every response now checks text/finish reason before JSON parsing and reports finish reason plus token counts; failed checks are cost-logged. Corrected `--check` passed on `gemini-3.8-flash`, `global`, 123 tokens.
- Ran the user-requested identical-input comparison on GA `gemini-4-argon` for pilot tasks 1 and 2 only. Flash remains pinned pending Claude's Stage 4b decision. Argon November/December prices are recorded separately.
- Pilot final successful requests: Flash task 1 14,401/13,113/0 tokens; task 2 4,772/4,224/15,883; task 3 zh 981/992/0; task 3 vi 1,447/1,542/2,431; task 4 5,639/2,358/5,302. Argon task 1 14,280/13,859/0; task 2 4,780/4,228/0 (input/output/thinking). Actual logged corrected-check plus all pilot attempts: $0.69781975.
- Successful-attempt Flash projection is $13.37 lower bound; about $15.23 with D58 task-3 sizing and about $25.49 with the observed task-1 retry factor. Argon task 1+2: $19.48 through November or $38.97 from December on one billed attempt, higher with observed retries. Full evidence in `docs/STAGE4A_REPORT.md`.
- Added 16 Stage 4 tests covering frozen counts, deterministic inputs, bad outputs, schema constraints, secrets, empty responses and `run_all.py` isolation. One canonical rebuild completed and all 54 non-rebuild tests pass. No full run started. Next: Claude Stage 4b.

## 2026-11-06 — Documentation consolidation; Stage 4 on Vertex AI; Stage 4 assignment [Claude]
- `docs/HANDOFF.md` cut to status, next assignment, planned sequence, notes, open problems and recent log; completed assignments, Codex evidence blocks, resolved notes and the full log moved **verbatim** to the new `docs/HANDOFF_ARCHIVE.md`.
- `docs/DECISIONS.md`: superseded decisions or parts marked in italics at the start of D23, D24, D26, D27, D31, D32, D36, D38, D39, D44, D46, D47, D53, D54, D55 and open item E; nothing deleted.
- User question: `chars` 3,138 → 3,140 = 祇 `c03206` and 畿 `c03207`, added at `4919d5b` (D56 G1) by the VI-only words 神祇 and 京畿; recorded in `GATES.md`.
- **D58 (amends D54, user instruction):** Stage 4 uses Gemini on Vertex AI (`aiplatform.googleapis.com`), login by `gcloud auth application-default login`, no API key; GA Gemini 3.8 Flash; hard ceiling $100; finish by 2026-12-20; estimate about $20-45 from the frozen build. No paid upgrade planned (Google's Free Trial page excludes only AI Studio and partner models). User guide: new `docs/VERTEX_SETUP.md` (budget alert included).
- **D59:** Stage 4 design: task-1 `vi_check` (D57 Q1) and `meanings_differ`; 自己 always in task 2; no reading fields in content; task 4 other-reading notes in `words.note_ja` (302 words); pilot before the full run. SCHEMA §5 (content files) added; UX_BACKLOG #3.
- `.gitignore`: `.env`, `.env.*` and credential-file patterns (D54 required `.env`; it was missing).
- No data or pipeline change. Next: User — Vertex AI setup; then Codex — Stage 4a.

## 2026-11-06 — D55 Vietnamese finalization applied; word list frozen [Claude]
- User confirmed `docs/VI_SHORTLIST.md` (all as proposed; Q1 a, Q2 yes, Q3 a; plus 岳父 nhạc phụ, 岳母 nhạc mẫu). DECISIONS D57.
- `pipeline/overrides.csv` 81 → 121 rows: 11 Vietnamese replacements (一 nhất, 詞 từ, 累 lụy, 圈 khuyên, 祝福 chúc phúc, 服從 phục tùng, 拖 tha, 拄 trụ, 馴 thuần, 岳父, 岳母) and 29 clears (rule-B values that are a different Vietnamese word). `config/vi_sources.json`: 7C character readings on (80/81 correct).
- Effect: HSK `vi` 4,239 → 4,245, all four 3,362 → 3,367; HSK verified character readings 1,835 → 1,913; one primary changed by the overrides (馴 thuần, the user's pick), tie 福 phúc/phước removed. Cards unchanged (7,354 / 8,555).
- Tests: `test_stage3_d53.py` updated for D57 (121 overrides, obsolete-only words, switch on, new test for cleared values); `test_chars.py` sanity range counts the `kaikki_en_char` verified tag. Full suite: rebuild test passes (identical); all non-rebuild tests OK.
- Why: D55 (user wants every known Vietnamese doubt settled before Stage 4). Remaining rule-B false matches are found by a Stage 4 meaning flag (D57 Q1 a). Next: Claude documentation consolidation and the Stage 4 assignment.

## 2026-11-06 — Repeat Stage 3 gate after D53, attempt 2: PASS; D55 short list [Claude]
- Rechecked G1-G3, R2, R4, R5, R6, checks 6, 8, 11, 13 on `4919d5b` against `0d581fa` and `7827546` (`docs/review_scripts/stage3_repeat_gate_attempt2_reference.py`). All 1,122 A2 values equal an independent implementation of D56 item 2 applied to 7C; 0 invented consonant + y spellings in `words`, `ff_candidates`, `rules_examples`; `ff_candidates` 2,504 rows with 0 overlap with `words`; VI-only 6 added / 6 dropped, no ID reused; 0 character primary or `*_all` changes, no tie created or broken; all 81 overrides apply; 38 tests OK; rebuild byte-identical. Gate logged in `GATES.md`.
- D55: wrote `docs/VI_SHORTLIST.md` for the user: 17 rule A/B vs A2 disagreements (replace 8), 42 rule-B values that are other Vietnamese words or variant spellings (clear 24, keep 18), 8 `obsolete_only` words (keep empty), 7C character readings (one switched-on build measured and discarded: 80/81 readings correct, HSK `vi` +32, 5 wrong new word values to clear), 調 / 馴, and a 50-word seeded sample (48/50; both errors are rule-B false matches, sized at about 7% of multi-character rule-B words by a second sample of 60). Three questions (Q1-Q3) for the user.
- No data, pipeline, config or override change. New evidence script `docs/review_scripts/d55_vi_shortlist_reference.py`.

## 2026-11-06 — Repeat Stage 3 gate fixes G1-G3 [Codex]
- Implemented D56's narrow A2 spelling convention in one shared function: only `hi/ki/li/mi/ti` syllables use `y`; 104 A2 words (32 HSK) lose invented spellings while rule A/B remains untouched. Rebuilt HSK coverage is unchanged; Vietnamese alignment mismatches fall from 298 to 200 and `rules_examples` from 2,232 to 2,190.
- Removed the pre-D53 legacy VI-only selection from false-friend filtering. `ff_candidates.csv` is 2,504 rows (440 removed, none added), with zero `form`/`trad`/`simp` overlap against any current word; 手紙 and 大丈夫 remain.
- Removed override-based VI-only pinning. Selection is now rank-and-cap only; a real rebuild without `overrides.csv` produced the same 1,201 VI-only IDs. Corrected frequency scores cause six additions and six drops; no existing ID changed or was reused.
- Current scope: 12,229 words, 3,140 chars, 24,497 `word_chars`; HSK coverage `ja` 5,703 / `ko` 7,114 / `pinyin` 11,028 / `vi` 4,239 / all four 3,362; cards 7,354 HSK / 8,555 total. No existing Korean or Vietnamese character primary changed; no override was added.
- Added D56 regression coverage for the named A2 examples, exact false-friend exclusion and override-independent VI-only selection. All 38 tests pass; two canonical rebuilds are byte-identical including `id_map.csv`.
- Why: repeat Stage 3 gate attempt 1 failures G1-G3. Next: Claude repeat gate attempt 2, then D55 Vietnamese finalization if it passes.

## 2026-11-05 — Repeat Stage 3 gate after D53, attempt 1: FAIL [Claude]
- Checked R1-R9, checks 1-13, C1, C2 on `97780a0` against `7827546` (`docs/review_scripts/stage3_repeat_gate_reference.py`). Passed: rows/IDs (no dropped ID reused), merges, coverage (HSK `vi` 4,239, all four 3,362), `card_eligible`, `vi_ambiguous`, VI-only bands, all 77 overrides, test words, Japanese, collisions, 36 tests and identical rebuild.
- **Failed:** (1) rule A2 respells every consonant + i as y (`canonicalize_iy`): 143 A2 words differ from 7C, 104 (32 HSK) with spellings no source has (皮膚 bỳ phu, 移 dy, 王妃 vương phy); about 50 such pairs reached `rules_examples.csv`. (2) `ff_candidates.csv` keeps its pre-D53 membership through a legacy VI-only selection, so 440 rows are now also VI-only words (D47).
- **User decisions (D52 tie rule):** `chars` overrides 鹿 록, 磊 뢰, 隸 례, 蘭 란, 丹 단, 易 이 (易 asked at this gate). Vietnamese primary changes 沒 một, 盆 bồn, 訪 phỏng, 武 vũ accepted.
- **Reviewed at the user's request:** Codex's pin of overridden VI-only words. Not accepted (D56 item 4); `x|行伍 항오` and `x|寂寥 적요` removed from `overrides.csv` because they stayed in the list only through the pin (ranks 1,199-1,200, `freq_score` 1,074 and 137 vs about 8,700 at the cut). `overrides.csv` 77 → 81 rows.
- **Confirmed for the user:** the VI-only churn (757 of 1,201 replaced) is D53 item 4's intended effect: 904 `ja_common` candidates instead of 342 fill the cap first; every dropped word was non-`ja_common` at levels 5-7.
- Rebuilt with the current code and 81 overrides: only the six primaries changed (no tie flip); 行伍/寂寥 left the VI-only list (IDs reserved), 槍法/法家 entered; coverage and cards unchanged. `tests/test_stage3_d53.py` override count 77 → 81; 35 non-rebuild tests OK; second rebuild byte-identical.
- D56 recorded; SCHEMA §1.8 row `words_kaikki_en`; HANDOFF: fixes G1-G3 for Codex, D55 list additions (調, 馴, 複合/凶悪, 自己), Stage 4 note on explaining other readings (user idea), planned-sequence step for documentation consolidation after the freeze (user request).

## 2026-11-05 — Source 7C integrated; Stage 3 rerun [Codex]
- Added reproducible download/licence handling and `load_kaikki_en.py` for Kaikki English-Wiktionary Vietnamese data. The locked file exactly matches the D36 measurement (83,424,329 bytes; SHA-256 `186cd0a62d876dada70c9761bc05e598c8cf7b9a48e0aa518bab6c649e28d945`); loader output is 14,513 raw pairs, 10,064 filtered aligned pairs / 9,995 forms, plus 917 chữ-Hán reading pairs.
- Implemented D53 rule A2 as a validated `1:1` indicator merge after A/B, including obsolete reporting, word evidence, rule tags, the D44 `i/y` canonical form (`自己` → `tự kỷ`), A2 candidates for overrides, and A2 fills for the frozen 2,944 false-friend rows.
- Reran D46 VI-only selection over rule A ∪ A2. The cap remains 1,201 including 越南; duplicate resolved word keys are audited and the three existing overridden VI-only rows stay within the cap. Final scope: 12,229 words, 24,496 word-character rows, 3,138 chars.
- Added D55 support: Vietnamese clears/replacements never enter `vi_alt` and are reported; optional 7C character verification lives behind `config/vi_sources.json` (committed off). Switch-on measurement: 46 confirmations, 36 first readings, HSK `vi` 4,271, all-four 3,381.
- Final switch-off coverage: HSK `vi` 4,239 and all-four 3,362; cards unchanged. Six Korean and four Vietnamese character primaries differ from `7827546` and are handed to Claude under D52 without new overrides. Two extra source-backed obsolete-only rows and the larger A2 alignment report are documented in HANDOFF.
- Added D53/D55 regression tests and updated two pre-D53 assertions for the reranked data. **36 tests pass**, including two byte-identical rebuilds and `id_map.csv`; downloader rerun uses every locked file unchanged.
- Next: Claude repeat Stage 3 gate (R1-R9, checks 1-13, C1/C2), then D55 Vietnamese finalization if it passes.

## 2026-11-05 — Vietnamese finalization step added (D55) [Claude]
- User decision: between the repeat Stage 3 gate and the word-list freeze, Claude prepares `docs/VI_SHORTLIST.md` (16 A/B vs A2 disagreements, about 19 wrong-looking composed readings, 6 `obsolete_only` words, 38 rule-B values filed under other characters, 7C character readings if seeded precision ≥ 95%, a fresh 50-word sample with target ≥ 98%). The user confirms, overrides are written, rebuild and recheck (D52 tie rule, all overrides apply), then freeze and the Stage 4 assignment.
- Found while recording it: the override code cannot clear a value and moves a replaced `vi` into `vi_alt` (accepted as correct by `judge()`), and overrides cannot verify or add character readings. D55 defines empty/replacing `vi` overrides that never feed `vi_alt`, and 7C character readings behind `config/vi_sources.json` (default off). Both were added to the current Codex task (items 8-9) and to GATES (R9). SCHEMA tags `kaikki_en_char`, `override_cleared`, `override_replaced`.
- Next assignment unchanged: Codex integrates 7C.

## 2026-11-05 — D36 Vietnamese source search [Claude]
- Checked 8 candidates, licence first (user limits: at most 8; precision ≥ 95% on a seeded sample; gain ≥ +300 HSK words or +3 pp). Downloads only to a scratch folder outside the repo; `raw/`, `pipeline/`, `data/` unchanged.
- **Accepted:** Kaikki English-Wiktionary Vietnamese entries (SOURCES 7C), for the word list only, as rule A2 (D53). Seeded overlap sample 199/200 (seed 36), whole overlap 99.45%; gain +356 HSK words, 35.18% → 38.41% (+3.23 pp). A2 fills only empty `vi`; 6 obsolete/archaic-only words are reported, not used (新聞 stays empty). VI-only selection takes A2 pairs as extra candidates.
- **Rejected (7D-7J):** CVDICT (machine-translated), wordfreq and Leipzig (syllable tokens; Leipzig terms unreadable, NC), Wikidata lexemes (no gain), HanViet data and duyet word list (GPL-2.0), English-Wiktionary Chinese descendants (gain +231, vernacular forms). No licensed Vietnamese word-frequency list found; D26 proxy stays.
- Added `docs/D36_VI_SOURCE_SEARCH.md` (candidates, numbers, 30 seeded new readings for the user's spot check, loop-1 lists), reference scripts `docs/review_scripts/d36_*.py`, SOURCES rows 7C-7J, D53, SCHEMA tags (`kaikki_en_han`, `obsolete_only`, `vi_only_report.source_vi`), GATES repeat-gate checks R1-R8 (incl. D52 tie rule and the 77 overrides).
- **Stage 4 mode (D54):** the user chose a Python batch script on the Gemini API (key in `GEMINI_API_KEY`, never committed) over an Antigravity agent session, after a cost/reproducibility/Rule 3 comparison.
- Why: D36 (35% Vietnamese coverage too low for the user's goal); the word list freezes only after the repeat gate (D46).

## 2026-11-05 — Stage 3 gate PASS: confirmed overrides applied [Claude]
- `pipeline/overrides.csv`: 77 user-confirmed rows (D52): 59 `words` (23 ko, 16 ja incl. the user's 家 か and 月 げつ, 19 vi) and 18 `chars` (茶 차, 寧 녕, 13 law-form base forms; 貝 패, 滑 활, 省 성, 更 경 to undo D39 tie flips the word overrides caused, confirmed by the user after the first rebuild).
- Rebuilt: HSK `vi` 3,861 → 3,880, all four languages 3,094 → 3,111, `rules_examples` 2,031 → 2,044, `char_primary_changes` 84 → 103; `card_eligible` unchanged; `*_all` sets unchanged.
- Tests: `tests/test_chars.py` and `tests/test_words.py` pinned 茶 = 다 (pre-D50 expectation) and now expect 차, like `tests/test_stage3_gate_fixes.py`. 29 tests OK; two rebuilds identical.
- Why: GATES check 9 / D50 item 4; Stage 3 gate recorded as PASS (attempt 2).

## 2026-11-05 — Stage 3 gate, attempt 2 [Claude]
- Reran checks 2, 5, 6, 7, 8, 9, 10, 11, C1, C2 and 13 against commit `e18e7e0` with independent scripts; all pass except check 9, which waits for the user. F1-F13 verified. 29 tests OK; the rebuild reproduces every committed output byte for byte.
- Scanned all 84 `char_primary_changes.csv` rows: one bad change (寧 → 령), override proposed.
- Wrote `docs/STAGE3_SHORTLIST.md`: proposed picks for the D50 short list (23 Korean, 14 Japanese, 19 Vietnamese word overrides; 茶 차 and 寧 녕 character overrides; optional group of 13 law-form characters). No override written, no data or code changed.
- Why: PROMPT Rule 11 and GATES check 9; the user confirms picks before they enter `overrides.csv` (D50 item 4).

## 2026-11-05 — Stage 3 gate fixes F1-F13 [Codex]
- Separated D43 Korean alignment acceptance from exact D39 normalization, restricted D39 counts to one-candidate/override evidence, preserved reading sets, and implemented `ko_law_form_suspect`.
- Replaced simulated word join counts with validated indicator merges for CC-CEDICT, Kaikki, JMdict, libhangul and Vietnamese matches; Stage 2 rows now record their actual validation arguments.
- Corrected single-character Japanese form matching and linked-row on'yomi, Vietnamese rule-B conflicts and headword glosses, grown-character simplified forms, VI-only audit columns, and CC-CEDICT-inventory pinyin segmentation.
- Rebuilt reports and tables: 12,229 words, 3,178 chars, 24,458 word-character rows; 5 pinyin/Korean/Vietnamese alignment exceptions (0 pinyin failures); 3 simplified-form mismatches; 84 primary changes. Card eligibility remains 7,354 HSK / 8,555 total.
- Added `tests/test_stage3_gate_fixes.py`. Full suite: 29 tests passed; two complete rebuilds produced identical final outputs and `pipeline/id_map.csv`. No override or new data decision was added; `DECISIONS.md` is unchanged.

## 2026-11-04 — Stage 3: word table [Codex]
- Added normalized CC-CEDICT and JMdict loaders; JMdict retains entity tag names for D42 ranking. Expanded Unihan variants, full libhangul aligned records/comments, and Kaikki first glosses.
- Implemented D40-D50 in `pipeline/build_words.py` and `stage3_match.py`: 11,028-row HSK dedupe; exact/fallback CC-CEDICT attachment; Japanese/Korean/Vietnamese dictionary matching; deterministic VI-only selection; character growth/linking; `word_chars`; D39 primary recomputation; rules, coverage, merge, ambiguity and mismatch reports; and D47 false-friend candidates.
- Final build: 12,229 words (11,028 HSK + 1,201 VI-only), 3,178 characters, 24,458 word-character rows, 2,944 false-friend candidates. HSK coverage is 5,732 Japanese, 7,110 Korean, 3,882 Vietnamese and 3,114 with all four languages; 7,354 HSK cards are eligible.
- C1/C2 evidence: 3,000→3,178 characters; 82 additions required by HSK words and 96 further exclusive additions required by VI-only words; zero ambiguous links; 12 simplified-form mismatches explicitly reported.
- Added `pipeline/overrides.csv` with its header only for gate-confirmed choices. No value was invented or hand-entered; 茶 remains 다 pending the D50 gate short list.
- Rescoped character/collision tests and added `tests/test_words.py`. Validation: 22 tests pass; the rebuild test ran the complete pipeline twice and all final outputs plus `id_map.csv` were identical.
- Updated `docs/SOURCES.md` usage log from planned to actual Stage 3 table/column use. No new decision was needed, so `DECISIONS.md` is unchanged.

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

## 2026-11-04 — Stage 2: implementation started, blocked on canonical key [Codex]
- Implemented the Stage 2 pipeline structure: shared NFC/Vietnamese/pinyin/phonology/ID helpers; per-source loaders for Unihan, KANJIDIC2, hsk30, OpenCC, libhangul, Kaikki, and FrequencyWords; the character builder/reports; `run_all.py`; and Stage 2 unit/rebuild tests.
- First build correctly detected a contract conflict in the raw HSK character list: source rows `着 → 著` (level 1) and `著 → 著` (level 4) both produce canonical `trad=著` under D33. This conflicts with the simultaneous requirements for 3,000 rows and a unique `trad` key. No row was dropped, renamed, or overridden because HANDOFF explicitly forbids improvising a rule.
- Pipeline stopped at the hsk30 loader validation. Claude must decide whether to merge to 2,999 canonical rows, introduce a documented `着` exception to keep 3,000 unique rows, or revise another contract requirement. No Stage 2 final tables are claimed complete.

## 2026-11-04 — Stage 1 review [Claude]
- Confirmed licences (D23): all sources usable; dataset will be CC BY-SA 4.0; hsk30 provenance risk accepted and recorded.
- Selected Vietnamese inputs (D24-D27): Kaikki for readings/Han forms, FrequencyWords for a frequency proxy; Unihan `kVietnamese` gated by verification flags after the 200-character cross-check (`docs/STAGE1_REVIEW.md`).
- Chose the shinjitai method (D28: inverted OpenCC + KANJIDIC2 tie-break, 16/16 on the prototype glyphs); fixed level semantics (D29); hsk30/JMdict/libhangul rules (D30-D32); source priority per column (D33).
- Updated SCHEMA (levels 1-7, source tags, new reports) and SOURCES (all rows decided). Saved reference scripts in `docs/review_scripts/`.
- Why: the review closes every blocking decision so Stage 2 can build `chars` without improvisation. The measured Vietnamese ceiling (about 35% of HSK words) is recorded as a source limit.

## 2026-11-04 — User decisions applied [Claude]
- D35: hsk30 provenance risk accepted by the user (personal, non-commercial; revisit if published commercially).
- D36: search for additional licensed Vietnamese sources moved to after Stage 3, before Stage 4; new Claude task recorded in HANDOFF.md. Next assignment unchanged (Codex, Stage 2).

## 2026-11-04 — Stage gates and Stage 2 key collision [Claude]
- PROMPT updated by the user (Rule 11: stage gates, Done-when criteria); committed together with this change. Created `docs/GATES.md`; logged the Stage 1 gate (PASS, evidence: 23/23 checksums, download rerun, licences, profiles).
- (SUPERSEDED by the entry below) D37: canonical-key collisions in `chars` are merged on `trad` (hsk30 `着`/`著` -> `trad=著`, `simp=着`, `level=1`); `chars` has 2,999 rows for 3,000 source characters, plus `char_key_collisions.csv`. SCHEMA updated. Why: words use the traditional form `著`; duplicate or exception keys would break IDs, merges and tests.

## 2026-11-04 — D37 revised [Claude, at the user's request]
- The earlier D37 merged 着/著 into one row keyed `著` and would have taken every reading from `著`, losing 着's Korean 착 and Japanese ちゃく. Replaced by: one row per source character (3,000 rows), `trad` non-unique, new unique column `key_char` (readings lookup + id_map key), word-to-character linking by simp then pinyin, Korean/Japanese word matching also on the `key_char` form (接著 -> 接着), glyph view uses `key_char`. Updated DECISIONS, SCHEMA, spec addenda, Stage 2 task.

## 2026-11-04 — One-to-many collision check [Claude, at the user's request]
- Measured the one simplified -> several traditional case: 83/3,000 HSK rows (89 variant characters, 88 without a row yet). D38: link words through their own `trad` string, extend `chars` in Stage 3 for every word character lacking a row, simp rule for added rows, position check against the word's `simp`.
- Corrected D37: `key_char = trad` for all rows except shared-`trad` rows (using the simplified Hanzi everywhere would find Korean readings for only 145 of 1,088 differing rows instead of 1,036).
- Added the standing C1 (many->one) and C2 (one->many) checks to `docs/GATES.md`, Stage 2 and Stage 3 tasks; reference script `docs/review_scripts/char_collision_reference.py`.

## 2026-11-04 — Stage 2: character table completed [Codex]
- Implemented revised D37 generically: 3,000 source-character rows; `key_char=trad` except in shared-`trad` groups, where source `Hanzi` supplies the unique reading/ID key. Unihan, KANJIDIC2/OpenCC, libhangul and Kaikki joins now use `key_char`; `simp` remains the HSK source `Hanzi`.
- Exported `chars.csv`/JSON and the Stage 2 reports: coverage, merge counts, missing Japanese forms, sound-rule pivot/examples, build summary, and `char_key_collisions.csv`. The sole collision is `著 -> {着, 著}`, and both rows retain their source-backed Korean/Japanese readings.
- Added `tests/test_char_collisions.py` for standing checks C1/C2 and expanded the character tests for `key_char`, 着/著, the six fixed characters in every language, NFC, source suffix removal, glyph mappings, coverage, and stable IDs.
- Fixed Unihan `kHangul` source-tag removal at the loader root: tags include values such as `:0N`, not only hexadecimal-looking tags such as `:0E`. Generated Korean readings no longer contain provenance suffixes.
- Validation: 16 tests pass; 3,000 rows; 45 missing `jp`, 49 missing `ja_on`, 0 missing `ko`, 0 missing `pinyin`, 709 missing `vi`; 1,835 verified Vietnamese primaries. Two consecutive rebuilds produced the same `chars.csv` SHA-256: `b6bffbc97b3d7eef0df4f77c389a8acd6091333473afeebe33e1076e99c08102`.
- Intermediate source-normalized CSVs remain reproducible and are git-ignored; `ff_candidates.csv` stays explicitly trackable for the Stage 3→4 handoff. No new data decision was needed, so `DECISIONS.md` is unchanged.

## 2026-11-04 Claude — Stage 2 gate
- PASS on attempt 1; evidence and the rules_report review are in `docs/GATES.md`. No data changes; no new decisions (non-blocking notes recorded in HANDOFF Open problems).

## 2026-11-04 Claude — Pre-Stage-3 readiness review (requested by the user; docs only, no pipeline or data change)
Measured with throw-away scripts on the checksum-locked `raw/` files and `data/staging/`. The scripts are not in the repo; the rules and numbers are in DECISIONS D39-D50.

### Step 0: user refinement of D39
Applied. Korean readings are normalized for 두음법칙 before counting; `ja_on` is out of scope and keeps KANJIDIC2 order. **One addition found by testing:** normalization must depend on position. Mapping 노→로 everywhere (怒's `ko_all` is 노;로) would turn 怒 into 로, so a syllable is mapped back only at word start, plus 열→렬 and 율→률 after a vowel or ㄴ. Simulated: 樂 락, 歷 력, 怒 노, 行 행.

### Pass 1: source joins against the raw data
**Looked at:** hsk30 rows and keys, CC-CEDICT per form, JMdict on every HSK word, hanja.txt on every HSK word, Kaikki rules A and B, FrequencyWords, VI-only candidates, ff filter, the 20 test words.
**Found:**
- 80 repeated `(trad, pinyin)` pairs, so "once per form and reading" and `id_map` could not hold (D41).
- PROMPT's step order cannot run: Korean matching needs readings of characters without rows (D40).
- Korean: hsk30 uses Taiwan forms and hanja.txt Korean forms, so trad-only matching missed 教育, 研究, 真理. Taking the first reading in file order gave 력사, 련습, 녀자, 화거. (D43)
- Japanese: D31's ranking gave 好 よしみ, 更 こもごも; `simp` matching gave 聽 ポンド; `sK`/`sk` were not handled. A blanket on'yomi preference was tried and rejected (今年 こんねん). (D42)
- Vietnamese: rule A with several values was undefined; polyphones could not be told apart, so test words 行 and 樂 had no reading (D44).
- `*_all` "unchanged" (D39) contradicted "primary first" (SCHEMA) and would have left 항 first in the glyph view (D39).
- `word_chars` had no pinyin column, though D37 and D39 both need one (D45).
- VI-only: about 1,212 candidates for 1,200 places, so the cap filters nothing, and syllable frequency put 自刎 at level 3 (D46). The `trad|ja|vi` ID key changes when a reading changes (D46).
- PROMPT's "frequent hanja.txt words" is impossible: the file has no frequency. The filter is now measured at about 2,880 rows (D47).
- Stage 3 and D36 order was unclear; the word list now freezes after the second round (D46).
- 手紙 and 越南 are not HSK words, so the test-word criterion was not measurable (D49, table in GATES).
- `words` had only an English gloss, though Stage 4 must compare meanings per language (D48).
**Changed:** D39 rewritten; D40-D50 added; SCHEMA columns, ID keys, merge table §1.8; spec addenda; GATES checklist and test-word table; HANDOFF task and sequence.

### Pass 2: re-read the new text against the data and the existing code
**Looked at:** every number and example written in Pass 1, re-measured; `tests/` and `pipeline/run_all.py`; the D37/D38 linking; variant duplicates.
**Found (several were errors in my own Pass 1 text):**
- Korean counts mixed forms and rows (7,123 is rows, 6,847 is forms): corrected. The ㅅ exception named 횟수, but hanja.txt has only 차수 for 次數: the relevant words are 숫자 and 찻간. 허락 was a wrong example; the ㄴ↔ㄹ allowance covers exactly one word, 곤란.
- CC-CEDICT fallback measured: 10,974 by key, 16 + 3 by fallback, 35 unmatched.
- `build_chars.py`, `tests/test_chars.py:23` and `test_c2` assume 3,000 rows and 88 missing variants, and would fail once `chars` grows (D40).
- Growth is 82 rows from HSK words, not D38's 88, because D30 keeps only the first form in 34 rows (D48, GATES C2).
- 6 VI-only candidates were spelling variants of HSK words (行爲 / 行為); 2 HSK words gain a reading through a variant (D44, D46).
- Link check: all 42 著/着 positions resolve by `simp`, 0 ambiguous; 2 `simp` mismatches (反覆, 答覆), which is the case D38 predicted.
- D42 said single-character readings ran in KANJIDIC2 order, which gives 樂 がく; changed to JMdict order among on'yomi, which gives らく.
- Missing rule: built `jp` when a character has no Japanese form (D42).
**Changed:** the items above; overrides extended to `chars` primaries (丹 → 란 is the example).

### Pass 3: consistency, from the reader's side (Codex, the gate, later stages)
**Looked at:** D39-D50 read through in full; HANDOFF as Codex will read it; each Done-when item asking "what number proves this?"; Stages 4 and 5 for effects of the new rules.
**Found:**
- The D39 count could pick a reading outside `*_all`, contradicting "set unchanged": such readings are now not counted and are reported.
- `ko_base` was undefined for the D43 exceptions (숫, 찻, 란): defined (D45).
- `ja_multi_candidates` is about 170 rows, not 80 (41 multi-character + 129 single): gate scope set accordingly.
- Glyph view would show 낙 / 락 / 악 / 요 and 력 / 역, unlike the prototype's 락 / 악 and 력: new `ko_base_all` (SCHEMA §3.5).
- Stage 5 rule examples showed primaries beside a pair's finals, which can disagree: examples now need pair = primaries (D45).
- Stale HANDOFF lines removed (Stage 2 "comes after Codex", the old D39 note, duplicated heads-up). A wrong "93%" in D46 corrected.
**Why I think little is left:** every expected count in SCHEMA §1.8 and GATES comes from a simulation of the written rule, and the test-word table matches the simulated output for all 20 words. **Not verified:** nothing has been built, so counts are expectations within a margin; the Vietnamese D39 simulation gives 12 changes, and 液 → giá looks wrong, so it is on the gate's list; `ko_base_all` and the D45 rules report were specified but not simulated; `kSemanticVariant` matches include some false friends (坐下 via 座下), sampled at the gate.

### Open: four questions in D50
Asked on 2026-11-04 and not answered. Defaults are recorded, and the user's existing decision on pinyin is left as it was.

## 2026-11-04 Claude — User's answers to D50 applied (docs only)
- **D39:** pinyin removed from the evidence rule; `chars.pinyin` keeps `kMandarin` order. `word_chars.pinyin_syllable` stays, because D37, D43 and D44 use it.
- **Japanese single-character words:** on'yomi first, confirmed. **Korean single-character words:** base form, confirmed.
- **Review lists:** Claude proposes at the Stage 3 gate, the user confirms the short list, then overrides are written and the data rebuilt (`GATES.md` check 9).
- **茶:** `chars.ko` must end as 차. Checked: the only one-candidate evidence word is 茶葉 다엽, so the first build gives 다, and even with 홍차 and 녹차 confirmed a 2-2 tie would keep 다. It therefore goes on the short list with an override, and Codex's test accepts 다 until then.
- **國 in the test table:** the user asked to fix or explain. Explained, not changed: JMdict's only entry for 国 is くに, so くに follows the chosen rule; こく is KANJIDIC2's reading and is `chars.ja_on`. Checking this showed the same applies to about 260 of 970 single-character forms, some with bad kun readings (電 いなずま). Falling back to KANJIDIC2 would change all of them, so it was put to the user as a follow-up rather than decided here.
- Also updated so nothing contradicts D39: D42, D43, D45, `SCHEMA.md` and the spec addendum (the spec wins on conflict, so its old line had to change).

## 2026-11-04 Claude — Single-character Japanese fallback (user decision; docs only)
- D42, D50: if JMdict has no on'yomi for a single-character word, `ja` = `chars.ja_on`, the JMdict readings go to `ja_alt`, and `source_ja=kanjidic2_on`. Simulated: 國 こく, 電 でん, 海 かい, 手 しゅ; 269 of 1,006 rows use it.
- Consequences written down: katakana-only words (吃, 噸) now get an on'yomi instead of an empty `ja`; expected `ja` rows rise from about 5,600 to about 5,650; 〇 keeps れい because KANJIDIC2 has no on'yomi for it.
- Boundary set by Claude: the fallback needs a JMdict entry for the form. About 580 single-character rows with no entry (很, 就) keep `ja` empty.
- GATES test table and check 10, HANDOFF task and Done-when, and SCHEMA (`ja`, `ja_common`, `source_ja`) updated. The D50 follow-up is closed.

## 2026-11-04 Claude — Stage 3 gate: FAIL, attempt 1
- **Checked:** the `GATES.md` Stage 3 checklist, on disk, with independent scripts; 22 tests and the double rebuild rerun (OK, `git status` clean afterwards).
- **Passed:** row and ID integrity, coverage, `card_eligible`, `word_chars` structure, all 20 test words, 30 of 30 sampled words traced to their sources.
- **Failed:** (1) `korean_base` returns the surface syllable and `apply_d39` counts non-evidence words: at least 49 wrong Korean primaries (流 유, 旅 여, 老 노), and the flag column was hard-coded. (2) The Korean variant graph was used for JMdict: 31 single-character rows with wrong forms (弄 瘧, 滾 菌); on'yomi looked up by `trad` gave 歲 とし. (3) No real `validate=` on the word merges; `merge_report.csv` carried literal text. (4) Smaller: `vi_only_report.csv` flags and columns, 10 empty `simp`, 41 unresolved pinyin rows.
- **Found beyond the checklist:** rule B accepts homophones (食物 thực vật, 不行 bất hạnh); 42% of `vi` words had no `gloss_vi`.
- **Decided:** D51. **Docs:** GATES (result, 手紙 `vi` table entry corrected), SCHEMA §1.7, spec addendum, HANDOFF (F1-F13, expected values). **Added:** `docs/review_scripts/stage3_ko_base_reference.py`.
- **Deferred:** short-list picks (about 205 rows) to attempt 2, because the fixes change the lists and the user should confirm once. `pipeline/overrides.csv` stays header-only. D36 search not started.
