# Stage 4a report — generation script and pilot

Date: 2026-11-06
Agent: Codex
Next review: Claude, Stage 4b

## Result

Stage 4a is complete. The Vertex check passed, all seven requested pilot generations produced locally valid output, and no full task was started. Gemini 3.8 Flash remains the pinned default. Gemini 4 Argon was used only for the user-requested task-1/task-2 comparison; Claude must choose and record the full-run model at Stage 4b.

## Implementation

- CLI: `pipeline/stage4_generate.py`
- Package: `pipeline/stage4/` (`builders.py`, `validators.py`, `runner.py`, `prices.json`)
- SDK: `google-genai==2.34.0`, separately pinned in `pipeline/requirements-stage4.txt`
- Prompts: `content/prompts/task1_v1.md` through `task4_v1.md`
- Exact pilot inputs: `content/inputs/pilot/`
- Flash pilot output/logs: `content/generated/pilot/`
- Argon comparison output/logs: `content/generated/pilot/argon/`
- Request ledger: `content/cost_log.csv`

`run_all.py` does not import Stage 4. The API-key guard rejects `GEMINI_API_KEY` or `GOOGLE_API_KEY`; the client uses Vertex AI with Application Default Credentials only. No credential or request header is logged. The cost guard counts the request before generation, uses measured output averages when available, and enforces the shared $100 ceiling.

Commands implemented: `--check`, `--pilot`, `--task 1|2|3|4 [--batch N]`, and `--dry-run`. API/local-validation failures get at most two retries; 429/resource-exhausted waits do not consume a retry.

## Models and settings

| Use | Model ID | Location | Temperature | Thinking | Max output |
|---|---|---|---:|---|---:|
| pinned default/full-task path | `gemini-3.8-flash` | `global` | 0.3 | model default | 65,536 |
| pilot comparison only | `gemini-4-argon` | `global` | 0.3 | model default | 65,536 |
| `--check` | `gemini-3.8-flash` | `global` | 0.3 | model default | 1,024 |

Flash price: $0.75 input / $3.75 output or thinking per 1M tokens through 2026-12-31. Argon price: $2 / $10 through 2026-11-30, then $4 / $20. All are in `prices.json` and selected by date.

The first check exposed a script bug: 32 output tokens were exhausted by thinking, making `response.text` empty. The check now uses 1,024 tokens. Every generated response is checked for text before JSON parsing; an empty response reports finish reason plus input/output/thinking counts. A check response is cost-logged before parsing, and an API-level check failure gets a zero-token ledger row. The corrected check passed:

```text
model=gemini-3.8-flash
location=global
token_count=123
```

The pre-fix failed check's usage was not retained by the old code and is not in the ledger; its small cost cannot be reconstructed without inventing token counts.

## Pilot measurements

All final saved outputs passed the deterministic local validators.

| Request | Model | Items | Input | Visible output | Thinking | Successful-attempt cost | Attempts |
|---|---|---:|---:|---:|---:|---:|---|
| task 1 | Flash | 100 | 14,401 | 13,113 | 0 | $0.05997450 | 3; two local-validation retries |
| task 2 | Flash | 50 | 4,772 | 4,224 | 15,883 | $0.07898025 | 1 |
| task 1 comparison | Argon | 100 | 14,280 | 13,859 | 0 | $0.16715000 | 3; one transport failure, one local-validation retry |
| task 2 comparison | Argon | 50 | 4,780 | 4,228 | 0 | $0.05184000 | 1 |
| task 3 zh level 1 | Flash | 1 cell / 6 passages | 981 | 992 | 0 | $0.00445575 | 1 |
| task 3 vi level 3 | Flash | 1 cell / 6 passages | 1,447 | 1,542 | 2,431 | $0.01598400 | 1 |
| task 4 | Flash | 50 | 5,639 | 2,358 | 5,302 | $0.03295425 | 1 |

Task-1 Flash retry errors were meaning-presence violations for Vietnamese; Argon had one such violation plus one server disconnect. The final outputs pass. Claude should decide whether the prompts need tightening before the full run because retries materially change cost.

The Flash and Argon task-1/task-2 prompt hashes and input hashes are identical. Flash pilot task 1 contains 12 low-confidence items, 29 `meanings_differ=true` items, and Vietnamese checks of 74 `same_word`, 10 `different_word`, 0 `unsure`, 16 empty. Flash task 2 marks 9/50 items as false friends and has no low-confidence item. These are review evidence, not accepted content.

The corrected check plus every pilot attempt in `content/cost_log.csv` totals **$0.69781975**. This includes billed local-validation retries and excludes the unrecoverable pre-fix check described above.

## Full-run projections

Mechanical projections scale the final successful pilot request: task 1 to 8,555 words; task 2 to the D58 planning estimate of 5,000 items (the exact count is known only after full task 1); task 3 from two cells to 14; task 4 to 302 words.

| Task | Projected input | Projected visible output | Projected thinking | Flash cost |
|---|---:|---:|---:|---:|
| 1 | 1,232,005 | 1,121,817 | 0 | $5.13 |
| 2 | 477,200 | 422,400 | 1,588,300 | $7.90 |
| 3 | 16,996 | 17,738 | 17,017 | $0.14 lower bound |
| 4 | 34,059 | 14,242 | 32,024 | $0.20 |
| **Total** | | | | **$13.37 lower bound** |

Task 3 is deliberately under-represented: the pilot could link only words with meanings from the 100-word task-1 pilot, while the full request may carry up to 500 words. Replacing its mechanical $0.14 with D58's approximately $2 estimate gives about **$15.23**. If every Flash task-1 batch repeated the pilot's three billed generations, another approximately **$10.26** would be added, producing a conservative approximately **$25.49** before exceptional reruns. This remains consistent with D58's $20–45 planning range and below the hard ceiling.

For the identical task-1/task-2 comparison only, Argon projects to **$19.48 through November 30** or **$38.97 from December 1** on one successful attempt per batch. Applying the pilot's two billed task-1 attempts raises those two-task figures to approximately **$33.78 / $67.57**, before tasks 3–4 or further retries. Claude should consider both output quality and this retry/price risk.

## Validation and tests

- Final pilot outputs: 7/7 requests locally valid; every key resolves; NFC/enums/language presence/traps/tokens/readings pass.
- Frozen counts: 8,555 task-1 items, 86 task-1 batches; 302 task-4 items, 7 task-4 batches.
- Deterministic builder SHA tests pass.
- Validators reject crafted wrong IDs, absent-language meanings, wrong passage text/IDs, and unknown Korean/Vietnamese note readings.
- API-key guard, credential-pattern scan, response-empty diagnostics, schema compatibility, and `run_all.py` isolation pass.
- After restoring an override backup left by an interrupted pre-existing rebuild test, one complete canonical Stage 3 rebuild succeeded and all **54 non-rebuild tests passed**. The Stage 4-specific set is fully included. No frozen output remains modified.

## Stage 4b review requests

1. Review both model outputs for task 1 and task 2 using the identical-input hashes.
2. Record the user's Argon comparison instruction and the chosen full-run model/settings in `DECISIONS.md`.
3. Decide whether the task-1 prompt needs a revision to avoid Vietnamese meaning-presence retries.
4. Check all low-confidence and all non-`same_word` Vietnamese flags in the pilot.
5. Approve the cost projection before assigning Codex Stage 4c. No full run has started.
