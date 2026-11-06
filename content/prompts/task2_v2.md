# Task 2: false-friend judgments (v2)

You are judging false friends for a vocabulary study tool. The learner is a native speaker of Japanese and Korean who is learning Chinese and Vietnamese. Dictionary facts, forms, readings, glosses, and any task-1 meanings in the JSONL input are given evidence. Never change or add a reading and never emit a reading or form field.

Return exactly one object per input `key`. Fill the fields in the order of the response schema: first the meanings, then the judgment.

## `meanings`

One entry for each language whose evidence field is non-empty: `ja` for Japanese, `ko` for Korean, `pinyin` for Chinese, `vi` for Vietnamese. `meaning_ja` is a concise Japanese dictionary-style meaning of the word as used in that language, from the evidence (task-1 meanings when given).

## `false_friend` (which languages are traps)

The baseline is the **Japanese** meaning; if `ja` is empty, the Korean meaning; if both are empty, the Chinese meaning.

- **The baseline language is never a trap.** Japanese is never listed.
- Chinese (`zh`) or Vietnamese (`vi`) is a trap when its meaning differs from the baseline enough that the learner would misunderstand it. Examples: 手紙 Chinese "toilet paper" → `zh`; 大丈夫 Chinese "a manly man" → `zh`; 勉強 Chinese "reluctantly" → `zh`; 新聞 Chinese "news" → `zh`; 博士 Vietnamese `bác sĩ` "doctor (physician)" → `vi`.
- Korean (`ko`) is a trap only when the Korean word is in common use and its meaning differs from the Japanese one (example: 工夫 Korean 공부 "study"). A rare or archaic Korean dictionary reading is not a trap.
- Do not flag ordinary nuance, register, part of speech, or pronunciation differences.
- A Vietnamese homophone proven to use different Han characters has already been removed from the input.

`is_trap` is true exactly for the languages listed in `false_friend`. An empty list means "not a false friend".

If uncertain, set `confidence=low` and give a short Japanese `low_reason`; otherwise `confidence=high` and an empty reason. Output JSON only.
