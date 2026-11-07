# Task 3: graded reading passages (v3, Vietnamese cells)

You are writing short reading practice for a Japanese-language vocabulary study tool. The request describes one language/level cell and supplies the only linkable Sino-vocabulary. Every `word_id`, display form, meaning, and level is fixed evidence. Never change, invent, or add a reading.

Return exactly six passages. Each passage must:

- contain 1–3 natural sentences in the requested language;
- have a natural Japanese `translation_ja` that translates **every** sentence of the passage completely;
- read like natural, modern, everyday language a teacher would use at that level (see "Natural Vietnamese" below);
- link at least three supplied vocabulary occurrences;
- link at least one word at the requested level when the supplied list contains one that fits naturally;
- use only supplied `word_id` values, with token `t` exactly equal to that word's `display` (Vietnamese comparison is case-insensitive, but preserve the supplied spelling);
- use simplified Chinese for `zh`;
- make every supplied Sino-word occurrence a linked token rather than an unlinked gloss token.

## Natural Vietnamese

The supplied list contains many Sino-Vietnamese words that are correct readings of the Han characters but are literary, archaic, or not the word a Vietnamese speaker uses today. **A supplied word is only a candidate. Use it only where an educated native speaker would naturally use that exact word in modern Vietnamese.** When everyday Vietnamese uses a different word for the meaning, write the everyday word (as a gloss token if it is not in the list) and do not use the list word.

Examples of what not to write, with the everyday word in brackets: `lão sư` (giáo viên, thầy giáo), `chủng tử` (hạt giống), `bộ điện ảnh` for one film (bộ phim), `địa đồ` (bản đồ), `phi cơ` (máy bay), `viết hán tự` (viết chữ Hán), `túc cầu` (bóng đá), `thục luyện văn pháp` (thành thạo ngữ pháp), `miêu tả tiên minh` (miêu tả rõ nét), `xuất sinh` (sinh ra), `quan tài phán` (thẩm phán), `nhiên hậu` (sau đó), `giáo tài` (giáo trình).

It is better to link exactly three natural words than to force more. A sentence that a Vietnamese teacher would correct is wrong even if every token validates.

Check every Vietnamese word and its tone and vowel marks before you answer: a wrong mark makes a different word (`bên ngoài` = outside, `bên ngoại` = the mother's side of the family).

## Tokens

Token shapes are exclusive:

- linked word: `{"t":"...","word_id":"..."}`
- native/function word: `{"t":"...","gloss_ja":"short Japanese gloss"}`
- punctuation only: `{"t":"。","punct":true}`

Do not put punctuation inside word tokens. Output JSON only in the required `{"passages":[...]}` shape.
