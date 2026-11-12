# Task 6: Vietnamese example sentences (v2)

You are writing example sentences for a vocabulary study tool. The learner is a native speaker of Japanese and Korean and is learning Vietnamese. Each input item is one Sino-Vietnamese word (a word written with Han characters in the past) with its dictionary data. For each item, write **one** short, natural Vietnamese sentence that uses the word, and a natural **Japanese translation**.

Everything in the input is fixed evidence. Never change the word or its spelling.

## Input fields

- `key`: copy it unchanged.
- `target`: the Vietnamese word, in lower case. The sentence must contain this exact word; capital letters are allowed only where Vietnamese spelling requires them (the start of the sentence, names such as Việt Nam).
- `trad`: the Han characters of the word (for reference only; never write Han characters in the sentence).
- `meaning_ja`: the meaning the app shows for this word in Vietnamese. **The sentence must use the word in this meaning.**
- `is_trap`: `true` when this Vietnamese meaning differs from what a Japanese or Korean speaker would expect from the same characters (a "false friend"). `contrast_meaning_ja` then gives the meaning the learner might wrongly assume. Write a sentence in which only the Vietnamese meaning makes sense, so the difference is clear. Check it: read the sentence as if the word meant `contrast_meaning_ja`. If it still makes sense, add context that rules that reading out. Example: for cố nhân (an old friend; contrast: a deceased person), "he remembered his cố nhân" fits both meanings; "he met his cố nhân again after twenty years" fits only the Vietnamese one.
- `vi_use`: `common` = an everyday word; `literary` = correct but formal, literary or technical; empty = not checked.
- `level`: the learner's level for this word, 1 (beginner) to 7 (advanced); empty means intermediate.

## The sentence

- Natural, modern Vietnamese that an educated native speaker would write today (standard northern spelling). Everyday topics.
- For a `literary` word, a formal sentence is right (news, official notices, writing about history, science or law), as long as a native speaker would really use this word there. Do not put a literary word into casual speech.
- Use native Vietnamese words for everything else wherever an everyday speaker would (máy bay, not phi cơ; giáo viên or thầy giáo, not lão sư; sau đó, not nhiên hậu), unless that word is the target.
- Length fits the level: level 1-2 about 4-9 words (syllables); level 3-4 about 6-12; level 5-7 or empty about 8-18. Never more than 25 syllables.
- Use the target word **once**, spelled exactly as `target`, with all tone and vowel marks.
- Check every word's tone and vowel marks before you answer; a wrong mark makes a different word (bên ngoài "outside", bên ngoại "the mother's side").
- Start with a capital letter and end with . ! or ?. Latin letters with Vietnamese marks, spaces and ordinary punctuation only. No Han characters, no Hangul.
- No real people's names, no brands, no politics, religion or violence as a **topic you choose**. When the target word itself is about crime, war, the military, weapons, death, illness, politics or religion (sát nhân, chiến tranh, tử hình), write a calm, factual sentence of the kind a newspaper, a history book or a textbook prints, with no graphic detail. Never return `no_sentence` because of the word's subject.

## The Japanese translation (`translation_ja`)

- A natural Japanese sentence that a Japanese reader would write, translating the whole Vietnamese sentence. Not word-for-word.
- `meaning_ja` is a dictionary gloss. Do not copy its wording into the translation when a Japanese speaker would say it differently in this sentence, and translate Vietnamese set expressions by their sense (bồi hồi → 「胸がいっぱいになる」「しみじみと」, not 「胸を揺らす」).
- At most 60 characters. Japanese only: no Vietnamese words, no Hangul.

## When you cannot write a good sentence

If a native speaker would not use this word in the meaning given (for example it is a dictionary-only reading, or everyday and formal Vietnamese both use another word), do not force a sentence: set `status` to `no_sentence`, leave `sentence` and `translation_ja` empty, and give the reason in `review_note`. Otherwise `status` is `ok`.

Before you choose `no_sentence`, think of today's formal fields as well as everyday speech: finance and business reports, law and administration, the press, sports reporting, medicine, education. A word that is current in one of these fields, in the meaning given, counts as used: write the sentence in that field (for example bán niên "half-year" is current in báo cáo tài chính bán niên, a company's half-year financial report). `no_sentence` is right when the word appears only in dictionaries, old texts or translations from Chinese (điện não for "computer": Vietnamese says máy tính), not when it is merely formal. Never invent a use you have not seen.

## `confidence` and `review_note`

- `confidence` is `high` when you are sure the sentence is natural and uses the given meaning; otherwise `low`.
- `review_note` is a short Japanese note for the reviewer (at most 80 characters): required when `confidence` is `low` or `status` is `no_sentence`, otherwise empty.

## Corrections

An item may carry `previous_error` (your earlier answer for this item failed an automatic check; the text says which) or `review_feedback` (a reviewer rejected your earlier answer and says why). Write a new answer that fixes exactly that problem and still follows every rule above.

Return exactly one object per input item, in input order, in the response schema's field order. Output JSON only.
