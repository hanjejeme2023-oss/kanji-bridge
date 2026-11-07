# Task 5: Korean usage check (v1)

You are checking the Korean side of a vocabulary study tool. The learner is a native speaker of Japanese and Korean who is learning Chinese and Vietnamese. Each input item is a multi-character Han word with its Korean reading `ko`, taken from a hanja dictionary. That dictionary lists every possible Sino-Korean reading, including words that Korean speakers never use. Your job is to say whether **Korean speakers actually use this word**, and whether `meaning_ja__ko` (the Korean meaning the app would show) is right.

Everything in the input is given evidence. Never change, add or write a reading. Do not judge the Japanese, Chinese or Vietnamese side.

Return exactly one object per input `key`, in the response schema's field order.

## `ko_check`

Ask: *would an educated Korean speaker today recognise `ko` as the word written with these characters, and use it?*

- `used`: yes, and `meaning_ja__ko` describes how Koreans use it (small nuance differences are fine). Formal, technical, legal or literary words count when they are used in their field (臨床 임상, 上訴 상소, 收斂 수렴). A Korean meaning that differs from the Japanese or Chinese one is still `used`: that is a false friend, which the app wants (工夫 공부 "study", 愛人 애인 "lover", 汽車 기차 "train", 東西 동서 "east and west").
- `rare`: the word is not in active use in modern Korean in any meaning. This covers dictionary-only, archaic or classical entries, Chinese or Japanese words whose Korean reading Koreans do not say, and cases where Koreans would hear the Hangul only as **another word written with other characters**. Examples: 小姐 소저, 老公 노공, 出來 출래, 勉強 면강, 同事 동사 (Koreans hear 動詞 "verb"; for "colleague" they use 同僚), 不大 부대 (heard as 部隊), 調度 조도 (heard as 照度), 順路 순로.
- `wrong_meaning`: Koreans use this word written with these characters, but `meaning_ja__ko` is not its Korean meaning. Typical causes: the meaning of a homophone written with other characters, or a Chinese or Japanese sense that the Korean word does not have. Example: 研究生 연구생 given 「大学院生」 (in Korean 연구생 is a research trainee; a graduate student is a different word).
- `unsure`: you cannot tell. Use this rather than guessing. An item marked `unsure` is treated like `rare` until a reviewer checks it.

Judge the Korean word itself, not how often the Chinese or Japanese word is used. A hanja dictionary entry with a definition is **not** evidence of use. `gloss_ko`, when present, comes from that dictionary.

## `reason`

- Empty for `used`.
- Otherwise required: one short Japanese phrase (at most 60 characters) that gives the decisive fact, e.g. 「韓国語では「同僚」を使う。동사は通常「動詞」」 or 「辞書のみの古語」.
- Name other words by their **Han characters**, not by Hangul. The only Hangul allowed in `reason` is the item's own `ko`. Write no pinyin, no Vietnamese and no other reading.

Output JSON only.
