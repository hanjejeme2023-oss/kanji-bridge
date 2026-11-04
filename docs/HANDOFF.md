# HANDOFF

Read `PROMPT.md` first, then this file. Do only the assignment for your role. Update this file, `CHANGELOG.md`, `DECISIONS.md` when done; `git commit`; stop with one line `Next: <agent> — <task>`.

## Current status
- Stage 0 (setup) — **DONE** by Claude, 2026-11-04.
- Stage 1 (sources and licences) — **DONE** by Codex; **Claude review DONE** 2026-11-04. All blocking source/licence decisions are closed (DECISIONS D23–D34). Evidence: `docs/STAGE1_REVIEW.md`; reference scripts (evidence, not pipeline): `docs/review_scripts/`.
- Contract files: `docs/SCHEMA.md` (updated: level 1–7, source tags, new reports), `config/rules.json`, `docs/DECISIONS.md` (D1–D34), `docs/final-data-spec.md` (+ Addenda), `docs/SOURCES.md` (all rows now decided).
- `raw/` is git-ignored and recreated by `pipeline/download.py` (checksums in committed `pipeline/source_manifest.csv`). Licence copies are in `licenses/`.
- Git identity: `Hanje Unesaki <311183901+hanjejeme2023-oss@users.noreply.github.com>` (D19). Check `git config user.email` before committing.
- Environment: Python 3.12.10 + pandas 3.1.1 (`pipeline/requirements.txt`). On this machine the Python with pandas is `<user folder>\AppData\Local\Programs\Python\Python312\python.exe`; the `python` on the bash PATH may be a Store stub without pandas.
- Prototype: `prototype/index.html` (frozen).

## Stage 1 review: outcome in brief (details in STAGE1_REVIEW.md)
- **Licences:** all accepted. hsk30 accepted with a recorded provenance risk (confirmed by the user, D35). Dataset will be **CC BY-SA 4.0**.
- **Vietnamese:** Kaikki (reading + Han form) and FrequencyWords (frequency proxy) selected. Unihan `kVietnamese` mixes Nôm readings (200-sample check: 31 covered, 29 agree; whole overlap 88%), so it is used only with verification flags. **Measured ceiling: about 35% of HSK words (3,832 / 11,092) and 61% of HSK characters (1,835 / 3,000) get a Vietnamese reading with evidence.** Cards in the Chinese target are unaffected (pinyin always exists); Vietnamese-target decks will be smaller than the HSK list. This is a source limit, not a bug; report it in `coverage_report.csv`.
- **Shinjitai:** inverted OpenCC `JPShinjitaiCharacters` (16/16 on the prototype's glyph pairs), KANJIDIC2 tie-break.

## NEXT ASSIGNMENT
**Agent: Codex — Stage 2: character table** (PROMPT "STAGE 2", steps 1–4)

Implement the rules exactly as written in DECISIONS; do not change them. If a rule is unworkable, write the problem under "Open problems" here and stop; do not improvise.

1. **Loaders** (one script per source, `pipeline/load_<source>.py`, output `data/staging/<source>.csv`): Unihan (pivot long→wide; fields kDefinition, kMandarin, kHangul, kVietnamese, kSimplifiedVariant, kTraditionalVariant, plus kHanyuPinyin / kXHC1983 if present in the zip; strip `:0E`-style suffixes), KANJIDIC2 (literal, ja_on in hiragana, grade, freq, meanings), hsk30 (chars + words per D30), OpenCC characters (skip the `#` line), libhangul single-character records, Kaikki (parse per D24: word pairs rule A, aligned character readings, attested Hán-Việt syllable set), FrequencyWords (per D25/D26 normalization). Common helpers in `pipeline/common.py`: NFC/strip, **Vietnamese normalizer (D25) with unit tests**, katakana→hiragana, Hangul final consonant, Vietnamese final regex, pinyin numbered→marked (for later).
2. **Build `chars`** per SCHEMA §1.1 and DECISIONS D24, D28, D29, D32, D33 (scope for this stage: the 3,000-character HSK list, trad keys from hsk30-chars; extended in Stage 3). IDs via `pipeline/id_map.csv` (key = `trad`). Use `merge(how="left"/"outer", indicator=True, validate=...)` everywhere; log `_merge` counts.
3. **Derive** `ko_final`, `vi_final` (formulas in `config/rules.json`), `in_hsk_chars`, `level`.
4. **Reports** in `data/final/`: `rules_report.csv` (pivot `ko_final` × `vi_final` using only characters with exactly one Korean reading and exactly one **verified** Vietnamese reading, i.e. `source_vi` ≠ `unihan_unverified`; plus a per-pair examples file for review), `no_jp_form.csv`, coverage per language column (isna counts), `_merge` counts per merge.
5. **Tests** in `tests/` (pytest or plain asserts; they must pass): Vietnamese normalizer (`thuỷ` equals `thủy`, `hoà` becomes `hòa`, `khoẻ` becomes `khỏe`; `loạn`, `toán`, `quý` unchanged); Hangul final (`학`→ㄱ, `국`→ㄱ, `법`→ㅂ, `일`→ㄹ, `안`→ㄴ, `심`→ㅁ, `강`→ㅇ, `가`→none); the 6 multi-target shinjitai cases (畫→画, 鬥→闘, 鹽→塩, 鋪→舗, 莊→荘, 驅→駆) and the 16 prototype glyph pairs (`docs/STAGE1_REVIEW.md` §3); fixed test characters 學 國 茶 行 生 樂 present with ko/vi/pinyin as in the prototype where the sources allow (學 학 học xué; 國 국 quốc guó; 茶 trà; 樂 with lạc/nhạc, 락/악, lè/yuè in the `_all` columns); duplicate-key check on `trad`/`char_id`; NFC check; **rebuild twice → identical output and identical IDs**.
6. **Validation checklist** (`data-pipeline-notes.md` §7) with the 20 fixed test words where they are characters; row counts per stage; log in CHANGELOG. Expected sanity numbers (flag any big deviation instead of hiding it): 3,000 rows; `jp` empty for about 45; verified Vietnamese primary for about 1,835; the 6 jp tie-break cases resolved as above.
7. Create a `pipeline/run_all.py` skeleton that runs download (verify only) → loaders → chars → reports (later stages append). Commit as `[Codex] Stage 2: chars table`.
8. Hand off to **Claude: Stage 2 review** (check `rules_report.csv` against `config/rules.json`: ㄱ→c/ch, ㅂ→p, ㄹ→t, ㄴ→n, ㅁ→m, ㅇ→ng/nh; investigate every large off-pattern cell).

## Planned sequence after Stage 2 (user-approved change, DECISIONS D36)
1. Claude: Stage 2 review → Codex: Stage 3 (words; word rules D24, D26, D27, D30-D32; VI-only additions top 1,200, bands in D27; report counts).
2. **Claude: Vietnamese source search (new task, before Stage 4).** After Codex's Stage 3, Claude reads `coverage_report.csv` and `vi_ambiguous.csv`, then:
   - searches for additional **licensed** Vietnamese resources: a Hán-Việt character dictionary (to verify/replace Unihan's Nôm-contaminated readings), a Chinese-Vietnamese or Sino-Vietnamese word list, a Vietnamese frequency list of words (not syllables); candidates to check include Wikimedia/Wiktionary-derived data other than Kaikki, open Vietnamese dictionaries, and Chinese-Vietnamese resources on GitHub/Hugging Face/academic sites;
   - records each candidate's licence from its own licence file in `docs/SOURCES.md` before anything is used; anything unlicensed, non-commercial-only, or of unclear provenance is rejected (the user is asked only for a licence judgment call);
   - measures each licensed candidate on the same yardsticks as Stage 1 (HSK words gained, agreement with existing readings on a seeded sample, precision of new readings) and records accepted sources and rules in DECISIONS;
   - hands off to Codex (integration + rebuild of `words`, `word_chars`, rules report) or, if nothing usable is found, to Gemini (Stage 4) with the ceiling recorded.
3. Codex: integrate accepted sources, rebuild Stage 3 outputs, report new coverage.
4. Gemini: Stage 4 (sized from the post-integration coverage).

## Heads-up for Stage 3 (not for this session)
- Word rules are fixed in D24, D26, D27, D30, D31, D32. VI-only additions: top 1,200, bands in D27. Report counts when built.
- **At the end of Stage 3, hand off to Claude (Vietnamese source search), not to Gemini** (D36).

## Notes for later stages
- **Stage 5 (Codex), user-approved addition — DECISIONS D20:** daily limit of 20 new (never-seen) cards in カード; reviews unlimited; no visible UI change except smaller counters. State in localStorage `kb_newtoday`. Add a test. List it in the Stage 5 side-by-side difference list.

## Rules to keep in mind (from PROMPT)
- No agent fills a missing reading/fact from its own knowledge. Missing stays empty and is reported.
- Do not edit `prototype/index.html`. Do not edit `SCHEMA.md`/spec/DECISIONS decisions; raise questions here in HANDOFF instead.
- If a source has no license or non-commercial-only terms: do not use it; stop and ask the user.

## Open problems / notes
- Vietnamese coverage ceiling (about 35% of HSK words) with the current licensed sources; the search for further licensed sources runs after Stage 3, before Stage 4 (D36).
- Source #7 stays excluded (D21).
- EDRDG data impose an update-procedure requirement; `download.py --refresh` exists; release documentation must explain updates.
- hsk30 provenance risk: **accepted by the user** (D35, personal non-commercial project; revisit if ever published commercially).

## Log
- 2026-11-04 Claude — applied user decisions: hsk30 accepted (D35); Vietnamese source search moved to after Stage 3 / before Stage 4 (D36). Next assignment unchanged: Codex Stage 2.
- 2026-11-04 Claude — Stage 1 review done: licences accepted, Vietnamese sources selected with verification rules, shinjitai method chosen, priorities set (D23–D34). Next: Codex Stage 2.
- 2026-11-04 Codex — Stage 1 done: downloader + checksums, all licensed-source profiles, licences copied, unlicensed Hán-Việt source excluded by user, two licensed Vietnamese replacements profiled, reproducibility verified. Next: Claude Stage 1 review.
- 2026-11-04 Claude — applied user decisions: new-card limit approved (D20); git email changed, Stage 0 commit author rewritten (D19). Next assignment unchanged.
- 2026-11-04 Claude — Stage 0 done (see CHANGELOG).
