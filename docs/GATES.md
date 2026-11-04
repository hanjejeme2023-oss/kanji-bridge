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
