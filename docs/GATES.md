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

| Stage | Gate date | Result | Attempt | Gate by |
|---|---|---|---|---|
| 1 | 2026-11-04 | PASS | 1 | Claude |
| 2 | 2026-11-04 | PASS | 1 | Claude |
| 3 | 2026-11-04 | **FAIL** | 1 | Claude |
| 3 | 2026-11-05 | **PASS** (short list confirmed and applied, D52) | 2 | Claude |

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
