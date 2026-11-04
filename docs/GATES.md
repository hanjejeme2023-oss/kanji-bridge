# GATES (PROMPT Rule 11)

Every stage 1-5 ends with a gate review by Claude. A gate checks the stage's **Done when** criteria with evidence (counts, file checks, the 20 test words, a small random sample). Pass: next stage assigned. Fail: exact failures and fixes go to the agent that did the stage, who fixes only those items and hands back. A second failure of the same gate: Claude stops and asks the user. Gates are short checks; non-blocking problems go to "Open problems" in HANDOFF for the Stage 6 loops.

## Standing collision checks (DECISIONS D37, D38) — run at the Stage 2 gate, the Stage 3 gate, and whenever `chars` grows

| Check | What to verify (with evidence) | Expected |
|---|---|---|
| **C1 many → one** (several source characters share one `trad`) | `char_key_collisions.csv`; `char_id` and `key_char` unique; every shared `trad` resolved by D37; after Stage 3: no word character unlinked or ambiguous without being listed in `char_ambiguous.csv` | Stage 2: exactly `著` → `着`, `著`; 3,000 rows |
| **C2 one → many** (one simplified character, several traditional forms) | HSK-list rows with more than one traditional variant; each variant used in a word `trad` has its own `chars` row (Stage 3); no empty `trad`; `char_simp_mismatch.csv` reviewed; counts reproduced | 83 rows / 89 non-first variants / 88 variants needing new rows (1, 覆, already a row); after Stage 3: 0 unlinked word characters |

Reference measurement: `docs/review_scripts/char_collision_reference.py`. Tests: `tests/test_char_collisions.py` (Codex).

| Stage | Gate date | Result | Attempt | Gate by |
|---|---|---|---|---|
| 1 | 2026-11-04 | PASS | 1 | Claude |
| 2 | 2026-11-04 | PASS | 1 | Claude |

## Stage 1 — sources and licences — PASS (attempt 1), 2026-11-04

Gate run after Rule 11 was added (the Stage 1 review had been done earlier under the old wording; criteria re-checked now against the files on disk).

| Done-when criterion | Evidence | Result |
|---|---|---|
| Every source downloaded or explicitly excluded with a reason | 9 sources downloaded (Unihan, KANJIDIC2, hsk30, CC-CEDICT, JMdict, libhangul, OpenCC, Kaikki, FrequencyWords); source #7 excluded with reason (no licence, missing input provenance; D21) | OK |
| `SOURCES.md` section 1 has no blank cells (要確認 only where Claude must decide) | All 12 table rows complete; the only remaining 要確認 text is the legend line in the file header; every earlier 要確認 resolved in D23 | OK |
| Every used source has its licence file in `licenses/` | 10 files in `licenses/`: Unicode, KANJIDIC2-EDRDG, JMdict-EDRDG, CC-CEDICT, CC-BY-SA-4.0, HSK30-MIT, LIBHANGUL-HANJA-BSD-3, OPENCC-Apache-2.0, KAIKKI, FREQUENCYWORDS | OK |
| `download.py` reruns without re-downloading unchanged files | Reran `pipeline/download.py`: every file reported `ok` (checksum verified), no download; `git status` shows `pipeline/source_manifest.csv` unchanged | OK |
| `SOURCE_PROFILES.md` covers every source | Sections 1-8 cover all downloaded sources plus the excluded one | OK |
| Extra check: raw files match the locked checksums | 23 / 23 files in `pipeline/source_manifest.csv` match their SHA-256 | OK |

Claude-review items (Stage 1 "Claude review (gate)"): licences confirmed (D23, D35), 200-sample Unihan `kVietnamese` cross-check done (`docs/STAGE1_REVIEW.md` section 2.2), shinjitai method chosen (D28), source priority set (D33). Non-blocking problem passed on: Vietnamese coverage ceiling (about 35% of HSK words), handled by the D36 search.

Fixes requested: none.

## Stage 2 — character table — PASS (attempt 1), 2026-11-04

| Done-when criterion | Evidence (rechecked on disk, not taken from the report) | Result |
|---|---|---|
| `chars` covers all 3,000 HSK characters; missing reported, not guessed | 3,000 rows; missing: jp 45, ja_on 49, vi 709 (ko 0, pinyin 0); `coverage_report.csv`, `no_jp_form.csv` present | OK |
| No duplicate `char_id` / `trad` key; collisions resolved by a decision | `char_id` and `key_char` unique; empty `trad` 0; `char_key_collisions.csv` = only 著 → 着 (L1), 著 (L4) (D37, C1) | OK |
| C2 one→many | counts reproduced by `tests/test_char_collisions.py` (83 / 89 / 88; 1,088 rows with simp≠trad all have `ko`) | OK |
| All text NFC | vi, ko, jp, pinyin checked NFC | OK |
| Test characters correct in every language | 學 学/学/がく/학/xué/học; 國 quốc; 茶 trà; 行 hành; 生 sinh; 樂 nhạc: all match their sources (see note 1) | OK |
| `rules_report.csv` exists | 7 rows; cells total 1,561 = rows of `rules_examples.csv` | OK |
| Tests pass; rebuild identical | `unittest discover` rerun: 16 tests OK (56 s), includes two rebuilds | OK |

**User-requested check: verified readings only.** All 1,561 rows behind `rules_report.csv` have `source_vi` in {`kaikki_aligned` 1,292, `unihan_hvsyl` 269}; `unihan_unverified` = 0 (456 such readings are excluded). 主 = chủ (`kaikki_aligned`); the Nôm reading chúa is in neither `vi` nor `vi_all`.

**`rules_report.csv` vs `config/rules.json`:** 1,554 of 1,561 (99.6%) follow the rules (ㄱ→c/ch 152/153; ㄴ→n 259/260; ㄹ→t 70/70; ㅁ→m 69/70; ㅂ→p 32/33; ㅇ→ng/nh 288/289; no patchim→open 684/686). The 7 off-pattern characters, each checked:

| char | ko / vi | Verdict |
|---|---|---|
| 伯 | 백 / bá (ㄱ→open) | real exception (explicit Kaikki alignment) |
| 幻 | 환 / ảo (ㄴ→open) | reading is in Kaikki; the usual Hán-Việt is huyễn. Keep, flag for loop 1 (accuracy) |
| 逼 | 핍 / bức (ㅂ→c) | real exception (Kaikki) |
| 承 | 승 / thừa (ㅇ→open) | real exception (Kaikki) |
| 刷 | 쇄 / loát (open→t) | real: the two languages follow different Middle Chinese readings |
| 揭 | 게 / yết (open→t) | real polyphone (Korean 게/걸) |
| 怎 | 즘 / chẩn (ㅁ→n) | **suspect**: `unihan_hvsyl`; expected chẩm. Passes only the weak syllable-attested test. Flag for loop 1 (accuracy) |

**Notes (non-blocking → HANDOFF Open problems):**
1. `chars.ko` primary = first Unihan `kHangul` (D32), and Unihan lists values alphabetically: 行 = 항 (`ko_all` 항;행), 茶 = 다 (다;차), 樂 = 낙. All are valid readings present in `ko_all`; `ko_final` is unaffected. Learner-visible Korean comes from libhangul word readings in Stage 3, so cards are unaffected. Stage 3 must align `word_chars` using the word-level reading and `ko_all`, not `chars.ko`.
2. `unihan_hvsyl` (300 characters) is a weaker check than `kaikki_aligned`: the Unihan syllable is an attested Hán-Việt syllable, not an explicit alignment. 怎 is the only suspect found in the rules table.

Fixes requested: none. Next: Codex, Stage 3.
