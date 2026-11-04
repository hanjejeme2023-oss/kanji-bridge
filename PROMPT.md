# USER INPUT

**Learner profile:** Native-level Korean and Japanese. Learning Mandarin Chinese and Vietnamese.

**App:** 漢字ブリッジ (Kanji Bridge). A PC-only study tool that uses shared Sino-Xenic vocabulary (學 → 학 / がく / xué / học) so a learner who knows Korean and Japanese can learn Chinese and Vietnamese faster.

**Final UI/UX (frozen):** `prototype/index.html`, one self-contained HTML file with 5 views. **Its UI/UX is the approved final design.** Only its data is a placeholder: the views run on small hardcoded arrays (`WORDS`, `RULES`, `FF`, `PASSAGES`, `GLYPHS`). This run replaces the data, not the design. The 5 views:
1. カード (Cards): spaced-repetition flashcards. Front: Japanese form + reading, Korean. Learner guesses Vietnamese and/or pinyin.
2. 音のルール (Sound rules): Korean final consonant (patchim) → Vietnamese final consonant correspondences, with a quiz.
3. 偽の友達 (False friends): words whose meaning differs across languages.
4. 読解 (Reading): short Chinese/Vietnamese sentences; tap a word to see all 4 languages.
5. 字体 (Glyphs): Japanese vs Korean/traditional vs simplified character forms.

**Project documents (read these first; they are the source of truth):**
- `docs/final-data-spec.md`: **what** to build: decisions (D1–D11), tables, columns, sources, build order. If documents disagree, this one wins.
- `docs/data-pipeline-notes.md`: **how** to build it: folder layout, pandas rules, source formats, validation checklist
- `docs/SOURCES.md`: data source and license log

**Goal of this run:** Replace every hardcoded array in the prototype with real, verified data produced by a reproducible Python pipeline, so the app works with the full HSK 3.0 vocabulary plus high-frequency Sino-Vietnamese words, with the UI/UX unchanged.

---

# YOUR ROLE AND GOAL

This project is built by three AI agents working in one shared local project folder. Each agent reads this whole prompt, then performs **only the work assigned to its own role**, and hands off through files. No agent does another agent's job.

| Agent | Role | Owns | Never does |
|---|---|---|---|
| **Claude** (Claude Code) | Architect and reviewer | Specs, decisions, schemas, static rule text, reviews, audits, final acceptance | Writing the bulk pipeline code; generating bulk content |
| **Codex** | Engineer | Python pipeline, downloads, validation and metrics scripts, app integration | Changing the spec or decisions without Claude; inventing data values |
| **Gemini** (as an agent in Antigravity, with access to the project folder) | Content generator (batch) | Content that cannot come from dictionaries: meanings per language, false-friend judgments, reading passages | Facts that exist in dictionaries (readings, characters, levels); editing pipeline code or data tables |

If you are not sure which agent you are, stop and ask the user.

The agents never talk to each other directly. They communicate only through files in the project folder, mainly `docs/HANDOFF.md`. The user starts one agent at a time. See **HOW TO RUN** at the end of this prompt.

---

# GLOBAL RULES

1. **Output definition:** A finished run delivers:
   - `pipeline/`: Python scripts that rebuild all data with one command (`python pipeline/run_all.py`), including `download.py` that recreates `raw/` from recorded URLs and checksums
   - `data/final/`: the tables in `final-data-spec.md` as CSV + JSON (UTF-8, NFC), plus `data.js` for the app (spec D5)
   - `app/index.html`: the prototype, now loading `../data/final/data.js` via `<script src>` instead of hardcoded arrays. It must work when opened directly from disk (`file://`) in Chrome or Edge, without a network connection. Do not use `fetch()` for local data. (The prototype's web fonts may fall back to system fonts when offline; that is acceptable and must not be changed.)
   - Updated `docs/` (see Rule 6)

2. **Facts come from dictionaries, never from an AI.** Characters, readings, pinyin, Hangul, Vietnamese readings and HSK levels must come from the sources in `docs/SOURCES.md`. No agent may fill in a missing reading from its own knowledge. Missing stays NaN and is reported.

3. **Code does row-level work, AI does not.** Cleaning, merging and transforming tables is done by Python (pandas) scripts. No agent edits rows by hand or by prompting row by row. The only per-row AI work is Gemini's content tasks (Stage 4), done in batches with structured output.

4. **Reproducibility:** `raw/` is read-only. A rebuild deletes and recreates `data/staging/` and `data/final/` only; `content/` (accepted AI output), `config/` and `pipeline/id_map.csv` are inputs and are kept. Rebuilding twice gives identical output, including IDs.

5. **License first, attribution last.** Before a source is used, record its license in `docs/SOURCES.md` section 1 from the source's own license file. Do not use sources with no license or non-commercial-only terms. If a share-alike (CC BY-SA) source is used, the published dataset must be CC BY-SA. Write the final attribution only in the final delivery.

6. **Working files (read at the start of every session, update at the end):**
   - `docs/HANDOFF.md`: current status and the **next assignment** (which agent, what task)
   - `docs/DECISIONS.md`: every key decision, who made it, and why
   - `docs/CHANGELOG.md`: what changed in each stage or loop, and why
   - `docs/SOURCES.md` section 2: which source feeds which table and column

7. **Version control:** Git in the project folder. Commit at the end of every session with a message like `[Codex] Stage 2: chars table`. Do not commit `raw/` (it is recreated by `download.py`; add it to `.gitignore`), but copy every source's license file into `licenses/` and commit that.

8. **Autonomy within your task:** Finish your assigned task completely without asking for routine choices. Ask the user only for decisions that are irreversible, change the spec, or need a license judgment. Then stop as described in HOW TO RUN.

9. **Effort:** Be thorough on keys, merges and validation; brief on cosmetics.

10. **UI/UX freeze:** The layout, visual design, views, navigation, interactions, wording, controls and keyboard shortcuts of `prototype/index.html` are final. No agent may redesign, restyle, add or remove views or features. Allowed app changes are only:
    - loading data from `data.js` instead of hardcoded arrays
    - changes the real data forces (e.g. SRS key = `word_id`, performance with thousands of items, handling missing languages, multiple readings)
    - fixing bugs, where the app does not behave the way the prototype already intends

    Any other UI/UX idea, from any agent or from the user's loop feedback, goes to `docs/UX_BACKLOG.md` for after this run, unless the user explicitly approves it in that loop.

---

# DATA RULES (apply in every script)

- Load with `encoding="utf-8"` (or `"utf-8-sig"`), correct `sep`, and `keep_default_na=False` on word columns. Replace only known dummy values with NaN, per column.
- Right after loading text: `.str.strip()`, `.str.normalize("NFC")`, lowercase where appropriate (Vietnamese, pinyin), remove source suffixes (Unihan `학:0E` → `학`).
- Canonical character key = **traditional form**. For words, use the traditional form given by the HSK source; never auto-convert simplified → traditional (one-to-many).
- Polyphones: `chars` keeps one row per character with primary + all readings; the correct reading of a word comes from word-level dictionaries (spec D6). Word dedupe keys include the reading.
- Merges: never the default `inner`. Use `how="left"` (backbone on the left) or `how="outer"` + `indicator=True`, always with `validate=`. Log `_merge` counts.
- `suffixes` name the source; overlapping columns are resolved by priority rules recorded in `DECISIONS.md`.
- Never `fillna` word data with values. NaN means "does not exist" or "missing from sources", and is reported.
- IDs (`c00001`, `w00001`, `p0001`) are assigned once and stored in `pipeline/id_map.csv`; rebuilds reuse them, new rows get new IDs.
- Every stage ends with the validation checklist in `data-pipeline-notes.md` §7, including the **20 fixed test words**: 學 國 茶 行 生 樂 經濟 大學 勉強 手紙 銀行 發展 歷史 博士 新聞 注意 主義 學習 心理 越南.

---

# STAGE 0: SETUP (Claude)

1. Read the three project documents and `prototype/index.html`.
2. Create the folder layout in `data-pipeline-notes.md` §2 plus `app/`, `docs/`, `tests/`, `licenses/`. Run `git init` if needed, add `.gitignore` (`raw/`, caches).
3. Write `docs/SCHEMA.md`: exact column names, types, ID formats, and the JSON/`data.js` shapes for every table in `final-data-spec.md`, **mapped to the fields each prototype view reads** (e.g. `WORDS.h` → `words.trad`). This is the contract between agents.
4. Write `config/rules.json` from the prototype's `RULES` text (spec D8).
5. Create `DECISIONS.md` (copy D1–D11 from the spec), `CHANGELOG.md`, and `HANDOFF.md` with the first assignment: Codex, Stage 1.

**Output:** folder layout, `SCHEMA.md`, `config/rules.json`, working files.

---

# STAGE 1: SOURCES AND LICENSES (Codex, then Claude review)

1. Write `pipeline/download.py`: downloads every source in `SOURCES.md` into `raw/<source>/` with its license file, and records URL, date and checksum. Ask the user if a source URL cannot be found.
2. Fill in `SOURCES.md` section 1 for each source.
3. Write `docs/SOURCE_PROFILES.md`: per source, format, encoding, row count, key columns, 10 sample rows, quality problems.
4. Hand off to Claude.

**Claude review:** confirm licenses (ask the user on any doubt), cross-check a sample of 200 Unihan `kVietnamese` readings against the Sino-Vietnamese data, choose the shinjitai ↔ traditional mapping method, and set source priority per column. Record all in `DECISIONS.md`. Hand off to Codex, Stage 2.

---

# STAGE 2: CHARACTER TABLE (Codex, then Claude review)

1. One loader script per source → `data/staging/`.
2. Build `chars` per the spec (scope: HSK 3.0 character list for now; extended in Stage 3 to every character used in `words`).
3. Derive `ko_final` and `vi_final` from the primary readings.
4. Validate. Export `chars` and a preliminary `rules_report.csv` from characters with exactly one Korean and one Vietnamese reading.

**Claude review:** check `rules_report.csv` against `config/rules.json` (ㄱ→c/ch, ㅂ→p, ㄹ→t, ㄴ→n, ㅁ→m, ㅇ→ng/nh). Investigate every large off-pattern cell: data error or real exception? Record the outcome. Hand off to Codex, Stage 3.

---

# STAGE 3: WORD TABLE (Codex)

1. Backbone: HSK 3.0 on the left. Attach CC-CEDICT (gloss, pinyin), JMdict (Japanese form + reading), hanja.txt (Korean), Sino-Vietnamese data (Vietnamese, frequency).
2. Add high-frequency Sino-Vietnamese words missing from HSK; set `origin` from the merge indicator; assign their `level` by the frequency-band rule (Claude decides the bands in `DECISIONS.md` if not yet decided; ask Claude via `HANDOFF.md`).
3. Build `word_chars` with aligned Korean and Vietnamese syllables. Report syllable-count mismatches; do not guess. Extend `chars` to every character used.
4. Rebuild `rules_report.csv` from all aligned pairs (spec D7).
5. **False-friend candidates (code, spec D10):** words already in `words` are covered by Gemini's per-language meanings (Stage 4, task 1). In addition, list forms **outside** `words` that are common Japanese or Korean words (JMdict entries marked common, frequent hanja.txt words) and also exist as a CC-CEDICT or Vietnamese entry (e.g. 手紙, 大丈夫). Write `data/staging/ff_candidates.csv` with each language's reading and dictionary gloss, and report its row count (expected: hundreds to a few thousand, not tens of thousands; if larger, tighten the filter and record it in `DECISIONS.md`).
6. Set `card_eligible` (spec D11). Validate and write `coverage_report.csv` (per level: words with all 4 languages, per language coverage).
7. Hand off to Gemini, Stage 4.

---

# STAGE 4: CONTENT GENERATION (Gemini, then Claude review, then Codex)

Inputs (read only): `data/final/words.csv`, `data/final/chars.csv`, `data/staging/ff_candidates.csv`. Write only to `content/`.

1. **Meanings per language:** for each word, the meaning as used in each language that has it, written in Japanese. JSON lines: `{"word_id", "meaning_ja__ja", "meaning_ja__ko", "meaning_ja__zh", "meaning_ja__vi", "confidence"}`. Use the dictionary glosses provided as the basis. Batches of 100.
2. **False-friend judgments:** for every word whose task-1 meanings differ across languages, and for each row of `ff_candidates.csv`, decide whether the meaning differs enough to mislead a learner. JSON lines: `{"word_id" or "form", "false_friend": ["zh", ...], "meanings": [{"lang", "meaning_ja", "is_trap"}], "confidence"}`. Copy readings from the inputs; never write a reading yourself.
3. **Reading passages:** for each level and language (zh, vi), short sentences built from words in `words.csv` at or below that level. Tokens: `{"t", "word_id"}` for linked words, `{"t", "gloss_ja"}` for function words (了, 的, có, và…), `{"t", "punct": true}` for punctuation; plus `translation_ja`. Target: at least 5 passages per level per language.
4. Mark uncertain items `"confidence": "low"`.
5. There are many batches. If they do not all fit in one session, record which batches are done in `HANDOFF.md` and hand off to Gemini again; Claude may review finished tasks while others continue. When all are done, hand off to Claude.

**Claude review:** check at least 50 random items per task plus every low-confidence item. Accept or reject per batch (reject if error rate > 5%), record reasons in `DECISIONS.md`. Rejected batches go back to Gemini with the reasons. Accepted batches are moved to `content/accepted/`. Then hand off to Codex to merge accepted content into `words` (`meaning_ja__*`, `false_friend`, `verified`), `ff_meanings` and `passages`, adding `ff_only` words to `words` with dictionary data. After merging and validating, Codex hands off to Codex, Stage 5.

---

# STAGE 5: APP INTEGRATION (Codex)

1. Have `run_all.py` export `data/final/data.js`. Copy the prototype to `app/index.html` and replace the five hardcoded arrays with adapters that read `window.KB_DATA` and produce the same shapes the existing view code expects (per `SCHEMA.md`).
2. Sound rules: rule text from `config/rules.json`; examples from the aligned pairs, up to 8 per rule, preferring low-level, high-frequency characters; the rule's existing quiz uses these examples. False friends: from `false_friend` + `ff_meanings`. Glyphs: characters whose 3 forms are not all identical, readings shown from the `*_all` columns joined with " / " (as the prototype does).
3. SRS key = `word_id`. Cards: only `card_eligible` words, ordered by `level`, then `freq_vi`. The existing target switch decides which words are due: ベトナム語 → words with `vi`; 中国語 → words with `pinyin`; 両方 → words with both.
4. Missing languages: keep the prototype's layout; show nothing (or the prototype's existing empty state) for a missing value, never "undefined" or "NaN".
5. Follow Global Rule 10. Compare every view side by side with `prototype/index.html`; list any visible difference in `HANDOFF.md` with the reason the data forced it.
6. Hand off to Codex: loop setup and loop 1, Step 1.

---

# STAGE 6: IMPROVEMENT LOOP (REPEAT 5 TIMES)

Each loop must leave the project measurably better. A loop that finds nothing to fix is a failed audit, not a finished project.

## Loop setup (before loop 1, Codex)
Write `tests/metrics.py`, which appends one row per loop to `docs/METRICS.md`:

| Metric | Target |
|---|---|
| Cross-source disagreement on a fresh random sample of 100 words (values that differ between sources, unresolved) | < 2% |
| Auditor manual check of 30 random words (all languages) | ≥ 29 / 30 correct |
| Fixed test words fully correct | 20 / 20 |
| HSK words with all 4 languages | as high as the sources allow; report the ceiling |
| Unexplained syllable-count mismatches in `word_chars` | 0 |
| Duplicate keys / unexplained `_merge` drops | 0 |
| Gemini content accepted in review | > 95% |
| Passage tokens that do not resolve | 0 |
| App views that fail or show console errors / "undefined" / "NaN" | 0 |
| Rebuild twice → identical output | yes |

## Loop themes
Every loop audits everything, but spends most fix effort on its theme:
1. **Accuracy:** readings, character forms, source priority
2. **Coverage:** missing languages, unmatched keys, polyphones, VI-only additions
3. **Content:** meanings, false friends, passages
4. **App:** every view with the full dataset (ordering, SRS, missing values, performance), no deviation from the frozen UI/UX
5. **Release:** documentation, reproducibility, licenses, leftovers

## Step 1: Measure (Codex)
1. Rebuild (`run_all.py`) and run `tests/` and `tests/metrics.py`. Draw a **new** random sample every loop (record the seed) in addition to the fixed test words.
2. Open `app/index.html` from disk, exercise every view, record console errors.
3. Hand off to the auditor.

## Step 2: Audit (independent Claude)
A **fresh Claude session** with no earlier context, using only this prompt, `docs/`, `data/`, `content/` and `app/`, so the work does not grade itself.
1. Read `METRICS.md` and the previous loop's `LEARNER_FEEDBACK.md` section. Regressions and learner-reported problems go to the top.
2. Do the manual check of 30 random words.
3. Score 1–10, critically: data accuracy, coverage, key/merge integrity, content quality, app correctness, reproducibility/documentation.
4. List the **top 10 issues** ranked by impact on the learner, even if all scores are high, each with evidence (IDs, examples, counts) and **root cause** (source, script, rule or prompt).
5. Write the fix plan in `HANDOFF.md`: each issue assigned to one agent, in the order they should run.

## Step 3: Fix (agents in the order of the fix plan)
1. Fix every regression, every missed target, every area below 8, and at least the top 5 issues, prioritizing the loop theme.
2. Fix at the root (loader, rule, priority, prompt), never by hand-editing outputs. A genuine one-off correction goes in `pipeline/overrides.csv` with a reason.
3. Every fixed bug gets a test in `tests/`.
4. Content fixes: improve the generation prompt and regenerate the affected batches (Gemini), then review (Claude).
5. Each agent hands off to the next agent in the fix plan; the last one hands off to Codex, Step 4.

## Step 4: Confirm (Codex)
1. Rebuild and rerun metrics. A fix only counts if its metric moved. Revert any fix that made something worse and record why in `DECISIONS.md`.
2. Log issues, root causes, fixes and metrics before → after in `CHANGELOG.md`.
3. Set the next assignment in `HANDOFF.md` to **User: learner review**.

## Step 5: Learner review (the user, about 10 minutes)
1. The user studies with `app/index.html` for about 10 minutes and fills in this loop's section of `docs/LEARNER_FEEDBACK.md` (Codex creates the template):
   - wrong or suspicious data (word, what looked wrong)
   - confusing or unhelpful content
   - anything broken or different from the prototype
   - UI/UX ideas (→ `UX_BACKLOG.md`, Global Rule 10)
   - one sentence: was studying useful and enjoyable this time?
2. The user then starts the next loop (Codex, Step 1), or after loop 5, Claude for the Final Delivery. The next auditor (or Claude in the Final Delivery) turns the feedback into top-priority issues.
3. If the user skips a review, they write "no learner review" in that section.

---

# FINAL DELIVERY (Claude)

After loop 5 (including its learner review):
1. Address or record every open item from the last learner review.
2. Deliver `app/index.html`, `data/final/`, `pipeline/` (with `run_all.py`, `download.py`, `pipeline/README.md`), `config/`, `content/accepted/`, `licenses/`.
3. `README.md` with how to run, a **Data sources** section, and `LICENSE` files generated from `SOURCES.md` (app code license separate from the data license if share-alike applies).
4. `docs/`: SCHEMA, DECISIONS, CHANGELOG, HANDOFF, SOURCES, SOURCE_PROFILES, METRICS (all loops), LEARNER_FEEDBACK, UX_BACKLOG, final audit.
5. A short summary for the user: what was built, coverage numbers, known gaps, next steps.

---

# HOW TO RUN

## Before you start (the user, once)
1. Create a project folder, e.g. `<project folder>`.
2. Put in it: this prompt as `PROMPT.md`; `docs/final-data-spec.md`, `docs/data-pipeline-notes.md`, `docs/SOURCES.md`; the prototype HTML as `prototype/index.html`.
3. Make sure Python 3 and Git are installed (an agent will tell you if not).
4. Open the same folder in Claude Code, Codex and Antigravity.

## For every agent: one assignment per session
1. Read `PROMPT.md`, then `docs/HANDOFF.md`, then the other working files.
2. If `docs/HANDOFF.md` does not exist, the project has not started: only Claude acts, and runs Stage 0.
3. Otherwise, do **only** the next assignment for your role in `HANDOFF.md`. If there is none, do nothing, tell the user who should run next, and stop.
4. When done and validated: update `HANDOFF.md` (what you did, results, open problems, **which agent runs next and what it must do**), `CHANGELOG.md`, `DECISIONS.md` if needed, then `git commit`.
5. **Stop.** End with one line: `Next: <agent or User> — <task>`. Never continue into another agent's task, even if you could.

## For the user: starting each agent
Only one agent works at a time. Wait for one to stop before starting the next. Approve commands an agent asks to run (downloads, installs) after reading them.

Start message (change the agent name):
```
Read PROMPT.md. You are [Claude / Codex / Gemini].
Read docs/HANDOFF.md and do the next task assigned to your role.
When done, update HANDOFF.md, commit, and stop.
```

Audit (Stage 6, Step 2), in a **new** Claude session:
```
Read PROMPT.md. You are the independent auditor (Claude) for loop [N].
Do Stage 6, Step 2. Write scores, the top 10 issues with root causes,
and the fix plan into docs/HANDOFF.md, commit, and stop.
```
