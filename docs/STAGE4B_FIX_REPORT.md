# Stage 4b-fix — D60 implementation and Argon re-pilot

Date: 2026-11-06
Agent: Codex
Next review: Claude, Stage 4b re-check

## Result

D60 and the user's additions 9-11 are implemented. The Argon check passed and all five re-pilot requests passed deterministic local validation on their first attempt. No full task was started. The canonical Stage 3 rebuild completed with the frozen counts and no `data/` diff.

## Runner and validation changes

- Pinned `gemini-4-argon` in `global` for every task; temperature 0.3, model-default thinking, maximum output 65,536.
- Tasks 1-3 use the unedited v2 prompts; task 4 remains v1. Task-1 v2 input SHA-256 is identical to the first pilot: `e0d78cd496151ac3d36aa04068fc8e7d3a4fecb36cf09b3cf78a90fb50fd906f`.
- Added the D60 response-schema property order, single-character/`unsure` task-1 rules, and task-2 baseline-language rule.
- Task 4 now reuses `pipeline.stage3_match.collapse_iy`, removes i/y-only and `unihan_unverified` Vietnamese differences, and drops empty items: **243 items / 5 batches**. Full task 4 also filters Vietnamese differences to task-1 `vi_check=same_word`.
- The UTC deadline guard refuses Argon requests on or after 2026-12-01 unless the user explicitly passes `--allow-after-deadline`.
- `--task N` is resumable: it revalidates the output and log against the current model, prompt SHA, input SHA, item count and local validator, skips valid batches, and runs missing/failed ones. `--batch N` remains the explicit forced rerun path. An offline test covers both the skip and failed-log rerun.
- Each SDK request has a 600-second timeout and one SDK transport attempt; a timeout reaches the runner as an ordinary counted retry (up to two runner retries). Attempt duration and total batch wall time are recorded.
- Usage now records `usage_metadata.total_token_count`. `unreported_tokens = max(total - input - output - thinking, 0)` is billed at the output rate in `cost_log.csv`, request cost, measured averages and the $100 ceiling estimate. The cost log was schema-migrated without changing prior costs.

## Check and re-pilot

`--check` passed: model `gemini-4-argon`, location `global`, 213 total tokens, 3.479 seconds, $0.000594. Project/location values were set only in the process environment and were not written to a project file.

All request times below are end-to-end batch wall time, including token counting; generation-call duration is also retained in `cost_log.csv`.

| Request | Items | Input | Output | Thinking | Total | Unreported | Wall time | Cost | Attempts |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Task 1 | 100 | 14,706 | 9,068 | 0 | 23,774 | 0 | 111.189 s | $0.120092 | 1 |
| Task 2 | 50 | 5,012 | 4,043 | 0 | 9,055 | 0 | 51.313 s | $0.050454 | 1 |
| Task 3 zh L1 | 1 cell | 1,215 | 1,526 | 0 | 2,741 | 0 | 23.405 s | $0.017690 | 1 |
| Task 3 vi L3 | 1 cell | 1,742 | 1,816 | 0 | 3,558 | 0 | 23.614 s | $0.021644 | 1 |
| Task 4 | 50 | 5,675 | 2,297 | 0 | 7,972 | 0 | 34.836 s | $0.034320 | 1 |
| **Re-pilot total** | | **28,350** | **18,750** | **0** | **47,100** | **0** | **244.357 s** | **$0.244200** | **5/5 first attempt** |

Argon still reports `thinking_tokens=0`, but on every re-pilot response `total_token_count = input + output`; therefore the newly conservative unreported-token charge is zero for this re-pilot. Future positive differences are charged at the output rate.

## Full-run projections from the re-pilot

Task 2 assumes the pilot's 22% `meanings_differ` rate: about 1,882 task-1 words plus 2,504 fixed candidates = about 4,386 items / 88 requests. Durations assume one attempt per request and the measured mean wall time. Task-3 inputs are deliberately smaller than the eventual 500-word cells, so its token/cost projection and the total cost are lower bounds.

| Task | Requests | Projected input | Projected output | Projected duration | Measured cost extrapolation |
|---|---:|---:|---:|---:|---:|
| 1 | 86 | 1,258,098 | 775,767 | 2 h 39 m | $10.27 |
| 2 | 88 | 439,653 | 354,652 | 1 h 15 m | $4.43 |
| 3 | 14 | 20,699 | 23,394 | 5 m 29 s lower bound | $0.28 lower bound |
| 4 | 5 | 27,580 | 11,163 | 2 m 49 s | $0.17 |
| **Total** | **193** | | | **about 4 h 3 m** | **$15.14 lower bound** |

The approved **$26-41 planning envelope** remains the safer full-run budget because it includes full task-3 payloads and retries. Both the measured extrapolation and planning envelope remain below the $100 hard ceiling.

## Claude re-check list

- 國, 茶: `vi_check=same_word`.
- 樂, 試, 塗: `vi_check=unsure`, `confidence=low`, never `different_word`.
- 勉強, 大丈夫, 手紙, 新聞: `ja` absent from `false_friend`.
- Task 1 completed with one presence-valid attempt; no retry.
- Every pilot log records Argon, `global`, v2/v1 prompt SHA, input SHA, total/unreported tokens, cost, timeout setting, attempts and wall time.

## Verification

- 63 non-rebuild tests pass after generation, including schema order, all new validator rules, 243-item task-4 count/filter, UTC guard, timeout, conservative total-token billing, credential scan and resume behavior.
- A direct canonical `run_all.py --skip-download` rebuild completed: 12,229 words (11,028 HSK + 1,201 VI-only), 3,140 chars, 24,497 `word_chars`, 2,504 false-friend candidates. `git diff -- data` is empty. The already-documented `pipeline/id_map.csv` line-ending-only working-tree diff remains untouched.
- No full-run directory or full task output was created.
