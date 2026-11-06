# Task 1: language-specific meanings (v2)

You are producing reviewed content for a vocabulary study tool. The learner is a native speaker of Japanese and Korean who is learning Chinese and Vietnamese. The JSONL input contains dictionary facts. Treat every form, reading, level, source label, and gloss as given evidence. Never change a reading, invent a reading, transliterate a reading, or write a reading in any field.

Return one JSON object for every input item, using exactly the supplied `word_id`. Fill the fields in the order of the response schema: decide `vi_check` first, then write the meanings.

## Step 1: `vi_check` (only when `vi` is non-empty)

If `vi` is empty, `vi_check` and `vi_check_reason` are empty strings. Otherwise choose one:

- `same_word`: the Vietnamese value is the Sino-Vietnamese reading of these same Han characters, even if its meaning shifted. Example: 自己 `tự kỷ` glossed "autistic" is the same written word with a shifted meaning (a false-friend question, not a different word). A gloss that only gives a personal-name or surname sense of the same characters is also `same_word`.
- `different_word`: `gloss_vi` clearly describes a word written with **other** Han characters that sound the same. You must be able to name those other characters in `vi_check_reason`. Example: 生詞 `sinh từ` glossed "shrine" describes 生祠, not 生詞.
- `unsure`: the evidence does not establish which written word the gloss describes.

Rules:

- **A single-character word (`trad` is one character) is never `different_word`.** Its `vi` is a reading of that character. If `gloss_vi` describes a native Vietnamese word or another character that happens to sound the same (for example 樂 `lạc` glossed "peanut"), use `unsure` and say so in `vi_check_reason`.
- `source_vi=composed_attested`: the value was composed from character readings, so `gloss_vi` may describe an unrelated homophone. Check it carefully.
- `source_vi=kaikki_en_han`: `gloss_vi` is English. For every other source it is Vietnamese.
- For `different_word` and `unsure`, `vi_check_reason` is required, written in Japanese, quoting the decisive part of `gloss_vi` in 「」 and naming the other characters when known. For `same_word` it is empty.

## Step 2: meanings

Write short Japanese dictionary-style meanings, as the word is used **in that language**, based on the supplied glosses (not merely on the Han characters).

| Field | Non-empty exactly when |
|---|---|
| `meaning_ja__ja` | `ja` is non-empty (a `jp` form without `ja` is not Japanese evidence) |
| `meaning_ja__ko` | `ko` is non-empty |
| `meaning_ja__zh` | `pinyin` is non-empty |
| `meaning_ja__vi` | `vi` is non-empty **and** `vi_check` is `same_word` or `unsure` |

`meaning_ja__vi` is empty **only** for `different_word`. For `same_word` and `unsure` it must be filled: use the sense supported by `gloss_vi`; if `gloss_vi` gives only a name sense or describes another word, give the meaning these characters have in Sino-Vietnamese use. Every other meaning field for a language whose reading is empty must be an empty string.

## Step 3: `meanings_differ`

`true` when the Chinese, Vietnamese or Korean meaning differs from the Japanese meaning (or from the Korean meaning when `ja` is empty) enough to mislead this learner. Ordinary nuance, register or part-of-speech variation is not enough. Ignore the Vietnamese value when `vi_check=different_word`.

## Step 4: confidence

- `confidence=low` for every `different_word` and `unsure`, and whenever the evidence is uncertain; `low_reason` is a short Japanese phrase.
- If the Korean reading looks like a rare or archaic dictionary entry that Korean speakers do not use for this meaning (for example 小姐 소저, 老公 노공, 勉強 면강), use `confidence=low` and exactly `low_reason="ko_rare"`.
- Otherwise `confidence=high` and `low_reason` is empty.

Write meanings and reasons in Japanese. Output JSON only, with no reading fields.
