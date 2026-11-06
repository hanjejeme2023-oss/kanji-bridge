# D36: Vietnamese source search (Claude, 2026-11-05)

Task: HANDOFF "Planned sequence after Stage 3", step 3, with the user's limits for this session: at most 8 candidates, most promising first; licence read before any download; acceptance bar = precision at least 95% on a seeded sample of the overlap with the current verified Vietnamese readings, **and** a gain of at least +300 HSK words with a Vietnamese reading or +3 percentage points of HSK coverage; 30 seeded new readings listed for the user's spot check; accepted for one use only. Downloads went to a scratch folder outside the repo. Nothing in `raw/`, `pipeline/` or `data/` was changed. Decision: **D53**.

Baseline (`data/final/coverage_report.csv`, commit `7827546`): 3,880 of 11,028 HSK words have `vi` (35.18%). +300 words = 37.9%; +3 pp = +331 words.

## 1. Candidates checked (8, in the order checked)

| # | Candidate | Licence (read from) | Downloaded? | Use tested | Result |
|---|---|---|---|---|---|
| 1 | **Kaikki English-Wiktionary, Vietnamese entries** (`kaikki.org/dictionary/Vietnamese/kaikki.org-dictionary-Vietnamese.jsonl`, 52,167 entries, extracted 2026-10-30 from the enwiktionary dump of 2026-10-01) | kaikki.org/dictionary/index.html, "Copyright and license": "made available under the same licenses as Wiktionary - both CC-BY-SA and GFDL". Same terms as accepted source 7A (D24). | Yes (scratch; SHA-256 `186cd0a6…d945`, 83,424,329 bytes) | word list (Hán-Việt word + Han form) | **ACCEPTED for the word list only** (rule A2, D53). Precision 199/200 on the seeded sample; +356 HSK words (+3.23 pp) |
| 2 | CVDICT (github.com/ph0ngp/CVDICT), Chinese–Vietnamese, 122k entries | README "License": CC BY-SA 4.0 (no LICENSE file; the README is the statement) | No | meanings / word list | **Rejected (Global Rule 2):** the README says most entries were translated from CC-CEDICT's English by a fine-tuned ChatGPT-4o model. AI-generated data cannot be a dictionary source. It also gives meanings, not Hán-Việt readings |
| 3 | wordfreq (github.com/rspeer/wordfreq), Vietnamese list | README "License": code Apache 2.0, data CC BY-SA 4.0 | No | word frequency | **Rejected (no gain):** Vietnamese is tokenized by UAX #29, so tokens are syllables, not words; its Vietnamese sources overlap FrequencyWords/OpenSubtitles (7B). It cannot replace the D26 syllable proxy. Data frozen since 2021 |
| 4 | Wikidata lexemes (Vietnamese) | Wikidata:Licensing: Lexeme namespace CC0 | No (SPARQL count only) | word list | **Rejected (no gain):** 87 Vietnamese lexemes, 1 with a Han-script (`vi-hani`) form |
| 5 | HanViet extension data (github.com/alienngator/zhongwen; Thiều Chửu 1942 + "Hán Việt Từ Điển Trích Dẫn © DTK") | LICENSE: GPL-2.0; CREDITS.md: DTK data used "with permission" of the author | No | character readings | **Rejected (licence):** GPL-2.0 cannot be relicensed into the CC BY-SA 4.0 dataset (D23), and the DTK part is a private permission, not a licence. No other digitized Thiều Chửu text with a licence file was found |
| 6 | duyet/vietnamese-wordlist | GitHub licence: GPL-2.0 | No | word list | **Rejected (licence):** GPL-2.0, as #5. Also alphabetical, not a frequency list |
| 7 | Leipzig Corpora Collection, Vietnamese | Terms page (wortschatz.uni-leipzig.de/en/usage) blocks automated reading (proof-of-work wall); search excerpts say CC BY-NC for its data/services and CC BY for downloaded corpora | No | word frequency | **Rejected:** licence page could not be read (Global Rule 5 needs it), the excerpt shows NC terms, and its Vietnamese lists are syllable tokens (same problem as #3) |
| 8 | Kaikki English-Wiktionary, **Chinese** entries: Vietnamese descendants (Sino-Xenic) | same page as #1 | Streamed (1.2 GB, not stored); 3,953 Vietnamese descendant rows, 3,687 forms | word list | **Rejected (gain and quality):** alone +231 HSK words (+2.09 pp, below the bar); precision 195/200; the 131 words it adds beyond rule A2 are mostly vernacular or pre-Hán-Việt forms (離 lìa, 鐵 sắt, 燈 đèn, 畫 vẽ, 信息 tin tức), not Hán-Việt readings |

Seen in searches but not counted as candidates: SDSU "Corpora of Vietnamese Texts" frequency lists (no licence statement found), Hugging Face `HanScript2HanViet2ModernViet_Literature` (poetry, partly AI-generated), Sketch Engine (commercial).

## 2. Accepted: rule A2 (Kaikki English-Wiktionary), how it was measured

Reference scripts (evidence, not pipeline): `docs/review_scripts/d36_enwikt_extract.py`, `d36_measure_pairs.py`, `d36_rule_a2_measure.py`, `d36_zh_descendants_extract.py`. Vietnamese strings are normalized with `pipeline.common.normalize_vietnamese` (D25). Comparisons treat i/y spellings as equal (D44 item 3: kì = kỳ).

**Pair extraction:** entries with `lang_code=vi`; Han form = the odd positional arguments of the `vi-etym-sino` etymology template joined (`{{vi-etym-sino|學|to learn|生|...}}` → 學生), plus the Han run in "Sino-Vietnamese word from <Han>" in `etymology_text`. 14,513 pairs, 11,376 forms. Kept only pairs whose syllable count equals the form's length. **Filter (measured):** dropped `pos` = `name` (1,361 pairs: Bỉ "Belgium" for 比, given names) and `romanization` (166), entries with an `alt-of` or `abbreviation` sense (236), first gloss naming a given name or surname (2). Character entries (`pos=character`) are not word pairs.

**Matching:** an HSK word's `trad`; for 2+ characters then `simp` (the build will also try the D43 variant forms, as rule A does).

| Measure | Value |
|---|---|
| HSK words with an existing `vi` and an A2 pair (overlap) | 2,918; agree (existing `vi` or `vi_alt` among A2 values) **2,902 = 99.45%** |
| of these, 2+ characters | 2,296; agree 2,294 (99.91%) |
| **seeded sample of the overlap** (`random.Random(36)`, n = 200) | **199 / 200 = 99.5%** (bar: 95%) |
| VI-only (`vi_freq`) overlap | 1,036; agree 1,036 |
| HSK words with empty `vi` that get exactly one A2 value | 362 (269 of 2 characters, 19 of 3+, 74 single characters); 0 with several values |
| of these, every sense of the entry tagged obsolete or archaic | 6 (新聞 tân văn, 戲劇 hí kịch, 伯父 bá phụ, 不宜 bất nghi, 岳父 nhạc phụ, 岳母 nhạc mẫu): **not used**, reported (D53) |
| **gain** | **+356 HSK words → 4,236 / 11,028 = 38.41% (+3.23 pp)**; both bars met |
| gain by level (before the 6) | L1 14, L2 26, L3 24, L4 29, L5 35, L6 38, L7 196 |
| gain words that already have `ja` and `ko` (all four after the gain) | 252 |
| character check of gain syllables against `chars.vi_all` | 170 all verified, 84 via an unverified Unihan reading, 108 outside `vi_all` (mostly real readings missing from `vi_all`: 匯 hối in 外匯 ngoại hối, 懇 khẩn in 誠懇 thành khẩn). These become `not_in_all` rows in `alignment_mismatches.csv` (D45) |

**Disagreements in the overlap (16, for loop 1, accuracy):** A2 fills only empty values (D53), so these do not change the build. Some show errors in the current data: 詞 now `tờ` (a Nôm reading, Kaikki-vi rule A), English Wiktionary `từ`; 奔 now `hợp` (known, Stage 3 gate note), not checked here. Others are different words with the same Han etymon (關 loan, 週 châu, 圈 khuyên, 經 canh, 拖 tha, 藏 tạng "Tibetan", 中 trúng, 散 tản, 拄 trụ, 累 lụy, 一 nhất vs nhứt) or accepted variants (祝福 chúc phúc / chúc phước, 服從 phục tùng / phục tòng).

**38 rule-B values that English Wiktionary gives under other characters (loop 1, accuracy):** for 38 words with `source_vi=composed_attested`, the Vietnamese word is an A2 entry whose Han form is different. About half are wrong compositions: 老是 lão thị (老視), 行人 hạnh nhân (杏仁), 燈光 đăng quang (登光), 長假 trưởng giả (長者), 嘆氣 thán khí (碳氣), 忠心 trung tâm (中心), 報酬 báo thù (報讎), 解讀 giải độc (解毒), 綠地 lục địa (陸地), 尚未 thượng vị (上位), 食用 thực dụng (實用), 無償 vô thường (無常), 友情 hữu tình (有情), 清明 thanh minh (聲明), 評定 bình định (平定), 小型 tiểu hình (小刑), 外行 ngoại hạng (外項), 外援 ngoại viện (外院), 登陸 đăng lục (登錄). The other half are spelling variants of the same word (秘密/祕密, 想象/想像, 辭典/詞典, 以往/已往, 振動/震動, 沉思/沈思, 環球/寰球, 激勵/激厲, 言辭/言詞, 模仿/摸仿, 設想/竊想, 周旋/周全, 原型/原形, 工夫/功夫, 電器/電氣, 收復/收服, 廉政/廉正, 家境/家景, 情景/情境). Extending the D51 conflict filter to A2 would therefore drop about 19 correct values too, so D53 does **not** extend it. Loop 1 should handle this list (overrides or a variant-aware filter).

**Character readings (not accepted this round):** the same file has 1,081 "chữ Hán form of X" character readings for 865 characters, separate from 3,873 Nôm readings. Against verified `chars.vi_all`: 543 / 556 agree (97.7%). It would confirm a Unihan reading for 45 of 465 unverified characters and give 36 of 740 characters without `vi` a reading. That is too small for this round and needs its own parsing rule (values such as `mĩ/mỹ`, `đan/đơn`). It also flags errors worth a loop-1 look (又 now `lại`, chữ Hán `hựu`; 局 `cục` vs `cuộc`). Not used in D53.

**Frequency:** no licensed Vietnamese **word** (multi-syllable) frequency list was found (#3, #7). D26's syllable proxy stays; VI-only levels remain a rough proxy (D46).

## 3. Thirty seeded new readings for the user's spot check

`random.Random(36).sample` of the 362 single-value gains, sorted by `word_id` (file: scratch `a2_spotcheck30.csv`). "chars" = the character check above. The Vietnamese value is copied from the English-Wiktionary entry. Before the D44 i/y rule; the build will write 自己 as `tự kỷ`.

| word_id | trad | pinyin | L | new `vi` | chars | entry (pos, tags): first gloss | etymology (evidence) |
|---|---|---|---|---|---|---|---|
| w00042 | 唱歌 | chànggē | 1 | xướng ca | unverified | verb: to sing | Sino-Vietnamese word from 唱歌 |
| w00380 | 晚 | wǎn | 1 | vãn | unverified | adj (literary): quiet as a venue is nearly over | Sino-Vietnamese word from 晚 |
| w00911 | 篇 | piān | 2 | thiên | outside | noun (historical): volume of a large book | Sino-Vietnamese word from 篇 ("volume") |
| w01247 | 自己 | zìjǐ | 2 | tự kỉ | verified | adj (colloquial, figurative): autistic | Sino-Vietnamese word from 自己 ("self") |
| w01364 | 持續 | chíxù | 3 | trì tục | verified | adj (in compounds): continuous | Sino-Vietnamese word from 持續 |
| w02075 | 訓練 | xùnliàn | 3 | huấn luyện | unverified | verb: to train; to coach | Sino-Vietnamese word from 訓練 |
| w02969 | 維修 | wéixiū | 4 | duy tu | verified | verb: to repair and maintain | Sino-Vietnamese word from 維修 |
| w03154 | 折 | zhé | 4 | chiết | unverified | verb (archaic): to extract | Sino-Vietnamese word from 折 |
| w04151 | 約束 | yuēshù | 5 | ước thúc | verified | verb: to restrain | Sino-Vietnamese word from 約束 |
| w04236 | 中毒 | zhòngdú | 5 | trúng độc | outside | verb: to get poisoned | Sino-Vietnamese word from 中毒 |
| w04625 | 跪 | guì | 6 | quỵ | outside | verb (colloquial): to kneel down | Sino-Vietnamese word from 跪. Compare quỳ, khuỵ |
| w04762 | 絕大多數 | juédàduōshù | 6 | tuyệt đại đa số | verified | noun: an absolute majority | Sino-Vietnamese word from 絕大多數 |
| w05523 | 豹 | bào | 7 | báo | outside | noun: leopard | Sino-Vietnamese word from 豹 ("leopard") |
| w05700 | 不宜 | bùyí | 7 | bất nghi | verified | adj (archaic, rare): inappropriate | Sino-Vietnamese word from 不宜 — **one of the 6 obsolete/archaic-only entries: not used** |
| w05998 | 喘 | chuǎn | 7 | suyễn | unverified | noun: asthma | Sino-Vietnamese word from 喘 ("to pant") |
| w06338 | 豆漿 | dòujiāng | 7 | đậu tương | outside | noun: soybean | Sino-Vietnamese word from 豆漿 ("soy milk") |
| w06340 | 逗 | dòu | 7 | đậu | outside | verb (archaic): to park, halt | Sino-Vietnamese word from 逗 |
| w06362 | 隊形 | duìxíng | 7 | đội hình | verified | noun: a roster | Sino-Vietnamese word from 隊形 ("battle formation") |
| w06572 | 封鎖 | fēngsuǒ | 7 | phong tỏa | unverified | verb: to blockade; to lock down | Sino-Vietnamese word from 封鎖 |
| w07024 | 和睦 | hémù | 7 | hòa mục | verified | adj (literary): harmonious | Sino-Vietnamese word from 和睦 |
| w07914 | 欄杆 | lángān | 7 | lan can | outside | noun: rail; banisters | Sino-Vietnamese word from 欄杆 |
| w08106 | 壟斷 | lǒngduàn | 7 | lũng đoạn | unverified | verb: to monopolize | Sino-Vietnamese word from 壟斷 |
| w08232 | 門當戶對 | méndānghùduì | 7 | môn đăng hộ đối | outside | phrase (idiomatic): to be well-matched for marriage | Sino-Vietnamese word from 門當戶對 |
| w08397 | 匿名 | nìmíng | 7 | nặc danh | unverified | adj: anonymous | Sino-Vietnamese word from 匿名 |
| w08791 | 全程 | quánchéng | 7 | toàn trình | verified | noun: the entire process | Sino-Vietnamese word from 全程 |
| w09053 | 生涯 | shēngyá | 7 | sinh nhai | outside | verb: to subsist | Sino-Vietnamese word from 生涯 |
| w09381 | 胎兒 | tāi'ér | 7 | thai nhi | verified | noun: fetus | Sino-Vietnamese word from 胎兒 |
| w10033 | 猩猩 | xīngxing | 7 | tinh tinh | outside | noun: a chimpanzee | Sino-Vietnamese word from 猩猩 ("ape; orangutan") |
| w10384 | 引入 | yǐnrù | 7 | dẫn nhập | verified | verb: to introduce | Sino-Vietnamese word from 引入 |
| w10943 | 自卑 | zìbēi | 7 | tự ti | outside | adj: feeling inferior | Sino-Vietnamese word from 自卑 |

My reading of the sample: all 30 values are the Hán-Việt reading of the word's characters, written as the dictionary entry gives it. In 6 rows the Vietnamese meaning differs from the Chinese (自己 "autistic", 豆漿 "soybean", 逗 "to halt", 晚 "quiet late", 生涯 "to subsist", 篇 "volume"). Those are false-friend material for Stage 4 task 2, not reading errors; Stage 4 sees them through `gloss_vi` (D53 item 6).
