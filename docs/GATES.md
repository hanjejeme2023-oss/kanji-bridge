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
| 7 | D39: recompute each primary from `word_chars`; `*_all` sets unchanged; `ja_on` = KANJIDIC2 first; both reports exist | 樂 락 or 악, 歷 력, 怒 노, 行 행; scan changes with a top count of 1 (about 33 for Korean; 丹 → 란, 液 → giá are bad) and write overrides |
| 8 | `rules_report.csv` rebuilt from verified pairs after D39 | 0 `unihan_unverified`; large cells follow `config/rules.json`; investigate new large off-pattern cells |
| 9 | Review lists: `ko_multi_candidates.csv`, `ja_multi_candidates.csv`, `vi_ambiguous.csv` | about 124, 170, 13 rows. Review all multi-character rows and all `vi_ambiguous` rows, and single-character rows at levels 1-3; settle per D50 item 4 by overrides whose values are dictionary candidates; the rest go to loop 1 |
| 10 | Sample 20 `libhangul_variant` words and all single-character `ja` values at levels 1-2 | variant false matches (坐下 via 座下) are listed; a rate above 5% means narrowing the variant fields |
| 11 | `ff_candidates.csv` | 2,500-3,300 rows; 手紙 and 大丈夫 present; none in `words` |
| 12 | Random sample of 30 words across levels against the sources (record the seed) | PROMPT gate |
| 13 | Tests pass; rebuild twice identical including `id_map.csv` | |

### Test words at Stage 3 (D49)
Empty means no value is expected from the current sources; the value must then be empty, not filled in. Values in brackets are also accepted because they are review-list items. Single-character `ja` and `ko` follow the D50 defaults; update this table if the user answers differently.

| Word | Row | `simp` | `jp` | `ja` | `ko` | `pinyin` | `vi` |
|---|---|---|---|---|---|---|---|
| 學 | HSK | 学 | 学 | がく | 학 | xué | học |
| 國 | HSK | 国 | 国 | くに | 국 | guó | quốc |
| 茶 | HSK | 茶 | 茶 | ちゃ | 차 (다) | chá | trà |
| 行 | HSK, 2 rows | 行 | 行 | ぎょう (こう) | 행 | xíng; háng | hành; hàng (or empty and in `vi_ambiguous`) |
| 生 | HSK | 生 | 生 | せい | 생 | shēng | sinh |
| 樂 | HSK, lè | 乐 | 楽 | らく | 락 | lè | lạc |
| 經濟 | HSK | 经济 | 経済 | けいざい | 경제 | jīngjì | kinh tế |
| 大學 | HSK | 大学 | 大学 | だいがく | 대학 | dàxué | đại học |
| 勉強 | HSK | 勉强 | 勉強 | べんきょう | 면강 | miǎnqiǎng | miễn cưỡng |
| 手紙 | **`ff_candidates.csv` only** (`words` in Stage 4) | | 手紙 (`form`) | てがみ | | shǒuzhǐ | |
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

Characters: 樂 `ko`=락 or 악, `ko_all` still contains 낙; 歷 `ko`=력; 行 `ko`=행; `ja_on` of all of them = KANJIDIC2 first.

| Stage | Gate date | Result | Attempt | Gate by |
|---|---|---|---|---|
| 1 | 2026-11-04 | PASS | 1 | Claude |
| 2 | 2026-11-04 | PASS | 1 | Claude |

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
