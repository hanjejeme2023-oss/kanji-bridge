# HANDOFF

Read `PROMPT.md` first, then this file. Do only the assignment for your role. Update this file, `CHANGELOG.md`, `DECISIONS.md` when done; `git commit`; stop with one line `Next: <agent> — <task>`.

## Current status
- Stage 0 (setup) — **DONE** by Claude, 2026-11-04.
- Stage 1 (sources and licences) — **DONE** by Codex; **Claude review DONE** 2026-11-04. All blocking source/licence decisions are closed (DECISIONS D23–D34). Evidence: `docs/STAGE1_REVIEW.md`; reference scripts (evidence, not pipeline): `docs/review_scripts/`.
- Contract files: `docs/SCHEMA.md` (updated: level 1–7, source tags, new reports), `config/rules.json`, `docs/DECISIONS.md` (D1–D52), `docs/final-data-spec.md` (+ Addenda), `docs/SOURCES.md` (all rows now decided).
- `raw/` is git-ignored and recreated by `pipeline/download.py` (checksums in committed `pipeline/source_manifest.csv`). Licence copies are in `licenses/`.
- Git identity: `Hanje Unesaki <311183901+hanjejeme2023-oss@users.noreply.github.com>` (D19). Check `git config user.email` before committing.
- Environment: Python 3.12.10 + pandas 3.1.1 (`pipeline/requirements.txt`). On this machine the Python with pandas is `<user folder>\AppData\Local\Programs\Python\Python312\python.exe`; the `python` on the bash PATH may be a Store stub without pandas.
- Prototype: `prototype/index.html` (frozen).
- Stage 2 (character table) — **DONE** by Codex, 2026-11-04. Revised D37 is implemented as two rows with unique `key_char`; 3,000 rows and all Stage 2 reports are committed. Stage 2 gate: PASS (Claude, 2026-11-04).
- **PROMPT Rule 11 (stage gates) is in force.** Gate results are logged in `docs/GATES.md`. Stage 1 gate: PASS. Stage 2 gate: PASS (both 2026-11-04).
- Pre-Stage-3 readiness review: **DONE** by Claude, 2026-11-04 (three passes, CHANGELOG; decisions D39-D50).
- Stage 3 (word table) — built by Codex, 2026-11-04. Gate attempt 1 failed; F1-F13 fixed by Codex, 2026-11-05. **Stage 3 gate: PASS (attempt 2, Claude, 2026-11-05)** after the user confirmed the review short list: `pipeline/overrides.csv` has 77 rows (D52). Evidence: `docs/GATES.md`; picks: `docs/STAGE3_SHORTLIST.md`.
- Current build: 12,229 words (11,028 HSK + 1,201 VI-only), 3,178 chars, 24,458 `word_chars`. HSK coverage: `ja` 5,703, `ko` 7,110, `vi` 3,880, all four 3,111; `card_eligible` 7,354 HSK / 8,555 total. **The word list is not frozen yet:** it freezes after the D36 round (D46).
- D36 Vietnamese source search — **DONE** by Claude, 2026-11-05. 8 candidates checked; **Kaikki English-Wiktionary Vietnamese entries accepted for the word list only (rule A2, D53)**: seeded precision 199/200, +356 HSK words (35.18% → 38.41%). Seven rejected (SOURCES 7D-7J). Evidence: `docs/D36_VI_SOURCE_SEARCH.md`. No licensed Vietnamese word-frequency list exists among them.
- **Stage 4 mode decided by the user: Python batch script on the Gemini API (D54).** The Stage 4 assignment is written by Claude after the repeat Stage 3 gate and the **Vietnamese finalization (D55)**, which the user added on 2026-11-05.

## NEXT ASSIGNMENT
**Agent: Codex — integrate source 7C (rule A2, D53) and rerun all of Stage 3.** Read D53 first; D44, D46, D47, D51 and D52 still apply where D53 does not change them. Do not improvise a data rule; if one is missing, stop and raise it here.

1. **Download (Global Rule 4, 5, 7):** add `kaikki-enwiktionary` to `pipeline/download.py` and `pipeline/source_manifest.csv`: data `https://kaikki.org/dictionary/Vietnamese/kaikki.org-dictionary-Vietnamese.jsonl` (Claude's measured copy: 83,424,329 bytes, SHA-256 `186cd0a62d876dada70c9761bc05e598c8cf7b9a48e0aa518bab6c649e28d945`; the file is rolling, so record whatever you download and state the difference) and licence page `https://kaikki.org/dictionary/index.html` ("Copyright and license" section) → copy to `licenses/KAIKKI-ENWIKTIONARY-LICENSE.html`. `raw/` stays uncommitted. Fill `docs/SOURCES.md` section 2 for 7C.
2. **Loader** (new `pipeline/load_kaikki_en.py` or an extension of `load_kaikki.py`): exactly D53 item 1. Output one row per (Han form, `vi`) with `pos`, first gloss, `obsolete_only`. Report the counts in your note (Claude measured 14,513 raw pairs; after the filter, pairs with syllables = characters).
3. **Rule A2 in the word match (D53 item 2)** for HSK words, after A, B and the D51 filter, only where `vi` is empty; `source_vi=kaikki_en_han`; `gloss_vi` = first gloss; `obsolete_only` → `vi_ambiguous.csv` `reason=obsolete_only`. Attach it as a real merge with `indicator=True` and a `validate=` argument, logged in `merge_report.csv` (add the row to SCHEMA §1.8 in your note; Claude updates SCHEMA at the gate if needed). `overrides.csv` must accept A2 values as candidates; overrides still apply last.
4. **D39 / D45 (D53 item 3):** A2 words are evidence words; `not_in_all` for syllables outside `vi_all`; `rules_examples.csv` tag `kaikki_en_han`.
5. **VI-only (D53 item 4):** rerun the D46 selection with the union of Kaikki-vi rule A and A2 pairs; add `source_vi` to `vi_only_report.csv`. New VI-only words get new IDs; dropped ones keep theirs unused.
6. **`ff_candidates.csv` (D53 item 5):** membership unchanged; fill empty `vi`/`gloss_vi` from A2.
7. **Tests:** (a) A2 never changes a non-empty A/B value (compare with a fixture of the `7827546` values, or test the rule on small frames); (b) **every one of the 77 `overrides.csv` rows still applies** (value in output = override value); (c) the six `obsolete_only` words are empty and reported; 新聞 `vi` empty; (d) one A2 word per length class (e.g. 唱歌 xướng ca, 絕大多數 tuyệt đại đa số, 豹 báo); (e) i/y collapse: 自己 = `tự kỷ`. Run all tests; rebuild twice, identical including `id_map.csv`.
8. **Override support for the Vietnamese finalization (D55 a):** `table=words`, `column=vi` accepts an empty `value` (clears `vi`); for `vi` overrides the old value is **not** moved to `vi_alt`, it goes to `vi_ambiguous.csv` with `reason=override_cleared` / `override_replaced`. Ko/ja overrides unchanged. Report whether any current output changes because of this (expected: none, the 19 current `vi` overrides replaced empty values; state it if not). Test: a cleared value is empty, not in `vi_alt`, and reported.
9. **7C character readings behind a switch (D55 b):** add `config/vi_sources.json` with `{"kaikki_en_char_readings": false}` and implement the rule in D55 (b), tag `kaikki_en_char`. **Build and hand off with the switch `false`**, so the repeat gate measures D53 alone. Also run it once with `true` (do not commit that build) and give in your note: characters confirmed, characters given a first reading, HSK `vi` coverage and all-four counts, `char_primary_changes` count. Test: with the switch `false` the output is identical to a build without the feature.
10. **Hand-off note:** counts of every report (as in the Stage 3 note), HSK coverage per language and all four, `card_eligible` HSK/total, VI-only selected/changed/dropped counts, `vi_ambiguous` by reason, `alignment_mismatches` by reason, and **a diff of `chars.ko`/`chars.vi` primaries and of `char_primary_changes.csv` against commit `7827546`** (Claude needs it for the D52 tie rule). Expected values: GATES "Stage 3 repeat gate after the D36 integration" (R1-R8). Explain any difference above about 2%; do not force numbers.

**At the end, hand off to Claude (repeat Stage 3 gate, GATES R1-R8 plus checks 1-13, C1, C2).** After it passes, Claude does the Vietnamese finalization (D55), not Stage 4.

## Stage 3 gate attempt 2: outcome in brief
- **Pass:** checks 2, 5, 6, 7, 8, 10, 11, 13, C1, C2 and the 20 test words. Real validated merges; VI-only report complete (1,201 selected); pinyin alignment 0 failures; Korean primaries match an independent recomputation exactly; single-character Japanese fixed; grown `simp` complete.
- **Short list (check 9):** confirmed by the user and applied: 59 word overrides (23 Korean, 16 Japanese incl. the user's 家 か and 月 げつ, 19 Vietnamese) and 18 character overrides (茶 차, 寧 녕, 13 law-form base forms, and 貝 패, 滑 활, 省 성, 更 경 to undo D39 tie flips caused by the word overrides). The 12 `ff_candidates` rule-B rows stay empty.
- **Tests:** 29 OK; two rebuilds identical. Two Stage 2/3 tests that pinned 茶 = 다 now expect 차 (D39/D50).
- Non-blocking findings for loop 1 are in "Open problems" below.

## Stage 1 review: outcome in brief (details in STAGE1_REVIEW.md)
- **Licences:** all accepted. hsk30 accepted with a recorded provenance risk (confirmed by the user, D35). Dataset will be **CC BY-SA 4.0**.
- **Vietnamese:** Kaikki (reading + Han form) and FrequencyWords (frequency proxy) selected. Unihan `kVietnamese` mixes Nôm readings (200-sample check: 31 covered, 29 agree; whole overlap 88%), so it is used only with verification flags. **Measured ceiling: about 35% of HSK words (3,832 / 11,092) and 61% of HSK characters (1,835 / 3,000) get a Vietnamese reading with evidence.** Cards in the Chinese target are unaffected (pinyin always exists); Vietnamese-target decks will be smaller than the HSK list. This is a source limit, not a bug; report it in `coverage_report.csv`.
- **Shinjitai:** inverted OpenCC `JPShinjitaiCharacters` (16/16 on the prototype's glyph pairs), KANJIDIC2 tie-break.

## COMPLETED ASSIGNMENT — Claude Stage 3 gate, attempt 2 (PASS after the user's short-list confirmation)

## COMPLETED ASSIGNMENT — Codex Stage 3 gate fixes (F1-F13)
Implemented only the corrections assigned after attempt 1. `pipeline/overrides.csv` remains header-only.

### Fixes
**Korean primaries (D39)**
- **F1. `ko_base` normalization.** `korean_base` (`stage3_match.py:128-152`) returns the surface syllable whenever it is in `ko_all`, so D39's mapping never happens for characters listing both forms. Split it: keep the current acceptance logic for the D43 alignment filter and law-pair comparisons, and add a normalization function implementing D39 exactly. Position 1: ㅇ+iotized vowel → ㄹ form, else ㄴ form; ㄴ+other vowel → ㄹ form; each only if that form is in `ko_all`; otherwise the syllable itself. Later positions: only 열→렬 and 율→률 after a vowel or ㄴ-final, only if in `ko_all`; otherwise the syllable itself. The D45 exceptions stay (숫→수, 찻→차, 곤란's 란→난). Use it for `ko_base` and for the D43 evidence counts.
- **F2. Evidence words.** `apply_d39` (`build_words.py:1055-1063`) counts every word. Count only D39's evidence words, for `ko` and `vi`: multi-character words with one candidate left or settled by an override, and single-character words with one candidate left. Readings outside `*_all` stay uncounted. The no-evidence report follows the same definition.
- **F3. `ko_law_form_suspect`.** Hard-coded `False` (line 1076). Compute it as D39 says.

**Merges**
- **F4. Real merges.** Build the D40 `ja_match`, `ko_match`, `vi_match` frames (one row per word key, only for words with a value) and attach them with `pd.merge(how="left", validate="1:1", indicator=True)`; CC-CEDICT exact key with `validate="m:1"` and `indicator=True`; Kaikki rule-A with `how="outer"`, `validate="m:1"`, `indicator=True`. `merge_report.csv` takes counts from `_merge` and `validate` from the argument actually passed. Fill the empty `validate` cells of the Stage 2 rows.

**Japanese (D51 items 1-2)**
- **F5.** `word_forms` (`build_words.py:219`): D43 variant forms only for 2+ characters, after the D42 forms. A single character with no D42 form in JMdict has no entry: `ja` empty, per D42.
- **F6.** `match_japanese_row` (line 276): take the on'yomi set from the linked `chars` row's `ja_on_all`.

**Vietnamese (D51 items 3-5)**
- **F7.** Rule-B conflict filter for 2+ characters, on HSK words, VI-only and `ff_candidates.csv`. Dropped values go to `vi_ambiguous.csv` with `reason=rule_b_conflict`, not to `vi_alt`. An override may use a value listed there.
- **F8.** One-character words use rule A on `trad` only. Any rule-A pair outside `vi_all` that reaches `rules_examples.csv` is tagged `kaikki_han`, not blank (鑑 giám).
- **F9.** `gloss_vi` for rule-B words: extend `load_kaikki.py` to keep each headword's first gloss; fill `words.gloss_vi` and `ff_candidates.gloss_vi`.

**Reports and columns**
- **F10.** `simp` of grown `chars` rows per D51 item 6. HSK-list rows unchanged.
- **F11.** `vi_only_report.csv` per SCHEMA §1.7: add `trad, word_id, rank, level`; `selected=true` on exactly the final VI-only rows, the seed included.
- **F12.** `pinyin_syllable`: a single-character word gets the whole pinyin; a word without a usable key is segmented by the set of CC-CEDICT syllables (D45). Only real failures stay in `alignment_mismatches.csv`.

**Tests**
- **F13.** Add to `tests/`, each failing on the current build: the primaries below; `ko_base` of 流行 = 류, 旅行 = 려, 分裂 = 렬; `ja_on` = first KANJIDIC2 value and `pinyin` = first `kMandarin` value for every row, and `*_all` sets equal to before D39 (D39 requires these, and they are missing); no single-character `jp` outside the D42 forms; the Japanese, Vietnamese and `simp` values below; `validate` values in `merge_report.csv` match a real call (a code-level test or a shared helper); `vi_only_report.csv` `selected=true` count = VI-only row count. Rerun everything, rebuild twice.

### Expected results at the re-check
These were computed independently where stated; any difference must be explained in your note, not forced.
| Item | Expected |
|---|---|
| `chars.ko` (recomputed: `docs/review_scripts/stage3_ko_base_reference.py`) | 老 로, 流 류, 旅 려, 連 련, 聯 련, 領 령, 律 률, 列 렬, 陸 륙, 輪 륜, 兩 량, 零 령, 冷 랭, 綠 록, 勞 로; 輯 집 (no evidence once 편즙 is excluded). Unchanged: 歷 력, 年 년, 女 녀, 怒 노, 行 행, 樂 락 or 악. 茶 stays 다 until the short list |
| `ko_law_form_suspect` | at least 爐, 廊, 虜, 魯, 碌 true |
| Japanese | 弄, 滾, 捉, 它, 她, 聽, 拆, 蛋, 掉: `jp` never 瘧, 菌, 杓, 佗, 他, 听, 責, 蜑, 棹; `ja` empty where the form has no JMdict entry. 歲 さい, 腳 きゃく, 內 ない, 值 ち, 戶 こ, 鄉 きょう, 號 ごう. 國 こく, 電 でん, 海 かい, 手 しゅ unchanged. 模仿 模倣, 身份 身分 unchanged. HSK `ja` about 5,700 |
| Vietnamese | 食物, 實物, 不行, 只是, 父女, 路面, 定為 `vi` empty and in `vi_ambiguous.csv`. 麵 empty, 穩 ổn. At most 21 rule-B words drop. Rule-B words with `gloss_vi`: nearly all of about 2,140 |
| `chars.simp` | 0 empty unless D51 6(d) applies; 餵 喂, 託 托, 譁 哗, 鵰 雕, 陀 陀, 簿 簿. `char_simp_mismatch.csv` about 3 rows (反覆, 答覆, 彷彿) |
| `alignment_mismatches.csv` | `pinyin` rows close to 0; 麵 and 穩 gone from `not_in_all` |
| `merge_report.csv` | same counts as before except the effects above |

In your note give the row counts of every report, `char_primary_changes.csv` with its count, and what changed in `card_eligible`. **At the end, hand back to Claude (Stage 3 gate, attempt 2).**

### Codex completion evidence (2026-11-05)
- F1-F3: D39 alignment acceptance and primary normalization are separate. Expected primaries now match: 老 로, 流 류, 旅 려, 連/聯 련, 領 령, 律 률, 列 렬, 陸 륙, 輪 륜, 兩 량, 零 령, 冷 랭, 綠 록, 勞 로, 輯 집; 流行/旅行/分裂 bases are 류/려/렬. Thirteen no-evidence Korean rows are marked law-form suspects, including 爐, 廊, 虜, 魯, 碌. 茶 remains **다** pending the gate short list.
- F4: CC-CEDICT exact and fallback, Kaikki outer, and all three match tables now use real pandas merges with `indicator=True` and the recorded `validate` argument. Stage 2 merge rows also have their actual validation cardinality. The Kaikki merge reports 1,714 HSK rows `both`; this is 1,697 distinct matched Han forms plus 17 repeated HSK `(trad, pinyin)` rows, whereas the attempt-1 count was a distinct-form simulation.
- F5-F6: HSK Japanese coverage is 5,703. The nine bad one-character variant matches are gone and their `ja` is empty; 歲/腳/內/值/戶/鄉/號 and 國/電/海/手 have the expected on'yomi; 模仿→模倣 and 身份→身分 remain.
- F7-F9: the seven named rule-B conflicts are empty and reported. There are 24 HSK conflict candidates but **21 previously selected HSK values drop**; the other three were already unresolved. Twelve additional false-friend conflicts are reported. Rule-B glosses cover 2,134 / 2,142 words and 614 / 616 false-friend rows with Vietnamese values. 鑑 giám is tagged `kaikki_han` in `rules_examples.csv`.
- F10-F12: grown-character `simp` has 0 empty values; 餵/託/譁/鵰/陀/簿 match the expected forms. `char_simp_mismatch.csv` is exactly 反覆, 答覆, 彷彿. `vi_only_report.csv` has all required columns and exactly 1,201 selected rows. Pinyin alignment has 0 failures; `alignment_mismatches.csv` now contains only 5 real Korean/Vietnamese exceptions.
- Tables: 12,229 words (11,028 HSK + 1,201 VI-only), 24,458 `word_chars`, 3,178 chars. HSK coverage: Japanese 5,703, Korean 7,110, pinyin 11,028, Vietnamese 3,861, all four 3,094. `card_eligible` is unchanged: 7,354 HSK / 8,555 total.
- Report rows: `cedict_unmatched` 35; `ja_multi_candidates` 149; `ko_multi_candidates` 136; `ko_unresolved` 53; `vi_ambiguous` 47 (11 several-candidate + 36 rule-B conflict: 24 word rows + 12 ff rows); `alignment_mismatches` 5; `char_primary_changes` **84**; `char_primary_no_evidence` 1,841; `char_ambiguous` 0; `char_simp_mismatch` 3; `char_key_collisions` 2; `no_jp_form` 48; `rules_examples` 2,031; `rules_report` 7; `coverage_report` 41; `merge_report` 37; `vi_only_report` 3,367; `ff_candidates` 2,944.
- F13: added seven focused regression tests. Full validation: **29 tests passed in 624.999 s**. The rebuild test ran the complete pipeline twice and compared every final file plus `pipeline/id_map.csv`: identical.

### What Claude does at attempt 2
Reruns the failed checks, scans `char_primary_changes.csv` (including top-count-1 changes and 寧, which D39's literal mapping may send to 령), then proposes picks for the short list (D50 item 4, including 茶 → 차, about 205 rows plus any `rule_b_conflict` rows) and stops for the user. Overrides, a rebuild and the D36 search come after that.

## Stage 3 gate attempt 1: outcome in brief
- **Passed:** row and ID integrity, coverage, `card_eligible`, `word_chars` structure, the 20 test words, the 30-word source sample (30 of 30), tests, rebuild identical.
- **Failed:** Korean base forms and evidence (at least 49 wrong primaries), wrong Japanese forms on single-character cards (31 rows), no real `validate=` merges, plus smaller report and rule items. Details: `docs/GATES.md`.

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
3. **Claude: Vietnamese source search (D36).** **DONE 2026-11-05: 7C accepted (D53); next is step 4 with Codex.** Reads `coverage_report.csv` and `vi_ambiguous.csv`, then:
   - searches for additional **licensed** Vietnamese resources: a Hán-Việt character dictionary (to verify/replace Unihan's Nôm-contaminated readings), a Chinese-Vietnamese or Sino-Vietnamese word list, a Vietnamese frequency list of words (not syllables); candidates to check include Wikimedia/Wiktionary-derived data other than Kaikki, open Vietnamese dictionaries, and Chinese-Vietnamese resources on GitHub/Hugging Face/academic sites;
   - records each candidate's licence from its own licence file in `docs/SOURCES.md` before anything is used; anything unlicensed, non-commercial-only, or of unclear provenance is rejected (the user is asked only for a licence judgment call);
   - measures each licensed candidate on the same yardsticks as Stage 1 (HSK words gained, agreement with existing readings on a seeded sample, precision of new readings) and records accepted sources and rules in DECISIONS.
4. **If a source is accepted:** Codex integrates it and **reruns all of Stage 3, including VI-only selection**; Claude repeats the Stage 3 gate. **If nothing is accepted:** Claude records the ceiling. *(Current: Codex integrates 7C, D53.)*
5. **Claude: Vietnamese finalization (D55, user decision 2026-11-05)**, after the repeat gate passes. Claude writes `docs/VI_SHORTLIST.md`: the 16 A/B vs A2 disagreements (incl. 詞 tờ → từ), the about 19 wrong-looking composed readings (empty or a dictionary candidate), the 6 `obsolete_only` words (empty or the candidate), the 38 rule-B values filed under other characters (keep the correct ones), 7C character readings (45 confirmations + 36 new readings; switch `config/vi_sources.json` on only if a seeded precision check gives ≥ 95%), and a fresh seeded sample of 50 words with `vi` (target ≥ 98% correct). **Stop for the user to confirm.** Then Claude writes the confirmed overrides, rebuilds, and rechecks: tests, rebuild identical, D52 tie rule, all overrides still apply. A rule-level cause found here goes to Codex before the freeze.
6. **The word list freezes here (D46, D55).** Claude writes the Stage 4 assignment (Gemini API batch script, D54), sized from the final coverage. **Gemini: Stage 4** only after this point.

## Notes for later stages
- **Stage 4 mode (D54):** Python batch script on the Gemini API, written by Codex; the assignment is written by Claude after the Vietnamese finalization (D55), which follows the repeat Stage 3 gate. **`gloss_vi` of a `kaikki_en_han` word is English** (D53); the Stage 4 prompt must say so.
- **Stage 4 (Gemini), sizes:** about 8,500 eligible words for task 1 and about 2,900 `ff_candidates` rows for task 2 before the D36 round. Words now carry `gloss_ja_en`, `gloss_ko`, `gloss_vi` (D48); a Korean reading that is a rare or archaic dictionary entry is marked `confidence: low` (D49). `ff_only` words get IDs `x|trad`.
- **Stage 5 (Codex):** glyph Korean readings use `ko_base_all`; a rule example uses only pairs equal to the primaries, and `ex[0]` = `key_char` (SCHEMA §3.2, §3.5, D45).
- **Stage 5 (Codex), user-approved addition — DECISIONS D20:** daily limit of 20 new (never-seen) cards in カード; reviews unlimited; no visible UI change except smaller counters. State in localStorage `kb_newtoday`. Add a test. List it in the Stage 5 side-by-side difference list.

## Rules to keep in mind (from PROMPT)
- No agent fills a missing reading/fact from its own knowledge. Missing stays empty and is reported.
- Do not edit `prototype/index.html`. Do not edit `SCHEMA.md`/spec/DECISIONS decisions; raise questions here in HANDOFF instead.
- If a source has no license or non-commercial-only terms: do not use it; stop and ask the user.

## Open problems / notes
- D36 search notes for loop 1 (accuracy; details in `docs/D36_VI_SOURCE_SEARCH.md`): (1) 16 words where A/B and English Wiktionary disagree, incl. 詞 `tờ` (a Nôm reading; English Wiktionary `từ`) and 奔 `hợp`; (2) 38 rule-B values that English Wiktionary files under other characters, about half wrong compositions (老是 lão thị, 行人 hạnh nhân, 忠心 trung tâm); (3) 7C character readings (chữ Hán vs Nôm separated) could confirm 45 unverified characters and flag 又 `lại`; not accepted this round.
- Stage 3 gate attempt 2 notes for loop 1 (non-blocking, details in `GATES.md`): (1) D43 filter accepts 저 for 朝著 조저 / 著落 저락 although they link to the 着 row (`ko_all` 착); the check seems to use `trad`, not the linked `key_char`. (2) Data errors D51 cannot catch: 液體 giá thể, 奔 hợp (Kaikki char reading); both in `rules_examples.csv`, not reachable by the Stage 5 rule view. (3) D39's position-1 mapping gives 異常 the base 리 (primary stays 이), same cause as 寧. (4) `overrides.csv` has no `table=ff_candidates`; three correct rule-B values (難民, 淡泊, 政治犯) stay empty unless that is added. (5) After V18 (兇惡 hung ác), VI-only 凶悪 also repeats the same Vietnamese word (attempt-1 note 2). (6) `char_primary_no_evidence.csv` reports `ko_law_form_suspect` before `chars` overrides, so the 12 overridden characters are still flagged; consider marking overridden rows.
- Stage 3 gate notes for loop 1 (non-blocking): (1) rule-B false compositions with no Kaikki etymology cannot be caught by D51 (人為 nhân vị, 手紙 thủ chỉ; 1 of 40 sampled multi-character rule-B words). (2) VI-only 凶悪 repeats HSK 兇惡: Kaikki's Han form uses the shinjitai 悪, which the D46 variant check does not link. (3) A few 2+ character JMdict variant matches are weak (蘋果 苹果 ひょうか, 眼裡 眼裏 まなうら).
- **Stage 4 input note:** `gloss_vi` on a rule-B word can be unrelated to the Han word (D51). Stage 4's prompt must tell Gemini to mark such a Vietnamese value `confidence: low` and not write a Vietnamese meaning for it. Claude adds this when writing the Stage 4 assignment.
- Known limits to report, not fix, in Stage 3: `hanja.txt` has no frequency, so a Korean reading may be a rare entry; `freq_vi` is a syllable proxy, so VI-only levels are rough until D36 finds a word list.
- Stage 2 gate notes (non-blocking): (1) resolved by D39 and D43. (2) Suspect Vietnamese readings for loop 1 accuracy: 怎 chẩn (expected chẩm; `unihan_hvsyl`), 幻 ảo (usual Hán-Việt huyễn). (3) `unihan_hvsyl` (300 chars) is a weaker check than `kaikki_aligned`.
- Resolved: hsk30 `着`/`著` collision → separate rows with `key_char` (D37, revised).
- Vietnamese coverage ceiling (about 35% of HSK words) with the current licensed sources; the search for further licensed sources runs after Stage 3, before Stage 4 (D36).
- Source #7 stays excluded (D21).
- EDRDG data impose an update-procedure requirement; `download.py --refresh` exists; release documentation must explain updates.
- hsk30 provenance risk: **accepted by the user** (D35, personal non-commercial project; revisit if ever published commercially).

## Log
- 2026-11-05 Claude — user added a Vietnamese finalization step (D55) between the repeat Stage 3 gate and the freeze; recorded in the planned sequence; Codex task extended with items 8-9 (empty/replace `vi` overrides that never feed `vi_alt`; 7C character readings behind a switch, default off), which the step needs. Next assignment unchanged: Codex integrates 7C.
- 2026-11-05 Claude — D36 Vietnamese source search: 8 candidates checked, licence first; Kaikki English-Wiktionary Vietnamese entries accepted for the word list only (rule A2, D53; precision 199/200, +356 HSK words, 38.41%); 7 rejected (SOURCES 7D-7J). User chose the Gemini API batch script for Stage 4 (D54). No data or pipeline changed. Next: Codex integrates 7C and reruns Stage 3.
- 2026-11-05 Claude — Stage 3 gate PASS (attempt 2): user-confirmed short list written to `overrides.csv` (77 rows incl. 4 tie fixes the user confirmed after the first rebuild); rebuild and 29 tests OK; 茶 = 차. Next: Claude D36 Vietnamese source search.
- 2026-11-05 Claude — Stage 3 gate attempt 2: F1-F13 verified; all rerun checks pass (29 tests OK, rebuild identical to `e18e7e0`); 84 primary changes scanned (寧 bad); short list proposed in `STAGE3_SHORTLIST.md`, no overrides written. Next: User confirms the short list, then Claude finishes the gate.
- 2026-11-05 Codex — Stage 3 gate fixes F1-F13 complete: corrected D39 normalization/evidence, real validated merges, D51 Japanese/Vietnamese behavior, reports and pinyin alignment; 29 tests pass and two rebuilds are identical. Next: Claude Stage 3 gate attempt 2.
- 2026-11-04 Claude — Stage 3 gate FAIL (attempt 1): at least 49 wrong Korean primaries (`ko_base` not normalized, non-evidence words counted), wrong Japanese forms on 31 single-character rows (variant graph used for JMdict), no real `validate=` merges, rule-B homophones, smaller report items. D51 recorded; F1-F13 assigned; short-list picks deferred to attempt 2. Next: Codex fixes.
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
