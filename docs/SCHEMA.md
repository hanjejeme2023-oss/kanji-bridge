# SCHEMA: contract between agents (Claude-owned)

Written in Stage 0 (2026-11-04). `final-data-spec.md` defines *what*; this file fixes the exact columns, types, IDs and the shapes the app reads.
If this file and the spec disagree, the spec wins, except where DECISIONS.md D12–D17 (spec addenda) say otherwise.

## 0. Global conventions

- UTF-8, NFC. CSV: `to_csv(index=False, encoding="utf-8")`, header row, `;` separates multi-values inside a cell.
- **Missing = empty cell in CSV, `null` in JSON, key omitted in `data.js`.** Never `"NaN"`, `"None"`, `"undefined"`, `"-"`.
- Booleans: CSV `true`/`false` (lowercase); JSON `true`/`false`.
- IDs: `c00001` (chars), `w00001` (words), `p0001` (passages). Assigned once in `pipeline/id_map.csv` (columns `kind,key,id`); keys: chars = `key_char` (D37); words = `trad|pinyin` (or `trad|ja|vi` if no pinyin); passages = `lang|level|n` as defined by Codex. Rebuild reuses IDs; new rows get the next free number; IDs are never reused or renumbered.
- Pinyin: tone marks, lowercase, syllables joined without spaces in `words.pinyin` (`xuéshēng`), as the prototype does. `chars.pinyin` is one syllable.
- Vietnamese: NFC, lowercase, modern tone placement (D25: `thủy`, `hòa`, not `thuỷ`, `hoà`), syllables separated by one space (`học sinh`). Korean: Hangul, no spaces inside a word.
- Japanese kana: hiragana. (KANJIDIC2 katakana on'yomi are converted.)
- `lang` codes: `ja`, `ko`, `zh`, `vi`. App labels: ja=日, ko=韓, zh=中, vi=越.

## 1. Tables (columns in order)

### 1.1 `chars` — one row per character (key `trad`)
| col | type | rule |
|---|---|---|
| char_id | str `cNNNNN` | |
| trad | str, 1 char | Chinese traditional form, used to match HSK words. **Not unique**: hsk30 `着` and `著` are separate rows that both have `trad=著` (D37). Unique key = `char_id` |
| key_char | str, 1 char | the character whose Unihan / KANJIDIC2 / libhangul / Kaikki entries supply this row's readings; unique; **equals `trad` for every row except rows whose `trad` is shared with another row, where it is the source Hanzi (`着`; the row `著` keeps `著`)**. `id_map.csv` key for chars (D37) |
| simp | str, 1 char | = `trad` if no simplification |
| jp | str, 1 char | Japanese form (shinjitai), = `trad` if unchanged. Mapping method: DECISIONS (Stage 1 review) |
| ja_on / ko / pinyin / vi | str | primary reading (D6). May be empty |
| ja_on_all / ko_all / pinyin_all / vi_all | str | `;`-separated, primary first, de-duplicated |
| ko_final | str | one of `ㄱ ㄴ ㄹ ㅁ ㅂ ㅇ` or other final jamo; empty = no final |
| vi_final | str | one of `c ch p t n m ng nh`; empty = open syllable |
| in_hsk_chars | bool | in the HSK 3.0 character list |
| level | int 1–7 | hsk30-chars `Level` (`7-9` is stored as **7**, D29); else min `words.level` of words using the character; empty if none (D14, D29) |
| gloss_en | str | Unihan kDefinition, for reference only |
| source_ko / source_vi / source_ja / source_pinyin | str | source tag of each primary reading. `source_vi` ∈ `kaikki_aligned` / `unihan_hvsyl` / `unihan_unverified` (D24). `unihan_unverified` readings are excluded from word composition and sound-rule pairs |

### 1.2 `words` — one row per word
| col | type | rule |
|---|---|---|
| word_id | str `wNNNNN` | SRS key |
| trad / simp | str | from hsk30 (or the source that added the word) |
| jp | str | Japanese written form from matched JMdict entry; else built per character from `chars.jp`; empty if not a Japanese word |
| ja | str | Japanese reading (hiragana); empty if no match |
| ko | str | Hangul |
| pinyin | str | |
| vi | str | |
| ja_alt / ko_alt / vi_alt | str | `;`-separated other readings; empty if none (D14) |
| gloss_en | str | CC-CEDICT first gloss(es), reference only |
| meaning_ja__ja / __ko / __zh / __vi | str | Japanese-language meaning as used in that language (Gemini, Stage 4); empty if language missing |
| note_ja | str | optional one-line note in Japanese (e.g. "日本語・韓国語では普通カタカナで…"); mostly empty (D14) |
| level | int 1–7 | HSK level (`7-9` stored as 7, D29), or frequency-band level 3–7 for VI-only words (D27) |
| freq_vi | int | Vietnamese frequency rank (1 = most frequent); empty if unknown |
| origin | `hsk` / `vi_freq` / `both` / `ff_only` | |
| card_eligible | bool | D11 |
| false_friend | str | `;`-separated lang codes where meaning differs from the others, e.g. `zh` or `ko;zh`; empty = not a false friend |
| syl_aligned | bool | true when `word_chars` gives a full Korean AND Vietnamese syllable alignment (D14) |
| verified | bool | |
| source_ja / source_ko / source_pinyin / source_vi / source_level | str | provenance tags. `source_vi` ∈ `kaikki_han` / `composed_attested` (D24); `source_ja` ∈ `jmdict` / `built_from_chars` (D31); `source_ko` = `libhangul`; `source_level` ∈ `hsk30` / `vi_band` |

### 1.3 `word_chars`
`word_id, position (int, 1-based), char_id, ko_syllable, vi_syllable`. A word's character at each position is matched to `chars` by the word's own `trad` string (D38): rows whose `trad` equals the character; if none, the row whose `key_char` equals it; if several (`trad` collision, D37), by the word's `simp` at that position, then by pinyin; undecidable cases leave `char_id` empty and go to `char_ambiguous.csv`. Position check: the linked row's `simp` equals the word's `simp` at that position, else the word goes to `char_simp_mismatch.csv`.
Unique on `(word_id, position)`. A word with a syllable-count mismatch gets rows with empty syllables and `syl_aligned=false`, and is listed in `data/final/alignment_mismatches.csv` (no guessing).

### 1.4 `ff_meanings`
`word_id, lang, reading, meaning_ja, is_trap`. Unique on `(word_id, lang)`. `reading` is copied from the dictionary column of the same language (`words.ja` / `ko` / `pinyin` / `vi`), never generated. At most one row per language per word.

### 1.5 `passages`
`passage_id, lang (zh|vi), level, translation_ja, tokens`.
CSV stores `tokens` as a JSON string; JSON/`data.js` as an array. Token = exactly one of:
- `{"t": "...", "word_id": "w00001"}` linked word
- `{"t": "...", "gloss_ja": "..."}` function word
- `{"t": "...", "punct": true}` punctuation

### 1.6 `rules` (build-time, exported to `data.js` and `rules.json`-shaped)
Not a pandas table to maintain: `config/rules.json` text + examples computed from aligned pairs (D7). Exported as the exact `RULES` shape (§3.2).

### 1.7 Reports (not read by the app)
`rules_report.csv` (pivot ko_final × vi_final of pair counts, plus per-pair examples), `char_key_collisions.csv`, `char_ambiguous.csv` (D37), `char_simp_mismatch.csv` (D38), `coverage_report.csv` (incl. `freq_vi_basis=syllable_min`, D26), `alignment_mismatches.csv`, `vi_ambiguous.csv` (words with ≥ 2 composed Vietnamese candidates, D24), `no_jp_form.csv` (characters without a Japanese form, D28), `ko_unresolved.csv` (D32).

## 2. `data.js` shape

```js
window.KB_DATA = {
  meta:   { built: "YYYY-MM-DD", counts: {chars: n, words: n, ...} },
  chars:  [ { char_id, trad, simp, jp, ja_on_all, ko_all, pinyin_all, vi_all, in_hsk_chars, level }, ... ],  // only columns the glyph view needs, see §3.5
  words:  [ {all words columns the app needs, see §3.1} ],
  word_chars: [ {word_id, position, ko_syllable, vi_syllable} ],  // only rows of words with syl_aligned
  ff_meanings: [ {word_id, lang, reading, meaning_ja, is_trap} ],
  passages: [ {passage_id, lang, level, translation_ja, tokens:[...]} ],
  rules:  [ {id, jong, kr, vi, label, jp, zh, ex:[[trad, ko, ja, vi, pinyin], ...]} ]
};
```
- Keys with missing values are **omitted** (not `null`, not `""`). Adapters must treat `undefined` as missing.
- Booleans are real booleans; integers are numbers.
- Size control: `chars` in data.js only holds characters needed by the glyph view (forms not all identical) and `words` only the columns in §3.1. Full tables stay in CSV/JSON.
- `tokens`' `word_id` must exist in `words` (build fails otherwise).
- File is a single statement `window.KB_DATA = {...};` in UTF-8, loadable by `<script src="../data/final/data.js">` from `file://`.

## 3. Mapping to prototype views (adapters live in `app/index.html`)

The view code stays as is. Adapters rebuild the prototype's array shapes from `KB_DATA`; field names on the left are what the view code reads.

### 3.1 `WORDS` (カード, 読解 detail, ruleTags)  ← `words` where `card_eligible` (deck) / any word (passage tokens, custom cards)
| prototype field | source | if missing |
|---|---|---|
| (new) `id` | `word_id` | never missing. **SRS/custom/`ffopen` key replaces `w.h`** (D13) |
| `h` | `trad` | never missing |
| `j` | `jp` | fall back to `trad` |
| `z` | `simp` | fall back to `trad` |
| `p` | `pinyin` | `''`; card needs target check (below) |
| `jr` | `ja` | `''` (render nothing) |
| `k` | `ko` | `''` |
| `v` | `vi` | `''` |
| `va` (new, optional) | `vi_alt` split on `;` | omit; `judge()` for Vietnamese also accepts these (D14) |
| `note` | `note_ja` | omit |
| `syl` (new) | `syl_aligned` + `word_chars` | `ruleTags` shows tags only when `syl` true, iterating `word_chars` instead of `[...w.k]` / `w.v.split(' ')` |

Deck rule: `card_eligible`, ordered by `level` then `freq_vi` (nulls last) then `word_id`. Due list is filtered by the target switch: `vi` → word has `v`; `zh` → has `p`; `both` → both. Words added from 読解 ("カードに追加") bypass `card_eligible` but not the target filter.
Front of card: `w.j` is always shown; `w.jr` and `w.k` shown only if non-empty. Card shows `alt` line when `h !== j`.

### 3.2 `RULES` (音のルール) ← `kb.rules`
Exactly the prototype shape: `{id, jong, kr, vi:[...], label, jp, zh, ex:[[char, ko, ja, vi, zh], ...]}`.
- `ex[i]` = `[chars.trad, chars.ko, chars.ja_on, chars.vi, chars.pinyin]` for rule-pairs (D7) — `ex[0]` is the progress-tracking key (`kb_rules`), so it must be unique within a rule.
- Max 8 examples per rule; prefer low `level`, then (for word-derived pairs) high frequency; deterministic order; **one char per example** (the quiz's `ex[0]` is a single character, shown in 96px).
- Examples chosen only from pairs where the Vietnamese final is in the rule's `vi` list (no exceptions in the quiz). Exceptions are in `rules_report.csv` and are not shown in this run.
- The rule needs at least 4 examples to quiz (the quiz uses 3 options and the "done" pool). If a rule has fewer, build fails.
- `NONE_RULE` and `viFinal()` stay in the app, same values as `config/rules.json`.

### 3.3 `FF` (偽の友達) ← `words` with `false_friend` ≠ '' + `ff_meanings`
| prototype field | source |
|---|---|
| `w` | `jp` else `trad` of the word (display) |
| (new) `id` | `word_id` — replaces `w` as the open/closed key (`ffopen`, `data-w`) (D13) |
| `safe` | `ff_meanings` rows with `is_trap=false`, order ja, ko, zh, vi: `[label, reading, meaning_ja]` |
| `trap` | rows with `is_trap=true`: `[label, reading_display, meaning_ja]` |
| `t` | `zh` if `zh` in `false_friend`, else `vi` if in it, else the first listed language (filter button shows words with `t===lang`; the すべて tab shows all) |

`label`: ja→`日`, ko→`韓`, zh→`中`, vi→`越`.
`reading_display` for traps: zh → `"<simp> <pinyin>"` when `simp` differs from `jp`/`trad`, else `<pinyin>` (prototype: `勉强 miǎnqiǎng`, `gōngfu`); vi → `vi`; ja → `ja`; ko → `ko`.
Tile line for a safe language = `meaning_ja` if non-empty, else the reading (prototype `s[2]||s[1]`).
The speaker button on a trap uses the first Hanzi token of `reading_display` (zh) or the Vietnamese (vi) — as in the prototype.

### 3.4 `PASSAGES` (読解) ← `passages`
| prototype field | source |
|---|---|
| `id` | `passage_id` |
| `lang` | `lang` |
| `name` | label + sequence number inside the language, ordered by `level` then `passage_id`: `越 1`, `越 2`, … / `中 1`, … (as the prototype) |
| `tr` | `translation_ja` |
| `toks[i].t` | token `t` |
| `toks[i].w` | WORDS-shaped object (§3.1) built from `words[word_id]` (ANY word, not only card-eligible) |
| `toks[i].g` | `gloss_ja` |
| `toks[i].x` | `1` when `punct` |

Passage order = language (vi first, then zh, as in the prototype), then `level`, then `passage_id`. Default selected passage = the first.
With dozens of passages the `#psel` segmented control must wrap onto several lines (CSS `flex-wrap:wrap` only) — the one allowed visible difference (data-forced, Global Rule 10).

### 3.5 `GLYPHS` (字体) ← `chars` where not (`jp == key_char == simp`)
Row = `[jp, key_char, simp, pinyin_display, ja_display, ko_display, vi_display]` (the second field is `key_char`, which equals `trad` except for `着`; D37) where
- `pinyin_display` = `pinyin_all` joined with `" / "`; `ja_display` = `ja_on_all`; `ko_display` = `ko_all`; `vi_display` = `vi_all`, each joined with `" / "` (as `'lè / yuè'`, `'らく / がく'`).
- Empty reading → `''` (render empty, never "undefined").
- Order: `level` ascending (empty last), then `char_id`.
- `pat()` and the quiz logic use indexes 0,1,2 exactly as the prototype. Quiz pool = rows with `jp != simp`; wrong options are `simp` of other rows.

### 3.6 Keys the app writes to localStorage (unchanged names)
`kb_srs` (key = `word_id`), `kb_custom` (array of `word_id`; prototype stored whole word objects), `kb_target`, `kb_auto`, `kb_rules` (per rule: array of `ex[0]` chars), `kb_glyph`, `kb_ex_open`.
Because the key type changes, the app reads old-format values defensively (ignore entries that are not known `word_id`s).

## 4. Hard failure conditions (build must stop, not warn)
- Duplicate key in any table; `tokens.word_id` not in `words`; a `ff_meanings.word_id` not in `words`; a rule with < 4 examples; a token or field that would render `undefined`/`NaN` in the app; non-NFC text in any final table.
