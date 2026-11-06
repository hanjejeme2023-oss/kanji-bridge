# Task 3: graded reading passages (v2)

You are writing short reading practice for a Japanese-language vocabulary study tool. The request describes one language/level cell and supplies the only linkable Sino-vocabulary. Every `word_id`, display form, meaning, and level is fixed evidence. Never change, invent, or add a reading.

Return exactly six passages. Each passage must:

- contain 1–3 natural sentences in the requested language;
- have a natural Japanese `translation_ja` that translates **every** sentence of the passage completely;
- read like natural, modern, everyday language a teacher would use at that level: do not force rare, literary or archaic words into a sentence just to link them (for example Vietnamese `nhiên hậu` or `giáo tài` where `sau đó` or `giáo trình` would be normal);
- link at least three supplied vocabulary occurrences;
- link at least one word at the requested level when the supplied list contains one;
- use only supplied `word_id` values, with token `t` exactly equal to that word's `display` (Vietnamese comparison is case-insensitive, but preserve the supplied spelling);
- use simplified Chinese for `zh`;
- make every supplied Sino-word occurrence a linked token rather than an unlinked gloss token.

Token shapes are exclusive:

- linked word: `{"t":"...","word_id":"..."}`
- native/function word: `{"t":"...","gloss_ja":"short Japanese gloss"}`
- punctuation only: `{"t":"。","punct":true}`

Do not put punctuation inside word tokens. Output JSON only in the required `{"passages":[...]}` shape.
