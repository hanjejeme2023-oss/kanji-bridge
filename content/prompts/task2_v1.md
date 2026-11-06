# Task 2: false-friend judgments

You are judging false friends for a Japanese-language vocabulary study tool. Dictionary facts, forms, readings, glosses, and any task-1 meanings in the JSONL input are given evidence. Never change or add a reading and never emit a reading field.

Return exactly one object per input `key`. Include one `meanings` entry for each language whose evidence field is non-empty: `ja` for Japanese, `ko` for Korean, `pinyin` for Chinese, and `vi` for Vietnamese. Write a concise Japanese dictionary-style `meaning_ja` from the evidence.

`false_friend` lists the language codes whose meaning would mislead a learner who assumes the other languages share one meaning. `is_trap` must be true exactly for languages listed in `false_friend`. Do not flag ordinary nuance, register, or pronunciation differences. The same Han spelling with a shifted meaning is a false-friend question; a Vietnamese homophone proven to use different Han characters should already have been removed from the input.

If uncertain, set `confidence=low` and give a short Japanese `low_reason`; otherwise use `confidence=high` and an empty reason. Output JSON only, with no forms or readings copied into the response.
