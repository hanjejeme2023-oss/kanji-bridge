# GATES (PROMPT Rule 11)

Every stage 1-5 ends with a gate review by Claude. A gate checks the stage's **Done when** criteria with evidence (counts, file checks, the 20 test words, a small random sample). Pass: next stage assigned. Fail: exact failures and fixes go to the agent that did the stage, who fixes only those items and hands back. A second failure of the same gate: Claude stops and asks the user. Gates are short checks; non-blocking problems go to "Open problems" in HANDOFF for the Stage 6 loops.

## Standing collision checks (DECISIONS D37, D38) — run at the Stage 2 gate, the Stage 3 gate, and whenever `chars` grows

| Check | What to verify (with evidence) | Expected |
|---|---|---|
| **C1 many → one** (several source characters share one `trad`) | `char_key_collisions.csv`; `char_id` and `key_char` unique; every shared `trad` resolved by D37; after Stage 3: no word character unlinked or ambiguous without being listed in `char_ambiguous.csv` | Stage 2: exactly `著` → `着`, `著`; 3,000 rows |
| **C2 one → many** (one simplified character, several traditional forms) | HSK-list rows with more than one traditional variant; each variant used in a word `trad` has its own `chars` row (Stage 3); no empty `trad`; `char_simp_mismatch.csv` reviewed; counts reproduced | On the base HSK rows: 83 rows / 89 non-first variants / 88 variants without a row (1, 覆, already a row). Stage 3 growth: **82** rows from HSK words, not 88, because D30 keeps only the first form in 34 rows (D48), plus about 108 from VI-only words; 0 unlinked word characters; `char_simp_mismatch.csv` about 2 rows among existing characters (反覆, 答覆) |

Reference measurement: `docs/review_scripts/char_collision_reference.py`. Tests: `tests/test_char_collisions.py` (Codex).

## Stage 3 gate checklist (written before Stage 3, pre-Stage-3 review; expected values measured on the raw files, D40-D49)

The gate also reruns C1 and C2 above. The Stage 3 gate is repeated after any D36 integration.

| # | Check | Expected |
|---|---|---|
| 1 | One row per `(trad, pinyin)` for HSK words; `word_id` unique; no duplicate ID key | 11,028 HSK rows (D41) |
| 2 | `merge_report.csv` has every merge in SCHEMA §1.8; `validate=` in the code | counts within about 2% of §1.8 |
| 3 | Coverage of HSK rows | `ko` about 64%, `ja` about 51%, `vi` about 35%, all four about 3,000; a large difference needs an explanation |
| 4 | `card_eligible` follows D11 exactly (recompute it from the columns) | about 7,350 HSK rows; no `built_from_chars`-only rows |
| 5 | VI-only: `vi_only_report.csv`, band counts match D27, no variant repeats of HSK words, no single characters, no IDs with readings in the key | about 1,200 rows + 越南 |
| 6 | `word_chars` unique on `(word_id, position)`; row count = sum of word lengths; `alignment_mismatches.csv` has a reason on every row | `count` mismatches explained; `ko_exception` few |
| 7 | D39: recompute each `ko` and `vi` primary from `word_chars`; `*_all` sets unchanged; `ja_on` = KANJIDIC2 first; `pinyin` = first `kMandarin` value; both reports exist | 樂 락 or 악, 歷 력, 怒 노, 行 행; 茶 per check 9; scan changes with a top count of 1 (about 33 for Korean; 丹 → 란, 液 → giá are bad) and write overrides |
| 8 | `rules_report.csv` rebuilt from verified pairs after D39 | 0 `unihan_unverified`; large cells follow `config/rules.json`; investigate new large off-pattern cells |
| 9 | Review lists: `ko_multi_candidates.csv`, `ja_multi_candidates.csv`, `vi_ambiguous.csv` | about 124, 170, 13 rows. **Claude proposes a pick for each row on the short list, then stops and asks the user to confirm (D50 item 4).** Short list: all multi-character rows, all `vi_ambiguous` rows, single-character rows at levels 1-3, and **茶 if `chars.ko` = 다** (proposed override `chars,茶,ko,차`; also propose 茶 차, 紅茶 홍차, 綠茶 녹차). Picks must be dictionary candidates. After confirmation, Claude writes the rows to `overrides.csv` and reruns `run_all.py` and the tests; the gate cannot pass before that. Other rows go to loop 1 |
| 10 | Sample 20 `libhangul_variant` words and all single-character `ja` values at levels 1-2 | variant false matches (坐下 via 座下) are listed; a rate above 5% means narrowing the variant fields. Fallback rows (`source_ja=kanjidic2_on`, about 269): `ja` = `chars.ja_on`, JMdict readings in `ja_alt`; 國 こく, 電 でん, 海 かい, 手 しゅ. A form with no JMdict entry has `ja` empty (about 580 rows) |
| 11 | `ff_candidates.csv` | 2,500-3,300 rows; 手紙 and 大丈夫 present; none in `words` |
| 12 | Random sample of 30 words across levels against the sources (record the seed) | PROMPT gate |
| 13 | Tests pass; rebuild twice identical including `id_map.csv` | |

### Test words at Stage 3 (D49)
Empty means no value is expected from the current sources; the value must then be empty, not filled in. Values in brackets are also accepted because they are review-list items. Single-character `ja` and `ko` follow the user's decisions in D50.

**國 is こく through the fallback (D42, D50 item 2):** JMdict's only entry for 国 is くに, which is not an on'yomi, so `ja` = `chars.ja_on` = こく, `source_ja=kanjidic2_on`, and くに is in `ja_alt`.

| Word | Row | `simp` | `jp` | `ja` | `ko` | `pinyin` | `vi` |
|---|---|---|---|---|---|---|---|
| 學 | HSK | 学 | 学 | がく | 학 | xué | học |
| 國 | HSK | 国 | 国 | こく | 국 | guó | quốc |
| 茶 | HSK | 茶 | 茶 | ちゃ | 차 (다 until the short list is confirmed) | chá | trà |
| 行 | HSK, 2 rows | 行 | 行 | ぎょう (こう) | 행 | xíng; háng | hành; hàng (or empty and in `vi_ambiguous`) |
| 生 | HSK | 生 | 生 | せい | 생 | shēng | sinh |
| 樂 | HSK, lè | 乐 | 楽 | らく | 락 | lè | lạc |
| 經濟 | HSK | 经济 | 経済 | けいざい | 경제 | jīngjì | kinh tế |
| 大學 | HSK | 大学 | 大学 | だいがく | 대학 | dàxué | đại học |
| 勉強 | HSK | 勉强 | 勉強 | べんきょう | 면강 | miǎnqiǎng | miễn cưỡng |
| 手紙 | **`ff_candidates.csv` only** (`words` in Stage 4) | | 手紙 (`form`) | てがみ | | shǒuzhǐ | (`thủ chỉ` accepted: rule B gives it, Kaikki's gloss is unrelated, Stage 4 judges it; table corrected at the gate, D51) |
| 銀行 | HSK | 银行 | 銀行 | ぎんこう | 은행 | yínháng | ngân hàng |
| 發展 | HSK | 发展 | 発展 | はってん | 발전 | fāzhǎn | phát triển |
| 歷史 | HSK | 历史 | 歴史 | れきし | 역사 | lìshǐ | lịch sử |
| 博士 | HSK | 博士 | 博士 | はかせ (はくし) | 박사 | bóshì | bác sĩ |
| 新聞 | HSK | 新闻 | 新聞 | しんぶん | 신문 | xīnwén | |
| 注意 | HSK | 注意 | 注意 | ちゅうい | 주의 | zhùyì | chú ý |
| 主義 | HSK | 主义 | 主義 | しゅぎ | 주의 | zhǔyì | chủ nghĩa |
| 學習 | HSK | 学习 | 学習 | がくしゅう | 학습 | xuéxí | học tập |
| 心理 | HSK | 心理 | 心理 | しんり | 심리 | xīnlǐ | tâm lý |
| 越南 | `vi_freq`, seeded (D46) | 越南 | 越南 | えつなん | 월남 | yuènán | việt nam |

Characters: 樂 `ko`=락 or 악, `ko_all` still contains 낙; 歷 `ko`=력; 行 `ko`=행; **茶 `ko`=차 when the gate passes** (다 is possible at Codex's first build, check 9); `ja_on` of all of them = KANJIDIC2 first (so 國 `chars.ja_on` = こく = its word's `ja`); `pinyin` = first `kMandarin` value.

### Stage 3 repeat gate after the D36 integration (D46, D53)
Rerun checks 1-13, C1 and C2 above, with these expected values and three extra checks. Baseline = commit `7827546` (Stage 3 PASS).

| # | Check | Expected |
|---|---|---|
| R1 | HSK coverage | `vi` about 4,236 / 11,028 (38.4%, +356; the D43 variant forms may add a few); all four about 3,360; `ja`, `ko`, pinyin unchanged; HSK `card_eligible` unchanged (7,354) |
| R2 | Rule A2 fills only empty values | no HSK word whose `vi` was non-empty at `7827546` has a different `vi`, except where an override says so; every `kaikki_en_han` value is a 7C pair for the word's form |
| R3 | `vi_ambiguous.csv` | previous rows minus any that A2 filled, plus 6 `obsolete_only` rows (新聞, 戲劇, 伯父, 不宜, 岳父, 岳母) |
| R4 | VI-only | `vi_only_report.csv` has `source_vi`; selected = VI-only row count; cap 1,200 + 越南; bands per D27; no variant repeat of an HSK word; changed and dropped VI-only words listed in the hand-off note; dropped IDs unused, not reused |
| R5 | **D52 tie rule** | diff `char_primary_changes.csv` (and `chars.ko`/`chars.vi`) against `7827546`; review every primary that changed and every tie created or broken by the new evidence words; a needed `chars` override goes to the user before the gate passes |
| R6 | **All 77 overrides still apply** | each `pipeline/overrides.csv` row's value equals the output value for its key and column (a test does this) |
| R7 | Test words | the table above, unchanged: 新聞 `vi` stays empty (`obsolete_only`) |
| R8 | 30 random words (new seed) | include at least 10 `kaikki_en_han` words, checked against the 7C entry |
| R9 | D55 support built, switched off | `config/vi_sources.json` has `kaikki_en_char_readings: false` and the build equals a build without the feature; empty and replacing `vi` overrides covered by tests; Codex's note gives the switched-on numbers |

After the repeat gate passes: **Vietnamese finalization (D55)**, then the freeze and the Stage 4 assignment.

| Stage | Gate date | Result | Attempt | Gate by |
|---|---|---|---|---|
| 1 | 2026-11-04 | PASS | 1 | Claude |
| 2 | 2026-11-04 | PASS | 1 | Claude |
| 3 | 2026-11-04 | **FAIL** | 1 | Claude |
| 3 | 2026-11-05 | **PASS** (short list confirmed and applied, D52) | 2 | Claude |
| 3 (repeat after D53) | 2026-11-05 | **FAIL** (A2 respelling, `ff_candidates` duplicates; fixes G1-G3) | 1 | Claude |
| 3 (repeat after D53) | 2026-11-06 | **PASS** (G1-G3 fixed; D55 Vietnamese finalization follows) | 2 | Claude |

## Stage 1 — sources and licences — PASS (attempt 1), 2026-11-04

Gate run after Rule 11 was added (the Stage 1 review had been done earlier under the old wording; criteria re-checked now against the files on disk).

| Done-when criterion | Evidence | Result |
|---|---|---|
| Every source downloaded or explicitly excluded with a reason | 9 sources downloaded (Unihan, KANJIDIC2, hsk30, CC-CEDICT, JMdict, libhangul, OpenCC, Kaikki, FrequencyWords); source #7 excluded with reason (no licence, missing input provenance; D21) | OK |
| `SOURCES.md` section 1 has no blank cells (要確認 only where Claude must decide) | All 12 table rows complete; the only remaining 要確認 text is the legend line in the file header; every earlier 要確認 resolved in D23 | OK |
| Every used source has its licence file in `licenses/` | 10 files in `licenses/`: Unicode, KANJIDIC2-EDRDG, JMdict-EDRDG, CC-CEDICT, CC-BY-SA-4.0, HSK30-MIT, LIBHANGUL-HANJA-BSD-3, OPENCC-Apache-2.0, KAIKKI, FREQUENCYWORDS | OK |
| `download.py` reruns without re-downloading unchanged files | Reran `pipeline/download.py`: every file reported `ok` (checksum verified), no download; `git status` shows `pipeline/source_manifest.csv` unchanged | OK |
| `SOURCE_PROFILES.md` covers every source | Sections 1-8 cover all downloaded sources plus the excluded one | OK |
| Extra check: raw files match the locked checksums | 23 / 23 files in `pipeline/source_manifest.csv` match their SHA-256 | OK |

Claude-review items (Stage 1 "Claude review (gate)"): licences confirmed (D23, D35), 200-sample Unihan `kVietnamese` cross-check done (`docs/STAGE1_REVIEW.md` section 2.2), shinjitai method chosen (D28), source priority set (D33). Non-blocking problem passed on: Vietnamese coverage ceiling (about 35% of HSK words), handled by the D36 search.

Fixes requested: none.

## Stage 2 — character table — PASS (attempt 1), 2026-11-04

| Done-when criterion | Evidence (rechecked on disk, not taken from the report) | Result |
|---|---|---|
| `chars` covers all 3,000 HSK characters; missing reported, not guessed | 3,000 rows; missing: jp 45, ja_on 49, vi 709 (ko 0, pinyin 0); `coverage_report.csv`, `no_jp_form.csv` present | OK |
| No duplicate `char_id` / `trad` key; collisions resolved by a decision | `char_id` and `key_char` unique; empty `trad` 0; `char_key_collisions.csv` = only 著 → 着 (L1), 著 (L4) (D37, C1) | OK |
| C2 one→many | counts reproduced by `tests/test_char_collisions.py` (83 / 89 / 88; 1,088 rows with simp≠trad all have `ko`) | OK |
| All text NFC | vi, ko, jp, pinyin checked NFC | OK |
| Test characters correct in every language | 學 学/学/がく/학/xué/học; 國 quốc; 茶 trà; 行 hành; 生 sinh; 樂 nhạc: all match their sources (see note 1) | OK |
| `rules_report.csv` exists | 7 rows; cells total 1,561 = rows of `rules_examples.csv` | OK |
| Tests pass; rebuild identical | `unittest discover` rerun: 16 tests OK (56 s), includes two rebuilds | OK |

**User-requested check: verified readings only.** All 1,561 rows behind `rules_report.csv` have `source_vi` in {`kaikki_aligned` 1,292, `unihan_hvsyl` 269}; `unihan_unverified` = 0 (456 such readings are excluded). 主 = chủ (`kaikki_aligned`); the Nôm reading chúa is in neither `vi` nor `vi_all`.

**`rules_report.csv` vs `config/rules.json`:** 1,554 of 1,561 (99.6%) follow the rules (ㄱ→c/ch 152/153; ㄴ→n 259/260; ㄹ→t 70/70; ㅁ→m 69/70; ㅂ→p 32/33; ㅇ→ng/nh 288/289; no patchim→open 684/686). The 7 off-pattern characters, each checked:

| char | ko / vi | Verdict |
|---|---|---|
| 伯 | 백 / bá (ㄱ→open) | real exception (explicit Kaikki alignment) |
| 幻 | 환 / ảo (ㄴ→open) | reading is in Kaikki; the usual Hán-Việt is huyễn. Keep, flag for loop 1 (accuracy) |
| 逼 | 핍 / bức (ㅂ→c) | real exception (Kaikki) |
| 承 | 승 / thừa (ㅇ→open) | real exception (Kaikki) |
| 刷 | 쇄 / loát (open→t) | real: the two languages follow different Middle Chinese readings |
| 揭 | 게 / yết (open→t) | real polyphone (Korean 게/걸) |
| 怎 | 즘 / chẩn (ㅁ→n) | **suspect**: `unihan_hvsyl`; expected chẩm. Passes only the weak syllable-attested test. Flag for loop 1 (accuracy) |

**Notes (non-blocking → HANDOFF Open problems):**
1. `chars.ko` primary = first Unihan `kHangul` (D32), and Unihan lists values alphabetically: 行 = 항 (`ko_all` 항;행), 茶 = 다 (다;차), 樂 = 낙. All are valid readings present in `ko_all`; `ko_final` is unaffected. Learner-visible Korean comes from libhangul word readings in Stage 3, so cards are unaffected. Stage 3 must align `word_chars` using the word-level reading and `ko_all`, not `chars.ko`.
2. `unihan_hvsyl` (300 characters) is a weaker check than `kaikki_aligned`: the Unihan syllable is an attested Hán-Việt syllable, not an explicit alignment. 怎 is the only suspect found in the rules table.

Fixes requested: none. Next: Codex, Stage 3.

## Stage 3 — word table — FAIL (attempt 1), 2026-11-04

Counts and keys are sound; the failures are in rule implementation. All numbers were measured on disk with independent scripts. The Korean recomputation is kept as `docs/review_scripts/stage3_ko_base_reference.py`.

| # | Check | Evidence | Result |
|---|---|---|---|
| 1 | One row per `(trad, pinyin)`; IDs | 11,028 HSK rows, 0 duplicates; `word_id` unique and equal to `id_map.csv` in all 12,229 rows; no non-NFC or sentinel text (the 3 `nan` hits are the real syllables nan / nan) | OK |
| 2 | Merges logged; `validate=` in the code | Counts within 2% of SCHEMA §1.8 (10,974 / 19 / 35; 1,669 `right_only`; HSK `ja` 5,732, `ko` 7,110, `vi` 3,882). **But `build_words.py` has one real merge with `validate=` (line 1171). The word merges are loops, and `merge_report.csv`'s `validate` column is literal text (lines 135-138, 607-608, 916-917); `both` is counted from non-empty values, not from `_merge`** | **FAIL** |
| 3 | Coverage | `ko` 64.47%, `ja` 51.98%, `vi` 35.20%, all four 3,114 | OK |
| 4 | `card_eligible` | Recomputed: 0 differences; 7,354 HSK, 8,555 total; no rows eligible on a built `jp` alone | OK |
| 5 | VI-only | 1,201 rows; bands 151 / 250 / 300 / 300 / 200 match D27 plus the seed; 0 single characters, 0 in HSK; 221 without pinyin. **`vi_only_report.csv`: 1,195 `selected=true` against 1,201 words (6 were converted to their traditional form: 佈告, 遊牧, 義母, 色慾, 昇平, 得誌); no `rank` or `level` columns (SCHEMA §1.7)** | **FAIL** (report only) |
| 6 | `word_chars` | Unique; 24,458 rows = sum of lengths; 0 unlinked; syllables rejoin to the word; `syl_aligned` recomputed with 0 differences. **41 `pinyin` / `count` rows are not count mismatches: "CC-CEDICT template did not resolve", including 4 single characters (誰, 熟, 血, 殼); D45's fallback was not implemented** | **FAIL** (small) |
| C1 / C2 | Collisions | `char_id`, `key_char` unique; only 著 → 着, 著; 0 ambiguous; 3,178 rows (+82 HSK, +96 VI-only). **10 grown rows have empty `simp` (陀, 簿, 赦...); 10 mismatches on grown rows, several from rare Unihan forms (餵 𫗭, 譁 𲂊, 鵰 𫛲, 託 讬)** | **FAIL** (D51 item 6) |
| 7 | D39 | `*_all` sets, `ja_on`, `pinyin` unchanged against Stage 2 (0 differences); finals consistent; test characters pass. **`ko_base` is not normalized and non-evidence words are counted; details below** | **FAIL** |
| 8 | `rules_report.csv` | 2,080 pairs, 0 unverified; large cells follow the rules; off-pattern cells small. 2 rows with a blank `source_vi` (麵, 鑑). Must be rebuilt after the check 7 fix | OK for now; recheck |
| 9 | Review lists | 136 / 154 / 12 rows (expected 124 / 170 / 13). Short list now 205 rows (ja 39 + 78, ko 46 + 30, vi 12). **Picks deferred to attempt 2:** the D43 counts use the faulty `ko_base`, so the lists will change, and the user should confirm once, on the final list | Deferred |
| 10 | Variant sample; single-character `ja` | 20 of 20 `libhangul_variant` words correct (seed 20261104); 坐下 좌하 is a known false match, so the rate is under 5%. **All 326 level 1-2 single-character `ja` values read: wrong forms and readings; details below** | **FAIL** |
| 11 | `ff_candidates.csv` | 2,944 rows, none in `words`, 手紙 and 大丈夫 present. `gloss_vi` on 1 of 626 `vi` rows (D51 item 5) | OK apart from the gloss |
| 12 | 30-word sample (seed 20261104, stratified by level, plus 3 VI-only) | Every value traced to its source: 30 of 30. One preferred reading is poor (相對 あいたい; on the review list). **Extra sample of 40 multi-character rule-B words: 39 plausible, 1 false (人為 nhân vị)** | OK |
| 13 | Tests; rebuild | 22 tests OK (652 s); two rebuilds identical; `git status` clean afterwards, so committed outputs reproduce | OK |
| | Test words | All 20 match the table (茶 다 pending the short list; 手紙 `vi` table entry corrected) | OK |

**Check 7, root causes.**
1. `korean_base` (`stage3_match.py:128-152`) tries the surface syllable first and returns it if it is in `ko_all`, so at position 1 유 stays 유 although D39 maps it to 류. D39's normalization never happens for characters that list both forms. Against an independent recomputation, 322 `word_chars` rows on 101 characters have the wrong `ko_base`.
2. `apply_d39` (`build_words.py:1055-1063`) counts all words, not D39's evidence words. So 편즙 (itself chosen by evidence) makes 輯 = 즙.
3. `ko_law_form_suspect` is hard-coded `False` (line 1076); 5 or more rows should be true (爐 노, 廊 낭, 虜 노, 魯 노, 碌 녹).

Effect: at least **49 wrong Korean primaries, 12 of them at levels 1-3**: 老 노 (로 15), 流 유 (류 29), 旅 여 (려 8), 連 연 (련 12), 領 영 (령 17), 律 율 (률 10), 列 열, 陸 육, 兩 양, 零 영, 冷 냉, 綠 녹, 勞 노. The learner sees these in the glyph and rule views. The Stage 3 tests missed them because they cover only 樂, 歷, 怒, 行, 茶, whose top counts did not change.

**Check 10, root causes.**
1. `word_forms` (`build_words.py:219`) passes the Korean variant graph to JMdict, for all word lengths. D42 has no variant forms. 31 single-character rows are affected, including the form shown on the card: 弄 瘧 (`gloss_ja_en` "ague"), 滾 菌 ("fungus"), 捉 杓 ("ladle"), 它 佗, 她 他, 聽 听 (ポンド in `ja_alt`), 穩 文, 拆 責, 蛋 蜑, 掉 棹.
2. `match_japanese_row` (line 276) looks up on'yomi by `key_form` or `trad`, not the linked row: 歲 とし, 腳 あし, 內 うち, 值 あたい, 戶 と, 鄉 さと (should be さい, きゃく, ない, ち, こ, きょう); 號 こう (`chars.ja_on` = ごう).

**Also found (Vietnamese, D51 items 3-4).** Rule B accepts homophones: 食物 thực vật and 實物 thực vật (植物), 不行 bất hạnh (不幸), 只是 chỉ thị (指示), 父女 phụ nữ (婦女), 路面 lộ diện (露面), 定為 định vị (定位), 視角 thị giác (視覺). 21 multi-character rule-B words have a `vi` that Kaikki attaches to another Han form, about half of them true errors; 食物 and 不行 are level 2. Rule A through `simp` or a variant on a single character: 麵 diện, 穩 văn.

**Fixes requested:** F1-F13 in `HANDOFF.md`. Attempt 2 reruns checks 2, 5, 6, 7, 8, 9, 10, 11, C1, C2 and 13, then the short list. A second failure stops and asks the user (Rule 11).

## Stage 3 — word table — attempt 2, 2026-11-05: checks pass, short list waiting for the user

Reran checks 2, 5, 6, 7, 8, 9, 10, 11, C1, C2 and 13 on commit `e18e7e0`. All numbers were measured with independent scripts on a snapshot of the committed outputs, not taken from Codex's note. The Korean recomputation reuses `docs/review_scripts/stage3_ko_base_reference.py`.

| # | Check | Evidence | Result |
|---|---|---|---|
| 2 | Merges | `merge_with_report` (`pipeline/common.py:160`) calls `DataFrame.merge` with `indicator=` and the `validate=` it records. Used for CC-CEDICT exact (`m:1`: 10,974 both / 54 left), fallback audit (`1:1`: 19 / 35), Kaikki outer (`m:1`: 1,714 both / 9,314 left / 1,669 right; left + both = 11,028), JMdict / libhangul / Vietnamese match tables (`1:1`, one row per word key with a value) and the Stage 2 rows (`one_to_one`, `many_to_one`). `merge_report.csv`: 37 rows, no empty `validate` | OK |
| 5 | VI-only | 1,201 words = 1,201 `selected=true`, same `word_id` set; `rank`, `level`, `trad`, `word_id` present; bands 151 / 250 / 300 / 300 / 200 in both `words` and the report; 0 single characters, 0 HSK forms; 越南 seeded (`việt nam`, 월남, えつなん). The six traditional-form conversions (佈告, 遊牧, 義母, 色慾, 昇平, 得誌) are now selected under their `trad` | OK |
| 6 | `word_chars` | 24,458 rows = sum of lengths; unique on `(word_id, position)`; 0 unlinked; Korean, Vietnamese and pinyin syllables rejoin to the word with 0 differences; 0 empty pinyin syllables. `alignment_mismatches.csv` 5 rows, each explained: 숫자, 찻간, 곤란 (`ko_exception`, D43), 行為 vi (`not_in_all`, rule A via 行爲), 鑑定 giám (`not_in_all`) | OK |
| C1 / C2 | Collisions | 3,178 rows (3,000 + 178); `char_id`, `key_char` unique; empty `trad` 0, empty `simp` 0; collisions only 著 → 着, 著; `char_ambiguous` 0. 14 grown rows' `simp` changed from attempt 1 (餵 喂, 託 托, 譁 哗, 鵰 雕, 陀/簿/赦/砲/疽/曚/檀/朕/悪/彷 filled). HSK-list rows: `simp`, `trad`, `jp`, `ja_on`, `pinyin`, `level` unchanged from Stage 2 (0 differences). `char_simp_mismatch.csv` = 反覆, 答覆, 彷彿 | OK |
| 7 | D39 | Independent recomputation: `ko_base` differs in 2 rows only (see note 1); recomputed primaries differ from the build in **0** characters. `*_all` sets equal to Stage 2 for all 3,000 HSK rows and to attempt 1 for the 178 grown rows (order changed for 77 `ko_all`, 5 `vi_all`; `ja_on_all`, `pinyin_all` untouched). Every primary is the first `*_all` value. Expected primaries all match (老 로, 流 류, 旅 려, 連/聯 련, 領 령, 律 률, 列 렬, 陸 륙, 輪 륜, 兩 량, 零 령, 冷 랭, 綠 록, 勞 로, 輯 집; 樂 락, 歷 력, 怒 노, 行 행, 年 년, 女 녀; 茶 다). `ko_law_form_suspect`: 13 rows incl. 爐, 廊, 虜, 魯, 碌. **`char_primary_changes.csv` scanned, all 84 rows** (79 ko, 5 vi): 31 changes with a top count of 1 are all dictionary base forms (藍 람, 陵 릉, 臘 랍 ...) or the standard reading (省 성, 貝 패, 滑 활, 豫 예, 若 약, 宅 택, 嫦 상, 賈 고). **One bad change: 寧 녕 → 령** (D39 maps 영 to the ㄹ form whenever it is in `ko_all`; 寧 is 녕); override proposed. The attempt-1 bad cases 丹 (단) and 液 (액) are now right | OK, 寧 on the short list |
| 8 | `rules_report.csv` | 2,031 pairs = `rules_examples.csv` rows; `source_vi`: `kaikki_aligned` 1,734, `unihan_hvsyl` 295, `kaikki_han` 2 (鑑 giám, 為 vi from 行爲), unverified 0, blank 0. 2,015 of 2,031 (99.2%) follow `config/rules.json`; no large off-pattern cell. 16 off-pattern pairs, each checked: real exceptions 伯, 逼, 承, 刷, 揭, 幻 (Stage 2), 不 부/bất (부 is the assimilated form), 復 부/phục, 刺 자/thích, 暴 폭/bạo, 咽 인/yết, 實 실/thực, 礮 포/bác (đại bác); suspect 怎 chẩn (Stage 2 note); **data errors 奔 hợp and 液 giá** (note 2) | OK |
| 9 | Review lists | 136 / 149 / 47 rows (expected about 124 / 170 / 13; the Vietnamese list grew by the 36 D51 `rule_b_conflict` rows). Short list: 76 Korean, 115 Japanese, 47 Vietnamese rows, plus 茶 and 寧. **Proposals in `docs/STAGE3_SHORTLIST.md`: 23 Korean, 14 Japanese, 19 Vietnamese word overrides, 2 character overrides, an optional group of 13 law-form characters.** Waiting for the user (D50 item 4) | **PENDING** |
| 10 | Japanese; variants | 1,586 single-character HSK words: `jmdict` 737, `kanjidic2_on` 269, `built_from_chars` 541, none 39. Fallback `ja` = linked `chars.ja_on` in 269 / 269. Every `jmdict` single-character `ja` is an on'yomi of the linked row except 〇 れい (D42 c). No single-character `jp` outside the word's own form or `chars.jp`. Levels 1-2: 400 rows, 12 changed from attempt 1, all as required (號 ごう, 歲 さい, 腳 きゃく; 她, 聽, 坐, 啊, 蛋, 掉, 份, 弄, 它 lose the variant form and `ja`). 國 こく, 電 でん, 海 かい, 手 しゅ with くに, いなずま, うみ, て in `ja_alt`. HSK `ja` 5,703. `libhangul_variant`: 290 words; new sample of 20 (seed 20261105) all correct (預約, 青少年, 教師, 清潔, 群眾 ...) | OK |
| 11 | `ff_candidates.csv` | 2,944 rows; 0 forms in `words`; 手紙 (thủ chỉ, gloss shown) and 大丈夫 present; `gloss_vi` on 614 of 616 rows with `vi` | OK |
| 13 | Tests; rebuild | `unittest discover`: **29 tests OK (418 s)**, including two full rebuilds; afterwards every file in `data/final/` and `pipeline/id_map.csv` matches the committed SHA-256 (the build reproduces commit `e18e7e0` exactly) | OK |
| | Test words | All 20 match the table: 茶 다 (short list), 行 háng `vi` empty and in `vi_ambiguous` (short list), 新聞 `vi` empty, 手紙 only in `ff_candidates`, 越南 `vi_freq` | OK |

**Notes (non-blocking, for loop 1 accuracy; added to HANDOFF "Open problems"):**
1. 朝著 조저 and 著落 저락 are linked to the 着 row (by `simp`, D37), whose `ko_all` is only 착, yet the D43 filter accepted 저. The filter appears to check the word's `trad` character (著), not the linked row's `key_char`. Two words; `ko_base` is empty, so D39 is unaffected. 朝著 조저 is also a false match ("towards" vs a court rank).
2. Rule-B and Kaikki data errors that D51 cannot catch: 液體 giá thể (a Kaikki headword for "substrate"; 液 has giá in `vi_all`), 奔 hợp (Kaikki char reading 奔 → hợp, count 1). Both reach `rules_examples.csv`; neither can reach the Stage 5 rule view, which needs the pair to equal the primaries (액/dịch, 분/bôn).
3. D39's literal position-1 mapping also gives 異常 이상 the base 리 (異 `ko_all` 이;리). The primary stays 이 (9 vs 7), so only `ko_base` and the rules pairs are affected. Same cause as 寧.
4. `pipeline/overrides.csv` supports only `table=words` and `table=chars`; D51 item 4 also allows confirming `ff_candidates` rule-B values. Three such values are correct (難民, 淡泊, 政治犯); proposal: leave them empty for Stage 4.

**Result so far:** every rerun check passes; F1-F13 are fixed. The gate is not recorded as PASS yet: check 9 requires the user to confirm the short list, after which Claude writes `overrides.csv`, rebuilds, reruns the tests and rechecks the changed rows.

### Stage 3 attempt 2 — completion after the user's confirmation (2026-11-05): **PASS**

| Item | Evidence | Result |
|---|---|---|
| Overrides | User confirmed the short list as proposed, group C3, plus 家 か and 月 げつ (D52). `pipeline/overrides.csv`: 59 `words` + 18 `chars` = 77 rows. All 77 applied (independent check: every value equals the built value). Previous value kept in `*_alt` for every word override | OK |
| Tie check (new) | The first rebuild flipped 4 primaries through D39 ties created by word overrides: 貝 배, 滑 골, 省 생, 更 갱. User confirmed `chars` overrides 貝 패, 滑 활, 省 성, 更 경; after the rebuild all four equal their pre-override values | OK |
| Characters | 20 rows changed against the attempt-2 build, all intended: 茶 차, 寧 녕, 13 C3 base forms, 台 대 (evidence from 台 대), 份 phần, 濕 thấp (`vi_final` m → p), 瓷 từ, 論 `ko_base_all` + 논 (from 의논). `*_all` sets: 0 changes in all four columns. `char_primary_changes.csv` 103 rows (18 `override`) | OK |
| Words | Only the 57 override words changed in content; the other changes are `freq_vi` dense ranks shifting because 19 more words have `vi` (D44). HSK `vi` 3,861 → 3,880; all four languages 3,094 → 3,111; `card_eligible` unchanged (7,354 HSK / 8,555 total). `rules_examples` 2,031 → 2,044 | OK |
| Test words | 茶 `ko` 차 (word and character); 行 háng `vi` hàng; all others unchanged | OK |
| Tests; rebuild | Full suite: the rebuild test passed (two runs identical); one assertion failed because two tests pinned 茶 = 다, the expected value before D50 (`tests/test_chars.py:84`, `tests/test_words.py:90`). Both are now 차, as D39 states for after the gate; 28 non-rebuild tests rerun OK, outputs byte-identical to the rebuilt files | OK |

Open items for loop 1 are in HANDOFF "Open problems". `char_primary_no_evidence.csv` still flags 12 law-form suspects because it reports the state before `chars` overrides; all 12 are overridden (listed in `char_primary_changes.csv` as `override`).

Stage 3 gate: **PASS**. Next: Claude, D36 Vietnamese source search.

## Stage 3 repeat gate after D53 — attempt 1, 2026-11-05: **FAIL**

Checked on commit `97780a0` (Codex, 7C integrated) against the Stage 3 PASS build `7827546`. All numbers were measured with independent scripts on a snapshot of the committed outputs; the comparisons are kept as `docs/review_scripts/stage3_repeat_gate_reference.py`.

| # | Check | Evidence | Result |
|---|---|---|---|
| 1 | Rows, IDs | 11,028 HSK + 1,201 VI-only = 12,229; 0 duplicate `(trad, pinyin)` or `word_id`; every `word_id` equals `id_map.csv` for its key (`trad\|pinyin` / `x\|trad`). `id_map`: all 15,407 baseline rows kept with the same IDs; 787 new rows (760 words from `w12230`, 27 chars from `c03179`); the 757 dropped VI-only IDs are not reused | OK |
| 2 | Merges | `merge_report.csv` 43 rows, no empty `validate`; new `words_kaikki_en` `1:1` with `indicator` (4,377 `both`, 7,852 `left_only`), added to SCHEMA §1.8 | OK |
| 3 / R1 | Coverage (HSK) | `ja` 5,703, `ko` 7,114 (+1: 寺 사, a single-character tie broken by new VI-only evidence), pinyin 11,028, `vi` 4,239 (+359; expected about 4,236), all four 3,362 (expected about 3,360) | OK |
| 4 | `card_eligible` | recomputed from the columns: 0 differences; 7,354 HSK / 8,555 total, unchanged | OK |
| R2 | A2 fills only empty values | 360 HSK words gained `vi`, all `kaikki_en_han`. Two HSK values that were non-empty at `7827546` changed, neither by A2 overwriting A/B: 調 diào `điều` → `điệu` (the D44 count for its rule-B candidates tied once VI-only evidence changed, the word fell to `vi_ambiguous`, then A2 filled it) and 馴 xùn `tuần` → empty (`several_candidates`; its only evidence word 馴鹿 left the VI-only list). Both go to the D55 short list. **But 143 A2 values are not 7C's spelling, and 104 of them (32 HSK) use a spelling no source has** (see below) | **FAIL** (spelling) |
| R3 | `vi_ambiguous.csv` | 51 rows: 32 `rule_b_conflict`, 8 `several_candidates`, 8 `obsolete_only` (the six expected plus source-backed 聘 sính, 隧道 tụy đạo), 3 `override_replaced` (占, 將, 更: A2 filled the empty value first, then the confirmed override replaced it; nothing enters `vi_alt`). Rows that A2 filled have left: 容易 dung dị, 激動 khích động, 長城, 風土 (ff) | OK |
| R4 | VI-only | `vi_only_report.csv` has `source_vi`; 1,201 selected = the VI-only `word_id` set; bands 151/250/300/300/200 + 越南; 0 single characters; 0 HSK `trad`/`simp`. **Churn: 444 kept, 757 added, 757 dropped.** All 757 dropped words are not `ja_common` (levels 5: 259, 6: 299, 7: 199; none at 3-4). Added: 562 `ja_common`, levels 3-7. The pool now has 904 `ja_common` candidates (342 before), so D46's rank fills the cap with them, as D53 item 4 expected (D56 item 5). Seeded samples (seed 55): added 戶籍 hộ tịch, 生態學, 不可 bất khả, 寄生蟲, 女王 nữ vương, 暗礁 ám tiêu, 收納, 上海, 明君, 結界; dropped 農學, 遺表, 鑛產, 假借, 苦瓜, 情狀, 屠宰, 幽暗, 石膏, 迷宮, 勇猛, 交承 giao thừa (a false composition). One new variant repeat the D46 check cannot see: VI-only 複合 phức hợp vs HSK 復合 (D55 list). **The three overridden VI-only words are pinned into the cap by a rule no decision states** (2 of them, 行伍 and 寂寥, only through the pin) | OK; pin not accepted (D56 item 4) |
| R5 | D52 tie rule | `*_all` sets: 0 differences in all four columns; `ja_on`, `pinyin`, HSK-list `simp`/`trad`/`jp`/`level`: 0 differences. **Korean primaries changed: 鹿 녹, 磊 뇌, 隸 예, 蘭 난, 丹 란, 易 역**, all because evidence words left the VI-only list (no evidence → Unihan's alphabetical order; 易 3:3 tie). User decisions: 鹿 록, 磊 뢰, 隸 례, 蘭 란, 丹 단, 易 이 (D56 item 1). **Vietnamese: 沒 một, 盆 bồn, 訪 phỏng, 武 vũ**, each the standard Hán-Việt reading from new evidence words; accepted. Ties created without a primary change (Vietnamese 當, 福, 縱, 易, 液; Korean 寧 and 茶, both overridden) are listed in HANDOFF for loop 1. `ko_law_form_suspect` rows not overridden: exactly 鹿, 磊, 蘭. 27 new grown characters checked (絶, 讎, 羣, 裏 리, 薔 장, 躇 저 ...): no law-form or wrong primary | OK after the six overrides |
| R6 | Overrides | all 77 applied at `97780a0` (independent check) | OK |
| R7 | Test words | all 20 unchanged against `7827546` (新聞 `vi` empty, `obsolete_only`; 茶 차; 行 háng hàng; 越南 `vi_freq`) | OK |
| 6 | `word_chars` | 24,496 rows = sum of word lengths; unique; 0 unlinked. `alignment_mismatches.csv` 301: 3 `ko_exception`, 298 Vietnamese `not_in_all` (296 from A2 words). About 100 of those come from the respelling below | OK (recheck after G1) |
| 7 | D39 | every primary is the first `*_all` value; test characters 樂 락, 歷 력, 行 행, 茶 차 | OK |
| 8 | `rules_report.csv` | 2,232 pairs (`kaikki_en_han` 824, `kaikki_han` 823, `kaikki_aligned` 317, `unihan_hvsyl` 268), 0 unverified; 21 off-pattern pairs, the attempt-2 list plus 著 trước/tác, 不 bất, 實 thực, 乘 thừa, 剩 thừa (real). **About 50 pairs use invented spellings** (兒 nhy, 二 nhỵ, 知 try, 皮 bỳ, 支 chy) | recheck after G1 |
| 9 | Review lists | `ko_multi_candidates` 139, `ja_multi_candidates` 157, `ko_unresolved` 53, `vi_ambiguous` 51 | OK |
| 10 | Japanese | HSK `ja`, `jp`, `source_ja` unchanged against `7827546` (0 differences) | OK |
| 11 | `ff_candidates.csv` | 2,944 rows, same forms as before; A2 filled 121 empty `vi`/`gloss_vi`. **440 rows are now also VI-only words** (亞熱帶, 惡人, 暗礁, 偉人 ...), against D47 ("not in `words`"). Cause: the code keeps the old membership by excluding the pre-D53 ("legacy") VI-only selection, following D53 item 5's "membership unchanged" literally. Stage 4 would add these forms a second time as `ff_only` | **FAIL** |
| 12 / R8 | 30 words (seed 20261106; 14 `kaikki_en_han`, 6 HSK + 6 VI-only drawn first, the rest 3 per level) | every Japanese, Korean and pinyin value traced to JMdict, hanja.txt (incl. variant forms 汚名, 早晩) and CC-CEDICT. Vietnamese: 10 of 14 A2 values equal the 7C entry (過渡 quá độ, 好客 hiếu khách, 預感 dự cảm, 全程, 雜貨 tạp hóa, 下部, 盟主, 執筆 chấp bút, 總選舉 tổng tuyển cử, 污名 ô danh); 4 are respelled: 王妃 `vương phy` (7C phi), 大學士 `đại học sỹ` (sĩ), 分離 `phân ly` (li), 美金 `mỹ kim` (mĩ). The other 16 words match their sources | **FAIL** (same cause as R2) |
| 13 | Tests; rebuild | `unittest discover`: **36 tests OK (754 s)**, including two full rebuilds; afterwards every file in `data/final/`, `ff_candidates.csv` and `id_map.csv` matched the committed SHA-256 | OK |
| R9 | D55 support | `config/vi_sources.json` `kaikki_en_char_readings: false`; 0 `kaikki_en_char` source tags; tests cover cleared and replaced `vi` overrides; switched-on numbers in Codex's note | OK |
| C1 / C2 | Collisions | 3,138 chars (3,178 − 67 dropped grown rows + 27 new); `char_id`, `key_char` unique; 0 empty `trad`/`simp`; collisions only 著 → 着, 著; `char_ambiguous` 0; every word character has a row and every grown row is used; `char_simp_mismatch.csv` = 反覆, 答覆 (彷彿 left with its VI-only word) | OK |

**The respelling (R2, R8, checks 6, 8).** `canonicalize_iy` (`pipeline/stage3_match.py:250`, called at `pipeline/build_words.py:503`) writes y for every A2 syllable ending in consonant + i: ki→ky 21, vi→vy 17, chi→chy 16, li→ly 14, si→sy 12, tri→try 11, khi→khy 11, nghi→nghy 10, thi→thy 9, nhi→nhy 8, di→dy 5, ti→ty 5, bi→by 4, phi→phy 4, mi→my 2, hi→hy 1. Learner-visible HSK cases: 皮膚 `bỳ phu`, 移 `dy`, 胎兒 `thai nhy`, 議程 `nghỵ trình`, 無疑 `vô nghy`, 遺址 `dy chỷ`. The staged sources show the convention: Kaikki-vi writes y only after h, k, l, m, t and never after other initials; 7C writes i everywhere. My D53 test example (`自己 = tự kỷ`; 7C has `tự kỉ`) implied a respelling rule without stating its limits; D56 item 2 states it. The `ff_candidates.csv` path does not respell, so the same form can differ (偉人: ff `vĩ nhân`, VI-only `vỹ nhân`).

**Claude actions at this gate:** user decisions recorded (易 asked; the others given by the user); `pipeline/overrides.csv` 77 → 81 rows (six `chars` overrides added; `x|行伍` and `x|寂寥` removed, D56 item 4); `run_all.py` rerun with the current code (results below); D56; SCHEMA §1.8 row for `words_kaikki_en`; HANDOFF fix list G1-G3 for Codex.

**Rebuild after the override change (current code, so G1-G3 are still open):** against `97780a0`, `chars` changed only in the six overridden primaries (with their `ko_all` / `ko_base_all` order, `ko_final` of 易 ㄱ → open) and 寥 `ko_base_all` (요 left with 寂寥 적요); **no other primary changed, so the removal created no tie flip**. Words: 行伍 (`w11990`) and 寂寥 (`w12212`) left the VI-only list, IDs reserved; 槍法 thương pháp (`w12987`) and 法家 pháp gia (`w12988`) entered with new IDs. All 81 overrides apply. HSK coverage and `card_eligible` unchanged (`vi` 4,239, all four 3,362; 7,354 / 8,555). `char_primary_changes` 101 → 107 (6 `override` rows), `ko_multi_candidates` 139 → 137, `rules_examples` 2,232 → 2,233; other reports unchanged. `tests/test_stage3_d53.py` expected 77 override rows and now expects 81; the 35 non-rebuild tests pass; a second `run_all.py` gave byte-identical outputs and `id_map.csv`.

**Fixes requested:** G1 (A2 spelling, D56 item 2), G2 (`ff_candidates.csv` membership, D56 item 3), G3 (remove the VI-only pin, D56 item 4); details and expected values in `HANDOFF.md`. Attempt 2 rechecks G1-G3, R2, R4, R5, R6, checks 6, 8, 11 and 13. A second failure of this repeat gate stops for the user (Rule 11).

## Stage 3 repeat gate after D53 — attempt 2, 2026-11-06: **PASS**

Checked on commit `4919d5b` (Codex, D56 G1-G3) against the attempt-1 build `0d581fa` and the Stage 3 PASS build `7827546`. Every number was measured independently from the committed files (read from git), not taken from Codex's note. Script: `docs/review_scripts/stage3_repeat_gate_attempt2_reference.py`.

| # | Check | Evidence | Result |
|---|---|---|---|
| G1 | A2 spelling (D56 item 2) | Code: `canonicalize_iy` is replaced by `canonicalize_a2_spelling` (`pipeline/stage3_match.py:250`, regex `[hklmt]i` on the toneless syllable), called on every A2 path: HSK words (`build_words.py:503`), VI-only candidates before `freq_score` (`:655`), `ff_candidates` (via `kaikki_en_candidates`, `:1710`). Data: **all 1,122 A2 values (361 HSK) equal an independent re-implementation of D56 applied to the 7C value** (1,116 under `trad`/`simp`, 6 through D43 variant forms: 玻璃←玻瓈, 報仇←報讎, 看台←看臺, 玫瑰←玟瑰, 喧嘩←喧譁, 讚嘆←讚歎); 0 mismatches. 49 A2 words carry a D56 y (kỳ, lý, mỹ, kỷ, tỷ, hy, tỳ), matching Codex's count. Consonant + y outside h/k/l/m/t: **0** in `words.vi`, 0 in `ff_candidates.vi`. h/k/l/m/t + i remains only in rule A/B values (24 words, 1 ff row: 科学技術 khoa học kĩ thuật, a Kaikki-vi headword), as D56 allows. Named tests: 皮膚 bì phu, 移 di, 支給 chi cấp, 王妃 vương phi, 胎兒 thai nhi, 議程 nghị trình, 自己 tự kỷ, 分離 phân ly, 美金 mỹ kim, 禁忌 cấm kỵ. Against `0d581fa` exactly 104 words changed `vi` (32 HSK), all A2 → A2 (持續 trỳ tục → trì tục, 皮 bỳ → bì, 而 nhy → nhi ...) | OK |
| G2 | `ff_candidates.csv` (D56 item 3) | 2,504 rows = 2,944 − 440; 0 added; overlap with `words` `trad`/`simp`/`jp`: 0 by `form`, 0 by `trad`, 0 by `simp`; all 440 removed rows are forms in `words`; `vi` unchanged on every kept row; 手紙, 大丈夫 present. The six dropped VI-only forms (行法, 解法, 無才, 拳法, 槍法, 法家) did not enter: none is a JMdict-common or frequent-hanja form that passes D47 | OK (check 11) |
| G3 | No pinning (D56 item 4) | `pinned_keys` and the legacy selection are deleted (`normal = unique_ranked.head(1200)`). `tests/test_rebuild.py` builds once without `overrides.csv` and asserts the same VI-only `word_id` set; I reran it (below) | OK |
| R4 | VI-only | 1,201 = 1,201 `selected=true`, same set; bands 151/250/300/300/200 + 越南; 0 single characters; 0 HSK `trad`/`simp` repeats. Against `0d581fa`: **6 added** (病理學 w12990, 奇功 w12991, 神祇 w12992, 京畿 w12993, 經期 w12994, 奇才 w12995, all level 7, A2), **6 dropped** (行法 w11468, 解法 w11469, 無才 w12985, 拳法 w12986, 槍法 w12987, 法家 w12988; IDs kept in `id_map.csv`, unused). The added words are the y-spelled A2 words whose corrected `freq_score` rose (kỳ is a frequent syllable). `id_map.csv`: 16,194 rows kept with identical IDs, 8 new (6 words, 祇 c03206, 畿 c03207); 0 reused | OK |
| R2 | A2 fills only empty values | Against `7827546`: the only HSK values that were non-empty and now differ are still 調 diào (điều → điệu) and 馴 xùn (tuần → empty), both already on the D55 list. HSK coverage unchanged: `ja` 5,703, `ko` 7,114, pinyin 11,028, `vi` 4,239, all four 3,362; `card_eligible` 7,354 HSK / 8,555 total | OK |
| R5 | D52 tie rule | Against `0d581fa`: **0 changes** in `ko`, `vi`, `ko_final`, `vi_final`, `ja_on`, `pinyin`, `simp`, `jp` and in the sets `ko_all`, `vi_all`, `ja_on_all`, `pinyin_all`, `ko_base_all` (3,138 common rows). New rows 祇 (기; 기;지) and 畿 (기), `vi` empty. `char_primary_changes.csv` 107 → 107, one tuple changed (行 ko 항→행, evidence 50 → 49). Evidence recount: 9 Vietnamese characters gain their first evidence because respelled syllables now match `vi_all` (皮 bì 2, 仕 sĩ, 嗜 thị, 妃 phi, 旨 chỉ, 氏 thị, 癡 si, 耳 nhĩ, 違 vi; all equal the primary); **no tie created or broken** | OK |
| R6 | Overrides | 81 rows (56 `words`, 25 `chars`): every value equals the output value | OK |
| 6 | `word_chars`, alignment | 24,497 rows; `alignment_mismatches.csv` 203 = 200 Vietnamese `not_in_all` + 3 `ko_exception` (298 → 200 after G1, as expected) | OK |
| 8 | `rules_examples.csv` | 2,190 rows (`kaikki_en_han` 824, `kaikki_han` 789, `kaikki_aligned` 312, `unihan_hvsyl` 265); 0 invented spellings (兒 nhy, 二 nhỵ, 知 try, 皮 bỳ gone) | OK |
| R8 | Attempt-1 sample words | The four respelled values of the seed-20261106 sample now follow D56: 王妃 vương phi, 大學士 đại học sĩ (7C sĩ), 分離 phân ly, 美金 mỹ kim | OK |
| 13 | Tests; rebuild | `unittest discover`: **38 tests OK (604 s)**, including the three-build rebuild test (with, without, with overrides). Afterwards `git status` shows no change in `data/`, `ff_candidates.csv` or `id_map.csv`: the build reproduces commit `4919d5b` byte for byte | OK |

**Non-blocking, for D55 / loop 1:** (1) `vi_alt` keeps tied rule-B candidates when `vi` is empty or later filled by A2: 馴 xùn (`vi` empty, `vi_alt` tuần;thuần) and 調 diào (`vi` điệu, `vi_alt` điều;điệu). `judge()` accepts `vi_alt`, so 調 diào also accepts điều (the tiáo reading). Cause: `build_words.py:1146` writes all candidates to `vi_alt` when the D44 count ties. (2) D56 writes 自卑 as `tự ty` (7C tự ti); both spellings are in use, as with công ty.

Stage 3 repeat gate: **PASS**. Next (same session, D55): Vietnamese finalization short list, `docs/VI_SHORTLIST.md`.

## D55 Vietnamese finalization applied (D57), 2026-11-06

User answer: all of `docs/VI_SHORTLIST.md` as proposed, Q1 a, Q2 yes, Q3 a, plus 岳父 nhạc phụ / 岳母 nhạc mẫu. Script: `docs/review_scripts/d55_apply_check.py` (compares with `4919d5b` and with the uncommitted switch-on-only build, so the effect of the overrides is separated from the effect of the switch).

| Item | Evidence | Result |
|---|---|---|
| Overrides | 81 → 121 rows (11 replacements, 29 clears); every row equals the output value; the 29 cleared words have empty `vi` and empty `vi_alt` and are listed `override_cleared` | OK |
| D52 tie rule | Against the switch-on-only build: **one character primary changed, 馴 tuần → thuần** (the 馴 word override is its only evidence word; thuần is the standard reading and the user's word pick). Ties: 福 phúc 2 / phước 2 → 3 / 1 (primary phúc unchanged, tie removed). 拄, 拖, 爺, 薪, 酬, 飼 lose their only evidence word, primaries unchanged. No other primary, `*_all` set, `ko` or `ja` value changed | OK |
| Characters (switch, against `4919d5b`) | 0 `ko`, `ja_on`, `pinyin`, `ko_all`, `ko_base_all` changes; `vi` primary: 36 new readings, 棟 chống → đống, 馴 tuần → thuần; `vi_final` 16; HSK-list verified readings 1,835 → 1,913 (`kaikki_en_char` 130) | OK |
| Words (against `4919d5b`) | 63 `vi` changes = 27 new rule-B values from the switch, 剩 thừa → thặng, 9 replacements, 2 obsolete-only filled, 24 clears (E1-E5 were empty at `4919d5b`); 0 `ko`, `ja`, `card_eligible` changes. HSK `vi` 4,239 → **4,245**, all four 3,362 → **3,367**; `card_eligible` 7,354 / 8,555; words with `vi` 5,446 | OK |
| Reports | `vi_ambiguous` 88 (32 `rule_b_conflict`, 29 `override_cleared`, 11 `override_replaced`, 8 `several_candidates`, 8 `obsolete_only`); `alignment_mismatches` 195; `rules_examples` 2,243; `char_primary_changes` 107; `char_primary_no_evidence` 1,782; `ff_candidates` 2,504 | OK |
| Tests; rebuild | Full suite: the three-build rebuild test passed (identical with, without and with overrides) and every file in `data/final/`, `ff_candidates.csv` and `id_map.csv` hashed identical before and after; one stale assertion failed (`tests/test_chars.py` counted only the Stage 2 verified tags, 1,783 < 1,800) and now counts `kaikki_en_char` (D55 b) with the range 1,880-1,950. `tests/test_stage3_d53.py`: 121 overrides, 岳父/岳母 filled, switch on, new test for the 29 clears. All 38 non-rebuild tests rerun OK | OK |

**The word list is frozen** (D46, D55, D57).

## Note: `chars` 3,138 → 3,140 (user question, 2026-11-06)

The two rows were added at commit `4919d5b` (Codex, D56 fixes G1-G3), not by D57: `chars.csv` has 3,138 rows at `97780a0` and `0d581fa`, 3,140 at `4919d5b`, `95fa8fd` and `8f7926b` (D57 changed no `char_id`). Checked with `git show <commit>:data/final/chars.csv`.

| char_id | Character | Readings | Word that needs it |
|---|---|---|---|
| `c03206` | 祇 | ko 기 (`ko_all` 기;지), pinyin qí, ja ぎ, `vi` empty | 神祇 `w12992` thần kỳ (VI-only, level 7) |
| `c03207` | 畿 | ko 기, pinyin jī, ja き, `vi` empty | 京畿 `w12993` kinh kỳ (VI-only, level 7) |

**Why:** D56 item 2 (G1) made Codex apply the A2 spelling function **before** `freq_score` is computed. 7C writes these words with `kì` (thần kì, kinh kì); scored in that spelling they had no `freq_score` at `0d581fa` (empty in that commit's `vi_only_report.csv`), so they could not be selected (D46 requires a score). After G1 they are spelled `kỳ` (h/k/l/m/t + i rule), get a score (9,550 and 9,177) and rank inside the 1,200 cap (1,145 and 1,166), replacing lower-ranked words. Six words entered this way (病理學, 奇功, 神祇, 京畿, 經期, 奇才) and six left (行法, 解法, 無才, 拳法, 槍法, 法家; IDs kept unused). Only 神祇 and 京畿 use a character no other word uses, so `chars` grows by exactly these two rows (D38 / D40 step 5: a row for every character used in `words`); no row was removed because every character of the dropped words is still used elsewhere. Already recorded at the attempt-2 gate (R4, R5 above). Both rows have empty `vi`: `kỳ` is not in their (empty) `vi_all`, so both words are listed `not_in_all` in `alignment_mismatches.csv` (D45), as expected.

## Stage 4b re-check (Argon re-pilot, before the full run), 2026-11-06: **PASS**, one fix before task 4

Pilot review, not the PROMPT Stage 4 gate (that is Claude 4d, after the full run). Input: `docs/STAGE4B_FIX_REPORT.md`, commit `f03010b`, `content/generated/pilot_v2/`.

| Item | Evidence | Result |
|---|---|---|
| Frozen data | `git diff HEAD -- data` empty; `pipeline/id_map.csv` working-tree diff empty with `--ignore-cr-at-eol` (line endings only); `stage3_match.py` change is an import fallback only | OK |
| Tests | 63 non-rebuild tests rerun by Claude with `unittest`: all OK (incl. resume, UTC guard, timeout, total-token billing, credential scan, schema order, D60 validators) | OK |
| D60 settings | every pilot_v2 log: `gemini-4-argon`, `global`, temperature 0.3, 600 s timeout, prompt and input SHA-256; task-1 input SHA equals the first pilot (`e0d78cd4…`); 5/5 requests valid on attempt 1 | OK |
| User items 9-11 | code read (`runner.py`) + tests; recorded as **D61** | OK |
| Cost | cost log migration kept all 15 earlier rows ($0.69781975); total spent $0.94261375 | OK |
| Task 1 | 國, 茶 `same_word`; 樂, 試, 塗 (and 行) `unsure` + low, Vietnamese meaning kept; 自己 `same_word` with "autistic" meaning, `meanings_differ`; 平價 = 評價, 團圓 = 團員, 傷口 = 商口, 自制 = 自製 `different_word`; ko_rare 6 (小姐, 老公, 勉強, 精英, 擋, 回來). **One regression:** 財源 tài nguyên now `different_word` "= 資源", but 資源 reads tư nguyên, so the claim is impossible (v1 Argon had `same_word`, correct). 1 wrong of 5 flags; every non-`same_word` flag is reviewed at 4d anyway | OK, note for 4d |
| Task 2 | `ja` in no `false_friend` (勉強 [zh, vi], 大丈夫 [ko, zh, vi], 手紙 [zh, vi], 新聞 [zh]); 自己 [vi]; 大丈夫 ko 대장부 trap is correct (common Korean word) | OK |
| Task 3 | 12 passages, every translation complete; minor: 「在我们国」 is unnatural Chinese (我们国家), 下车 rendered 下りて | OK, 4d sample |
| Task 4 | 243 items; i/y and `unihan_unverified` differences gone. **New finding:** 「異性」では「리」と読む — 異性 is 이성. In the full task-4 input 9 Korean differences have a `reading_here` (`ko_base`) that is not the syllable written in `ko` (異 ×6, 諾言, 鬧鐘, 寧靜): D39 base-mapping artefact (Stage 3 gate attempt 2 note 3). The validator cannot catch it (the wrong syllable is in the input) | **Fix before task 4: D62 item 6 (Codex)** |

**For Claude 4d (method):** for every `different_word`, a script checks that the characters named in `vi_check_reason` can be read as the `vi` value from `chars.vi_all` (catches 財源 → 資源 tư nguyên).

Re-check: **PASS**. The full run may start after Codex Stage 4c-prep (D62: launcher, `--status`, retry wait, lock, task-4 Korean filter). Run plan: D62; user steps: `docs/VERTEX_SETUP.md` part E2.

## Stage 4 gate part 1 (task 1), 2026-11-07: **PASS**, all 86 batches accepted; 16 corrections before tasks 2-4

PROMPT Stage 4 review for task 1 (D62 item 2). Full evidence: `docs/STAGE4D_TASK1_REVIEW.md`; reference script `docs/review_scripts/stage4d_task1_reference.py`.

| Item | Evidence | Result |
|---|---|---|
| Done-when (task 1) | 8,555 / 8,555 `card_eligible` words, unique `word_id`; 86/86 logs valid; Claude's validator rerun 0 failures; inputs byte-identical to a fresh build; one prompt SHA, Argon `global` 0.3 | OK |
| Frozen data | no diff in `data/`, `config/` (before D63's new file), `overrides.csv`; `id_map.csv` line endings only | OK |
| Cost | ledger $14.37353775 (task 1 $13.43 incl. one failed validation attempt); 6 transport failures logged at $0 (D61 gap, worst case about $1) | OK |
| Codex fix `c2caac3` | `count_tokens` inside the counted retry loop; `Stage4Error` still fatal; failed log + continue; `python -u` | OK |
| Token drop (user note 1) | bimodal 0.381 vs 0.564 output tokens per stored character at equal content size: response formatting only; about $3.1 of padding | OK, no action |
| b083 (user note 2) | 100 VI-only `kaikki_en_han` words; gloss is the Han entry's own gloss; 15 sampled agree | OK |
| Fixed items | 20 test words + 自己, 財源, 容易, 小姐, 老公: 0 errors (財源 regression gone) | OK |
| Random 50 (seed 20261106) | 0 errors | OK |
| All `different_word` (46) | 12 wrong (same word), 4 right for the gloss but `vi` also real; ≤ 2 per batch | corrected by D63 overlay |
| `unsure` (9 multi + 40 single), `ko_rare` (60 of 930), other low (2), `meanings_differ` (25) | 0 errors | OK |

**PASS.** Batches stay in `content/generated/task1/` until part 2. Before sitting 2: Codex applies D63 (`config/task1_review.csv` overlay in task 2-4 builders; task-3 `ko_rare` rule).

## Stage 4 gate part 2 (tasks 2, 3, 4), 2026-11-07: **PASS for tasks 2 and 4 (with overlays) and task-3 Chinese; task-3 Vietnamese b008-b014 REJECTED**

PROMPT Stage 4 review for tasks 2-4 (D62 item 2). Full evidence: `docs/STAGE4D_PART2_REVIEW.md`; reference script `docs/review_scripts/stage4d_part2_reference.py`. Decision: **D64**.

| Item | Evidence | Result |
|---|---|---|
| Done-when | task 2: 3,937 items = every `meanings_differ` word, 自己, the 16 D63 words, all 2,504 `ff_candidates` rows; task 3: 6 passages in each of 14 cells, all tokens resolve; task 4: 212 notes ≤ 80 characters; validator rerun 0 failures; inputs byte-identical to a fresh build; no reading field in any output | OK |
| Run | 98/98 batches first attempt; one prompt SHA per task; Argon `global` 0.3; ledger $21.87953175 (sitting 2 $7.51), room $78.12 | OK |
| Frozen data | no diff in `data/`, `config/` (before this gate's new files), `overrides.csv`; `id_map.csv` line endings only | OK |
| User Q1: task 4 234 → 212 | 22 dropped = Vietnamese-only differences without a `same_word` check: 13 non-`same_word` words + 9 words with no task-1 result (not `card_eligible`; their notes could never be shown); 2 of the 16 D63 words have task-4 differences, both kept | OK |
| User Q2: task-2 output tokens | three fixed tokens-per-character levels at equal stored content: response layout only; about $2.05 of padding | OK, no action |
| User Q3: D63 words in task 2 | 16/16 Vietnamese meaning + judgment; `gloss_vi` withheld for the 4 `blank` rows; 0 errors | OK |
| Task 2 review | fixed items, 50 random, all 9 low, all 68 ff Vietnamese traps, all 64 Korean traps, 25 word Vietnamese traps: 31 errors / 3,937 (25 ff Vietnamese homophones or place names + 3 non-trap place-name meanings, 6 Korean homophones; 手紙's vi trap included) | **ACCEPT** 79; Korean → `config/task2_review.csv`; Vietnamese → step-6 group B |
| Task 3 review | all 84 passages: zh natural; vi about 1 in 5 forces literary/archaic words, one wrong word (bên ngoại) | zh **ACCEPT** b001-b007; vi **REJECT** b008-b014 → `task3_v3.md` |
| Task 4 review | 50 random: 0 model errors; script: 5 notes quote a Korean example whose written syllable differs (效率 효율, 戀愛 연애), builder-caused | **ACCEPT** 5; → `config/task4_review.csv` |

Next: Codex 4c-prep3 (task-3 prompt per language), user reruns task 3 (Vietnamese cells) and answers `docs/VI_CLEAR_SHORTLIST.md`, then Claude re-checks task 3 and applies step 6.

## Stage 4 gate part 3 (task-3 Vietnamese rerun; step 6), 2026-11-07: **PASS**, task 3 accepted with an overlay; all task 1-4 content accepted

Evidence: `docs/STAGE4D_PART3_REVIEW.md`; scripts `docs/review_scripts/stage4d_part3_reference.py`, `stage4d_part3_step6.py`. Decisions: **D65**, **D66**.

| Item | Evidence | Result |
|---|---|---|
| Task-3 rerun integrity | validator rerun 14/14 OK; inputs byte-identical to a fresh build; vi b008-b014 prompt SHA = v3 text, zh b001-b007 = v2; Argon `global` 0.3, thinking 0, first attempt; ledger $22.24585975, room $77.75 | OK |
| Task-3 Vietnamese, all 42 passages | forced archaic class gone; 6 one-off slips (Hangul in one translation; học sinh for university students; nghiêm cách; điều độ misused; khoa ngoại khoa; có tự giác) | **ACCEPT** b008-b014 with `config/task3_review.csv` (drop 4, trim 2); each cell ≥ 5 passages; every resulting passage passes `validate_task3` |
| Step 6 (user-confirmed) | 37 `vi` overrides (158 rows, all apply), 28 `clear_vi` rows; rebuild vs HEAD: only those 37 `vi` changed, `ko`/`ja`/chars unchanged; D52 ties 15 → 14, no new tie (液 giá/dịch gone) | OK |
| Step-6 consequences | `card_eligible` 8,555 → 8,554 (季女); task-4 builder 234 → 228 items before the D59 filter (6 `different_word` words already outside the 212 notes); HSK `vi` 4,211, all four 3,345 | accepted (D65 item 2); 4 test constants updated |
| Tests | `unittest discover`: 79 tests incl. the three-build rebuild test, which passed; afterwards every `data/final/` file equals the first rebuild (SHA-256). Non-rebuild rerun after the constant updates: 78 tests, **1 failure kept on purpose**: 平價 keeps `vi_alt` *bằng giá* after its `vi` clear (`test_d55_cleared_values_stay_out_of_vi_alt`); build fix → Codex 4c-prep4 item 0 | OK with one known gap |
| Accepted content | 86 + 79 + 14 + 5 batches (output, log, input) moved to `content/accepted/taskN/` | OK |
| Korean finding (user) | five examples are task-1 card words; `ko_rare` review-only; sample: task 1 misses about 10-14%, `ff_candidates` about 28% | → task 5 (D66) before 4e |

Next: Codex 4c-prep4 (vi_alt fix, accepted layout, task 5), User `-Tasks 5`, Claude gate part 4, Codex 4e.

## Stage 4 gate part 4 (task 5, usage check), 2026-11-07: **PASS for 103 of 104 batches** (with an overlay); b055 to rerun; user sample open

Evidence: `docs/STAGE4D_PART4_REVIEW.md`; scripts `docs/review_scripts/stage4d_part4_reference.py`, `stage4d_part4_effects.py`; user sample `docs/TASK5_USER_SAMPLE.md`. Decision: **D68**.

| Item | Evidence | Result |
|---|---|---|
| Run integrity | `--status` 103/104 validated, b055 failed; 104 inputs byte-identical to a fresh build; 103 outputs re-validated; 31 reason-script failures + 6 transport retries; ledger $35.42644775 (task 5 $13.18), room $64.57 | OK; b055 → D68 item 1 (reason rule = warning for task 5, rerun b055 only) |
| Every HSK level 1-3 flag (user item 2) | 335 read (ko 239, ja 96): 6 clear false positives, 3 class corrections, 8 borderline to the user | corrected in `config/task5_review.csv` |
| D66 item 7 samples | ko rare/task-1 high 50 (2 FP), ko used/task-1 `ko_rare` all 15 (9 FN), ff rows rare 50 (1 FP), ko used 50 (0), ja rare 50 (1 FP), ja used 40 (0), ja `wrong_meaning` 2 (1), vi 60 (0 blocking), `unsure` 1 (奔 hợp, known data error) | clear FP 11 / 487 flags = 2.3%; no batch above 5% |
| Held-out cases | rare 10/13 (折中, 疑義 corrected; 會意 defensible); used 8/8; user's five 5/5; 工夫, 愛人, 汽車, 小心, 東西, 大丈夫, 新聞, 自己 `used`; task-2 Korean traps 52/58 `used`, the other 6 right | OK |
| Japanese baseline dropped (D67 item 2) | 82 entries read; 4 re-based on Korean → `config/task2_retrap.csv` (8 rows); 應當 waits for user B7; 師長 → overlay | OK |
| App effect | （ ）: Korean 1,479 cards, Japanese 436; 偽の友達: 276 of 1,245 entries change, 2 leave (D68 fixed notes; the D67 rule would have removed 131); Vietnamese `literary` 1,261 of 5,077 | reported to the user |

Next: Codex 4c-prep5 (D68 item 1), User reruns b055 and answers `docs/TASK5_USER_SAMPLE.md`, Claude gate part 4b (b055 + user answers; move task 5 to `content/accepted/`), Codex 4e.

## Stage 4 gate part 4b (task 5: b055 and the user's sample answers), 2026-11-07: **PASS**, task 5 accepted in full (104/104)

Evidence: `docs/STAGE4D_PART4_REVIEW.md` §8; script `docs/review_scripts/stage4d_part4b_reference.py`; answers in `docs/TASK5_USER_SAMPLE.md`. Decision: **D69**.

| Item | Evidence | Result |
|---|---|---|
| b055 rerun integrity | user rerun, first attempt, $0.077528; ledger $35.50397575 (= `cost_log.csv` sum), room $64.50; 104 inputs byte-identical to a fresh build; `runner.batch_state` 104/104 validated at the accepted paths; 18 `reason_warnings`, all in b055 (17 vi, 1 ko), review-note text only | OK |
| b055 review | 33 flags + 91 `used` checks read: 3 clear false positives (欠缺 けんけつ, 親生 친생, 輕型 경형), 1 borderline → `used` (青春期 청춘기), 1 missed `rare` (氣味 기미) = 5 / 100 items | **ACCEPT** with 5 rows in `config/task5_review.csv` |
| User sample (D67 item 6) | A: 0 of 40 "not used" flags wrong (class not re-opened); C: 26/26 agreed; B: 9 `used`, 4 `rare` (user's final decisions) | 9 rows added; `task5_review.csv` 40 rows (fail-closed check passes) |
| 應當 and other task-2 effects | おうとう `rare` → Korean 응당 = Chinese: no trap → 2 rows in `config/task2_retrap.csv` (10 rows); 霍亂, 會同 baseline back; 那邊 re-based on Korean, zh trap still valid; no other change | OK |
| App effect (104 batches, both overlays) | （ ）: Korean 1,500 cards, Japanese 437 (both 241); `wrong_meaning` ko 18, ja 1; 偽の友達 275 of 1,245 entries change, 3 leave (孫子, 內衣, 應當); Vietnamese `literary` 1,277 of 5,126 | reported |
| Accepted layout | 104 outputs, logs and inputs moved to `content/accepted/task5/` (+ `inputs/`); 87 non-rebuild tests pass | OK; launcher `-Status` still reads task 5 from `content/generated/` (prints 0/104 missing) → Codex 4e item 0 |

Next: Codex 4e (merge, with D68/D69 additions), then Codex Stage 5.
