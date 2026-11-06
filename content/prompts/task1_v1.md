# Task 1: language-specific meanings

You are producing reviewed content for a Japanese-language vocabulary study tool. The JSONL input contains dictionary facts. Treat every form, reading, level, source label, and gloss as given evidence. Never change a reading, invent a reading, transliterate a reading, or add a meaning for a language whose reading field is empty.

Return one JSON object for every input item, using exactly the supplied `word_id`. Write short Japanese dictionary-style meanings for each language in which the word is actually present:

- Japanese only when `ja` is non-empty. A `jp` form without `ja` is not Japanese evidence.
- Korean only when `ko` is non-empty.
- Chinese only when `pinyin` is non-empty.
- Vietnamese only when `vi` is non-empty and it is the same written Han word.

Base the meanings on the supplied gloss fields and forms. Do not translate merely from the Han characters. `meaning_ja__*` values must be concise Japanese, not readings. Set `meanings_differ=true` when the meanings in the languages present differ enough to mislead a learner; normal nuance or register variation alone is not enough.

For every non-empty `vi`, audit `vi_check`:

- `same_word`: the Vietnamese reading belongs to the same Han characters, even if its meaning shifted. Example: 自己 `tự kỷ` meaning “autistic” is the same written word and may be a false friend.
- `different_word`: the Vietnamese string is a homophone for a different Han spelling. Example: 生詞 `sinh từ` with a “shrine” gloss is evidence for 生祠, not 生詞. Leave `meaning_ja__vi` empty, set `confidence=low`, and put a short reason in `vi_check_reason` that cites the supplied gloss evidence exactly enough for review.
- `unsure`: the evidence cannot establish which written word it describes. Give the evidence in `vi_check_reason` and set `confidence=low`.
- Empty only when input `vi` is empty.

Important source cautions: `source_vi=composed_attested` was composed from character readings, so its `gloss_vi` may describe an unrelated homophone. A `source_vi=kaikki_en_han` `gloss_vi` is English; other Vietnamese glosses are Vietnamese.

Set `confidence=low` with a short `low_reason` whenever evidence is uncertain. If the Korean reading looks like a rare or archaic dictionary entry (for example 小姐 소저 or 老公 노공), use exactly `low_reason="ko_rare"`. Otherwise use `confidence=high` and an empty `low_reason`. Output Japanese text only in meaning/reason fields. Output JSON only and no reading fields.
