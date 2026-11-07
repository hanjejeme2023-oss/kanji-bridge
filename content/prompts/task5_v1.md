# Task 5: usage check for Japanese, Korean and Vietnamese readings (v1)

You are checking a vocabulary study tool for a learner who is a native speaker of Japanese and Korean and is learning Chinese and Vietnamese. Each input item is a Han word with its dictionary readings. The dictionaries list every reading they know, including words that speakers of that language do not actually use. Your job is to say, for each language listed in the item's `checks`, whether **speakers of that language actually use this word**.

Everything in the input is given evidence. Never change, add or write a reading. Do not judge Chinese.

Return exactly one object per input `key`, in the response schema's field order. For a language **not** listed in `checks`, its check field and its reason field are empty strings.

## `ja_check` and `ko_check` (Japanese `ja`, Korean `ko`)

Ask: *would an educated native speaker today recognise this reading as the word written with these characters, and use it?*

- `used`: yes, and the given meaning in that language (`meaning_ja__ja` for Japanese, `meaning_ja__ko` for Korean) describes how speakers use it; small nuance differences are fine. Formal, technical, legal or literary words count when they are used in their field (Korean 臨床 임상, 上訴 상소; Japanese 収斂 しゅうれん). A meaning that differs from the other languages is still `used`: that is a false friend, which the tool wants (Korean 工夫 공부 "study", 愛人 애인 "lover"; Japanese 愛人 あいじん "mistress").
- `rare`: the word is not in active modern use in any meaning. This covers dictionary-only, archaic or classical entries; Chinese words that speakers of this language do not say (including katakana renderings of Chinese pronunciation); and cases where speakers would hear the reading only as **another word written with other characters**. Korean examples: 小姐 소저, 老公 노공, 出來 출래, 勉強 면강, 同事 동사 (Koreans hear 動詞 "verb"; for "colleague" they use 同僚), 不大 부대 (heard as 部隊), 調度 조도 (heard as 照度), 順路 순로. Japanese examples: 同事 どうじ, 錄取 ろくしゅ (for "colleague" and "to admit" Japanese uses other words).
- `wrong_meaning`: speakers use this word written with these characters, but the given meaning is not its meaning in that language (typically the meaning of a homophone written with other characters, or a Chinese sense this language does not have). Korean example: 研究生 연구생 given 「大学院生」 (in Korean 연구생 is a research trainee; a graduate student is a different word).
- `unsure`: you cannot tell. Use this rather than guessing; a reviewer checks every `unsure`.

Judge the word itself in that language, not how common the Chinese word is. A dictionary entry with a definition is **not** evidence of use; `gloss_ko` comes from a hanja dictionary and `gloss_ja_en` from a dictionary that also lists rare words.

## `vi_use` (Vietnamese `vi`)

The Vietnamese value is a correct Sino-Vietnamese reading of these characters and has already been checked to be the same word. Ask: *is it the word a Vietnamese speaker uses today in everyday speech and ordinary writing for this meaning?*

- `common`: yes (經濟 kinh tế, 學生 học sinh, 電話 điện thoại, 問題 vấn đề). A single character counts when it is used on its own or is the normal reading taught for it (茶 trà, 學 học).
- `literary`: understood and correct, but formal, literary, dated or technical, and everyday Vietnamese normally uses a different word for this meaning (飛機 phi cơ, 足球 túc cầu, 老師 lão sư, 地圖 địa đồ, 飯 phạn).
- `unsure`: you cannot tell.

## Reasons (`ja_reason`, `ko_reason`, `vi_reason`)

- Empty when the check is `used` or `common`; otherwise required.
- One short Japanese phrase, at most 80 characters, giving the decisive fact, e.g. 「韓国語では「同僚」を使う。동사は通常「動詞」」, 「辞書のみの古語」, 「日常語は固有語の別の語」.
- Name other words by their **Han characters** or describe them in Japanese. The only Hangul allowed is the item's own `ko`; the only Latin-letter text allowed is the item's own `vi` or a part of it. Write no other reading of any language.

Output JSON only.
