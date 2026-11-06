# Task 4: notes for non-primary readings

You are writing one-line Japanese notes for a vocabulary study tool. Each input word lists a Korean or Vietnamese character reading used in that word, the character's primary reading, and up to three evidence examples for each. These readings and examples are fixed dictionary facts. Never change, normalize, infer, transliterate, or add a reading.

Return exactly one object per `word_id`. `note_ja` must be one natural Japanese line of at most 80 characters. Explain that the character is usually read with the supplied `primary` (include a supplied primary example when available) but is read with the supplied `reading_here` in this word. Cover each listed difference concisely when a word has more than one.

Quote every mentioned word, character, and reading with Japanese corner brackets `「…」`. You may quote only the input word, listed character, supplied readings, or supplied example words. Any Hangul or Vietnamese Latin-letter token in the note must occur exactly in this item's input readings. Use Japanese language labels such as 韓国語 and ベトナム語, not Latin abbreviations. Output JSON only and no separate reading field.
