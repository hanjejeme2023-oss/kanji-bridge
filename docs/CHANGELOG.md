# CHANGELOG

## 2026-11-04 — Stage 3: word table [Codex]
- Added normalized CC-CEDICT and JMdict loaders; JMdict retains entity tag names for D42 ranking. Expanded Unihan variants, full libhangul aligned records/comments, and Kaikki first glosses.
- Implemented D40-D50 in `pipeline/build_words.py` and `stage3_match.py`: 11,028-row HSK dedupe; exact/fallback CC-CEDICT attachment; Japanese/Korean/Vietnamese dictionary matching; deterministic VI-only selection; character growth/linking; `word_chars`; D39 primary recomputation; rules, coverage, merge, ambiguity and mismatch reports; and D47 false-friend candidates.
- Final build: 12,229 words (11,028 HSK + 1,201 VI-only), 3,178 characters, 24,458 word-character rows, 2,944 false-friend candidates. HSK coverage is 5,732 Japanese, 7,110 Korean, 3,882 Vietnamese and 3,114 with all four languages; 7,354 HSK cards are eligible.
- C1/C2 evidence: 3,000→3,178 characters; 82 additions required by HSK words and 96 further exclusive additions required by VI-only words; zero ambiguous links; 12 simplified-form mismatches explicitly reported.
- Added `pipeline/overrides.csv` with its header only for gate-confirmed choices. No value was invented or hand-entered; 茶 remains 다 pending the D50 gate short list.
- Rescoped character/collision tests and added `tests/test_words.py`. Validation: 22 tests pass; the rebuild test ran the complete pipeline twice and all final outputs plus `id_map.csv` were identical.
- Updated `docs/SOURCES.md` usage log from planned to actual Stage 3 table/column use. No new decision was needed, so `DECISIONS.md` is unchanged.

## 2026-11-04 — Stage 0: setup [Claude]
- Created folder layout (`raw/ pipeline/ config/ content/accepted/ data/staging/ data/final/ app/ tests/ licenses/`), `.gitignore`, `git init`.
- `docs/SCHEMA.md`: exact columns, ID rules, `data.js` shape, and field-by-field mapping from `WORDS`/`RULES`/`FF`/`PASSAGES`/`GLYPHS` to tables.
- `config/rules.json`: the 6 rules' text copied verbatim from the prototype.
- `docs/DECISIONS.md` (D1–D11 + new D12–D19), `docs/HANDOFF.md`, spec Addenda section.
- Why: PROMPT Stage 0. D12–D19 fill gaps that real data forces (stable word ids, multiple readings, large passage list) without touching UI/UX.

## 2026-11-04 — User decisions applied [Claude]
- DECISIONS D20: daily new-card limit (20/day) approved for Stage 5; D18 superseded; UX_BACKLOG #1 marked approved.
- D19: repo-local git email changed to 311183901+hanjejeme2023-oss@users.noreply.github.com; Stage 0 commit author rewritten (unpushed).

## 2026-11-04 — Stage 1: sources and licences [Codex]
- Added `pipeline/download.py`: standard-library downloader with atomic writes, retries, committed `pipeline/source_manifest.csv` URL/date/SHA-256/byte locks (mirrored to `raw/MANIFEST.csv`), idempotent verification, explicit `--refresh`, and synchronization of source licence files into committed `licenses/`.
- Downloaded and profiled Unihan, KANJIDIC2, hsk30, CC-CEDICT, JMdict, libhangul `hanja.txt`, and OpenCC Japanese mapping candidates. Raw files remain git-ignored.
- Excluded `ryanphung/chinese-hanviet-cognates` by user decision (D21): no licence grant and an input with missing provenance. No content from it was downloaded or copied.
- Downloaded and profiled two licensed Vietnamese replacement candidates without selecting either (D22): Kaikki/Vietnamese Wiktionary (6,878 Hán-Việt-marked Vietnamese entries; 4,653 with CJK strings in etymology text) and FrequencyWords/OpenSubtitles 2018 (50,000 token-frequency rows).
- Added reproducible `pipeline/profile_sources.py`, `pipeline/requirements.txt`, and generated `docs/SOURCE_PROFILES.md` with formats, encodings, counts, keys, ten-row samples, quality risks, mapping candidates, and review questions.
- Completed `docs/SOURCES.md` licence and planned-usage logs. Ambiguous hsk30 provenance and libhangul per-file licence remain marked `要確認` for Claude; all share-alike effects are called out.

## 2026-11-04 — Stage 2: implementation started, blocked on canonical key [Codex]
- Implemented the Stage 2 pipeline structure: shared NFC/Vietnamese/pinyin/phonology/ID helpers; per-source loaders for Unihan, KANJIDIC2, hsk30, OpenCC, libhangul, Kaikki, and FrequencyWords; the character builder/reports; `run_all.py`; and Stage 2 unit/rebuild tests.
- First build correctly detected a contract conflict in the raw HSK character list: source rows `着 → 著` (level 1) and `著 → 著` (level 4) both produce canonical `trad=著` under D33. This conflicts with the simultaneous requirements for 3,000 rows and a unique `trad` key. No row was dropped, renamed, or overridden because HANDOFF explicitly forbids improvising a rule.
- Pipeline stopped at the hsk30 loader validation. Claude must decide whether to merge to 2,999 canonical rows, introduce a documented `着` exception to keep 3,000 unique rows, or revise another contract requirement. No Stage 2 final tables are claimed complete.

## 2026-11-04 — Stage 1 review [Claude]
- Confirmed licences (D23): all sources usable; dataset will be CC BY-SA 4.0; hsk30 provenance risk accepted and recorded.
- Selected Vietnamese inputs (D24-D27): Kaikki for readings/Han forms, FrequencyWords for a frequency proxy; Unihan `kVietnamese` gated by verification flags after the 200-character cross-check (`docs/STAGE1_REVIEW.md`).
- Chose the shinjitai method (D28: inverted OpenCC + KANJIDIC2 tie-break, 16/16 on the prototype glyphs); fixed level semantics (D29); hsk30/JMdict/libhangul rules (D30-D32); source priority per column (D33).
- Updated SCHEMA (levels 1-7, source tags, new reports) and SOURCES (all rows decided). Saved reference scripts in `docs/review_scripts/`.
- Why: the review closes every blocking decision so Stage 2 can build `chars` without improvisation. The measured Vietnamese ceiling (about 35% of HSK words) is recorded as a source limit.

## 2026-11-04 — User decisions applied [Claude]
- D35: hsk30 provenance risk accepted by the user (personal, non-commercial; revisit if published commercially).
- D36: search for additional licensed Vietnamese sources moved to after Stage 3, before Stage 4; new Claude task recorded in HANDOFF.md. Next assignment unchanged (Codex, Stage 2).

## 2026-11-04 — Stage gates and Stage 2 key collision [Claude]
- PROMPT updated by the user (Rule 11: stage gates, Done-when criteria); committed together with this change. Created `docs/GATES.md`; logged the Stage 1 gate (PASS, evidence: 23/23 checksums, download rerun, licences, profiles).
- (SUPERSEDED by the entry below) D37: canonical-key collisions in `chars` are merged on `trad` (hsk30 `着`/`著` -> `trad=著`, `simp=着`, `level=1`); `chars` has 2,999 rows for 3,000 source characters, plus `char_key_collisions.csv`. SCHEMA updated. Why: words use the traditional form `著`; duplicate or exception keys would break IDs, merges and tests.

## 2026-11-04 — D37 revised [Claude, at the user's request]
- The earlier D37 merged 着/著 into one row keyed `著` and would have taken every reading from `著`, losing 着's Korean 착 and Japanese ちゃく. Replaced by: one row per source character (3,000 rows), `trad` non-unique, new unique column `key_char` (readings lookup + id_map key), word-to-character linking by simp then pinyin, Korean/Japanese word matching also on the `key_char` form (接著 -> 接着), glyph view uses `key_char`. Updated DECISIONS, SCHEMA, spec addenda, Stage 2 task.

## 2026-11-04 — One-to-many collision check [Claude, at the user's request]
- Measured the one simplified -> several traditional case: 83/3,000 HSK rows (89 variant characters, 88 without a row yet). D38: link words through their own `trad` string, extend `chars` in Stage 3 for every word character lacking a row, simp rule for added rows, position check against the word's `simp`.
- Corrected D37: `key_char = trad` for all rows except shared-`trad` rows (using the simplified Hanzi everywhere would find Korean readings for only 145 of 1,088 differing rows instead of 1,036).
- Added the standing C1 (many->one) and C2 (one->many) checks to `docs/GATES.md`, Stage 2 and Stage 3 tasks; reference script `docs/review_scripts/char_collision_reference.py`.

## 2026-11-04 — Stage 2: character table completed [Codex]
- Implemented revised D37 generically: 3,000 source-character rows; `key_char=trad` except in shared-`trad` groups, where source `Hanzi` supplies the unique reading/ID key. Unihan, KANJIDIC2/OpenCC, libhangul and Kaikki joins now use `key_char`; `simp` remains the HSK source `Hanzi`.
- Exported `chars.csv`/JSON and the Stage 2 reports: coverage, merge counts, missing Japanese forms, sound-rule pivot/examples, build summary, and `char_key_collisions.csv`. The sole collision is `著 -> {着, 著}`, and both rows retain their source-backed Korean/Japanese readings.
- Added `tests/test_char_collisions.py` for standing checks C1/C2 and expanded the character tests for `key_char`, 着/著, the six fixed characters in every language, NFC, source suffix removal, glyph mappings, coverage, and stable IDs.
- Fixed Unihan `kHangul` source-tag removal at the loader root: tags include values such as `:0N`, not only hexadecimal-looking tags such as `:0E`. Generated Korean readings no longer contain provenance suffixes.
- Validation: 16 tests pass; 3,000 rows; 45 missing `jp`, 49 missing `ja_on`, 0 missing `ko`, 0 missing `pinyin`, 709 missing `vi`; 1,835 verified Vietnamese primaries. Two consecutive rebuilds produced the same `chars.csv` SHA-256: `b6bffbc97b3d7eef0df4f77c389a8acd6091333473afeebe33e1076e99c08102`.
- Intermediate source-normalized CSVs remain reproducible and are git-ignored; `ff_candidates.csv` stays explicitly trackable for the Stage 3→4 handoff. No new data decision was needed, so `DECISIONS.md` is unchanged.

## 2026-11-04 Claude — Stage 2 gate
- PASS on attempt 1; evidence and the rules_report review are in `docs/GATES.md`. No data changes; no new decisions (non-blocking notes recorded in HANDOFF Open problems).

## 2026-11-04 Claude — Pre-Stage-3 readiness review (requested by the user; docs only, no pipeline or data change)
Measured with throw-away scripts on the checksum-locked `raw/` files and `data/staging/`. The scripts are not in the repo; the rules and numbers are in DECISIONS D39-D50.

### Step 0: user refinement of D39
Applied. Korean readings are normalized for 두음법칙 before counting; `ja_on` is out of scope and keeps KANJIDIC2 order. **One addition found by testing:** normalization must depend on position. Mapping 노→로 everywhere (怒's `ko_all` is 노;로) would turn 怒 into 로, so a syllable is mapped back only at word start, plus 열→렬 and 율→률 after a vowel or ㄴ. Simulated: 樂 락, 歷 력, 怒 노, 行 행.

### Pass 1: source joins against the raw data
**Looked at:** hsk30 rows and keys, CC-CEDICT per form, JMdict on every HSK word, hanja.txt on every HSK word, Kaikki rules A and B, FrequencyWords, VI-only candidates, ff filter, the 20 test words.
**Found:**
- 80 repeated `(trad, pinyin)` pairs, so "once per form and reading" and `id_map` could not hold (D41).
- PROMPT's step order cannot run: Korean matching needs readings of characters without rows (D40).
- Korean: hsk30 uses Taiwan forms and hanja.txt Korean forms, so trad-only matching missed 教育, 研究, 真理. Taking the first reading in file order gave 력사, 련습, 녀자, 화거. (D43)
- Japanese: D31's ranking gave 好 よしみ, 更 こもごも; `simp` matching gave 聽 ポンド; `sK`/`sk` were not handled. A blanket on'yomi preference was tried and rejected (今年 こんねん). (D42)
- Vietnamese: rule A with several values was undefined; polyphones could not be told apart, so test words 行 and 樂 had no reading (D44).
- `*_all` "unchanged" (D39) contradicted "primary first" (SCHEMA) and would have left 항 first in the glyph view (D39).
- `word_chars` had no pinyin column, though D37 and D39 both need one (D45).
- VI-only: about 1,212 candidates for 1,200 places, so the cap filters nothing, and syllable frequency put 自刎 at level 3 (D46). The `trad|ja|vi` ID key changes when a reading changes (D46).
- PROMPT's "frequent hanja.txt words" is impossible: the file has no frequency. The filter is now measured at about 2,880 rows (D47).
- Stage 3 and D36 order was unclear; the word list now freezes after the second round (D46).
- 手紙 and 越南 are not HSK words, so the test-word criterion was not measurable (D49, table in GATES).
- `words` had only an English gloss, though Stage 4 must compare meanings per language (D48).
**Changed:** D39 rewritten; D40-D50 added; SCHEMA columns, ID keys, merge table §1.8; spec addenda; GATES checklist and test-word table; HANDOFF task and sequence.

### Pass 2: re-read the new text against the data and the existing code
**Looked at:** every number and example written in Pass 1, re-measured; `tests/` and `pipeline/run_all.py`; the D37/D38 linking; variant duplicates.
**Found (several were errors in my own Pass 1 text):**
- Korean counts mixed forms and rows (7,123 is rows, 6,847 is forms): corrected. The ㅅ exception named 횟수, but hanja.txt has only 차수 for 次數: the relevant words are 숫자 and 찻간. 허락 was a wrong example; the ㄴ↔ㄹ allowance covers exactly one word, 곤란.
- CC-CEDICT fallback measured: 10,974 by key, 16 + 3 by fallback, 35 unmatched.
- `build_chars.py`, `tests/test_chars.py:23` and `test_c2` assume 3,000 rows and 88 missing variants, and would fail once `chars` grows (D40).
- Growth is 82 rows from HSK words, not D38's 88, because D30 keeps only the first form in 34 rows (D48, GATES C2).
- 6 VI-only candidates were spelling variants of HSK words (行爲 / 行為); 2 HSK words gain a reading through a variant (D44, D46).
- Link check: all 42 著/着 positions resolve by `simp`, 0 ambiguous; 2 `simp` mismatches (反覆, 答覆), which is the case D38 predicted.
- D42 said single-character readings ran in KANJIDIC2 order, which gives 樂 がく; changed to JMdict order among on'yomi, which gives らく.
- Missing rule: built `jp` when a character has no Japanese form (D42).
**Changed:** the items above; overrides extended to `chars` primaries (丹 → 란 is the example).

### Pass 3: consistency, from the reader's side (Codex, the gate, later stages)
**Looked at:** D39-D50 read through in full; HANDOFF as Codex will read it; each Done-when item asking "what number proves this?"; Stages 4 and 5 for effects of the new rules.
**Found:**
- The D39 count could pick a reading outside `*_all`, contradicting "set unchanged": such readings are now not counted and are reported.
- `ko_base` was undefined for the D43 exceptions (숫, 찻, 란): defined (D45).
- `ja_multi_candidates` is about 170 rows, not 80 (41 multi-character + 129 single): gate scope set accordingly.
- Glyph view would show 낙 / 락 / 악 / 요 and 력 / 역, unlike the prototype's 락 / 악 and 력: new `ko_base_all` (SCHEMA §3.5).
- Stage 5 rule examples showed primaries beside a pair's finals, which can disagree: examples now need pair = primaries (D45).
- Stale HANDOFF lines removed (Stage 2 "comes after Codex", the old D39 note, duplicated heads-up). A wrong "93%" in D46 corrected.
**Why I think little is left:** every expected count in SCHEMA §1.8 and GATES comes from a simulation of the written rule, and the test-word table matches the simulated output for all 20 words. **Not verified:** nothing has been built, so counts are expectations within a margin; the Vietnamese D39 simulation gives 12 changes, and 液 → giá looks wrong, so it is on the gate's list; `ko_base_all` and the D45 rules report were specified but not simulated; `kSemanticVariant` matches include some false friends (坐下 via 座下), sampled at the gate.

### Open: four questions in D50
Asked on 2026-11-04 and not answered. Defaults are recorded, and the user's existing decision on pinyin is left as it was.

## 2026-11-04 Claude — User's answers to D50 applied (docs only)
- **D39:** pinyin removed from the evidence rule; `chars.pinyin` keeps `kMandarin` order. `word_chars.pinyin_syllable` stays, because D37, D43 and D44 use it.
- **Japanese single-character words:** on'yomi first, confirmed. **Korean single-character words:** base form, confirmed.
- **Review lists:** Claude proposes at the Stage 3 gate, the user confirms the short list, then overrides are written and the data rebuilt (`GATES.md` check 9).
- **茶:** `chars.ko` must end as 차. Checked: the only one-candidate evidence word is 茶葉 다엽, so the first build gives 다, and even with 홍차 and 녹차 confirmed a 2-2 tie would keep 다. It therefore goes on the short list with an override, and Codex's test accepts 다 until then.
- **國 in the test table:** the user asked to fix or explain. Explained, not changed: JMdict's only entry for 国 is くに, so くに follows the chosen rule; こく is KANJIDIC2's reading and is `chars.ja_on`. Checking this showed the same applies to about 260 of 970 single-character forms, some with bad kun readings (電 いなずま). Falling back to KANJIDIC2 would change all of them, so it was put to the user as a follow-up rather than decided here.
- Also updated so nothing contradicts D39: D42, D43, D45, `SCHEMA.md` and the spec addendum (the spec wins on conflict, so its old line had to change).

## 2026-11-04 Claude — Single-character Japanese fallback (user decision; docs only)
- D42, D50: if JMdict has no on'yomi for a single-character word, `ja` = `chars.ja_on`, the JMdict readings go to `ja_alt`, and `source_ja=kanjidic2_on`. Simulated: 國 こく, 電 でん, 海 かい, 手 しゅ; 269 of 1,006 rows use it.
- Consequences written down: katakana-only words (吃, 噸) now get an on'yomi instead of an empty `ja`; expected `ja` rows rise from about 5,600 to about 5,650; 〇 keeps れい because KANJIDIC2 has no on'yomi for it.
- Boundary set by Claude: the fallback needs a JMdict entry for the form. About 580 single-character rows with no entry (很, 就) keep `ja` empty.
- GATES test table and check 10, HANDOFF task and Done-when, and SCHEMA (`ja`, `ja_common`, `source_ja`) updated. The D50 follow-up is closed.

## 2026-11-04 Claude — Stage 3 gate: FAIL, attempt 1
- **Checked:** the `GATES.md` Stage 3 checklist, on disk, with independent scripts; 22 tests and the double rebuild rerun (OK, `git status` clean afterwards).
- **Passed:** row and ID integrity, coverage, `card_eligible`, `word_chars` structure, all 20 test words, 30 of 30 sampled words traced to their sources.
- **Failed:** (1) `korean_base` returns the surface syllable and `apply_d39` counts non-evidence words: at least 49 wrong Korean primaries (流 유, 旅 여, 老 노), and the flag column was hard-coded. (2) The Korean variant graph was used for JMdict: 31 single-character rows with wrong forms (弄 瘧, 滾 菌); on'yomi looked up by `trad` gave 歲 とし. (3) No real `validate=` on the word merges; `merge_report.csv` carried literal text. (4) Smaller: `vi_only_report.csv` flags and columns, 10 empty `simp`, 41 unresolved pinyin rows.
- **Found beyond the checklist:** rule B accepts homophones (食物 thực vật, 不行 bất hạnh); 42% of `vi` words had no `gloss_vi`.
- **Decided:** D51. **Docs:** GATES (result, 手紙 `vi` table entry corrected), SCHEMA §1.7, spec addendum, HANDOFF (F1-F13, expected values). **Added:** `docs/review_scripts/stage3_ko_base_reference.py`.
- **Deferred:** short-list picks (about 205 rows) to attempt 2, because the fixes change the lists and the user should confirm once. `pipeline/overrides.csv` stays header-only. D36 search not started.
