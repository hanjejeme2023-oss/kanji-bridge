# Stage 4 gate part 3: task-3 Vietnamese rerun, step 6, Korean finding (Claude, 2026-11-07)

Input: the user's rerun of task 3 b008-b014 with `content/prompts/task3_v3.md` (2026-11-07 17:58-18:01 UTC); the user's answer to `docs/VI_CLEAR_SHORTLIST.md` ("All as proposed. A27: clear."); the user's Korean finding on the ten false friends of part 2 §6. Scripts (read-only unless stated): `docs/review_scripts/stage4d_part3_reference.py` (sections `integrity passages overlay`), `docs/review_scripts/stage4d_part3_step6.py` (writes the step-6 rows with `--write`).

**Result (D65, D66):** task 3 **Vietnamese b008-b014 accepted** with `config/task3_review.csv` (4 passages dropped, 2 edited by deleting a token); step 6 applied (37 `vi` overrides, 28 `clear_vi` rows); all accepted task 1-4 batches moved to `content/accepted/`. Korean finding confirmed and wider than reported: new **task 5 (Korean usage check)**, Codex 4c-prep4 first, then one user run, then Claude gate part 4, then Codex 4e.

## 1. Task 3 rerun: integrity

| Check | Evidence | Result |
|---|---|---|
| Validator rerun | `validators.validate` on all 14 outputs: 0 failures; 14 logs `validation.ok` | OK |
| Inputs = fresh build | all 14 `content/inputs/task3/bNNN.jsonl` byte-identical to `builders.task_batches(3, task-1 output)` | OK |
| Prompt | b008-b014 log `prompt_sha256` `e8449a3d` = SHA of `runner.prompt_text(3, vi cell)` (v3); b001-b007 `c77d9809` (v2) unchanged | OK |
| Settings | `gemini-4-argon`, temperature 0.3, thinking 0, unreported 0; every batch first attempt | OK |
| Coverage | 6 passages per cell; every passage links ≥ 4 words (vi) and a word at the cell's level | OK |
| Cost | rerun $0.38532 (7 rows); ledger total **$22.24585975**, room $77.75 | OK |

## 2. Task 3 Vietnamese: all 42 passages read

**The forced archaic class is gone.** None of the 13 named words or anything like them (`lão sư`, `chủng tử`, `quan tài phán` …); the passages read like modern textbook Vietnamese at every level, with everyday words as gloss tokens (`sinh viên`, `máy tính`, `bản đồ`-type choices). Remaining problems are single, unrelated slips:

| Passage | Problem | Handling |
|---|---|---|
| b008 L1 #1 | `học sinh … ở trường đại học`: *học sinh* is a school pupil; university students are *sinh viên* | drop |
| b010 L3 #4 | `translation_ja` contains Korean (「パスポートを 안전한場所に」); `chuyến bay quốc nội` (everyday: *nội địa*) | drop |
| b011 L4 #5 | `một cách nghiêm cách`: literary *nghiêm cách* (everyday *nghiêm túc / nghiêm khắc*), repeats *cách* | drop |
| b014 L7 #6 | `điều độ giờ giấc`: *điều độ* is linked to 調度 ("dispatch, adjust") but used as "keep regular hours"; the tap shows the wrong meaning | drop |
| b013 L6 #3 | `Khoa ngoại khoa` repeats *khoa* | delete the token `Khoa`; `ngoại khoa` → `Ngoại khoa` |
| b013 L6 #4 | `đều có tự giác bảo vệ` unidiomatic | delete the token `có` |

Acceptable, not counted: `trận địa chấn`, `mắc trọng bệnh`, `khai thông đường cao tốc`, `giao thông đình trệ` (press register), `đầu hàng trước tội của mình` (marked but understandable), `Không` linked to 空 (the negator is the 空 reading; task-1 meaning says so).

**Overlay `config/task3_review.csv`** (Claude's review decision; columns `batch, passage, action, token_index, generated, review, reason`; `passage` 1-based, `token_index` 0-based in the generated token list): `drop` (fail-closed on `translation_ja`), `delete_token` (fail-closed on the token JSON), `set_t` (fail-closed on the old `t`; only on a linked token). Reference implementation `apply_task3_review` in the part-3 script: every kept and edited passage passes `validate_task3`; no new Vietnamese word is written (two deletions, one capital). After the overlay: b008, b010, b011, b014 keep **5** passages, b009, b012, b013 keep 6 (target ≥ 5 per cell, PROMPT Stage 4). The Hangul check over all 84 translations and every `gloss_ja` finds only the dropped b010 #4.

**Why accept, not reject:** 6 of 42 passages (14%) had a slip, against about 1 in 5 with forced words in v2; after the overlay 0 known errors remain in 38 passages. The per-batch 5% line cannot separate batches of 6 passages (one slip = 17%), and the remaining slips are one-off, unrelated mistakes that the prompt already forbids in general terms; a third run would trade them for other one-offs at the same expected rate. The systematic class that a prompt could fix (D64 item 4) is fixed. Recorded as D65 item 1 (amends D64 item 4 for passages). A second rejection would also have triggered Global Rule 11 (stop and ask the user).

## 3. Step 6 (D57 Q1, D64 item 5): user-confirmed clears applied

User answer 2026-11-07: **"All as proposed. A27: clear."**

- **Group A, 37 `pipeline/overrides.csv` rows** (`words`, `vi` → empty; reason cites the list number): A1-A39 without A20 低迷 and A36 預算 (kept). 季女 is VI-only, key `x|季女`. The script asserts that the candidate set (task-1 `different_word` + multi-character `unsure`, after D63) is exactly the 39 listed words and that every current `vi` equals the listed value.
- **Group B, 28 `config/task2_review.csv` rows**, action `clear_vi`: `meaning_ja_generated` / `is_trap_generated` = the task-2 Vietnamese entry (fail-closed), `false_friend_review` = the generated list without `vi` (B1 上達, B11 手紙, B28 新規 keep `zh`; the rest become empty), `meaning_ja_review` empty.

**Rebuild check** (`d55_apply_check.py HEAD`):

| Check | Result |
|---|---|
| Overrides | 158 rows, **all apply**; cleared `vi` 66 |
| `words` | 12,229 rows, keys unchanged (`_merge` both 12,229); `vi` changed for exactly the 37 words; `ko`, `ja` unchanged |
| `chars` | 3,140; no primary, `*_all`, final or source change |
| D52 ties (`word_chars` `vi_syllable` counts per character) | 15 → 14: no new tie; the tie 液 giá 1 / dịch 1 is gone (液體 *giá thể*, the known data error, was cleared). 領 lĩnh 9 → 8 vs lãnh 7, primary unchanged |
| Side effects | 季女 (VI-only, `vi` was its only target language) is no longer `card_eligible`: **8,555 → 8,554**. `char_primary_no_evidence.csv` +4 (荷, 痕, 瀾, 蓮: their only word evidence was cleared; primaries unchanged). `rules_examples.csv`: the exception pair 液 giá removed |
| Coverage | HSK `vi` 4,245 → **4,211**; all four 3,367 → **3,345**; words with `vi` 5,446 → 5,409 |
| Note | 平價 keeps `vi_alt` *bằng giá* after the clear (the build keeps `vi_alt`): Stage 5 must not emit `va` when `v` is empty (handed to Codex 4e/5) |

Tests and rebuild identity: `GATES.md` "Stage 4 gate part 3".

## 4. Accepted files moved

`git mv` of every task 1-4 batch: `content/generated/taskN/bNNN.{jsonl,log.json}` → `content/accepted/taskN/`, `content/inputs/taskN/bNNN.jsonl` → `content/accepted/taskN/inputs/`. 86 + 79 + 14 + 5 batches. Pilots stay where they are (not used). Codex 4e reads only `content/accepted/` and applies the overlays `config/task1_review.csv`, `task2_review.csv`, `task3_review.csv`, `task4_review.csv` fail-closed. Since step 6 changed `words`, rebuilt task-1 inputs no longer match the accepted inputs; that is expected and is why the accepted inputs are kept with the outputs.

## 5. Korean finding (user, 2026-11-07)

User: the Korean readings of 同事 동사, 不大 부대, 順路 순로, 調度 조도, 研究生 연구생 are words Koreans do not use for these meanings (동료; 부대 / 조도 normally 部隊 / 照度); the user suggested a small Argon pass over the `ff_candidates` Korean readings.

**Evidence:**

1. All five are **HSK card words** (w01045, w00031, w09274, w06279, w03064), not `ff_candidates` rows. They went through task 1, which marked only 不大 `ko_rare`; 同事, 順路, 調度, 研究生 were `high`. Task 2 then wrote Korean meanings for them (同事 ko 「同僚、または同じ事柄」), which the 偽の友達 view would show.
2. **`ko_rare` has no effect downstream.** It is a review-only field (SCHEMA §5): the 930 task-1 `ko_rare` words (847 multi-character) would still get `meaning_ja__ko` and their Korean `ff_meanings` rows.
3. **Task 1 misses many** (Claude's own reading, seed 1109, task-1 Korean readings *not* flagged): about 4 of 40 card words (折中 절중, 誠信 성신, 風沙 풍사, 廉正 염정), about 5-6 of 40 task-2 words (開張 개장, 會意 회의, 事宜 사의, 差數 차수, 王牌 왕패, 得意 득의 borderline), and about 8-9 of 30 `ff_candidates` rows, which were never checked (浴衣 욕의, 小羊 소양, 牛角 우각, 奇麗 기려, 嫩葉 눈엽, 世相 세상, 疑義 의의, 幾度 기도, 橙色 등색 borderline). Its precision looked good (半天 반천, 出來 출래, 知道 지도, 重新 중신 …).

So the problem is real and wider than the `ff_candidates` rows: an estimated ~700 unflagged card words and ~650 `ff_candidates` rows besides the 847 already flagged. The rule, scope, cost and run plan are in **D66**; the prompt is `content/prompts/task5_v1.md`.

**Held-out cases for gate part 4** (not in the prompt): rare 誠信, 會意, 事宜, 差數, 王牌, 折中, 小羊, 幾度, 世相, 奇麗, 嫩葉, 浴衣, 疑義; used 用意 용의, 唯獨 유독, 文件 문건, 教書 교서, 上場 상장, 臨床 임상, 告白 고백, 言論 언론; real Korean false friends that must stay `used`: 工夫 공부, 愛人 애인, 汽車 기차, 小心 소심, 東西 동서 (in the prompt as examples, so a weaker test) and every Korean trap of task 2.
