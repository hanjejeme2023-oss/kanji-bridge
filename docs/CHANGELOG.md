# CHANGELOG

## 2026-11-12 — Stage 5 gate: PASS, Stage 5 complete (app v2) [Claude]
- Gate of the app phase (Parts A-D) against Stage 5 Done-when, D71/D76, APP_PHASE §4 and Global Rule 10: **PASS** (`docs/GATES.md`, **D77**). New review scripts `docs/review_scripts/stage5_gate_run.py` + `stage5_gate_harness.js`: copy `app/` alone to a temp folder and run it from `file://` in headless Chrome/Edge with every host blocked, exercising all five views (0 console errors, 0 "undefined"/"NaN"/"null" in 17 view states, every feature check passes).
- Independent re-derivation of `glyphs`, `examples` offsets and counts from the final tables; 154/154 non-rebuild tests; one fresh rebuild 273 s, byte-identical. Part D's long test times were machine load (Part D changed no code the slow tests or the build run).
- D76 item 9 corrected (214 no-pinyin words are in the カード deck, offered only under ベトナム語); 「該当する単語はない」 accepted; SCHEMA §3.6 lists `kb_newtoday`; APP_PHASE marked done.
- HANDOFF: restored the ≈ 210 lines Codex removed in Parts C/D without archiving (verbatim in `HANDOFF_ARCHIVE.md` §6; still-valid open problems, notes and rules back in HANDOFF); new rule D77 item 7. Non-blocking loop-4 items: 使われ方 duplicates for reduplicated words, stale `tests/stage5_benchmark.py`, render time (≈ 3 s headless for 字体 すべて). User click-through checklist and a real-app console benchmark in HANDOFF. Next: Codex — Stage 6 loop setup and loop 1 Step 1. No request sent.

## 2026-11-12 — App phase Part D: false-friend cards and reading review [Codex]
- Reformatted 偽の友達 language lines as meaning followed by a muted parenthesized reading (for example 「韓 列車（기차）」), while retaining D68 fixed-note rows. Open entries now show available Chinese and Vietnamese examples, preferring the language's `ff` row and falling back to `card`, with highlighted targets, Chinese pinyin and Japanese translations. 字体's small 偽の友達 mark now switches to the list and opens that exact word.
- Added the approved 偽の友達 list/flashcard modes and 中国語/ベトナム語 trap switch. A round selects up to 20 trap-language entries by lifetime `miss` descending, then never-seen status, then `word_id`; 「まだ」 increments `miss` and appends the card to the current queue, while 「わかった」 increments `ok`. State persists as `{miss, ok}` under `<word_id>:<lang>` in `kb_ffcard`; Enter/Space flips and 1/2 rates; speech uses the existing mute guard.
- Added 読解 `kb_unknown` marking on every linked-word tap, a per-passage わからない review list that reopens the same detail sheet, and `kb_read` passage-leave tracking. A selector's ✓ is computed at render time only when the passage has been left and none of its linked word IDs is currently unknown; clearing via the existing card/glyph `clearUnknown` makes ✓ appear, and marking the same word in any passage removes it again.
- Extended Stage 5 tests for list formatting/fixed notes, example preference/fallback/absence, 20-card and weak-first ordering, 「まだ」 queue behavior, storage cleaning, 読解 first-display/leave/mark/clear/re-mark ✓ rules, review markup and leave triggers. Focused app tests **21/21 pass** after the final rebuild; the full offline non-rebuild suite **154/154 passes in 831.888 s**; full override-independent rebuild determinism **passes in 2,102.021 s**. Inline JavaScript compiles, `app/data.js` is byte-identical to `data/final/data.js`, and `prototype/index.html` is unchanged. Offline only: no request, `--check`, `count_tokens` or browser automation.

## 2026-11-12 — App phase Part C: sound-rule and glyph typing tests [Codex]
- Added the 音のルール table test. 「テストする」 changes the existing complete-example table's Vietnamese and Chinese cells into shared-judge inputs with tone hints; Enter/blur judges and 「テストをやめる」 restores the table. `kb_ruletest` stores per-rule/per-character language results while reopened/reloaded inputs remain empty and retain only the stored green/red background. The original multiple-choice `kb_rules` progress is untouched.
- Expanded 字体 from the Part B differing-form subset to all 2,164 ordered character rows. Word readings appear before remaining character readings (還 `hái / huán / xuán`; 行 starts `xíng / háng`, `hành / hàng`), and every non-empty target gets its per-reading tone hint.
- Replaced the old 字体 multiple-choice card with the full-list pinyin/Vietnamese typing quiz. Results are stored by `char_id` in `kb_glyphquiz`; legacy word keys are ignored; reopened inputs are empty with their stored colors. Added filtered right/answered scoring, level 1-7 filters and 間違えた字だけ while retaining the four existing filters. Empty target lists render no input.
- Added lazy 使われ方 panels on every glyph row: target character/syllable highlights, up to three Chinese and Vietnamese examples, 文語, 例なし, 581 accepted character notes, and small 偽の友達 marks that switch tabs. Panels are closed by default and open after a quiz answer in the current session.
- Added `clearUnknown(word_id)`: a fully correct card clears its mark; a correct glyph-language response clears only the single-character word IDs whose pinyin/vi/`vi_alt` reading was actually typed. Part D will add the marks.
- Extended Stage 5 tests for Part C storage/empty reopen cells, shared judging callbacks, glyph count/order/readings, legacy-key filtering, filters/score, usage content/highlights/tags/notes/marks and targeted clearing. **151/151 non-rebuild tests pass** in 250.711 s; focused app tests **18/18 pass** after the rebuild; full override-independent two-canonical-build determinism **passes in 787.510 s**. Inline JavaScript compiles; standalone `app/data.js` is byte-identical; the prototype is unchanged. Offline only: no request, `--check`, `count_tokens` or browser automation.

## 2026-11-12 — App phase Part B: shared typing and multi-character cards [Codex]
- Rebuilt `glyphs` as D76's one-row-per-character shape: 2,164 rows = 1,520 characters covering 1,571 single-character words plus 644 character-only rows. Word readings are distinct and ordered by level/ID; character-only `unihan_unverified` Vietnamese readings remain empty. `usage` stays at 2,164 rows. The compact payload is 6,631,692 bytes.
- Added one shared Chinese/Vietnamese judging implementation for カード and the Part C typing tests. Chinese ignores tones/case/spaces/apostrophes/hyphens and accepts `ü`/`v`/`u:`. Vietnamese performs full per-syllable Telex conversion (shape keys, late `w`, and tone keys), ignores only tones, preserves ă/â/ê/ô/ơ/ư/đ distinctions, accepts `vi_alt`, and supports several comma/slash-separated readings.
- Added tone hints, Enter/Space advance behavior, the persisted global `kb_mute` toggle, per-tab item counts and the five fixed explanations. The existing 字体 view reads the new glyph shape but remains limited to the 1,246 differing-form characters until Part C; 音のルール, 偽の友達 and 読解 otherwise retain their pre-Part-C/D behavior.
- カード now contains only the 6,983 multi-character eligible words (172 / 370 / 783 / 795 / 891 / 885 / 3,087 across levels 1-7); saved single-character SRS entries stay untouched but are not offered. Correct answers accept the shared judge and revealed cards show available task-6 Chinese/Vietnamese examples with highlighted targets and no placeholder for a missing example.
- Tests cover the D76 glyph counts/order and 還/行/得 cases; full Telex including `tieenf`/`tieen` right and `tien` wrong, `dduowngf`, late-`w` spellings, initial x/r/s, shape mismatches, `vi_alt`, several readings, tone hints, global controls, deck membership and examples. All 148 non-rebuild tests pass; the full override-independent, two-canonical-build determinism test passes in 741.913 s. Offline only: no request, `--check`, `count_tokens` or browser automation.

## 2026-11-12 — User's answers to the app-phase design choices (D76) [Claude]
- Recorded the user's answers to every choice D71/D75 left open as D76: 字体 one row per character (2,164 rows) with several readings (any one, or several separated by a comma or slash, is right; all readings shown; per-reading tone hints, also for Vietnamese); full Telex (letter and tone keys) in カード, 音のルール and 字体; Space as proposed; the 音のルール test and 字体 quiz keep each item's green/red in localStorage but reopen with empty boxes; 読解 ✓ = passage left at least once and none of its words marked わからない; fixed wording confirmed.
- Accepted Part A's browser benchmark (page load 0.35 s, adapter cold 40 ms, 偽の友達 median 147 / max 700 ms, 字体 median 69 / max 561 ms; `data.js` 6.32 MiB): no data split. Noted for the Stage 5 gate: 411 words without `pt` (215 without pinyin + 196 `ff_only`), none of them typed in カード or 字体.
- `docs/APP_PHASE.md`: Part A marked done; remaining work re-cut into Part B (glyph data change first, shared judging with Telex and several readings, tone hints, global controls, カード), Part C (音のルール test, 字体), Part D (偽の友達, 読解), with test cases for Telex and several readings. SCHEMA §2.1 `glyphs` shape `[char_id, [word_id...], level, [py...], [vi...]]`; §3.6 app-phase localStorage keys. D71/D75 marked as amended. HANDOFF: next = Codex Part B only. No request sent.

## 2026-11-12 — App phase Part A: task-6 merge and standalone data [Codex]
- Added an offline, fail-closed task-6 merge. It verifies all 224 accepted main logs/inputs against a fresh deterministic build, validates the two accepted rerun batches and 25-key round-1 set, selects the highest rerun answer, and applies the 29-row review overlay only when `generated` matches. Final additions: 10,367 `examples` (zh card 5,783 / zh ff 560 / vi card 3,909 / vi ff 115; 998 pinyin punctuation-space normalizations) and 581 `char_notes`.
- Extended `data.js` with compact examples/notes, 2,215 glyph rows over 2,164 characters, 2,164 usage rows, pinyin tone digits on 12,097 words (411 omitted) and 1,277 literary flags. The payload is 6,622,497 bytes (6.32 MiB), +2,855,721 bytes (+2.72 MiB) from 3.59 MiB and below the 8 MiB stop limit.
- The build copies identical bytes to `app/data.js`, builds `app/index.html` with `<script src="data.js">`, and keeps the pre-Part-C 字体 view limited to differing-form characters. The `app/` directory now runs alone; no Part B/C UI feature was added. Updated the offline browser benchmark for the new compact arrays; no browser automation was used.
- Task-6 status now reads accepted content (zh 127/127, vi 84/84, notes 13/13). Python task/dry-run/pilot/rerun modes and PowerShell `-Tasks 6` refuse before client creation; the launcher no longer retries accepted task 6. No request was sent. The user keeps the gcloud login for now; VERTEX_SETUP part H is later.
- Tests: 143 non-rebuild tests pass. Rebuild determinism was strengthened to hash `app/data.js` and `app/index.html` as well as all final data and IDs; PASS in 853.270 s. Added a short retry around Windows atomic replaces after a transient scanner lock caused one preliminary rebuild attempt to fail; the retry has a regression test.

## 2026-11-12 — Task-6 re-check: task 6 accepted (D75); app-phase contract [Claude]
- Re-checked the user's G7 run (resume of the 56 zh keys + rerun round 1): zh 127/127, vi 84/84, notes 13/13 validated; integrity and cost verified ($0.301874; ledger $52.76321975). Read all 81 new answers and ran the tone-aware pinyin check over every new zh sentence (0 mismatches). 24 of 25 reruns fix their feedback; thành nhân dropped (overlay row 29). Recorded the gate's too-strict 王妃 feedback.
- Recorded the user's sample answers (30/30 ○) in `docs/TASK6_USER_SAMPLE.md`.
- Accepted task 6 and moved outputs, logs, inputs and `rerun1/` to `content/accepted/task6/` (checksums identical; 134 non-rebuild tests pass). Overlay `config/task6_review.csv` 29 rows. Added `docs/review_scripts/task6_recheck.py`.
- Wrote the app-phase contract: `docs/APP_PHASE.md` (Codex Parts A/B/C, fixed wording) and SCHEMA §2.1 (`examples`, `char_notes`, `glyphs`, `usage`, words `pt`/`lit`, `app/data.js`); SCHEMA §1.9/§1.10 expected counts and the effective-answer rule. D75. No request sent.

## 2026-11-12 — Task-6 validator and runner fixes (D74 item 1) [Codex]
- Completed the pinyin inventory, accepted uppercase tone-marked vowels and added log-only `translation_script` warnings. All 11,108 stored full-run items and 150 pilot items revalidate. Status stays zh 85 validated plus 42 partial with the same 56 failed keys, vi 84/84 and notes 13/13. Full-run logs match the D73 zh/vi v2 and notes v1 prompt hashes.
- Task-6 logs keep the last answer object for each failed key and append request records across attempts. Validated rerun batches are skipped on retry. Offline tests exercise older logs and failed-key-only resume.
- Dry-run completed for 11,164 items in 224 batches. The round-1 input test built all 25 review keys (19 zh and 6 vi) with their feedback and without a client. All 135 tests pass, including rebuild determinism in an isolated copy. No request sent.

## 2026-11-12 — Stage 4 task-6 gate (D74) [Claude]
- Integrity of the full run (user, overnight 11-12): inputs = fresh build, v2/v1 prompt SHAs, all 11,108 stored items re-validate; run $16.788226, ledger $52.46134575.
- Diagnosed the 42 partial zh batches (56 keys): two validator bugs, not model errors: `PINYIN_SYLLABLES` lacks ran/rang/rao (然 让 染 绕 …) and `ZH_PINYIN_RE` lacks capital tone-marked vowels (sentences starting with 按/爱/二 …). Answers of failed items are not logged, so they must be resumed after Codex's fix (D74 item 1).
- Content review: 3,934 items read + script pinyin check of all zh sentences; 48 errors (1.22%) + 5 pinyin; no systematic class, no prompt change. `config/task6_review.csv` (28 rows), `config/task6_rerun.csv` round 1 (25 keys), `docs/TASK6_USER_SAMPLE.md` (30 items, Japanese only). Evidence `docs/TASK6_GATE_REVIEW.md`; scripts `docs/review_scripts/task6_gate_reference.py`, `task6_gate_write.py`.
- Committed the task-6 outputs, logs and cost-log rows (still in `content/generated/task6/` until acceptance). VERTEX_SETUP G7 updated. No request sent by Claude.

## 2026-11-11 — Task-6 pilot review (D73) [Claude]
- Read all 150 pilot items (`docs/TASK6_PILOT_REVIEW.md`): zh 50/50 good (3 minor: 2 gloss-copy translations, 北京 pinyin lower case); vi 3 clear errors of 50 (sát nhân refused by the v1 violence rule, bán niên wrongly refused, cố nhân trap not evident); notes 50/50 correct (one extra reading). Pilot cost $0.169144 incl. check (two single-item repairs); ledger $35.67311975.
- Prompts `task6_zh_v2.md`, `task6_vi_v2.md` (five added rules; schema/validator unchanged); notes stay v1. `pipeline/stage4/runner.py` `TASK6_PROMPT_FILES` zh/vi paths → v2 (two lines). Offline dry-run base $16.84; offline status OK; 54 Stage 4 tests (task6, safety, validators) pass.
- Committed the pilot outputs/logs and the cost-log rows. `VERTEX_SETUP.md` part G6-night (overnight steps). No request sent by Claude.

## 2026-11-11 — Stage 4 task-6 support (D72), offline [Codex]
- Added deterministic task-6 builders for 5,783 zh card + 565 zh false-friend sentences, 4,051 vi card + 142 vi false-friend sentences, and 623 character notes. The contract counts, false-friend coverage conflicts (20 zh / 8 vi), N1-N3 selection and global batch ranges b001-b224 match exactly; task-6 inputs preserve the specified field order.
- Added the three ordered response schemas and strict task-6 validation: whole-batch key/schema checks; item-isolated repair errors; Mandarin syllable inventory/alignment DP with erhua, neutral tones and apostrophes; exact target tones and 一/不; simplified-character enforcement; Vietnamese orthography, length and case-insensitive whole-word target; Japanese translations, notes and warnings.
- Added task-6 generation, at most two failed-item repairs, `partial`/`failed_keys` resume, three-kind pilot, review rerun rounds, per-kind offline status and a truly offline dry-run. The fixed Free Trial deadline guard is 2026-11-16T08:00:00Z with explicit post-upgrade override; the hard ceiling is $200 and the task-6 fallback reserves 200 output tokens per item. Tasks 1-5 remain refused.
- Wrote 224 deterministic full input batches and three 50-item pilot inputs. Dry-run estimate: zh $10.479970, vi $5.591154, notes $0.640156, base total $16.711280; D72's repair/pilot/rerun planning envelope remains $23 expected / $27 conservative / $36 worst. Offline status reports all 224 task-6 batches missing and the unchanged $35.50397575 ledger.
- Added task-6 builder, schema, validator, repair/resume, ceiling, deadline, offline and rerun safety tests. **129/129 non-rebuild tests pass.** No request was sent; no final data, accepted content, prompt, overlay, prototype, app or rebuild step changed.

## 2026-11-11 — User decisions after app v1 (D71); Stage 4 task 6 design (D72) [Claude]
- Recorded the user's decisions after trying app v1 (`8e41236`) as **D71**: カード multi-character only, single-character words move to 字体; a typing rule for every tab (tones shown, letters judged; Vietnamese keeps ă â ê ô ơ ư đ, Telex accepted); Enter/Space, mute, item counts; 偽の友達 option A, example sentences and flashcards; example sentences on cards; 字体 typing quiz with a 使われ方 panel and usage notes; 音のルール typing test; 読解 わからない marks; `app/` folder runs alone; ceiling $100 → **$200**. Global Rule 10 exception for exactly these features (user approval); Global Rule 1 amended for packaging. The Stage 5 gate is postponed until after the app phase; its extra check items (user's browser timings, 1,246 字体 rows, 9,171 `word_chars` rows, passage-selector wrap, atomic writes, `data.js` size after task 6) are listed in HANDOFF.
- Designed **Stage 4 task 6** (**D72**, `docs/TASK6_DESIGN.md`): zh 6,348 sentences (5,783 card + 565 false-friend), vi 4,193 (4,051 + 142), 623 字体 usage notes = 11,164 items / 224 requests of 50; false-friend coverage decided by code (identical meaning string); fail-closed validator with pinyin syllable alignment, dictionary target pinyin, no sandhi, no traditional-only characters, case-insensitive Vietnamese target; item-level repair, rerun rounds, pilot, offline dry-run; credit date guard at **2026-11-16 08:00 UTC** with an explicit override. Estimate ≈ $18 base / $23 expected / $27 conservative / $36 worst; ≈ 6.5-7 h.
- Wrote prompts `content/prompts/task6_zh_v1.md`, `task6_vi_v1.md`, `task6_note_v1.md`. SCHEMA §1.9 `examples`, §1.10 `char_notes`, §2 packaging note, §5 task 6. UX_BACKLOG #5 note, #7 (字体 flashcards, not now), #8. VERTEX_SETUP parts G (re-enable for task 6) and H (revoke and disable afterwards).
- No data, code or app change; no request sent. Next: Codex — Stage 4 task-6 support (offline).

## 2026-11-08 — Stage 5: full-data offline app integration [Codex]
- Added deterministic `data/final/data.js` export to `run_all.py` and reproducible `app/index.html` generation from the untouched frozen prototype. Full payload: 3,766,776 bytes; 12,508 words, 9,171 aligned word-character rows, 4,044 false-friend rows, 80 passages, six sound rules and 1,246 glyph rows.
- Replaced the five prototype arrays with SCHEMA adapters: 8,554-card ordered/target-filtered deck; ID-keyed SRS/custom/false-friend state; aligned rule tags and primary-pair examples; stored false-friend reading-display precedence; resolved passages; glyph `ko_base_all`; missing values blank; Vietnamese alternate judging; `note_ja` only in 読解 detail.
- Implemented D20's 20-new-card local-day limit (`kb_newtoday`) with unlimited reviews and persistent introduced-but-unrated cards. The only layout rule added is `#psel{flex-wrap:wrap}` so 80 passage pills do not overflow; all other prototype UI remains frozen.
- Performance gate: 3.59 MiB; Node full-adapter cold 148.82 ms, warm median 56.47 ms; deck sort median 23.71 ms; false-friend/glyph HTML median 5.36/1.44 ms. Browser `file://` was blocked by the automation policy, so no browser number was estimated; `tests/stage5_benchmark.py` generates an exact offline browser benchmark for the user.
- Added 10 Stage 5 tests and a browser benchmark. 113 non-rebuild tests pass. Full three-build determinism test passes in 755.136 s with byte-identical final outputs including `data.js` and stable VI-only membership without overrides.
- Fixed reproducible Windows `OSError 22` failures when one pipeline stage immediately rewrote another stage's CSV/JSON: shared writers now write sibling temp files and atomically replace targets, preventing partial exports without changing bytes. No API request; `prototype/index.html` unchanged. Next: Claude Stage 5 gate.

## 2026-11-07 — Stage 4 final gate re-check (D70): PASS; Stage 4 complete [Claude]
- Independent check of `b1c511f` against `7362ecf`: all `word_id`/`passage_id` match `^w\d{5}$`/`^p\d{4}$` and come from `pipeline/id_map.csv` (+359 rows; old rows unchanged); a fresh `run_all.py` leaves the tree clean, so IDs are stable.
- 年下 / 裁縫 single pinyin and their zh `ff_meanings` readings; 279 `ff_only` `source_pinyin=cc-cedict`; an unknown `task3_review.csv` batch stops the merge (unit test + end-to-end injection).
- Diff is exactly the expected one; counts 12,508 / 4,044 / 1,242 / 80; 103 non-rebuild tests pass. No API request. Next: Codex Stage 5.

## 2026-11-07 — Stage 4e-fix: D70 ID contract and focused corrections [Codex]
- Wired the 279 `ff_only` words and 80 kept passages into the persistent ID allocator. New `id_map.csv` rows are `w12996`-`w13274` in `ff_candidates.csv` order and `p0001`-`p0080` in accepted task-3 batch order, with passage keys retaining their pre-review position; `ff_meanings` follows the word IDs.
- Reduced 年下 / 裁縫 to the first CC-CEDICT pinyin value, changed all 279 `ff_only` pinyin provenance tags to `cc-cedict`, and made an unknown task-3 review batch fail closed.
- Added regressions for ID formats, every final ID/key association, ID persistence, pinyin/provenance, and the unknown-batch guard. Expected-diff audit: only 279 word IDs, their 853 `ff_meanings` rows, 80 passage IDs, 2 pinyin values, 279 source tags, 2 Chinese FF readings, and 359 ID-map additions changed. Counts remain 12,508 / 4,044 / 1,242 / 80.
- All 104 tests pass in 708.048 s, including the two-rebuild byte-identity check and override-independence rebuild. Offline only; no protected Stage 4 input or Stage 3 data changed. Stage 5 not started.

## 2026-11-07 — Stage 4 final gate (4e) attempt 1: FAIL on IDs; D70 [Claude]
- Independent check of `data/final/` after `3bf6c74`: schema columns/types, NFC, Stage 3 columns unchanged, usage counts (= D69 reference), `ff_meanings` (readings, traps, fixed notes, 12 static entries), `ff_only` rows, 80 passages (0 unresolved tokens), no review-only text, fresh rebuild byte-identical, 100 non-rebuild tests: all OK.
- FAIL: 279 `ff_only` words use the id_map key `x|trad` as `word_id` and 80 passages use `lang|level|n` as `passage_id`; none are in `id_map.csv` (PROMPT data rules, SCHEMA §0). Also fixed in the same pass: two `ff_only` pinyin values with `;` (年下, 裁縫), `source_pinyin` tag `cedict` → `cc-cedict`, `task3_review.csv` rows with an unknown batch must fail.
- SCHEMA §0 (passage key `n` = position before drops; IDs always from id_map), §1.2 (`ff_only` pinyin), §1.4/§3.3 (static rows store their reading cell in `reading_display`) amended. D70; GATES entry.

## 2026-11-07 — Stage 4e: accepted content merged into final tables [Codex]
- Added the offline `pipeline/merge_stage4.py` build step and wired it into `run_all.py`. All D63-D69 review overlays are fail-closed against accepted output; task-5 reasons and all other review-only fields stay out of `data/final/`.
- Added `words` usage/content fields, 279 dictionary-backed `ff_only` rows, `ff_meanings` (4,044 rows), and reviewed `passages` (80 rows). Final words = 12,508; false-friend entries = 1,242. D64 drops one empty-reading Vietnamese trap without removing its entry.
- Added `pipeline/extract_prototype_config.py`; committed its exact frozen-prototype extractions: 34 static FF rows across 12 entries and the 越南 note. The merge re-extracts in memory and validates both config files and all static readings.
- Task 5 now reports 104/104 from `content/accepted/`; runner, dry-run and launcher attempts for every accepted task 1-5 fail before client creation. Offline status: spend $35.50397575, room $64.49602425.
- Claude comparison: exact match — ko/ja rare 1,500/437 (both 241), wrong_meaning 18/1, vi literary 1,277 + one unsure, 227 Korean and 76 Japanese fixed-note rows, 275 changed entries, and three departures (孫子, 內衣, 應當).
- Added fail-closed overlay, schema/type/key, dictionary-reading, token-resolution and no-reason-leak tests. All 100 non-rebuild tests and the rebuild-determinism test pass (101 total); two full rebuilds are byte-identical.

## 2026-11-07 — Stage 4 gate part 4b: task 5 accepted in full; D69 [Claude]
- b055 rerun (user, $0.078; ledger $35.50397575) checked: inputs equal a fresh build, 104/104 batches validate; 18 `reason_warnings` (review notes only). 5 corrections (欠缺 けんけつ, 親生 친생, 輕型 경형, 青春期 청춘기 → `used`; 氣味 기미 → `rare`) → accepted.
- User's answers to `docs/TASK5_USER_SAMPLE.md`: A and C all agreed; B: 9 readings `used` (那邊, 其實, 第一聲, 接受, 慶祝, 宣布, 霍亂, 必定, 會同), 4 `rare`. `config/task5_review.csv` 26 → 40 rows.
- 應當 おうとう `rare` → Korean 응당 = Chinese, no trap: 2 rows in `config/task2_retrap.csv` (8 → 10), the entry leaves 偽の友達. Other part-B changes checked against task 2: no further retrap.
- App effect (104 batches): Korean （ ） on 1,500 cards, Japanese 437; 275 of 1,245 false-friend entries change, 3 leave; Vietnamese `literary` 1,277.
- Task-5 outputs, logs and inputs moved to `content/accepted/task5/`. The launcher's `-Status` still reads task 5 from `content/generated/` (Codex 4e item 0). UX_BACKLOG #6 (learner-facing explanation of unused readings). New script `docs/review_scripts/stage4d_part4b_reference.py`.

## 2026-11-07 — Stage 4c-prep5: D68 task-5 reason warnings [Codex]
- Changed only task 5's reason-script checks: a Hangul run outside the item's `ko` or a Latin-letter run outside its `vi` now returns a structured `{key, field, text}` warning instead of rejecting the response. All other task-5 validation remains fail-closed, and task 1-4 validators are unchanged.
- Successful generation logs now include `reason_warnings`, including an empty list when there are none. Offline regressions cover `기사는` (input `기사`), foreign Latin text, warning log persistence, an empty warning list and the existing strict rules.
- All 87 non-rebuild tests pass. Offline launcher status remains task 5 = 103/104 validated, 1 failed, 0 missing. A fresh offline resume classification names only `b055`; the task-5 input aggregate remains `dcc14617dd28328d60593053c7f9db23bc1ce33ba607742e79bcdd04b374f0ab`, and b055's fresh input/prompt SHAs match its failed log. No request was sent and no task was started.

## 2026-11-07 — Stage 4 gate part 4: task 5 accepted except b055; D68 [Claude]
- Task-5 run checked: inputs equal a fresh build, 103 outputs re-validated; b055 failed 3/3 on one review note (「기사는」); ledger $35.43 (task 5 $13.18).
- Review: all 335 HSK level 1-3 `rare`/`wrong_meaning` flags and the D66 samples (487 flags, 2.3% clear false positives); held-out cases, the user's five, real false friends and task-2 Korean traps checked. New overlays `config/task5_review.csv` (26 rows) and `config/task2_retrap.csv` (8 trap flags re-based on Korean where the Japanese reading is rare; 4e only).
- D68: task-5 reason script rule becomes a warning (Codex 4c-prep5; b055 rerun only); user change to D67: a word stays in 偽の友達 and each unused Japanese/Korean language shows a fixed note (`config/ff_fixed_notes.csv`; SCHEMA §1.4 `reading_display`, §3.3; no UI change).
- App effect (103 batches): Korean （ ） on 1,479 cards, Japanese 436; 276 of 1,245 false-friend entries change, 2 leave; Vietnamese `literary` 1,261 of 5,077.
- User sample `docs/TASK5_USER_SAMPLE.md`. Task-5 output, inputs and cost log committed (still in `content/generated/task5/`).

## 2026-11-07 — Stage 4c-prep4: accepted layout and D67 task 5 [Codex]
- Fixed the D65 clear gap: clearing a word's `vi` now also clears `vi_alt`. A canonical rebuild changed only 平價 `vi_alt` (`bằng giá` → empty) in `words.csv`/`words.json`.
- Tasks 1-4 now validate and report from `content/accepted/`; runner/dry-run and launcher attempts to regenerate them fail with a D65 refusal. Offline status reports all accepted batches (86/86, 79/79, 14/14, 5/5).
- Added the deterministic D67 task-5 builder, response schema, strict local validator, resume/status/ceiling support and launcher `-Tasks 5`. Scope: 10,400 items / 104 batches; checks ko 9,090, ja 1,919, vi 5,126; batch-hash aggregate `dcc14617dd28328d60593053c7f9db23bc1ce33ba607742e79bcdd04b374f0ab`.
- The conservative no-log estimator uses 1,650,000 input and 120 chargeable output tokens per item: $15.78 at the November Argon rate. All 85 non-rebuild tests pass; one canonical rebuild completed. No request was sent and no task was started.

## 2026-11-07 — D67: user decisions on the usage check (task 5) [Claude]
- Korean option A with parentheses; Japanese check added (1,919 `ja_common=false` card words; `ja_common=true` and ff rows count as used by JMdict evidence); Vietnamese `vi_use` flag, data only; one user-approved UI change (`ruleTags` ignores the parentheses); the 12 prototype false friends kept as static content (`config/ff_static.csv`, 4e); user sample at gate part 4; Stage 5 performance and Final licence notes.
- `content/prompts/task5_v1.md` rewritten (not yet sent); SCHEMA §1.2 (`ja_use`, `ko_use`, `vi_use`), §3.1 (`jr`/`k` parentheses, `ruleTags`), §5 (task 5, `ff_static`). Task 5: 10,400 items / 104 requests, about $7-16. UX_BACKLOG #4 updated, #5 added.
- Backup check: no secret or credential file tracked or in history; 36 MB; `docs/BACKUP.md` with user steps. No data or code change.

## 2026-11-07 — Stage 4 gate part 3: task-3 Vietnamese accepted, step 6 applied, Korean usage check planned [Claude]
- Task 3 Vietnamese rerun (prompt v3, user run, $0.385) reviewed in full: the forced archaic class is gone; 6 single slips in 42 passages → `config/task3_review.csv` (drop 4, trim 2 by token deletion); every cell keeps ≥ 5 passages; all 14 task-3 batches accepted (D65).
- Step 6 (user: "All as proposed. A27: clear."): 37 `vi` clears in `pipeline/overrides.csv` (158 rows) and 28 `clear_vi` rows in `config/task2_review.csv`, written by `docs/review_scripts/stage4d_part3_step6.py`. Rebuild: only those 37 `vi` values changed; no primary or tie change (液 giá/dịch tie gone); `card_eligible` 8,555 → 8,554 (季女); HSK `vi` 4,211, all four 3,345. Test constants 8,555 → 8,554 updated.
- All task 1-4 batches (outputs, logs, inputs) moved to `content/accepted/taskN/` (D65 item 3).
- User Korean finding: the five examples are task-1 card words; `ko_rare` was review-only; task 1 misses many rare Korean readings and `ff_candidates` rows were never checked → task 5 Korean usage check, prompt `content/prompts/task5_v1.md`, 9,091 items, about $4-7 (D66). UX_BACKLOG #4.

## 2026-11-07 — Stage 4c-prep3: task-3 prompt per language [Codex]
- Task 3 now resolves its prompt from each cell: Chinese uses unchanged `task3_v2.md`; Vietnamese uses Claude's unchanged `task3_v3.md`. Request text, log SHA, resume validation, offline status, cost estimation and dry-run all use the resolved cell prompt. Tasks 1, 2 and 4 retain their single prompts.
- Resume/dry-run checks happen before rewriting an already validated input. The seven Chinese v2 batches remain valid; the seven Vietnamese batches logged with the v2 SHA are stale and selected for rerun. Dry-run now reports only the unvalidated batch count.
- Added offline regressions for per-language selection, Chinese-v2 skip, Vietnamese-v2 rerun, pending-only dry-run, prompt-matched ceiling estimation and unchanged prompt behavior for tasks 1, 2 and 4. All **78 non-rebuild tests pass**; one canonical rebuild completed successfully.
- Offline launcher `-Status`: task 1 **86/86**, task 2 **79/79**, task 3 **7/14**, task 4 **5/5** validated; spend $21.87953175, room $78.12046825. No request was sent, no task was started, and no file under `content/generated/`, `content/inputs/`, `config/` or `content/prompts/` was modified.

## 2026-11-07 — Stage 4 gate part 2: tasks 2-4 reviewed [Claude]
- Committed the user's sitting-2 output: `content/inputs/task{2,3,4}/`, `content/generated/task{2,3,4}/` (79 + 14 + 5 batches, all validated on the first attempt), `content/cost_log.csv` (total $21.87953175).
- Gate (`docs/GATES.md`, `docs/STAGE4D_PART2_REVIEW.md`, **D64**): task 2 accepted (79); task 3 Chinese accepted (b001-b007), **Vietnamese rejected (b008-b014)**; task 4 accepted (5).
- New `config/task2_review.csv` (6 Korean homophone corrections, `same_as_ja`) and `config/task4_review.csv` (5 notes with a wrong Korean example corrected); new prompt `content/prompts/task3_v3.md` for the Vietnamese passage cells.
- New error class found: Vietnamese values of `ff_candidates` rows were never checked; 25 of 68 Vietnamese traps there come from a different word or a place name (敬老 = "reading glasses"). They join the step-6 list as group B.
- `docs/VI_CLEAR_SHORTLIST.md`: step-6 list for the user (39 words + 28 forms, with dictionary links and plain-language evidence).
- User questions answered: task 4 234 → 212 (13 non-`same_word` + 9 non-card words, D63 words kept); task-2 token levels = layout only (about $2.05); all 16 D63 words handled in task 2.
- Reference script `docs/review_scripts/stage4d_part2_reference.py`.

## 2026-11-07 — Stage 4c-prep2: D63 downstream overlay [Codex]
- Added a fail-closed `config/task1_review.csv` overlay loader. It verifies unique review/output/frozen keys and exact `trad`, `vi` and original `vi_check` matches, then changes exactly the 16 reviewed `vi_check` values in memory; generated task-1 files remain untouched. Every task 2-4 build, including offline status and resume hashing, uses the overlay.
- Task 2 always includes the 16 reviewed words with their Vietnamese reading, keeps or blanks `gloss_vi` per the review, and leaves the missing task-1 Vietnamese meaning empty for task 2 to supply. Frozen count: **3,937 items / 79 batches**.
- Task 3 Vietnamese inputs now accept `same_word` entries with high confidence or `low_reason=ko_rare`; `different_word` and missing Vietnamese meanings remain excluded. Frozen count: **14 cell-items / 14 batches**, containing **6,455 linkable-word entries**.
- Task 4 applies the overlay before its `vi_check` filter, retaining reviewed Vietnamese differences. Frozen count: **212 items / 5 batches**.
- Added offline regressions for the 16 exact changes, mismatch refusal, task-2 membership/gloss policy, task-3 `ko_rare` inclusion and `different_word` exclusion, and task-4 reviewed-difference retention. All **74 non-rebuild tests pass**. Launcher `-Status`: task 1 86/86 validated; tasks 2/3/4 0/79, 0/14, 0/5; spend $14.37353775, room $85.62646225. No task was started; no file under `content/generated/` was modified.

## 2026-11-07 — Stage 4 gate part 1: task 1 accepted [Claude]
- Committed the user's sitting-1 output: `content/inputs/task1/`, `content/generated/task1/` (86 batches), `content/cost_log.csv` (total $14.37353775).
- Gate **PASS** (`docs/GATES.md`, `docs/STAGE4D_TASK1_REVIEW.md`): all 86 batches accepted; 0 errors in 50 random items, the fixed words, `unsure`, `ko_rare` samples; 16 of 46 `different_word` decisions wrong or not to be applied.
- **D63:** `config/task1_review.csv` (16 rows) is an overlay on the task-1 output for tasks 2-4 and the 4e merge (`vi_check` → `same_word`, forced task-2 items with `vi`); task-3 Vietnamese linkable words no longer lose `ko_rare` words. Draft step-6 clear list (30 + 9) in the review.
- User run-log notes answered: low output tokens = response formatting only (about $3.1 padding); b083 all `same_word` is plausible; b040 hangs logged at $0 (D61 gap). Codex fix `c2caac3` checked: correct.
- Reference script `docs/review_scripts/stage4d_task1_reference.py`. No pipeline or data change.

## 2026-11-06 — Stage 4c sitting-1 transport retry and live output fix [Codex]
- Root cause of the top-level `RemoteProtocolError`: the ceiling estimate called `count_tokens` before `generate_batch` entered its retry wrapper. Moved token counting into the existing per-batch attempt budget while retaining a successful count across later generation retries. A transport failure from either `count_tokens` or `generate_content` now waits 30 seconds, then 60 seconds, is recorded with its operation, and after the third failure writes the batch `failed` and continues. This includes 504 `DEADLINE_EXCEEDED` and `httpx`/`httpcore` transport exceptions; fatal access errors, 429 handling and immediate local-validation retries are unchanged.
- The PowerShell launcher now invokes Python with `-u`, so successful progress lines are not buffered behind the launcher.
- Added no-network regressions for exhausted `count_tokens` `RemoteProtocolError` handling (including advancing to the next batch), 504 retry exhaustion and unbuffered launcher invocation. All **69 non-rebuild tests pass**.
- Offline launcher `-Status` proves resume safety after the user's sitting 1: task 1 **86/86 validated, 0 failed, 0 missing**; task 2 0/79, task 3 0/14 and task 4 0/5; spend $14.37353775, room under the $100 ceiling $85.62646225. Codex did not modify, stage or commit any file under `content/`; prompts, model, settings and task inputs are unchanged. Next: Claude — Stage 4 gate part 1 (task 1).

## 2026-11-06 — Stage 4c-prep: safe user launcher and task-4 Korean filter [Codex]
- Added `pipeline/stage4/run_stage4.ps1` for Windows PowerShell 5.1: repository-root discovery, safe User-scope Vertex setting copy, API-key refusal, fixed Python 3.12 selection, Windows keep-awake with `finally` reset, ordered comma-separated tasks, two delayed launcher retries, stop-before-next-task behavior and a final status summary.
- Added offline, resume-aware `--status` with validated / failed / missing counts, the task-1 prerequisite for tasks 2-4, spend to date and room under the $100 ceiling. Added a PID lock for `--task`, `--pilot` and `--check`; live locks refuse a second run, stale locks are replaced and owned locks are removed on every exit. `--status` ignores the lock.
- API/transport retries now wait 30 then 60 seconds; local-validation retries remain immediate and 429 handling is unchanged.
- D62 task-4 filtering now compares Korean `ko_base` to the word's written syllable. Exactly the nine named mapped-base artefacts are removed (243 → 234 items); remaining aligned Korean `reading_here` values are asserted against the written syllable. 議論, 風餐露宿, 胡思亂想 and 喜怒哀樂 remain.
- Added no-network tests for the 234-item filter, exact dropped/kept forms, written syllables, retry waits, live/stale locks and offline status. All 67 non-rebuild tests pass. The 86 deterministic task-1 batch hashes are unchanged (aggregate SHA-256 `b7cde3cb000b853d61f534545f4aceed50e346427006af81ee2050192600af48`). Launcher `-Status` passed. `-Check` proved the User-scope copy, then the restricted Codex sandbox failed DNS resolution for `oauth2.googleapis.com`; it was not retried or worked around, so the user must run `-Check` in a normal new PowerShell window. No request reached the model and no full-run task was started.

## 2026-11-06 — Stage 4b re-check; Stage 4c run plan [Claude]
- Re-check of Codex's Stage 4b-fix (`f03010b`): **PASS** (`docs/GATES.md`). Frozen data unchanged (`id_map.csv` line endings only); 63 non-rebuild tests rerun OK; all pilot_v2 logs on Argon/`global` with the D60 settings; re-check list met. Notes for the Stage 4 gate: 財源 "= 資源" (impossible reading) and minor task-3 wording.
- New finding: 9 task-4 Korean differences carry a D39-mapped base that is not the written syllable (「異性」では「리」); filter assigned (D62 item 6), 243 → 234 items.
- **D61:** user items 9 (total-token billing), 10 (resume), 11 (timeout, UTC deadline guard) verified and recorded, with their known small gaps.
- **D62:** Stage 4c is started by the user in a new PowerShell window, in two sittings (task 1, Claude review, tasks 2-4); Codex Stage 4c-prep adds a launcher (User-scope variables, keep-awake, auto-resume), `--status`, retry wait and a lock. User steps: new `docs/VERTEX_SETUP.md` part E2. No pipeline code or data changed. Next: Codex Stage 4c-prep.

## 2026-11-06 — Stage 4b-fix: D60 and Argon re-pilot [Codex]

- Pinned Argon and v2 prompts; added response property ordering, D60 validators, the 243-item task-4 filter, the UTC deadline guard, and a 600-second per-request timeout.
- Added resumable `--task N` batch validation/skip behavior and a test; explicit `--batch N` remains a forced rerun.
- Added `total_token_count` and conservative unreported-token billing at the output rate to the ledger, measured averages and $100 ceiling calculation.
- Argon check and all five `pilot_v2` requests passed on the first attempt. Re-pilot: 28,350 input, 18,750 output, 0 thinking, 47,100 total, 0 unreported tokens, $0.244200; request wall times and full-run projections are in `docs/STAGE4B_FIX_REPORT.md`.
- 63 non-rebuild tests pass; canonical rebuild completed with no frozen-data diff. No full run started. Next: Claude Stage 4b re-check.

## 2026-11-06 — Stage 4b pilot review [Claude]
- Verified the frozen build after Codex's override-backup restore: `pipeline/overrides.csv` byte-identical to `03b3bf9` (121 rows); no file under `data/` differs; `pipeline/id_map.csv` differs in line endings only.
- Reviewed both models' task-1/task-2 pilot outputs on identical inputs, all Flash task-3/task-4 outputs, all low-confidence and non-`same_word` items, retry causes and costs: `docs/STAGE4B_REVIEW.md` (10 side-by-side examples), script `docs/review_scripts/stage4b_compare.py`.
- D60: Gemini 4 Argon for all tasks, full run by 2026-11-30; prompts `task1_v2.md`, `task2_v2.md`, `task3_v2.md` added (v1 kept); schema `propertyOrdering`, two validator rules, task-4 input filter and a date guard assigned to Codex with an Argon re-pilot. No pipeline code or data changed. Next: Codex Stage 4b-fix.

## 2026-11-06 — Stage 4a Vertex generation script and pilot [Codex]
- Added `pipeline/stage4_generate.py` and `pipeline/stage4/`: deterministic builders for four tasks, strict local validators, Vertex-only ADC client, API-key guard, structured schemas, retries/backoff, token accounting, date-aware Flash/Argon prices, and a shared $100 hard ceiling. Pinned `google-genai==2.34.0` separately; `run_all.py` remains isolated.
- Added versioned English prompts, exact pilot JSONL inputs, per-request outputs/logs, and `content/cost_log.csv`. No readings are emitted by model outputs. Final saved pilot output passed every local validator.
- Fixed check handling after the first 32-token check returned empty text: check budget 1,024; every response now checks text/finish reason before JSON parsing and reports finish reason plus token counts; failed checks are cost-logged. Corrected `--check` passed on `gemini-3.8-flash`, `global`, 123 tokens.
- Ran the user-requested identical-input comparison on GA `gemini-4-argon` for pilot tasks 1 and 2 only. Flash remains pinned pending Claude's Stage 4b decision. Argon November/December prices are recorded separately.
- Pilot final successful requests: Flash task 1 14,401/13,113/0 tokens; task 2 4,772/4,224/15,883; task 3 zh 981/992/0; task 3 vi 1,447/1,542/2,431; task 4 5,639/2,358/5,302. Argon task 1 14,280/13,859/0; task 2 4,780/4,228/0 (input/output/thinking). Actual logged corrected-check plus all pilot attempts: $0.69781975.
- Successful-attempt Flash projection is $13.37 lower bound; about $15.23 with D58 task-3 sizing and about $25.49 with the observed task-1 retry factor. Argon task 1+2: $19.48 through November or $38.97 from December on one billed attempt, higher with observed retries. Full evidence in `docs/STAGE4A_REPORT.md`.
- Added 16 Stage 4 tests covering frozen counts, deterministic inputs, bad outputs, schema constraints, secrets, empty responses and `run_all.py` isolation. One canonical rebuild completed and all 54 non-rebuild tests pass. No full run started. Next: Claude Stage 4b.

## 2026-11-06 — Documentation consolidation; Stage 4 on Vertex AI; Stage 4 assignment [Claude]
- `docs/HANDOFF.md` cut to status, next assignment, planned sequence, notes, open problems and recent log; completed assignments, Codex evidence blocks, resolved notes and the full log moved **verbatim** to the new `docs/HANDOFF_ARCHIVE.md`.
- `docs/DECISIONS.md`: superseded decisions or parts marked in italics at the start of D23, D24, D26, D27, D31, D32, D36, D38, D39, D44, D46, D47, D53, D54, D55 and open item E; nothing deleted.
- User question: `chars` 3,138 → 3,140 = 祇 `c03206` and 畿 `c03207`, added at `4919d5b` (D56 G1) by the VI-only words 神祇 and 京畿; recorded in `GATES.md`.
- **D58 (amends D54, user instruction):** Stage 4 uses Gemini on Vertex AI (`aiplatform.googleapis.com`), login by `gcloud auth application-default login`, no API key; GA Gemini 3.8 Flash; hard ceiling $100; finish by 2026-12-20; estimate about $20-45 from the frozen build. No paid upgrade planned (Google's Free Trial page excludes only AI Studio and partner models). User guide: new `docs/VERTEX_SETUP.md` (budget alert included).
- **D59:** Stage 4 design: task-1 `vi_check` (D57 Q1) and `meanings_differ`; 自己 always in task 2; no reading fields in content; task 4 other-reading notes in `words.note_ja` (302 words); pilot before the full run. SCHEMA §5 (content files) added; UX_BACKLOG #3.
- `.gitignore`: `.env`, `.env.*` and credential-file patterns (D54 required `.env`; it was missing).
- No data or pipeline change. Next: User — Vertex AI setup; then Codex — Stage 4a.

## 2026-11-06 — D55 Vietnamese finalization applied; word list frozen [Claude]
- User confirmed `docs/VI_SHORTLIST.md` (all as proposed; Q1 a, Q2 yes, Q3 a; plus 岳父 nhạc phụ, 岳母 nhạc mẫu). DECISIONS D57.
- `pipeline/overrides.csv` 81 → 121 rows: 11 Vietnamese replacements (一 nhất, 詞 từ, 累 lụy, 圈 khuyên, 祝福 chúc phúc, 服從 phục tùng, 拖 tha, 拄 trụ, 馴 thuần, 岳父, 岳母) and 29 clears (rule-B values that are a different Vietnamese word). `config/vi_sources.json`: 7C character readings on (80/81 correct).
- Effect: HSK `vi` 4,239 → 4,245, all four 3,362 → 3,367; HSK verified character readings 1,835 → 1,913; one primary changed by the overrides (馴 thuần, the user's pick), tie 福 phúc/phước removed. Cards unchanged (7,354 / 8,555).
- Tests: `test_stage3_d53.py` updated for D57 (121 overrides, obsolete-only words, switch on, new test for cleared values); `test_chars.py` sanity range counts the `kaikki_en_char` verified tag. Full suite: rebuild test passes (identical); all non-rebuild tests OK.
- Why: D55 (user wants every known Vietnamese doubt settled before Stage 4). Remaining rule-B false matches are found by a Stage 4 meaning flag (D57 Q1 a). Next: Claude documentation consolidation and the Stage 4 assignment.

## 2026-11-06 — Repeat Stage 3 gate after D53, attempt 2: PASS; D55 short list [Claude]
- Rechecked G1-G3, R2, R4, R5, R6, checks 6, 8, 11, 13 on `4919d5b` against `0d581fa` and `7827546` (`docs/review_scripts/stage3_repeat_gate_attempt2_reference.py`). All 1,122 A2 values equal an independent implementation of D56 item 2 applied to 7C; 0 invented consonant + y spellings in `words`, `ff_candidates`, `rules_examples`; `ff_candidates` 2,504 rows with 0 overlap with `words`; VI-only 6 added / 6 dropped, no ID reused; 0 character primary or `*_all` changes, no tie created or broken; all 81 overrides apply; 38 tests OK; rebuild byte-identical. Gate logged in `GATES.md`.
- D55: wrote `docs/VI_SHORTLIST.md` for the user: 17 rule A/B vs A2 disagreements (replace 8), 42 rule-B values that are other Vietnamese words or variant spellings (clear 24, keep 18), 8 `obsolete_only` words (keep empty), 7C character readings (one switched-on build measured and discarded: 80/81 readings correct, HSK `vi` +32, 5 wrong new word values to clear), 調 / 馴, and a 50-word seeded sample (48/50; both errors are rule-B false matches, sized at about 7% of multi-character rule-B words by a second sample of 60). Three questions (Q1-Q3) for the user.
- No data, pipeline, config or override change. New evidence script `docs/review_scripts/d55_vi_shortlist_reference.py`.

## 2026-11-06 — Repeat Stage 3 gate fixes G1-G3 [Codex]
- Implemented D56's narrow A2 spelling convention in one shared function: only `hi/ki/li/mi/ti` syllables use `y`; 104 A2 words (32 HSK) lose invented spellings while rule A/B remains untouched. Rebuilt HSK coverage is unchanged; Vietnamese alignment mismatches fall from 298 to 200 and `rules_examples` from 2,232 to 2,190.
- Removed the pre-D53 legacy VI-only selection from false-friend filtering. `ff_candidates.csv` is 2,504 rows (440 removed, none added), with zero `form`/`trad`/`simp` overlap against any current word; 手紙 and 大丈夫 remain.
- Removed override-based VI-only pinning. Selection is now rank-and-cap only; a real rebuild without `overrides.csv` produced the same 1,201 VI-only IDs. Corrected frequency scores cause six additions and six drops; no existing ID changed or was reused.
- Current scope: 12,229 words, 3,140 chars, 24,497 `word_chars`; HSK coverage `ja` 5,703 / `ko` 7,114 / `pinyin` 11,028 / `vi` 4,239 / all four 3,362; cards 7,354 HSK / 8,555 total. No existing Korean or Vietnamese character primary changed; no override was added.
- Added D56 regression coverage for the named A2 examples, exact false-friend exclusion and override-independent VI-only selection. All 38 tests pass; two canonical rebuilds are byte-identical including `id_map.csv`.
- Why: repeat Stage 3 gate attempt 1 failures G1-G3. Next: Claude repeat gate attempt 2, then D55 Vietnamese finalization if it passes.

## 2026-11-05 — Repeat Stage 3 gate after D53, attempt 1: FAIL [Claude]
- Checked R1-R9, checks 1-13, C1, C2 on `97780a0` against `7827546` (`docs/review_scripts/stage3_repeat_gate_reference.py`). Passed: rows/IDs (no dropped ID reused), merges, coverage (HSK `vi` 4,239, all four 3,362), `card_eligible`, `vi_ambiguous`, VI-only bands, all 77 overrides, test words, Japanese, collisions, 36 tests and identical rebuild.
- **Failed:** (1) rule A2 respells every consonant + i as y (`canonicalize_iy`): 143 A2 words differ from 7C, 104 (32 HSK) with spellings no source has (皮膚 bỳ phu, 移 dy, 王妃 vương phy); about 50 such pairs reached `rules_examples.csv`. (2) `ff_candidates.csv` keeps its pre-D53 membership through a legacy VI-only selection, so 440 rows are now also VI-only words (D47).
- **User decisions (D52 tie rule):** `chars` overrides 鹿 록, 磊 뢰, 隸 례, 蘭 란, 丹 단, 易 이 (易 asked at this gate). Vietnamese primary changes 沒 một, 盆 bồn, 訪 phỏng, 武 vũ accepted.
- **Reviewed at the user's request:** Codex's pin of overridden VI-only words. Not accepted (D56 item 4); `x|行伍 항오` and `x|寂寥 적요` removed from `overrides.csv` because they stayed in the list only through the pin (ranks 1,199-1,200, `freq_score` 1,074 and 137 vs about 8,700 at the cut). `overrides.csv` 77 → 81 rows.
- **Confirmed for the user:** the VI-only churn (757 of 1,201 replaced) is D53 item 4's intended effect: 904 `ja_common` candidates instead of 342 fill the cap first; every dropped word was non-`ja_common` at levels 5-7.
- Rebuilt with the current code and 81 overrides: only the six primaries changed (no tie flip); 行伍/寂寥 left the VI-only list (IDs reserved), 槍法/法家 entered; coverage and cards unchanged. `tests/test_stage3_d53.py` override count 77 → 81; 35 non-rebuild tests OK; second rebuild byte-identical.
- D56 recorded; SCHEMA §1.8 row `words_kaikki_en`; HANDOFF: fixes G1-G3 for Codex, D55 list additions (調, 馴, 複合/凶悪, 自己), Stage 4 note on explaining other readings (user idea), planned-sequence step for documentation consolidation after the freeze (user request).

## 2026-11-05 — Source 7C integrated; Stage 3 rerun [Codex]
- Added reproducible download/licence handling and `load_kaikki_en.py` for Kaikki English-Wiktionary Vietnamese data. The locked file exactly matches the D36 measurement (83,424,329 bytes; SHA-256 `186cd0a62d876dada70c9761bc05e598c8cf7b9a48e0aa518bab6c649e28d945`); loader output is 14,513 raw pairs, 10,064 filtered aligned pairs / 9,995 forms, plus 917 chữ-Hán reading pairs.
- Implemented D53 rule A2 as a validated `1:1` indicator merge after A/B, including obsolete reporting, word evidence, rule tags, the D44 `i/y` canonical form (`自己` → `tự kỷ`), A2 candidates for overrides, and A2 fills for the frozen 2,944 false-friend rows.
- Reran D46 VI-only selection over rule A ∪ A2. The cap remains 1,201 including 越南; duplicate resolved word keys are audited and the three existing overridden VI-only rows stay within the cap. Final scope: 12,229 words, 24,496 word-character rows, 3,138 chars.
- Added D55 support: Vietnamese clears/replacements never enter `vi_alt` and are reported; optional 7C character verification lives behind `config/vi_sources.json` (committed off). Switch-on measurement: 46 confirmations, 36 first readings, HSK `vi` 4,271, all-four 3,381.
- Final switch-off coverage: HSK `vi` 4,239 and all-four 3,362; cards unchanged. Six Korean and four Vietnamese character primaries differ from `7827546` and are handed to Claude under D52 without new overrides. Two extra source-backed obsolete-only rows and the larger A2 alignment report are documented in HANDOFF.
- Added D53/D55 regression tests and updated two pre-D53 assertions for the reranked data. **36 tests pass**, including two byte-identical rebuilds and `id_map.csv`; downloader rerun uses every locked file unchanged.
- Next: Claude repeat Stage 3 gate (R1-R9, checks 1-13, C1/C2), then D55 Vietnamese finalization if it passes.

## 2026-11-05 — Vietnamese finalization step added (D55) [Claude]
- User decision: between the repeat Stage 3 gate and the word-list freeze, Claude prepares `docs/VI_SHORTLIST.md` (16 A/B vs A2 disagreements, about 19 wrong-looking composed readings, 6 `obsolete_only` words, 38 rule-B values filed under other characters, 7C character readings if seeded precision ≥ 95%, a fresh 50-word sample with target ≥ 98%). The user confirms, overrides are written, rebuild and recheck (D52 tie rule, all overrides apply), then freeze and the Stage 4 assignment.
- Found while recording it: the override code cannot clear a value and moves a replaced `vi` into `vi_alt` (accepted as correct by `judge()`), and overrides cannot verify or add character readings. D55 defines empty/replacing `vi` overrides that never feed `vi_alt`, and 7C character readings behind `config/vi_sources.json` (default off). Both were added to the current Codex task (items 8-9) and to GATES (R9). SCHEMA tags `kaikki_en_char`, `override_cleared`, `override_replaced`.
- Next assignment unchanged: Codex integrates 7C.

## 2026-11-05 — D36 Vietnamese source search [Claude]
- Checked 8 candidates, licence first (user limits: at most 8; precision ≥ 95% on a seeded sample; gain ≥ +300 HSK words or +3 pp). Downloads only to a scratch folder outside the repo; `raw/`, `pipeline/`, `data/` unchanged.
- **Accepted:** Kaikki English-Wiktionary Vietnamese entries (SOURCES 7C), for the word list only, as rule A2 (D53). Seeded overlap sample 199/200 (seed 36), whole overlap 99.45%; gain +356 HSK words, 35.18% → 38.41% (+3.23 pp). A2 fills only empty `vi`; 6 obsolete/archaic-only words are reported, not used (新聞 stays empty). VI-only selection takes A2 pairs as extra candidates.
- **Rejected (7D-7J):** CVDICT (machine-translated), wordfreq and Leipzig (syllable tokens; Leipzig terms unreadable, NC), Wikidata lexemes (no gain), HanViet data and duyet word list (GPL-2.0), English-Wiktionary Chinese descendants (gain +231, vernacular forms). No licensed Vietnamese word-frequency list found; D26 proxy stays.
- Added `docs/D36_VI_SOURCE_SEARCH.md` (candidates, numbers, 30 seeded new readings for the user's spot check, loop-1 lists), reference scripts `docs/review_scripts/d36_*.py`, SOURCES rows 7C-7J, D53, SCHEMA tags (`kaikki_en_han`, `obsolete_only`, `vi_only_report.source_vi`), GATES repeat-gate checks R1-R8 (incl. D52 tie rule and the 77 overrides).
- **Stage 4 mode (D54):** the user chose a Python batch script on the Gemini API (key in `GEMINI_API_KEY`, never committed) over an Antigravity agent session, after a cost/reproducibility/Rule 3 comparison.
- Why: D36 (35% Vietnamese coverage too low for the user's goal); the word list freezes only after the repeat gate (D46).

## 2026-11-05 — Stage 3 gate PASS: confirmed overrides applied [Claude]
- `pipeline/overrides.csv`: 77 user-confirmed rows (D52): 59 `words` (23 ko, 16 ja incl. the user's 家 か and 月 げつ, 19 vi) and 18 `chars` (茶 차, 寧 녕, 13 law-form base forms; 貝 패, 滑 활, 省 성, 更 경 to undo D39 tie flips the word overrides caused, confirmed by the user after the first rebuild).
- Rebuilt: HSK `vi` 3,861 → 3,880, all four languages 3,094 → 3,111, `rules_examples` 2,031 → 2,044, `char_primary_changes` 84 → 103; `card_eligible` unchanged; `*_all` sets unchanged.
- Tests: `tests/test_chars.py` and `tests/test_words.py` pinned 茶 = 다 (pre-D50 expectation) and now expect 차, like `tests/test_stage3_gate_fixes.py`. 29 tests OK; two rebuilds identical.
- Why: GATES check 9 / D50 item 4; Stage 3 gate recorded as PASS (attempt 2).

## 2026-11-05 — Stage 3 gate, attempt 2 [Claude]
- Reran checks 2, 5, 6, 7, 8, 9, 10, 11, C1, C2 and 13 against commit `e18e7e0` with independent scripts; all pass except check 9, which waits for the user. F1-F13 verified. 29 tests OK; the rebuild reproduces every committed output byte for byte.
- Scanned all 84 `char_primary_changes.csv` rows: one bad change (寧 → 령), override proposed.
- Wrote `docs/STAGE3_SHORTLIST.md`: proposed picks for the D50 short list (23 Korean, 14 Japanese, 19 Vietnamese word overrides; 茶 차 and 寧 녕 character overrides; optional group of 13 law-form characters). No override written, no data or code changed.
- Why: PROMPT Rule 11 and GATES check 9; the user confirms picks before they enter `overrides.csv` (D50 item 4).

## 2026-11-05 — Stage 3 gate fixes F1-F13 [Codex]
- Separated D43 Korean alignment acceptance from exact D39 normalization, restricted D39 counts to one-candidate/override evidence, preserved reading sets, and implemented `ko_law_form_suspect`.
- Replaced simulated word join counts with validated indicator merges for CC-CEDICT, Kaikki, JMdict, libhangul and Vietnamese matches; Stage 2 rows now record their actual validation arguments.
- Corrected single-character Japanese form matching and linked-row on'yomi, Vietnamese rule-B conflicts and headword glosses, grown-character simplified forms, VI-only audit columns, and CC-CEDICT-inventory pinyin segmentation.
- Rebuilt reports and tables: 12,229 words, 3,178 chars, 24,458 word-character rows; 5 pinyin/Korean/Vietnamese alignment exceptions (0 pinyin failures); 3 simplified-form mismatches; 84 primary changes. Card eligibility remains 7,354 HSK / 8,555 total.
- Added `tests/test_stage3_gate_fixes.py`. Full suite: 29 tests passed; two complete rebuilds produced identical final outputs and `pipeline/id_map.csv`. No override or new data decision was added; `DECISIONS.md` is unchanged.

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
