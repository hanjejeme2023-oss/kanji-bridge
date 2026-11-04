# GATES (PROMPT Rule 11)

Every stage 1-5 ends with a gate review by Claude. A gate checks the stage's **Done when** criteria with evidence (counts, file checks, the 20 test words, a small random sample). Pass: next stage assigned. Fail: exact failures and fixes go to the agent that did the stage, who fixes only those items and hands back. A second failure of the same gate: Claude stops and asks the user. Gates are short checks; non-blocking problems go to "Open problems" in HANDOFF for the Stage 6 loops.

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
