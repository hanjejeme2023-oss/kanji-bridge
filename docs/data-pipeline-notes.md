# Data Pipeline Design Notes: 漢字ブリッジ

Working notes built while going through the TIA Section F (pandas) lessons. They explain **how** the data is built.
**What** must be built (tables, columns, decisions) is defined in `final-data-spec.md`; if the two ever disagree, the spec wins.

Last updated: 2026-11-04 (Section F complete; after 3-pass document audit)

---

## 1. Goal

Produce the tables in `final-data-spec.md` (`chars`, `words`, `word_chars`, `ff_meanings`, `passages`) from public dictionaries with a reproducible Python pipeline.

- The Sino-Xenic link (學 → 학 / 学 がく / xué / học) is the backbone and the app's core value.
- Not every word exists in every language (嗎, native Korean/Japanese words). Missing is allowed but must be **explicit** (NaN), never guessed.

## 2. Folder layout and stages

```
raw/            downloads, untouched (read-only). Recreated by pipeline/download.py (URLs + checksums)
pipeline/       scripts; id_map.csv; overrides.csv
config/         rules.json (static rule text)
content/        AI-generated content (Gemini) — NOT deleted by rebuilds
data/staging/   one clean table per source        ← rebuilt
data/final/     tables + data.js for the app       ← rebuilt
```

```
download   pipeline/download.py → raw/
load       one loader per source → standard column names (F11)
clean      strip, NFC, replace dummy values, dedupe within source (F12, F15)
link       merge sources on keys (F13)
resolve    priority rules for overlapping columns
content    merge accepted content/ files (glosses, false friends, passages)
validate   counts, isna, duplicates, merge indicators, coverage (F12, F14)
export     CSV + JSON + data.js
```

Rules:
- Raw files are never edited. All changes happen in scripts, so `python pipeline/run_all.py` can rebuild everything.
- A rebuild deletes and recreates **`data/staging/` and `data/final/` only**. `content/` (AI output) and `pipeline/id_map.csv` are inputs and are kept.
- Every source gets the **same column names** at load time (`rename`).
- Keep source columns (`source_*`) so every value can be traced.
- LLMs write the scripts; scripts do the row-level work. Per-row LLM work is only for content (meanings, false-friend judgments, passages), batched and reviewed.

## 3. Sources

See the table in `final-data-spec.md` and the license log in `SOURCES.md`. Format notes:

| Source | Format | Loading |
|---|---|---|
| Unihan | tab-separated, long format: `U+5B78<TAB>kHangul<TAB>학:0E`, `#` comments | `read_csv(sep="\t", comment="#", header=None, names=[...])`, then `pivot` long → wide; convert `U+XXXX` with `chr(int(x[2:], 16))` |
| KANJIDIC2 | XML | `pandas.read_xml` or `xml.etree`; on'yomi are katakana |
| hsk30 | CSV | `read_csv(encoding="utf-8")` |
| CC-CEDICT | text lines `trad simp [pin1 yin1] /gloss/gloss/`, `#` comments | `str.extract(r'^(\S+) (\S+) \[(.+?)\] /(.+)/$')` (tested) |
| JMdict | XML | XML parsing; one entry has several kanji forms and readings |
| hanja.txt | text, colon-separated (to confirm) | `read_csv(sep=":", comment="#")` after checking |
| hanviet cognates | TBD | profile in Stage 1 |

## 4. Lessons → pipeline mapping

### F11 Loading / formats
- `sep="\t"` for TSV; `encoding="utf-8"` always; `"utf-8-sig"` for Excel CSVs with BOM.
- `keep_default_na=False` on word columns: real words like "NA"/"null" must not become NaN. Then convert only *known* dummy values ourselves.
- Output: `to_csv(index=False, encoding="utf-8")`; JSON with `ensure_ascii=False`. Pickle only for temporary checkpoints.

### F12 Cleaning
- `dropna` is a **reporting** tool here, not a deletion tool. Never default `dropna()` on the final tables.
- Never `fillna` word data with values. Only fill `""` at export if the app needs it.
- `replace` per column only, never table-wide.
- `drop_duplicates` is pre-merge hygiene + post-merge check. Word dedupe keys include the reading (行 xíng vs háng).
- `map` + dict for lookups (level labels, language codes, kana conversion). Always `isna()` after `map`.

### F13 Merge / concat
- `concat(ignore_index=True)` to stack same-shaped files.
- Never the default `inner`: `how="left"` (backbone left) or `how="outer"` + `indicator=True`, and always `validate=`.
- Many-to-many explosion: check `df[key].duplicated().sum()` on both sides before each merge.
- `suffixes` named after sources, then explicit priority rules (recorded in DECISIONS).
- Prefer `rename` + `reset_index()` over index merges.
- `melt` / `pivot` for long ↔ wide (Unihan is long).

### F14 Groupby / pivot
- Validation & reporting: `groupby("source").size()`, `groupby("level", dropna=False).count()`.
- groupby drops NaN keys → `dropna=False` when auditing.
- `pivot_table` default is mean → always `aggfunc="count"` / `"size"`.
- Sound rules: `pivot_table(index="ko_final", columns="vi_final", values="pair_id", aggfunc="count", fill_value=0)` over **aligned syllable pairs** (spec D7). Big cells = rules, small cells = exceptions.

### F15 Text (dates not needed)
- `.str.strip`, `.str.normalize("NFC")`, `.str.lower`, `.str.split`, `.str.len`, `.str.replace(regex)`, `.str.contains`, `.str.extract(regex)`.
- Hangul final consonant: `(ord(ch) - 0xAC00) % 28` → index into the 28-item list (tested).
- Vietnamese final: `str.extract(r'(ng|nh|ch|c|p|t|n|m)$')` on NFC, lowercased syllables; NaN = open syllable (tested).
- Pinyin tone numbers → tone marks: one converter function applied with `.map`.
- Katakana → hiragana: shift code points by `-0x60` for the katakana block.

## 5. Keys and the hard problems

- Canonical character key = **traditional form**.
- Word keys: use the traditional form given by hsk30; do not convert simplified → traditional automatically (one-to-many).
- Japanese words: match JMdict entries by their kanji form against the word's traditional/Japanese form. Japanese shinjitai ≠ traditional (学 vs 學), so a shinjitai ↔ traditional mapping is needed (method decided in Stage 1).
- Polyphones: resolved at word level (spec D6). Character tables keep all readings.
- Same form, different meaning (勉強): matched, then flagged as a false-friend candidate, never silently treated as a cognate.

## 6. Text-cleaning checklist
- strip; collapse internal whitespace
- NFC for all text, before any dedupe or merge
- full-width vs half-width (Japanese sources)
- pinyin canonical form = tone marks
- Hangul source suffixes (`:0E`) removed

## 7. Validation checklist (every run)
- Row counts per stage (logged)
- `isna().sum()` per language column → coverage report
- `duplicated(subset=key).sum() == 0` per table
- `_merge` value counts for every merge
- `groupby(..., dropna=False)` coverage by level and source
- `word_chars` syllable-count mismatches
- 20 fixed test words (listed in the prompt) checked by eye

## 8. Open decisions (made in Stage 1–3, recorded in DECISIONS)
- Source priority per column when sources conflict
- Shinjitai ↔ traditional mapping method
- Frequency bands that give VI-only words a level
- Section G (EDA/visualization): light pass only; PCA / feature engineering / predictive modeling not needed
