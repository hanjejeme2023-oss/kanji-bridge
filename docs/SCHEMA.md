# SCHEMA: contract between agents (Claude-owned)

Written in Stage 0 (2026-11-04). `final-data-spec.md` defines *what*; this file fixes the exact columns, types, IDs and the shapes the app reads.
If this file and the spec disagree, the spec wins, except where DECISIONS.md D12–D17 (spec addenda) say otherwise.

## 0. Global conventions

- UTF-8, NFC. CSV: `to_csv(index=False, encoding="utf-8")`, header row, `;` separates multi-values inside a cell.
- **Missing = empty cell in CSV, `null` in JSON, key omitted in `data.js`.** Never `"NaN"`, `"None"`, `"undefined"`, `"-"`.
- Booleans: CSV `true`/`false` (lowercase); JSON `true`/`false`.
- IDs: `c00001` (chars), `w00001` (words), `p0001` (passages). Assigned once in `pipeline/id_map.csv` (columns `kind,key,id`); keys: chars = `key_char` (D37); words = `trad|pinyin` for HSK words, `x|trad` for every other word (`vi_freq`, `ff_only`; D46, because their readings can change when sources are added); passages = `lang|level|n`, where `n` is the passage's 1-based position in the accepted task-3 output **before** `config/task3_review.csv` drops, so a drop never renumbers another passage (D70). Every final ID, including `ff_only` words and passages, comes from `id_map.csv`; a key is never used as an ID (D70). Rebuild reuses IDs; new rows get the next free number; IDs are never reused or renumbered.
- Pinyin: tone marks, lowercase, syllables joined without spaces in `words.pinyin` (`xuéshēng`), apostrophes kept (`píng'ān`; D41). `chars.pinyin` is one syllable.
- Vietnamese: NFC, lowercase, modern tone placement (D25: `thủy`, `hòa`, not `thuỷ`, `hoà`), syllables separated by one space (`học sinh`). Korean: Hangul, no spaces inside a word.
- Japanese kana: `chars.ja_on*` hiragana (KANJIDIC2 katakana converted). `words.ja` keeps JMdict's script, so loanwords are katakana; the single-character fallback is hiragana (D42).
- `lang` codes: `ja`, `ko`, `zh`, `vi`. App labels: ja=日, ko=韓, zh=中, vi=越.

## 1. Tables (columns in order)

### 1.1 `chars` — one row per source character (unique keys `char_id`, `key_char`; D37)
| col | type | rule |
|---|---|---|
| char_id | str `cNNNNN` | |
| trad | str, 1 char | Chinese traditional form, used to match HSK words. **Not unique**: hsk30 `着` and `著` are separate rows that both have `trad=著` (D37). Unique key = `char_id` |
| key_char | str, 1 char | the character whose Unihan / KANJIDIC2 / libhangul / Kaikki entries supply this row's readings; unique; **equals `trad` for every row except rows whose `trad` is shared with another row, where it is the source Hanzi (`着`; the row `著` keeps `著`)**. `id_map.csv` key for chars (D37) |
| simp | str, 1 char | = `trad` if no simplification |
| jp | str, 1 char | Japanese form (shinjitai), = `trad` if unchanged. Mapping method: DECISIONS (Stage 1 review) |
| ja_on / ko / pinyin / vi | str | primary reading (D6). May be empty. `ko`, `vi` come from word evidence after Stage 3; `ja_on` stays KANJIDIC2 first and `pinyin` stays `kMandarin` first (D39) |
| ja_on_all / ko_all / pinyin_all / vi_all | str | `;`-separated, primary first, de-duplicated. D39 reorders, never adds or drops |
| ko_base_all | str | `ko_all` without readings that are only 두음 forms of another `ko_all` reading: a reading is removed if it is a D39 form of another listed reading and has no later-position evidence (樂 `락;악;요`, 歷 `력`, 怒 keeps `노;로`). Primary first. For the glyph view (§3.5) |
| ko_final | str | one of `ㄱ ㄴ ㄹ ㅁ ㅂ ㅇ` or other final jamo; empty = no final |
| vi_final | str | one of `c ch p t n m ng nh`; empty = open syllable |
| in_hsk_chars | bool | in the HSK 3.0 character list |
| level | int 1–7 | hsk30-chars `Level` (`7-9` is stored as **7**, D29); else min `words.level` of words using the character; empty if none (D14, D29) |
| gloss_en | str | Unihan kDefinition, for reference only |
| source_ko / source_vi / source_ja / source_pinyin | str | source tag of each primary reading, recomputed when D39 changes it. `source_vi` ∈ `kaikki_aligned` / `kaikki_en_char` (7C chữ Hán reading, only when `config/vi_sources.json` switches it on, D55) / `unihan_hvsyl` / `unihan_unverified` (D24). `unihan_unverified` readings are excluded from word composition and sound-rule pairs |

### 1.2 `words` — one row per word
| col | type | rule |
|---|---|---|
| word_id | str `wNNNNN` | SRS key |
| trad / simp | str | from hsk30 (or the source that added the word) |
| jp | str | Japanese written form from matched JMdict entry; else built per character from `chars.jp`; empty if not a Japanese word |
| ja | str | Japanese reading as JMdict gives it (hiragana, or katakana for loanwords); for a single-character word with no on'yomi in JMdict, `chars.ja_on` (D42); empty if the form has no JMdict entry |
| ja_common | bool | the top-ranked JMdict pair for the form has a priority tag (D42); false if the form has no entry |
| ko | str | Hangul |
| pinyin | str | one value; for an `ff_only` word the first CC-CEDICT value of `ff_candidates.pinyin` (D70) |
| vi | str | |
| ja_alt / ko_alt / vi_alt | str | `;`-separated other readings; empty if none (D14) |
| pos / hsk_ids | str | HSK part of speech (union) and source IDs, `;`-separated (D41); empty for non-HSK words |
| gloss_en | str | CC-CEDICT first gloss(es), reference only |
| gloss_ja_en / gloss_ko / gloss_vi | str | first JMdict sense (English), hanja.txt comment, first Kaikki gloss (for `source_vi=kaikki_en_han`: the English-Wiktionary first gloss, in English, D53); input for Stage 4, not in `data.js` (D48) |
| meaning_ja__ja / __ko / __zh / __vi | str | Japanese-language meaning as used in that language (Gemini, Stage 4); empty if language missing |
| note_ja | str | optional one-line note in Japanese (e.g. "日本語・韓国語では普通カタカナで…"); mostly empty (D14) |
| level | int 1–7 | HSK level (`7-9` stored as 7, minimum if the word repeats, D29, D41), or frequency-band level 3–7 for VI-only words (D27, D46); empty for `ff_only` |
| freq_vi | int | Vietnamese frequency rank (dense, 1 = most frequent, D44); empty if the word has no `vi` or a syllable is not in the list |
| origin | `hsk` / `vi_freq` / `both` / `ff_only` | |
| card_eligible | bool | D11 |
| false_friend | str | `;`-separated lang codes where meaning differs from the others, e.g. `zh` or `ko;zh`; empty = not a false friend |
| syl_aligned | bool | true when `word_chars` gives a full Korean AND Vietnamese syllable alignment (D14) |
| verified | bool | |
| ja_use / ko_use | `used` / `rare` / `wrong_meaning` / '' | Stage 4 task 5 after `config/task5_review.csv` (D66, D67). '' = not checked: empty reading, single character, or (`ja_use`) `ja_common=true` / `ff_only` form, which JMdict marks common. `rare` → the reading is displayed in （ ）, the language's meaning is dropped, it leaves `false_friend`, and its `ff_meanings` row becomes a fixed-note row (D68 item 3); `wrong_meaning` → meaning and false-friend entry dropped, reading shown normally |
| vi_use | `common` / `literary` / `unsure` / '' | task 5 (D67 item 4); data only in this run, not read by the app |
| source_ja / source_ko / source_pinyin / source_vi / source_level | str | provenance tags. `source_vi` ∈ `kaikki_han` / `composed_attested` (D24) / `kaikki_en_han` (rule A2, D53); `source_ja` ∈ `jmdict` / `kanjidic2_on` (D42); a word with only a built `jp` (D31) has `ja` empty, and `built_from_chars` tags that form; `source_ko` ∈ `libhangul` / `libhangul_variant` (D43); `source_level` ∈ `hsk30` / `vi_band`. A value set by `overrides.csv` keeps its source tag; the override file records the reason. A `words` `vi` override may have an empty value, which clears `vi` (D55) |

### 1.3 `word_chars`
`word_id, position (int, 1-based), char_id, pinyin_syllable, ko_syllable, ko_base, vi_syllable`. `ko_syllable` is as written in the word (역), `ko_base` is the D39 form (력); a language the word lacks leaves the syllable empty, which is not a mismatch (D45). A word's character at each position is matched to `chars` by the word's own `trad` string (D38): rows whose `trad` equals the character; if none, the row whose `key_char` equals it; if several (`trad` collision, D37), by the word's `simp` at that position, then by pinyin; undecidable cases leave `char_id` empty and go to `char_ambiguous.csv`. Position check: the linked row's `simp` equals the word's `simp` at that position, else the word goes to `char_simp_mismatch.csv`.
Unique on `(word_id, position)`. A word with a syllable-count mismatch gets rows with empty syllables for that language and `syl_aligned=false`, and is listed in `data/final/alignment_mismatches.csv` with a reason (D45; no guessing).

### 1.4 `ff_meanings`
`word_id, lang, reading, reading_display, meaning_ja, is_trap`. Unique on `(word_id, lang)`. `reading` is copied from the dictionary column of the same language (`words.ja` / `ko` / `pinyin` / `vi`), never generated. At most one row per language per word. `reading_display` is '' except (D68): (a) a `ja`/`ko` row whose `ja_use`/`ko_use` is `rare` → the fixed text of `config/ff_fixed_notes.csv` for that language (ja 「（日本語ではほぼ使わない）」, ko 「（韓国語ではほぼ使わない）」), with `meaning_ja` = '' and `is_trap=false`; (b) every `config/ff_static.csv` row → its reading cell verbatim (D70: the prototype text, e.g. 勉強 韓 「（普通は 공부 と言う）」, 手紙 中 `手纸 shǒuzhǐ`, 娘 日 `むすめ`, which is `ja_alt`; validated against the dictionary readings, D67 item 5). Static rows win over (a).

### 1.5 `passages`
`passage_id, lang (zh|vi), level, translation_ja, tokens`.
CSV stores `tokens` as a JSON string; JSON/`data.js` as an array. Token = exactly one of:
- `{"t": "...", "word_id": "w00001"}` linked word
- `{"t": "...", "gloss_ja": "..."}` function word
- `{"t": "...", "punct": true}` punctuation

### 1.6 `rules` (build-time, exported to `data.js` and `rules.json`-shaped)
Not a pandas table to maintain: `config/rules.json` text + examples computed from aligned pairs (D7). Exported as the exact `RULES` shape (§3.2).

### 1.7 Reports (not read by the app)
`rules_report.csv` (pivot ko_final × vi_final of distinct pairs, D45), `rules_examples.csv`, `char_key_collisions.csv`, `char_ambiguous.csv` (D37), `char_simp_mismatch.csv` (D38), `char_primary_changes.csv`, `char_primary_no_evidence.csv` (D39), `coverage_report.csv` (incl. `freq_vi_basis=syllable_min`, D26), `merge_report.csv`, `alignment_mismatches.csv` (D45), `cedict_unmatched.csv` (D41), `ja_multi_candidates.csv` (D42), `ko_multi_candidates.csv`, `ko_unresolved.csv` (D43), `vi_ambiguous.csv` (words with no single Vietnamese value after D44, or a rule-B value dropped by D51; columns as now plus `reason` = `several_candidates` / `rule_b_conflict` / `obsolete_only` (D53) / `override_cleared` / `override_replaced` (a `vi` value removed or replaced by `overrides.csv`, D55; such a value never goes to `vi_alt`)), `vi_only_report.csv` (`han, trad, word_id, vi_values, source_vi, selected, reason, freq_score, rank, level`; `source_vi` = `kaikki_han` or `kaikki_en_han` (D53); `han` is Kaikki's form, `trad` the final word form, D46, D51), `no_jp_form.csv` (characters without a Japanese form, D28). `data/staging/ff_candidates.csv` has the columns in D47.

### 1.8 Stage 3 merges (D40; `merge_report.csv` logs every line)
| Left | Right | Key | `validate` | Expected |
|---|---|---|---|---|
| expanded hsk30 (11,110) | none: group by `(trad, pinyin)` | | unique after | 11,028 rows |
| words | CC-CEDICT | `cedict_key` | `m:1` | 10,974 `both`; 54 go to the D41 fallback, 35 stay unmatched |
| words | Kaikki rule-A Han forms (deduped, 3,366) | `trad` | `m:1`, `how="outer"`, `indicator` | `right_only` feeds D46 candidates (about 1,670 pairs, about 1,212 pass) |
| words (`trad`, `pinyin`) | `ja_match` | word key | `1:1` | about 5,650 |
| words | `ko_match` | word key | `1:1` | about 7,100 |
| words | `vi_match` | word key | `1:1` | about 3,870 |
| words (all, HSK + VI-only) | `kaikki_en_match` (rule A2, D53; one row per word key with an A2 value) | word key | `1:1`, `indicator` (`words_kaikki_en`) | 4,377 `both` at the D53 build; A2 fills `vi` only where it is still empty |
| characters of words | `chars` | D37/D38 linking, not a plain merge | row count = sum of word lengths | 0 unlinked; about 190 new rows |
Each `*_match` table holds one row per word key, so a form with several dictionary entries can never multiply rows.

### 1.9 `examples` (Stage 4 task 6, D72; written by the app-phase merge after task 6 is accepted)
`word_id, lang (zh|vi), use (card|ff), sentence, pinyin, translation_ja, target, target_start (int, 0-based character index), target_len (int)`. Unique on `(word_id, lang, use)`. `pinyin` is the whole-sentence pinyin for zh and '' for vi. `target` = `words.simp` (zh) or `words.vi` (vi); `target_start` is the first occurrence found by code (vi case-insensitive). One row per accepted task-6 sentence item after `config/task6_review.csv` and rerun rounds; no row for `no_sentence`, dropped or never-validated items. 偽の友達 uses the `ff` row of the word and language, else its `card` row (`docs/TASK6_DESIGN.md` §1, §7).

### 1.10 `char_notes` (Stage 4 task 6, D72)
`char_id, note_ja`. Unique on `char_id`; only non-empty accepted notes (one line, ≤ 60 characters, Japanese; may name an everyday Chinese or Vietnamese word). Shown in the 字体 使われ方 panel (D71 item 6).

## 2. `data.js` shape

```js
window.KB_DATA = {
  meta:   { built: "YYYY-MM-DD", counts: {chars: n, words: n, ...} },
  chars:  [ { char_id, trad, key_char, simp, jp, ja_on_all, ko_base_all, pinyin_all, vi_all, in_hsk_chars, level }, ... ],  // only columns the glyph view needs, see §3.5
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
- **D71 item 9 (app phase):** the build also copies `data.js` to `app/data.js` and `app/index.html` loads `<script src="data.js">`, so the `app/` folder runs alone. **D72 (app phase):** `examples` and `char_notes` are added (compact arrays); the D71 views may need more `chars` rows (single-character card words in 字体) and more `word_chars` columns/rows (使われ方 examples). Claude writes the exact §2/§3 changes when assigning the app phase; re-measure size and load time then (D71 item 12).

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
| `jr` | `ja`, as `（ja）` when `ja_use=rare` (D67) | `''` (render nothing) |
| `k` | `ko`, as `（ko）` when `ko_use=rare` (D67) | `''` |
| `v` | `vi` | `''` |
| `va` (new, optional) | `vi_alt` split on `;` | omit; `judge()` for Vietnamese also accepts these (D14) |
| `note` | `note_ja` | omit |
| `syl` (new) | `syl_aligned` + `word_chars` | `ruleTags` shows tags only when `syl` true, iterating `word_chars` instead of `[...w.k]` / `w.v.split(' ')`; it never reads the displayed `k`, and strips `（ ）` and `( )` from `k` wherever it would (user-approved exception to Global Rule 10, D67 item 3) |

Deck rule: `card_eligible`, ordered by `level` then `freq_vi` (nulls last) then `word_id`. Due list is filtered by the target switch: `vi` → word has `v`; `zh` → has `p`; `both` → both. Words added from 読解 ("カードに追加") bypass `card_eligible` but not the target filter.
Front of card: `w.j` is always shown; `w.jr` and `w.k` shown only if non-empty. Card shows `alt` line when `h !== j`.

### 3.2 `RULES` (音のルール) ← `kb.rules`
Exactly the prototype shape: `{id, jong, kr, vi:[...], label, jp, zh, ex:[[char, ko, ja, vi, zh], ...]}`.
- `ex[i]` = `[chars.key_char, chars.ko, chars.ja_on, chars.vi, chars.pinyin]` for rule-pairs (D7); only pairs where `ko_base` = `chars.ko` and `vi_syllable` = `chars.vi`, so the shown readings are the pair's (D45) — `ex[0]` is the progress-tracking key (`kb_rules`), so it must be unique within a rule.
- Max 8 examples per rule; prefer low `level`, then (for word-derived pairs) high frequency; deterministic order; **one char per example** (the quiz's `ex[0]` is a single character, shown in 96px).
- Examples chosen only from pairs where the Vietnamese final is in the rule's `vi` list (no exceptions in the quiz). Exceptions are in `rules_report.csv` and are not shown in this run.
- The rule needs at least 4 examples to quiz (the quiz uses 3 options and the "done" pool). If a rule has fewer, build fails.
- `NONE_RULE` and `viFinal()` stay in the app, same values as `config/rules.json`.

### 3.3 `FF` (偽の友達) ← `words` with `false_friend` ≠ '' + `ff_meanings`
| prototype field | source |
|---|---|
| `w` | `jp` else `trad` of the word (display) |
| (new) `id` | `word_id` — replaces `w` as the open/closed key (`ffopen`, `data-w`) (D13) |
| `safe` | `ff_meanings` rows with `is_trap=false`, order ja, ko, zh, vi: `[label, reading_display \|\| reading, meaning_ja]` (a fixed-note row has an empty meaning, so the tile shows the note: D68) |
| `trap` | rows with `is_trap=true`: `[label, reading_display, meaning_ja]` |
| `t` | `zh` if `zh` in `false_friend`, else `vi` if in it, else the first listed language (filter button shows words with `t===lang`; the すべて tab shows all) |

`label`: ja→`日`, ko→`韓`, zh→`中`, vi→`越`.
`reading_display` for traps (the stored `ff_meanings.reading_display` when non-empty, i.e. a static row; otherwise computed): zh → `"<simp> <pinyin>"` when `simp` differs from `jp`/`trad`, else `<pinyin>` (prototype: `勉强 miǎnqiǎng`, `gōngfu`); vi → `vi`; ja → `ja`; ko → `ko`.
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
- `pinyin_display` = `pinyin_all` joined with `" / "`; `ja_display` = `ja_on_all`; `ko_display` = `ko_base_all` (so 歷 shows `력` and 樂 starts `락 / 악`, as in the prototype; PROMPT Stage 5 says `*_all`, this is the D39 refinement); `vi_display` = `vi_all`, each joined with `" / "` (as `'lè / yuè'`, `'らく / がく'`).
- Empty reading → `''` (render empty, never "undefined").
- Order: `level` ascending (empty last), then `char_id`.
- `pat()` and the quiz logic use indexes 0,1,2 exactly as the prototype. Quiz pool = rows with `jp != simp`; wrong options are `simp` of other rows.

### 3.6 Keys the app writes to localStorage (unchanged names)
`kb_srs` (key = `word_id`), `kb_custom` (array of `word_id`; prototype stored whole word objects), `kb_target`, `kb_auto`, `kb_rules` (per rule: array of `ex[0]` chars), `kb_glyph`, `kb_ex_open`.
Because the key type changes, the app reads old-format values defensively (ignore entries that are not known `word_id`s).

## 4. Hard failure conditions (build must stop, not warn)
- Duplicate key in any table; an `overrides.csv` value that is not a dictionary candidate for that word or character (D43); `tokens.word_id` not in `words`; a `ff_meanings.word_id` not in `words`; a rule with < 4 examples; a token or field that would render `undefined`/`NaN` in the app; non-NFC text in any final table.

## 5. Stage 4 content files (D54, D58, D59)
Written only by the Stage 4 script (Codex's code, Gemini's content); read by the Stage 4 merge (Codex). `run_all.py` never calls the API; `content/` is a pipeline input (Global Rule 4). All files UTF-8, NFC, committed. **No folder may be named `raw`** (`.gitignore`).

| Path | Content |
|---|---|
| `content/prompts/task<N>_v<k>.md` | prompt text; a changed prompt gets a new version file |
| `content/inputs/task<N>/b<NNN>.jsonl` | the exact items sent, built deterministically from the frozen tables |
| `content/generated/task<N>/b<NNN>.jsonl` | model output, one JSON object per item |
| `content/generated/task<N>/b<NNN>.log.json` | `model`, `location`, settings, `prompt_sha256`, `input_sha256`, usage (input / output / thinking tokens), `usd`, attempts, validation result, timestamp |
| `content/generated/pilot/` | pilot run (Stage 4a); never merged |
| `content/accepted/task<N>/` | batches accepted at the Stage 4 gate (Claude moves them); the merge reads only this |
| `content/cost_log.csv` | one row per request: `timestamp, task, batch, attempt, model, input_tokens, output_tokens, thinking_tokens, usd` |

**Output objects** (enforced by the API schema and re-validated locally; no object has a reading field, readings are copied from the tables at merge):
- Task 1 (one per `card_eligible` word): `word_id, meaning_ja__ja, meaning_ja__ko, meaning_ja__zh, meaning_ja__vi, meanings_differ (bool), vi_check (same_word | different_word | unsure | ""), vi_check_reason, confidence (high | low), low_reason`. A meaning is non-empty exactly when that language's reading (`ja`, `ko`, `pinyin`, `vi`) is non-empty, except `vi_check=different_word` → `meaning_ja__vi` empty. → `words.meaning_ja__*`.
- Task 2: `key` (`word_id`, or `form` for an `ff_candidates.csv` row), `false_friend` (list of lang codes), `meanings` (`[{lang, meaning_ja, is_trap}]`, one per language present), `confidence`, `low_reason`. → `words.false_friend` (`;`-joined), `ff_meanings` (§1.4; `reading` copied from the table), `ff_only` words (IDs `x|trad`). For the 12 prototype false friends, `config/ff_static.csv` (D67 item 5) replaces the generated rows of the languages it has.
- Task 3: `passages` = `[{translation_ja, tokens}]`, tokens as §1.5. → `passages` (IDs `lang|level|n`).
- Task 5 (D66, D67): `key, ja_check, ja_reason, ko_check, ko_reason, vi_use, vi_reason`; a check is non-empty exactly for the languages in the item's `checks`; `ja_check`/`ko_check` ∈ `used | rare | wrong_meaning | unsure`, `vi_use` ∈ `common | literary | unsure`; a reason is empty iff its check is `used`/`common`. → `words.ja_use`, `ko_use`, `vi_use` after `config/task5_review.csv` (an `unsure` left by the review counts as `rare` / `literary`); reasons are review-only and never copied into `data/final/`. **D68:** for task 5 the Hangul/Latin-letter rule on reasons is a warning (`reason_warnings` in the batch log), not a failure; every other task-5 rule stays fail-closed.
- **Task 6 (D72, `docs/TASK6_DESIGN.md`):** one object per item, three schemas by batch kind: zh `key, status, sentence, pinyin, translation_ja, confidence, review_note`; vi `key, status, sentence, translation_ja, confidence, review_note`; note `key, note_ja, confidence, review_note`. Keys `{word_id}:{zh|vi}:{card|ff}` and `{char_id}:note`. `status` ∈ `ok | no_sentence`. Item-level repair requests and rerun rounds (`content/generated/task6/rerun<N>/`, `config/task6_rerun.csv`) are logged per request. → `examples`, `char_notes` (§1.9, §1.10) after `config/task6_review.csv`; `review_note` and `confidence` are review-only.
- Task 4: `word_id, note_ja` (one line, ≤ 80 characters). → `words.note_ja`; `config/word_notes.csv` (`word_id, note_ja`, static text, e.g. 越南 from the prototype, D14) comes first when a word has both.

Review-only fields (`meanings_differ`, `vi_check`, `vi_check_reason`, `confidence`, `low_reason`) stay in `content/` and are not added to `words`; `verified` = true for words whose task-1 batch was accepted at the Stage 4 gate.
