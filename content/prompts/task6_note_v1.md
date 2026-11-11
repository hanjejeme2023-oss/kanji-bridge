# Task 6: character usage notes (v1)

You are writing short notes for the character view of a vocabulary study tool. The learner is a native speaker of Japanese and Korean and is learning Mandarin Chinese and Vietnamese. For each character, the tool shows its readings and up to three example words per language, taken from its word list. These examples can mislead: for example, the only Vietnamese words with this character may all be literary, or there may be none, while everyday speech uses a different word for the meaning.

For each input character, write **one line in Japanese** (`note_ja`) that tells the learner how the character's meaning is **actually expressed in everyday Chinese and/or Vietnamese**, when that differs from what the examples suggest. Leave `note_ja` empty when the examples already give a fair picture or you have nothing reliable to add.

## Input fields

- `key`: copy it unchanged.
- `char`, `simp`, `jp`: the character in traditional, simplified and Japanese forms.
- `pinyin`, `vi`: its main Chinese and Vietnamese readings (fixed; never change them).
- `meaning_en`: a short dictionary gloss.
- `zh_examples`: up to three Chinese example words shown (simplified form and pinyin), or empty.
- `vi_examples`: up to three Vietnamese example words shown (Han form, Vietnamese, and `literary` when the word is literary), or empty.
- `vi_single_use`: how the character on its own is used in Vietnamese: `common`, `literary`, or empty when not checked.
- `reason`: why this character was selected: `vi_examples_literary` (every Vietnamese example is literary), `vi_single_literary` (the character alone is a literary word in Vietnamese), `vi_no_examples`, or `zh_no_examples`.

## The note

- One line, at most 60 characters, plain and factual, written for a learner. Examples of the style:
  - 幫: 「ベトナム語で「手伝う」は普通 giúp đỡ と言う」
  - 飯: 「ベトナム語で「ご飯」は普通 cơm。phạn は文語」
  - 錢: 「中国語では「お金」の意味で日常的に使う（钱）」
- You may name an everyday word of the language: Vietnamese in its normal Latin spelling with all marks, Chinese in simplified characters. Name only words you are certain of; never write a reading of the character itself other than the given `pinyin` or `vi`.
- Do not repeat the example words or the readings without adding information. Do not explain the character's shape.
- No Hangul, no pinyin with tone numbers.

## `confidence` and `review_note`

- `confidence` is `high` when you are sure the note is correct; otherwise `low` (a reviewer checks every note).
- `review_note` is a short Japanese note for the reviewer (at most 80 characters), required when `confidence` is `low`, otherwise empty.

## Corrections

An item may carry `previous_error` (your earlier answer for this item failed an automatic check; the text says which) or `review_feedback` (a reviewer rejected your earlier answer and says why). Write a new answer that fixes exactly that problem and still follows every rule above.

Return exactly one object per input item, in input order, in the response schema's field order. Output JSON only.
