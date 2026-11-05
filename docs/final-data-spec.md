# Final Data Spec: derived from the 漢字ブリッジ final UI/UX

Source: 漢字ブリッジ（試作版） artifact, 5 views: カード / 音のルール / 偽の友達 / 読解 / 字体. Reviewed 2026-11-04.
**The UI/UX of that file is final.** Only its hardcoded data is a placeholder. This spec defines the data that replaces it.
Principle: work backwards. The views decide which tables we need; the pipeline (see data-pipeline-notes.md) only has to produce these.

Users: Annie (Korean + Japanese as base) learning Chinese + Vietnamese. PC only, opened as a local file.

Last updated: 2026-11-04 (after 3-pass document audit)

---

## Decisions

| # | Decision | Date |
|---|---|---|
| D1 | **Normalized tables**, not one tab per view and not one giant table. Every fact is stored once; views read shared tables via IDs. | 11-04 |
| D2 | **Word backbone = HSK 3.0** (defines which words exist and their level). | 11-04 |
| D3 | **Vietnamese has no official level word list** (a 6-level proficiency framework/test exists, but no HSK-style vocab list was found). Vietnamese side = HSK words with a Sino-Vietnamese cognate + **high-frequency Hán-Việt words missing from HSK**, ordered by frequency. Combine with `merge(how="outer", indicator=True)`. | 11-04 |
| D4 | Exports: CSV for human review; JSON for publishing; **`data.js`** for the app (see D5). | 11-04 |
| D5 | The app is opened directly from disk (`file://`). Browsers block `fetch()` of local JSON there, so the app loads one generated script, `data/final/data.js` (`window.KB_DATA = {...}`), via `<script src>`. | 11-04 (audit) |
| D6 | **Polyphones are resolved at word level, not by splitting character rows.** Unihan's per-language reading lists are not aligned with each other (樂: lè/yuè, 락/악, lạc/nhạc cannot be paired automatically). `chars` keeps one row per character with a primary reading plus all readings per language; the correct reading for a word comes from the word-level dictionaries. | 11-04 (audit; replaces the earlier "one row per reading" idea) |
| D7 | **Sound-rule pairs come from aligned syllables**: (a) characters with exactly one Korean and one Vietnamese reading, plus (b) syllable-by-syllable alignment of words in `word_chars`. | 11-04 (audit) |
| D8 | **Rule definitions (the 6 rules' titles and explanation text) are small static UI content**, kept as a config file written by Claude. Only their examples, counts and exceptions are generated from data. | 11-04 (audit) |
| D9 | **Japanese on'yomi in kana come from KANJIDIC2**, not Unihan (Unihan `kJapaneseOn` is romaji). | 11-04 (audit) |
| D10 | False friends come from two places: (a) words in `words` whose per-language meanings differ, and (b) **code-generated candidates outside `words`**: common Japanese/Korean words that also exist as a Chinese or Vietnamese entry (e.g. 手紙, 大丈夫). Gemini judges both; review verifies. | 11-04 (audit) |
| D11 | Card eligibility: a word appears in Cards only if it has a `level`, (Japanese reading or Korean) **and** (pinyin or Vietnamese). The Cards target switch further limits due cards to words that have the target language(s). `ff_only` words appear only in 偽の友達. Other words still exist in the tables. | 11-04 (audit) |

## Sources (candidates; contents + licenses verified in Stage 1, see SOURCES.md)

| Data | Source | Notes |
|---|---|---|
| chars: Hangul, Vietnamese, pinyin, variants, English | **Unihan** (kHangul, kVietnamese, kMandarin, kSimplifiedVariant, kTraditionalVariant, kDefinition) | kHangul values look like `학:0E` (strip the source suffix). Use kHangul, not deprecated kKorean. kVietnamese quality reportedly uneven → cross-check |
| chars: Japanese on'yomi (kana), Japanese form | **KANJIDIC2** | on'yomi in katakana → convert to hiragana for display |
| words: list + level + traditional form | **ivankra/hsk30** (11,092 terms, trad, pinyin, POS; 3,000-char list) | use its traditional column; do not convert simplified→traditional automatically (one-to-many, 发 → 發/髮) |
| words: Chinese gloss | **CC-CEDICT** | |
| words: Japanese form + reading | **JMdict** | word readings ≠ joined on'yomi (学校 がっこう) |
| words: Korean | **libhangul hanja.txt** | Hangul ↔ Hanja, characters and words |
| words: Vietnamese + frequency | **chinese-hanviet-cognates** (URL to confirm) | also the cross-check for Unihan kVietnamese |
| Japanese shinjitai ↔ traditional mapping | TBD in Stage 1 (Unihan variant fields are not a clean shinjitai map) | method recorded in DECISIONS |
| glosses, false-friend judgments, passages | AI (Gemini), human-verified | |

## What each view needs

| View | Prototype array | Real data | Who makes it |
|---|---|---|---|
| カード | `WORDS` (h, j, z, p, jr, k, v) | `words` (eligible per D11) | dictionaries + code |
| 音のルール | `RULES` (6 rules: text + examples as [char, ko, ja, vi, zh]) | rule text from `config/rules.json` (D8) + up to 8 examples per rule from aligned pairs (D7), preferring low-level, high-frequency characters | Claude (text) + code |
| 偽の友達 | `FF` (word, safe meanings, trap meanings + reading) | `words` where `false_friend` is set + `ff_meanings` | code (candidates) + Gemini (judgment) + review |
| 読解 | `PASSAGES` (tokens: word / function word / punctuation) | `passages` | Gemini + review |
| 字体 | `GLYPHS` (jp, trad, simp, pinyin, ja, ko, vi) | `chars` where the 3 forms are not all identical; readings from `*_all` joined with " / " | dictionaries + code |

## Tables

All text UTF-8, NFC. IDs are zero-padded, assigned once, and kept in `pipeline/id_map.csv` so rebuilds reproduce the same IDs and new rows get new IDs.

### chars: one row per character
| col | example | notes |
|---|---|---|
| char_id | c00001 | |
| trad | 學 | canonical key |
| simp | 学 | |
| jp | 学 | Japanese form |
| ja_on | がく | primary on'yomi, hiragana |
| ko | 학 | primary Hangul reading |
| pinyin | xué | primary, tone marks |
| vi | học | primary Hán-Việt reading |
| ja_on_all / ko_all / pinyin_all / vi_all | がく | `;`-separated, all readings |
| ko_final | ㄱ | derived from `ko` |
| vi_final | c | derived from `vi`; empty = open syllable |
| in_hsk_chars | true | in the HSK 3.0 character list |

Scope: union of the HSK 3.0 character list and every character used in `words`.

### words: one row per word
| col | example | notes |
|---|---|---|
| word_id | w00001 | **SRS key in the app** |
| trad / simp / jp | 學生 / 学生 / 学生 | trad + simp from hsk30 (or the source that added the word); jp from the matched JMdict entry, else built per character from `chars.jp` |
| ja | がくせい | Japanese reading (NaN if not a Japanese word) |
| ko | 학생 | |
| pinyin | xuéshēng | |
| vi | học sinh | |
| gloss_en | student | |
| meaning_ja__ja / meaning_ja__ko / meaning_ja__zh / meaning_ja__vi | 学ぶ人 | meaning of the word **as used in** ja/ko/zh/vi, written in Japanese (for display) |
| level | 1 | HSK level; for VI-only words, a level assigned from frequency bands (rule in DECISIONS) |
| freq_vi | 1234 | Vietnamese frequency rank |
| origin | hsk / vi_freq / both / ff_only | ff_only = added only as a false-friend word |
| card_eligible | true | D11 |
| false_friend | | language codes where the meaning differs, e.g. `zh` or `ko;zh` |
| verified | true | human/auditor checked |
| source_* | | which source gave each language |

### word_chars: word ↔ characters in order
| word_id | position | char_id | ko_syllable | vi_syllable |
|---|---|---|---|---|
| w00001 | 1 | c00001 | 학 | học |
| w00001 | 2 | c00042 | 생 | sinh |

Rows where the syllable count does not match the character count are reported, not guessed.

### ff_meanings: per-language meaning for the 偽の友達 tiles
| word_id | lang | reading | meaning_ja | is_trap |
|---|---|---|---|---|
| w00321 | ja | べんきょう | 勉強する | false |
| w00321 | zh | miǎnqiǎng | 無理に・しぶしぶ | true |

Readings are copied from the dictionary tables, never generated.

### passages
| col | notes |
|---|---|
| passage_id | p0001 |
| lang | zh / vi |
| level | max level of words used |
| translation_ja | |
| tokens | ordered list; each token is one of: `{t, word_id}` (linked word), `{t, gloss_ja}` (function word such as 了, 的, có, và), `{t, punct: true}` |

### config/rules.json (static, written by Claude)
The 6 rules from the prototype (ㄱ→c/ch, ㅂ→p, ㄹ→t, ㄴ→n, ㅁ→m, ㅇ→ng/nh): id, Korean final, Vietnamese finals, title, Japanese explanation, Chinese explanation. Examples are filled from data at build time.

### Derived at build time (not hand-made)
- Rule examples, counts, exceptions: pivot of aligned (ko_final, vi_final) pairs (D7).
- `rules_report.csv` for review.

## Output files
`data/final/`: `chars`, `words`, `word_chars`, `ff_meanings`, `passages` as `.csv` + `.json`, plus `data.js` (all of them bundled for the app), `rules_report.csv`, `coverage_report.csv`.

## Build order
1. Sources + licenses (Stage 1)
2. `chars` (Unihan + KANJIDIC2, cross-checked) → 字体
3. `words` + `word_chars` (hsk30 × CC-CEDICT × JMdict × hanja.txt × hanviet data, + VI-frequency additions) → カード, 音のルール examples
4. False-friend candidates (code) → judgments + `meaning_ja__*` (Gemini) → review → 偽の友達
5. Passages (Gemini) → review → 読解
6. `data.js` + app integration

---

## Addenda (Stage 0, Claude, 2026-11-04)
Gap-fillers decided while mapping the prototype to tables; details and reasons in `DECISIONS.md` D12–D19, exact shapes in `SCHEMA.md`.
- `chars.level`; `words.ja_alt`, `ko_alt`, `vi_alt`, `note_ja`, `syl_aligned` added (D14).
- `data.js` = reduced normalized tables + precomputed `rules` in the prototype's `RULES` shape; missing values are omitted keys (D12).
- App keys SRS / custom deck / false-friend tiles by `word_id` (D13).
- Rule examples: single characters, non-exception, ≤ 8 per rule, ≥ 4 required (D17).
- `chars.trad` is not unique: source characters sharing a traditional form (hsk30 `着`/`著`) stay separate rows; unique key `char_id`, new column `key_char`; words link to rows by simp, then pinyin (D37).

## Addenda (pre-Stage-3 review, Claude, 2026-11-04)
Rules in `DECISIONS.md` D39-D50. **Where PROMPT Stage 3 and these disagree, these win.** PROMPT itself stays unchanged.
- Build order: PROMPT's step order is replaced by D40. `chars` grows before matching; `word_chars` and D39 come after matching.
- PROMPT step 2 and D36: VI-only words are added now with the current sources; if the D36 search accepts a source all of Stage 3 reruns; the word list freezes only after that (D46).
- PROMPT step 5, "frequent hanja.txt words": not implementable, the file has no frequency data. Korean-only false-friend candidates are dropped; the filter is D47.
- PROMPT Stage 3 Done-when, "20 test words": 18 are HSK words, 越南 is a seeded `vi_freq` word, 手紙 is checked in `ff_candidates.csv` (D49; table in `GATES.md`).
- PROMPT Stage 5, glyph readings "from the `*_all` columns": Korean uses `ko_base_all` (SCHEMA §3.5).
- `chars` primaries: `ko`, `vi` from word evidence, Korean with 두음법칙 normalization; `ja_on` keeps KANJIDIC2 order and `pinyin` keeps `kMandarin` order (D39, D50).
- New columns: `chars.ko_base_all`; `words.ja_common`, `pos`, `hsk_ids`, `gloss_ja_en`, `gloss_ko`, `gloss_vi`; `word_chars.pinyin_syllable`, `ko_base` (SCHEMA).
- Stage 3 gate corrections to the matching rules: D51 (variant forms for Japanese only at 2+ characters; on'yomi from the linked `chars` row; single-character Vietnamese rule A on `trad` only; rule-B conflict filter; `gloss_vi` for rule-B words; `simp` of grown rows).
