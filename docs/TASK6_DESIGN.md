# Stage 4 task 6: example sentences and character usage notes (design, D72)

Claude, 2026-11-11. Contract for Codex (task-6 support), the user (pilot and run) and Claude (pilot review, gate). Decisions: D71 (user's app decisions), D72 (this design). Counts are from `data/final/` at `8e41236`.

**Hard date:** every Gemini request must be sent before **2026-11-16 00:00 America/Los_Angeles = 2026-11-16 08:00 UTC**. After that, Google's Free Trial credit no longer pays for Vertex/Gemini unless the account is upgraded (Google email, reported by the user 2026-11-11). The user may upgrade on 11/14 if the work is late; otherwise the runner refuses (§6.5).

## 1. Scope and counts

| Kind | Items | Batches (50) | Source |
|---|---:|---:|---|
| `zh` card sentences | 5,783 | | multi-character `card_eligible` words, `origin` ∈ {`hsk`, `both`}, `pinyin` ≠ '' |
| `zh` false-friend sentences | 565 | | `ff_meanings` `lang=zh` rows not covered by a card item (below) |
| **zh total** | **6,348** | **127** | |
| `vi` card sentences | 4,051 | | multi-character `card_eligible` words with `vi` ≠ '' (all origins) |
| `vi` false-friend sentences | 142 | | `ff_meanings` `lang=vi` rows not covered by a card item |
| **vi total** | **4,193** | **84** | |
| **notes** (字体 usage notes) | **623** | **13** | §2.3 |
| **Total** | **11,164** | **224** | |

**False-friend coverage rule (decides "conflict" by code, no model judgment).** A false-friend row (`ff_meanings`, `lang` ∈ {zh, vi}) is covered by the word's card item of the same language when that card item exists **and** the card meaning (`words.meaning_ja__zh` / `__vi`) is the **identical string** to the row's `meaning_ja`. The card item then carries the row's `is_trap` and contrast meaning, and its sentence serves both the card and the 偽の友達 entry. Otherwise the row gets its own `ff` item.
- zh: 1,190 rows; 645 have a card item, 625 with the identical meaning → covered; **20** differ + 545 without a card item (279 `ff_only`, 117 `vi_freq` words, 149 single characters) = **565** `ff` items.
- vi: 618 rows; 484 have a card item, 476 identical → covered; **8** differ + 134 without a card item (85 single characters, 49 `ff_only`) = **142** `ff` items.
- So all 963 false-friend card words and all 279 `ff_only` words get a sentence for every language whose row exists (1,190 zh + 618 vi rows; every row has a reading). The 117 `vi_freq` words with a Chinese false-friend row are included because 偽の友達 shows a Chinese meaning for them; like every item they may come back `no_sentence` (§3).
- Single-character card words (1,571) get **no card sentence** (they move to 字体, D71 item 1); 字体 uses existing words as examples (D71 item 6) and the notes below.

## 2. Item builder (`pipeline/stage4/builders.py`, `build_task6_items()`)

Reads only `data/final/words.csv`, `ff_meanings.csv`, `chars.csv`, `word_chars.csv`, and only columns that the task-6 merge never writes (the merge adds new tables, §7), so a rebuild after the merge reproduces the same inputs. Deterministic; NFC; no API call. Fails closed: a card zh item with empty `simp`/`meaning_ja__zh`, a vi item with empty `meaning_ja__vi`, a duplicate key, a field-order difference.

### 2.1 Sentence items

Key: `{word_id}:{lang}:{use}`, `use` ∈ `card` / `ff` (e.g. `w01644:zh:card`, `w13085:zh:ff`).

| Field (in this order) | zh | vi |
|---|---|---|
| `key` | ✓ | ✓ |
| `target` | `words.simp` | `words.vi` (= `ff_meanings.reading` for `ff`; equal for all 618 rows) |
| `target_pinyin` | `words.pinyin` (= `ff_meanings.reading`; equal for all 1,190 rows) | — |
| `trad` | ✓ | ✓ |
| `meaning_ja` | card: `meaning_ja__zh`; ff: the row's `meaning_ja` | card: `meaning_ja__vi`; ff: the row's `meaning_ja` |
| `is_trap` | bool: the covering/own `ff_meanings` row's `is_trap`; `false` if the word has no row | same |
| `contrast_meaning_ja` | when `is_trap`: `meaning_ja` of the first `ff_meanings` row of the same word with `is_trap=false` and non-empty `meaning_ja`, in the order ja, ko, zh, vi (skipping the item's language); else '' | same |
| `vi_use` | — | `words.vi_use` |
| `level` | `words.level` as a string ('' for `ff_only`) | same |
| `pos` | `words.pos` | — |

Order: zh card (level ascending, then `word_id`), zh ff (`word_id`), vi card, vi ff (same), notes. Each kind is chunked into batches of **50** separately; batch names continue across kinds: **zh b001-b127, vi b128-b211, notes b212-b224** (Codex's dry-run prints the exact boundaries).

### 2.2 Japanese/Korean are never sentence languages
No ja/ko sentences (D71: only Chinese and Vietnamese).

### 2.3 Note items (字体 usage notes)

字体 character set (D71 item 1): glyph rows (`chars` where not `jp == key_char == simp`, 1,246) ∪ characters of single-character `card_eligible` words (1,571 words, 1,520 characters, 602 already glyph rows) = **2,164 characters** (2,215 rows if each polyphone card word keeps its own row; the app design decides, D71).

Example words, as the 使われ方 panel will show them (D71 item 6), from `word_chars` by `char_id`:
- **zh examples:** multi-character words with `origin` ∈ {hsk, both}, `pinyin` ≠ '' and a `pinyin_syllable` at that position; order `level`, `word_id`; first 3. Fields `simp`, `pinyin`.
- **vi examples:** multi-character `card_eligible` words with `vi` ≠ '' and a `vi_syllable` at that position; order: `vi_use=literary` last, then `level`, `freq_vi` (empty last), `word_id`; first 3. Fields `trad`, `vi`, `literary` (bool).

A character is a note item when it is in the 字体 set and **any** of:
- **N1 `vi_examples_literary` / `vi_single_literary`:** `chars.vi` ≠ '' and (it has vi examples and **every** one is `literary`, or its own single-character card word has `vi_use=literary`) — 506 characters, any level;
- **N2 `vi_no_examples`:** `chars.vi` ≠ '', no vi example, `chars.level` ≤ 4 — 106 more;
- **N3 `zh_no_examples`:** `chars.pinyin` ≠ '', no zh example, `chars.level` ≤ 4 — 11 more.

**623 items.** `reason` lists the first matching rule (N1 split into its two names). Fields in order: `key` (`{char_id}:note`), `char` (`key_char`), `simp`, `jp`, `pinyin` (`chars.pinyin`), `vi` (`chars.vi`), `meaning_en` (`chars.gloss_en`, first 80 characters), `zh_examples` (list of `{simp, pinyin}`), `vi_examples` (list of `{trad, vi, literary}`), `vi_single_use` (the single-character card word's `vi_use`, else ''), `reason`. Order `chars.level`, `char_id`. A note may come back empty (nothing useful to add).

## 3. Output schemas (`propertyOrdering` in this order; strings unless stated; no other keys)

- **zh:** `key, status, sentence, pinyin, translation_ja, confidence, review_note`
- **vi:** `key, status, sentence, translation_ja, confidence, review_note`
- **note:** `key, note_ja, confidence, review_note`
- `status` ∈ `ok` / `no_sentence`; `confidence` ∈ `high` / `low`. The response is a JSON array with one object per input item, in input order. Prompts: `content/prompts/task6_zh_v1.md`, `task6_vi_v1.md`, `task6_note_v1.md` (**amended by D73 after the pilot: zh and vi use `task6_zh_v2.md`, `task6_vi_v2.md`; notes stay v1**), selected per batch kind (as task 3 selects per language). `review_note` is review-only and never merged.

## 4. Validator (`pipeline/stage4/validators.py`, `validate_task6`)

**Batch level (whole-batch failure → normal retry):** valid JSON array; exactly the input keys, same order, no duplicates; every object has exactly the schema's keys; enum values valid.

**Item level (failure → item repair, §6.2).** All strings NFC, no leading/trailing space, no line break or tab, no Hangul (U+1100-11FF, U+3130-318F, U+A960-A97F, U+AC00-D7AF, U+D7B0-D7FF) in any field.
1. `status=no_sentence` → `sentence`, `pinyin`, `translation_ja` empty and `review_note` non-empty. `status=ok` → `sentence` and `translation_ja` non-empty; zh `pinyin` non-empty. `confidence=low` → `review_note` non-empty. `review_note` ≤ 80 characters (a non-empty note with `high`/`ok` is allowed; review-only).
2. **zh `sentence`:** only Han characters (U+3400-4DBF, U+4E00-9FFF, U+20000-2FFFF, plus 〇 U+3007) and the punctuation ，。！？、：；“”‘’《》（）—…; no Latin letter, digit, space or kana; 1-30 Han characters; last character 。！？ (optionally followed by ” or ’); contains `target` at least once; contains no **traditional-only character** = a `chars.trad`/`key_char` value whose `simp` differs and that is not the `simp` of any `chars` row nor in any `words.simp`.
3. **zh `pinyin` alphabet:** NFC; letters a-z/A-Z, the tone-marked vowels āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ, ü, apostrophe `'` (U+0027 or ’ U+2019, normalised to U+0027), space, and the punctuation , . ! ? : ; " “ ” ( ) — … only. No digits (tone numbers), no `v`, no `u:`.
4. **zh syllable alignment:** strip punctuation; split on spaces, then on apostrophes; segment each piece into syllables with the standard Mandarin syllable inventory (≈ 410 toneless syllables; compare lowercased with tone marks removed, ü kept distinct from u), each syllable optionally carrying an erhua `r` (not on `er`) and at most one tone mark. Try segmentations (dynamic programming) until one aligns: each syllable consumes one Han character of the sentence in order; an erhua syllable also consumes the next character, which must be 儿. All Han characters must be consumed exactly. No aligning segmentation → invalid (`pinyin does not align with the characters`).
5. **zh target pinyin:** for some occurrence of `target`, the aligned syllables joined (lowercase, apostrophes and spaces removed) equal `target_pinyin` normalised the same way, **tone marks included** (e.g. 一点儿 → `yīdiǎnr`, 东西 → `dōngxi`). If several segmentations align and they differ at the target, invalid.
6. **zh sandhi:** every 一 aligns to `yī` or `yi`, every 不 to `bù` or `bu` (dictionary convention: 109/109 一-words and 122/122 不-words in `words.pinyin` use yī/bù).
7. **zh pinyin warning (not a failure):** a Han character whose `chars.pinyin_all` (all rows with that `simp`) is known and does not contain the aligned toneless syllable is listed in the log's `warnings` (key, character, syllable). Claude reads every warning at the gate.
8. **vi `sentence`:** letters a-z/A-Z and the Vietnamese letters (ă â đ ê ô ơ ư with every tone mark, upper and lower case), digits, space, and . , ! ? ; : " ' “ ” ‘ ’ ( ) - – … only; no Han, kana or Hangul; starts with an upper-case letter (optionally after an opening quote); ends with . ! ? (optionally followed by a closing quote); 3-25 syllables (tokens split on spaces and hyphens, punctuation removed); each syllable carries at most one tone mark (after NFD: U+0300, U+0301, U+0303, U+0309, U+0323); `target` occurs as a whole word, **case-insensitive** (casefold both; spaces in `target` match one space; no letter immediately before or after), at least once.
9. **`translation_ja`** (zh, vi): ≤ 60 characters; contains at least one hiragana, katakana or Han character; no Latin letter with a diacritic (U+00C0-024F, U+1E00-1EFF) and no other Latin letters except ASCII (for loanword abbreviations such as CD).
10. **note `note_ja`:** may be empty; if non-empty, ≤ 60 characters and contains at least one hiragana or katakana; Latin letters (incl. Vietnamese) and Han characters allowed.
11. Warnings (log only): `target` occurs more than once; zh sentence where `target` is followed or preceded by a character forming a longer `words.simp` entry (e.g. 大学 inside 大学生); empty `note_ja`.

## 5. Model and settings
Same as tasks 1-5: **`gemini-4-argon`**, Vertex AI, location `global`, ADC only (no API key; refusal if `GEMINI_API_KEY`/`GOOGLE_API_KEY` is set), temperature **0.3**, thinking at the model default, max output 65,536, timeout 600 s, structured output with the §3 schema.

## 6. Runner (`pipeline/stage4/runner.py`, launcher `run_stage4.ps1`)

1. **CLI:** `--task 6` (all pending batches), `--task 6 --batch N`, `--task 6 --dry-run` (offline: items, batches and estimated tokens/cost per kind; **no network call, not even `count_tokens`**), `--pilot6`, `--task 6 --rerun-round N`, `--status` (task 6 shown per kind: validated / partial / failed / missing; spend; room under the ceiling; time left to the credit deadline). Tasks 1-5 keep their D65 refusal. Launcher parameters: `-Tasks 6`, `-Pilot6`, `-Tasks 6 -RerunRound N`, `-AllowAfterCreditDeadline`, and the existing `-Status`, `-Check`.
2. **Item repair (new, task 6 only):** after a response passes the batch-level checks, items that fail §4 are sent again in a **repair request** containing only those items, each with `previous_error` (the validator message, English, one line); at most **2 repair requests** per batch attempt; valid items are kept. The batch is `validated` when every item is valid (`no_sentence` is valid). If items are still invalid after the repairs, the batch is `partial`: the output keeps the valid items, the log lists `failed_keys`, and the next `--task 6` resumes only those keys (as a repair). The launcher's existing automatic rerun (2 min wait, at most 2 more passes) covers `partial` like `failed`. Items still failing at the gate are dropped (no example shown).
3. **Logs and resume:** as D61 item 10, plus per-request entries (full / repair, keys, usage, cost) in the batch log and one `cost_log.csv` row per request (`attempt` like `1`, `1r1`, `1r2`). A batch is skipped only when its output and log exist, model / prompt SHA / input SHA / item count match, and the output re-validates.
4. **Ceiling:** `prices.json` `hard_ceiling` **200.0** (D71 item 11). Before every request (full and repair): spent + this request's conservative estimate (counted input tokens + **200** output tokens per item, `FALLBACK_CHARGEABLE_OUTPUT_PER_ITEM[6] = 200`) must stay ≤ $200, else stop.
5. **Credit date guard (new):** constant `CREDIT_DEADLINE_UTC = 2026-11-16T08:00:00Z` (= 2026-11-16 00:00 PST, UTC−8; daylight saving ended 2026-11-01). Use this fixed UTC instant, **not** `zoneinfo` (Windows Python has no time-zone database without the `tzdata` package). Checked before client creation and before every request of every mode (`--check`, `--pilot6`, `--task 6`, repairs, reruns, `count_tokens`). At or after it: refuse with a message that names the credit deadline and the flag. Override: `--allow-after-credit-deadline` (launcher `-AllowAfterCreditDeadline`), only after the user has upgraded. The Argon 2026-12-01 guard stays.
6. **Lock, keep-awake, User-scope variables, API-key refusal, 30/60 s API retry waits, `python -u`:** unchanged (D62).
7. **Pilot `--pilot6`:** three requests, outputs in `content/generated/pilot_task6/`, inputs in `content/inputs/pilot_task6/`; never merged. Items (deterministic, built with the §2 builder, then filtered):
   - **zh (50):** the card items of 大學 學習 銀行 新聞 經濟 發展 注意 歷史 心理 博士 勉強 主義 東西 老師 愛人 工夫 自己; the ff item of 手紙 and 大丈夫; then level-1 card items in builder order up to 40; then the first 10 level-7 card items.
   - **vi (50):** the card items of 大學 學習 銀行 經濟 發展 注意 歷史 心理 博士 勉強 主義 越南 自己 工夫 飛機 老師; the vi ff items of 大丈夫 and the first 6 single-character vi ff items; then `vi_use=literary` card items in builder order up to 40; then the first 10 `vi_freq` card items.
   - **note (50):** 幫 if selected, then the first 49 note items in builder order.
8. **Reruns after the gate:** `config/task6_rerun.csv` (Claude-owned; columns `round, key, reason`). `--task 6 --rerun-round N` builds the current items for that round's keys, adds `review_feedback` = `reason`, chunks by kind into batches of 50, writes `content/generated/task6/rerun<N>/bNNN.*`, and validates/repairs as above. A later round replaces earlier output for the same key. An unknown key fails closed.

## 7. Accepted layout, overlay and merge (merge = app phase, after acceptance)

- Claude moves accepted batches to `content/accepted/task6/` (+ `inputs/`, logs, `rerun<N>/`), as tasks 1-5.
- **Overlay `config/task6_review.csv`** (Claude's review decision; columns `key, action, generated, review, reason`), fail-closed (`generated` must equal the latest accepted output field): `drop` (no example/note shown; `generated` = sentence or note), `set_translation_ja` (corrected Japanese translation), `set_note_ja` (corrected Japanese wording of a note; Chinese/Vietnamese words in it unchanged). Claude never writes Chinese or Vietnamese sentence text: a wrong sentence is dropped or rerun.
- **Merge (Codex, offline, `run_all.py`)** adds two tables, nothing else:
  - `examples`: `word_id, lang (zh|vi), use (card|ff), sentence, pinyin (zh; '' for vi), translation_ja, target, target_start, target_len` (code finds the first occurrence; vi case-insensitive); unique `(word_id, lang, use)`; no row for `no_sentence`, dropped or never-validated items. 偽の友達 uses the `ff` row, else the `card` row of the same word and language.
  - `char_notes`: `char_id, note_ja` (non-empty only).
  - `data.js` gets both (compact arrays). Re-measure `data.js` size and load time after the merge (D71 C, about +2-3 MB expected) and decide whether to split.

## 8. Review plan (Claude gate; user sample)

The user is a native speaker of Japanese and Korean and a learner of Chinese and Vietnamese, so **Claude judges the Chinese and Vietnamese**; the user checks only the Japanese.
1. Integrity: inputs equal a fresh build; every output re-validates; ledger total; prompt SHAs.
2. Script pre-screen (`docs/review_scripts/task6_gate_reference.py`): all §4 warnings, `no_sentence` and `low` items, length outliers per level, identical or near-identical sentences across items, `target` inside a longer word, trap items whose sentence also fits `contrast_meaning_ja` (read).
3. **Read in full:** every zh card item at level 1-3 (**1,174**), every vi card item at level 1-3 (**894**), every `ff` item (**707**), every note (**623**), every `low` / `no_sentence` item and every warning. **Seeded samples** (seed recorded): 150 zh and 150 vi card items at level 4-7; 100 zh and 100 vi card items that also serve a trap entry. About 3,900 items + low/warnings, in two sittings (zh first, while vi is still running if possible).
4. Error classes: unnatural or wrong sentence; wrong sense (not `meaning_ja`); trap meaning not evident; pinyin wrong outside the target; Vietnamese spelling/tone mark wrong; literary word in a casual sentence; wrong or unnatural Japanese translation; note wrong or not useful.
5. **Decision:** every wrong item gets an overlay row (`drop`, `set_translation_ja`, `set_note_ja`) or a rerun row. A **systematic** class (≥ 5% of the items read in one kind, or one that a prompt rule can fix) → prompt v2 for that kind and a rerun round for every item of the class that code can select, else for the affected batches. One-off errors never reject a batch.
6. **User sample (about 10 minutes):** `docs/TASK6_USER_SAMPLE.md`, **30 items** (12 zh, 12 vi, 6 notes), seeded, showing the sentence, its Japanese translation and the meaning; the user marks only whether the **Japanese** is natural and helpful (○ / △ with a short comment / ×). The user is not asked to judge Chinese or Vietnamese.

## 9. Cost and run-time estimate (conservative)

Measured Argon basis (`content/cost_log.csv`): about 71-87 output tokens/s; task 1 ≈ 117 output tokens per item (four meanings and reasons). Prices: $2 / 1M input, $10 / 1M output (thinking billed as output; Argon logged 0 thinking so far).

| Kind | Requests | Input tokens | Output tokens (per item) | Base cost | Time per request | Time |
|---|---:|---:|---:|---:|---:|---:|
| zh | 127 | 0.83M (≈ 6.5k/request) | 0.95M (150) | $11.2 | ≈ 110 s | ≈ 3.9 h |
| vi | 84 | 0.48M (≈ 5.8k) | 0.50M (120) | $6.0 | ≈ 85 s | ≈ 2.0 h |
| note | 13 | 0.18M (≈ 13.7k) | 0.05M (80) | $0.9 | ≈ 50 s | ≈ 0.2 h |
| **Full run** | **224** | **1.5M** | **1.5M** | **≈ $18** | | **≈ 6 h** |

- **With margins:** repairs/retries +15%, pilot ≈ $0.4, one rerun round (≈ 10% of items) ≈ $2 → **≈ $23 expected; conservative estimate $27; worst case ≈ $36** (output twice the estimate). Ledger now $35.50 → about **$59-72 after task 6**, far below the $200 ceiling.
- **Run time:** about **6 h**, plan **6.5-7 h** with repairs and retry waits; sequential (no parallel requests: lower risk with an unknown rate limit). zh finishes about 4 h after the start.

## 10. Schedule (all requests before 2026-11-16 08:00 UTC)

| Day | Who | What |
|---|---|---|
| 11-11 | Claude | D71, D72, prompts v1, this design (done) |
| 11-12 | Codex | task-6 support, offline (builder, schemas, validator, repair, ceiling $200, credit guard, pilot, rerun rounds, dry-run, tests) |
| 11-12 | User | re-enable Vertex (`VERTEX_SETUP.md` part G), `-Check`, `-Pilot6` (3 requests, ≈ $0.4, ≈ 5 min) |
| 11-12 | Claude | pilot review; prompt v2 if needed (no cost: the full run has not started) |
| 11-13 morning | User | `-Tasks 6` (≈ 6.5-7 h) |
| 11-13 evening | Claude | gate part A: zh (when zh batches are done) |
| 11-14 | Claude, User | gate part B: vi, notes, overlay, rerun round 1 list; user sample (30 items); user runs rerun round 1 |
| **11-14 evening** | **User** | **Decision point:** if rerun + re-check cannot end before 11-16 08:00 UTC, upgrade or accept without the open items (they show no example) |
| 11-15 | Claude, User | re-check round 1; round 2 only if needed; **last request before 2026-11-15 23:59 PT**; then revoke and disable (part H) |

Then Claude assigns the app phase (D71 app changes + task-6 merge) to Codex; the Stage 5 gate (with the D71 C items) follows the app phase.

## 11. Tests Codex adds (offline)
Builder counts per kind (5,783 / 565 / 4,051 / 142 / 623) and batch boundaries; coverage rule (the 20 + 8 meaning-differs rows become `ff` items); deterministic inputs (two builds identical); every validator rule with a passing and a failing case, including erhua (一点儿 yīdiǎnr, 哪儿 nǎr), neutral tone (东西 dōngxi, 对不起 duìbuqǐ), apostrophe (Xī'ān), sandhi rejection (yíxià), a traditional-only character, the vi case-insensitive match (Việt Nam / việt nam) and a vi syllable with two tone marks; repair flow (only failing items re-sent; partial status; resume of `failed_keys`); ceiling $200; credit guard (refuses at 2026-11-16T08:00:00Z, allows 07:59:59Z, override flag) in every mode; dry-run makes no network call; rerun-round unknown key fails; tasks 1-5 still refused.
