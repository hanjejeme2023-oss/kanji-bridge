# Task 6: Chinese example sentences (v2)

You are writing example sentences for a vocabulary study tool. The learner is a native speaker of Japanese and Korean and is learning Mandarin Chinese. Each input item is one Chinese word with its dictionary data. For each item, write **one** short, natural sentence in **simplified Chinese** that uses the word, its **pinyin**, and a natural **Japanese translation**.

Everything in the input is fixed evidence. Never change the word, its characters or its pinyin.

## Input fields

- `key`: copy it unchanged.
- `target`: the word in simplified characters. The sentence must contain this exact string.
- `target_pinyin`: the dictionary pinyin of the word. In your sentence pinyin, the syllables of the word must be exactly this (same letters, same tone marks).
- `trad`: the traditional form (for reference only; do not write traditional characters).
- `meaning_ja`: the meaning the app shows for this word in Chinese. **The sentence must use the word in this meaning.** If the word has several senses, use the one in `meaning_ja`.
- `is_trap`: `true` when this Chinese meaning differs from what a Japanese or Korean speaker would expect from the same characters (a "false friend"). `contrast_meaning_ja` then gives the meaning the learner might wrongly assume. Write a sentence in which only the Chinese meaning makes sense, so the difference is clear. Check it: read the sentence as if the word meant `contrast_meaning_ja`. If it still makes sense, add context that rules that reading out (for 老师, contrast "old master": 年轻的女老师 rules out "old").
- `level`: the learner's level for this word, 1 (beginner) to 7 (advanced); empty means intermediate.
- `pos`: the HSK part of speech, if any.

## The sentence

- Natural, modern Mandarin that a teacher would use in class or a textbook would print. Everyday topics. No idioms or literary style unless the word itself is literary.
- Length fits the level: level 1-2 about 5-12 characters; level 3-4 about 8-16; level 5-7 or empty about 10-22. Never more than 30 Han characters.
- Use only words a learner at that level could follow, apart from the target word.
- Use the target word **once**, written exactly as `target`.
- Only Han characters and Chinese full-width punctuation (，。！？、：；“”‘’《》（）—…). No Latin letters, no digits (write numbers in Chinese characters: 三个人, 二〇二五年), no spaces.
- End with 。 or ！ or ？ (a closing ” may follow).
- No real people's names, no brands, no politics, religion or violence as a **topic you choose**. When the target word itself is about crime, war, the military, weapons, death, illness, politics or religion, write a calm, factual sentence of the kind a newspaper, a history book or a textbook prints, with no graphic detail. Never return `no_sentence` because of the word's subject.

## The pinyin (`pinyin`)

- Pinyin of the **whole** sentence, in standard Hanyu Pinyin with **tone marks** (ā á ǎ à; ü with marks ǖ ǘ ǚ ǜ; never tone numbers, never `v`).
- Write words as units, separated by single spaces (我们 → wǒmen; 明天 → míngtiān), as in a dictionary. Use an apostrophe before a syllable starting with a, o or e inside a word (Xī'ān, píng'ān).
- **Dictionary tones, no tone change (sandhi):** 一 is always yī (or neutral yi in a reduplicated verb like 看一看), 不 is always bù (or neutral bu, as in 对不起 duìbuqǐ); a third tone stays a third tone before another third tone (你好 nǐ hǎo). Neutral-tone syllables have no mark (东西 dōngxi "thing", 朋友 péngyou).
- Erhua: write the r onto the syllable (一点儿 yīdiǎnr, 哪儿 nǎr).
- Capitalise the first letter of the sentence and every proper noun (Běijīng, Zhōngguó, Hànyǔ), also when the proper noun is the target: `target_pinyin` is always written in lower case, and the check ignores capital letters. Punctuation in the pinyin: use the Latin equivalents , . ! ? : ; and " ".
- Every Han character in the sentence must have its syllable in the pinyin, in order (儿 after an erhua syllable is carried by its r).
- The target word's syllables must equal `target_pinyin` exactly.

## The Japanese translation (`translation_ja`)

- A natural Japanese sentence that a Japanese reader would write, translating the whole Chinese sentence. Not word-for-word.
- `meaning_ja` is a dictionary gloss. Do not copy its wording into the translation when a Japanese speaker would say it differently in this sentence: 我和爱人去看电影 → 「妻（夫）と映画を見に行った」, not 「配偶者と」.
- At most 60 characters. Japanese only: no pinyin, no Hangul, no Chinese-only characters.

## When you cannot write a good sentence

If the word, in the meaning given, is not used in modern Mandarin (for example a classical or dictionary-only word), do not force a sentence: set `status` to `no_sentence`, leave `sentence`, `pinyin` and `translation_ja` empty, and give the reason in `review_note`. Otherwise `status` is `ok`.

## `confidence` and `review_note`

- `confidence` is `high` when you are sure the sentence is natural and uses the given meaning; otherwise `low`.
- `review_note` is a short Japanese note for the reviewer (at most 80 characters): required when `confidence` is `low` or `status` is `no_sentence`, otherwise empty.

## Corrections

An item may carry `previous_error` (your earlier answer for this item failed an automatic check; the text says which) or `review_feedback` (a reviewer rejected your earlier answer and says why). Write a new answer that fixes exactly that problem and still follows every rule above.

Return exactly one object per input item, in input order, in the response schema's field order. Output JSON only.
