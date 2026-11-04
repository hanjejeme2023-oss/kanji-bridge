# DECISIONS

Every key decision: who, when, why. Newest additions at the bottom of each section.

## A. Spec decisions (copied from `final-data-spec.md`; made by the user/architect on 2026-11-04)

| # | Decision | Date | By |
|---|---|---|---|
| D1 | **Normalized tables**, not one tab per view and not one giant table. Every fact is stored once; views read shared tables via IDs. | 11-04 | user + Claude |
| D2 | **Word backbone = HSK 3.0** (defines which words exist and their level). | 11-04 | user + Claude |
| D3 | **Vietnamese has no official level word list.** Vietnamese side = HSK words with a Sino-Vietnamese cognate + **high-frequency Hán-Việt words missing from HSK**, ordered by frequency. Combine with `merge(how="outer", indicator=True)`. | 11-04 | user + Claude |
| D4 | Exports: CSV for human review; JSON for publishing; `data.js` for the app. | 11-04 | user + Claude |
| D5 | App is opened from disk (`file://`); `fetch()` of local JSON is blocked, so the app loads `data/final/data.js` (`window.KB_DATA`) via `<script src>`. | 11-04 | user + Claude |
| D6 | Polyphones are resolved at word level, not by splitting character rows. `chars` keeps one row per character with primary reading + all readings. | 11-04 | user + Claude |
| D7 | Sound-rule pairs come from aligned syllables: (a) characters with exactly one Korean and one Vietnamese reading, plus (b) syllable alignment of words in `word_chars`. | 11-04 | user + Claude |
| D8 | Rule titles/explanations are static content in `config/rules.json`, written by Claude. Examples, counts, exceptions come from data. | 11-04 | user + Claude |
| D9 | Japanese on'yomi in kana come from KANJIDIC2, not Unihan. | 11-04 | user + Claude |
| D10 | False friends: (a) words in `words` whose per-language meanings differ, and (b) code-generated candidates outside `words`. Gemini judges both; Claude reviews. | 11-04 | user + Claude |
| D11 | Card eligibility: has `level`, (Japanese reading or Korean) **and** (pinyin or Vietnamese). Target switch further limits due cards. `ff_only` words appear only in 偽の友達. | 11-04 | user + Claude |

## B. Stage 0 decisions (Claude, 2026-11-04) — spec addenda

These fill gaps the prototype's views force. They are additions, not changes, to D1–D11. Also mirrored in the "Addenda" section of `final-data-spec.md`.

| # | Decision | Why |
|---|---|---|
| D12 | `data.js` holds the normalized tables (`chars` reduced, `words` reduced, `word_chars`, `ff_meanings`, `passages`) **plus** a precomputed `rules` array in the prototype's `RULES` shape. App adapters rebuild `WORDS`, `FF`, `PASSAGES`, `GLYPHS` from the tables. Missing values are **omitted keys** in `data.js` (never null/""/NaN strings). | Rule examples are build-time derived, so the app should not recompute them; omitting missing keys keeps the file small (thousands of words) and makes "undefined" handling one rule for adapters. |
| D13 | **Stable keys**: SRS (`kb_srs`), custom deck (`kb_custom`) and open false-friend tiles are keyed by `word_id`, not by the Hanzi string. `kb_custom` stores ids, not word objects. | Hanzi strings are not unique once polyphones are included (行 xíng / háng). Required by PROMPT Stage 5 task 3. |
| D14 | Added columns: `chars.level`; `words.ja_alt/ko_alt/vi_alt`, `words.note_ja`, `words.syl_aligned`. `judge()` for Vietnamese also accepts `vi_alt`. | `chars.level` orders the glyph list; alternates support multiple readings (PROMPT Rule 10 allows "multiple readings"); `note_ja` keeps the 越南 loanword note the prototype has; `syl_aligned` replaces the prototype's implicit "same number of syllables" check in `ruleTags`. |
| D15 | Reading-view passage selector may wrap onto several lines (CSS `flex-wrap:wrap` only). Passage names are `越 N` / `中 N`, numbered per language by level then id. | ≥ 5 passages × 6 levels × 2 languages = 60+ buttons; one row would overflow. Smallest change that the data forces. |
| D16 | False-friend trap reading is composed in the adapter: zh → `"<simp> <pinyin>"` if simp differs from the displayed word, else pinyin; vi → `vi`. `ff_meanings.reading` stores only the raw dictionary reading. | Prototype shows both forms (`勉强 miǎnqiǎng`, `gōngfu`); the table must stay "copied from dictionary, never generated". |
| D17 | Rule examples are single characters (not words), from non-exception pairs only, max 8 per rule, min 4 or the build fails. Order: low `level`, then high frequency, deterministic. Exceptions go to `rules_report.csv`, not to the app, this run. | Quiz shows `ex[0]` at 96 px and tracks progress by it; exceptions in a quiz would teach the wrong answer. A UX idea (showing exceptions) → `UX_BACKLOG.md`. |
| D18 | ~~Cards: no daily new-card limit this run.~~ **Superseded by D20** (user approved the limit on 2026-11-04). | |
| D19 | Git commits are made with the identity set in the repo-local config (`Hanje Unesaki <311183901+hanjejeme2023-oss@users.noreply.github.com>`; changed from [earlier address removed] on the user's instruction 2026-11-04, and the unpushed Stage 0 commit was rewritten to the new author). `raw/` is not committed; `licenses/` is. Each commit message starts `[Agent] Stage N: …`. | PROMPT Global Rule 7. |
| D20 | **Daily new-card limit, approved by the user** (Global Rule 10 user-approval exception), 2026-11-04. In カード, at most **20 never-seen cards per day** are introduced; reviews of already-seen cards (those in `kb_srs`) are not limited. No visible UI change except that the existing counters (`残り N 枚`, `今日 N 枚`, progress bar) show smaller numbers. Day = local calendar date; the count of new cards introduced today is stored in localStorage (new key `kb_newtoday` = `{date, ids[]}`; a card introduced today stays in the due list until rated, even after reload). New cards follow the deck order (level, then `freq_vi`). Applies after the target filter (a card not matching the target switch does not use up the quota). Cards added from 読解 ("カードに追加") count as new cards. Implemented in Stage 5, covered by a test. | User decision. Thousands of cards would otherwise be due on first use. |

## C. Open decisions (owner → when)
- Source priority per column → Claude, Stage 1 review
- Shinjitai ↔ traditional mapping method → Claude, Stage 1 review
- Frequency bands that give VI-only words a `level` → Claude, before Stage 3 (Codex may ask via HANDOFF)
- License judgments (esp. libhangul `hanja.txt`, share-alike impact) → Claude, with the user if in doubt, Stage 1 review
