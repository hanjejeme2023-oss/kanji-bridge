# Stage 4 gate part 1: task 1 review (Claude, 2026-11-07)

Input: `content/inputs/task1/` and `content/generated/task1/` (86 batches, 8,555 items), run by the user on 2026-11-06 (sitting 1, D62); `content/cost_log.csv`. Reference script: `docs/review_scripts/stage4d_task1_reference.py` (read-only; reproduces every number below).

**Result: all 86 batches ACCEPTED** (no batch above 5% errors; the most in one batch is 2 of 100, b077). **16 `vi_check=different_word` decisions are corrected** by `config/task1_review.csv` (D63) before tasks 2-4.

## 1. Done-when and run integrity

| Check | Evidence | Result |
|---|---|---|
| Every eligible word has a result | 8,555 items = 8,555 `card_eligible` words, `word_id` unique, 86/86 logs `validation.ok` | OK |
| Local validator rerun by Claude | `validators.validate(1, …)` on all 86 output files: 0 failures | OK |
| Inputs = frozen tables | every `content/inputs/task1/bNNN.jsonl` is byte-identical to a fresh `build_task1_batches()` | OK |
| Frozen data | `git diff HEAD -- data config pipeline/overrides.csv` empty before this review; `pipeline/id_map.csv` differs in line endings only | OK |
| Settings | every log: `gemini-4-argon`, `global`, temperature 0.3, one prompt SHA (`8d684318…`, task1_v2), thinking 0, unreported 0 | OK |
| Attempts | 80 batches first attempt; 5 with 2 attempts (b004, b005, b039: transport; b080: 500; b054: validation), 1 with 3 (b040: 504 + disconnect) | OK |
| Cost | ledger total **$14.37353775** (pilot/check $0.94; task 1 $13.43 incl. the failed b054 attempt $0.167); room under the $100 ceiling $85.63 | OK |
| No reading in output | task-1 output has no reading field; validator checks key set | OK |

## 2. User's run-log notes

1. **Low output tokens (b028 etc.): formatting only, confirmed.** Output tokens per stored character are bimodal: **0.381** in 13 batches (b028, b029, b043, b056, b059, b062, b072, b073, b074, b076, b081, b083, and the short b086) vs **0.564** in 69 batches, with 4 mixed batches at 0.46-0.48 (b006, b046, b080, b085). The stored content per batch has the same size in both groups (mean meaning length 29.2 vs 30.0 characters per item, 3.39 vs 3.32 languages per item). The runner stores re-serialised JSON, so the raw response bytes are not kept; but the same content at two fixed token rates can only be response formatting (indentation/spaces), not content. The padded batches cost about 313k extra output tokens, **about $3.1**; not worth a code change (the model chooses the layout under `application/json`).
2. **b083 all `same_word`: plausible, not a skipped judgment.** All 100 items are VI-only level 5-7 words from `kaikki_en_han`, whose English gloss is Kaikki's gloss of the entry that names these Han characters (二分 binary, 確率 probability, 白血球 leukocyte, 餘震 aftershock); meanings and glosses agree in all 15 sampled. b075-b085 (all VI-only) are 99-100% `same_word` for the same reason; `kaikki_en_han` overall is 1,049 / 1,057 `same_word`.
3. **b040 server hangs:** two attempts of about 600 s each (504 `DEADLINE_EXCEEDED`, then `RemoteProtocolError`), logged at $0; the third attempt validated. All $0 transport rows in task 1: b004, b005, b039, b040 ×2, b080 (6). D61's known gap applies: if Google bills any of them, the worst case is about $0.17 each, **about $1 in total**. The Cloud Billing report (Vertex AI, after about one day) shows the real figure.

**Codex fix `c2caac3`** (read): `count_tokens` and the ceiling check now run inside the per-batch retry loop; a `Stage4Error` (ceiling, deadline) still stops the run; a transport error on either call uses the counted 30/60-second retries and then writes a failed log and continues; a successful count is kept across later generation retries; the launcher calls `python -u`. Correct for the sitting-1 crash; no change needed.

## 3. Review sample (PROMPT Stage 4 gate)

| Set | Size | Errors | Notes |
|---|---|---|---|
| Fixed items | 20 test words in task 1 + 自己, 財源, 容易, 小姐, 老公 | 0 | 國, 茶 `same_word`; 行 L1, 樂 `unsure` with the Vietnamese meaning kept; 勉強 JA 勉強・学習, `differ`, `ko_rare`; 自己 VI 自閉症の, `differ` → task 2; 財源 now `same_word` (the re-pilot regression is gone); 博士 VI 医師 `differ`. 手紙, 大丈夫 are `ff_candidates` (task 2) |
| Random | 50 (seed 20261106) | 0 | good catches: 出港 xuất cảng 輸出する, 改裝 cải trang 変装する, 供應 JA 供応 (もてなす) |
| `different_word` | all 46 | **12 wrong, 4 keep-vi** | §4 |
| `unsure` | all 9 multi-character + 40 of 522 single-character | 0 | single characters: gloss describes a native homophone (開 khai, 夢 mộng, 大 đại), Sino-Vietnamese meaning kept as instructed |
| `ko_rare` | 60 of 930 | 0 | 眼睛 안정, 飛機 비기, 麵包 면포, 南瓜 남과: hanja-dictionary entries Koreans do not use. 930 is high but matches `hanja.txt` (no frequency, D49) |
| `meanings_differ=true` | 25 of 1,419 | 0 serious | broad (牙, 初步, 彼此 are marginal) but task 2 decides `false_friend`; over-inclusion costs about 10 extra task-2 requests |
| Other `low` | all 2 `same_word` low that are not `ko_rare` (鮮美, 香水: place-name gloss) | 0 | |

## 4. `different_word` (46): 30 right, 16 corrected

The D62 character check (each character the reason names must have the `vi` syllable in `chars.vi_all`) flags impossible names (最少 → 最小 fails at 小 tiểu; 商賣 → 商業 fails; 開場 → 開学 fails), but a passing name is not proof (符効, 色態 pass and are not words), so every item was judged by hand.

**Wrong: same word, `vi` correct (12):** 符號 phù hiệu, 複製 phục chế, 色彩 sắc thái, 裝置 trang trí, 和諧 hòa hài, 精細 tinh tế, 開場 khai trường (its own reason ends "same_wordとする"), 響應 hưởng ứng, 商賣 thương mại, 最少 tối thiểu, 證紙 chứng chỉ, 不勤 bất cần. Pattern: 9 of 12 have a `kaikki_han` / `kaikki_en_han` source, which names these characters itself; the model treated a meaning shift (裝置 = decorate, a real false friend) as a different word.

**Right for the gloss, but `vi` is also a real word for these characters (4):** 聲明 thanh minh (gloss = 清明), 公正 công chính (gloss = 工政), 財力 tài lực (gloss = 才力), 團圓 đoàn viên (gloss = 團員). `vi` stays; the gloss is withheld from task 2.

**Right (30), the draft clear list for step 6 (D57 Q1, user confirms later):** 星期 tinh kỳ, 手指 thủ chỉ, 信封 tín phong, 大型 đại hình, 期中 kỳ trung, 童年 đồng niên, 消防 tiêu phòng, 依法 y pháp, 中斷 trung đoạn, 傷口 thương khẩu, 一行 nhất hạng, 案件 yên kiện, 標示 tiêu thị, 波瀾 ba lan, 低調 đê điều, 地步 địa bộ, 更改 canh cải (native compound; no characters named), 公事 công sự, 海盜 hải đạo, 進出 tấn xuất, 境界 cảnh giới, 平價 bình giá, 傷痕 thương ngân, 手勢 thủ thế, 推移 suy di, 液體 giá thể (known data error), 真假 chân giả, 蓮步 liên bộ, 自制 tự chế, 季女 quý nữ.

Error rate: 16 / 8,555 overall; at most 2 per batch (b077: 商賣, 最少), so no batch is rejected. A rerun would cost a runner change (D61 item 10) and could repeat the error; the 16 are corrected by D63 instead.

## 5. D63 correction (before sitting 2)

`config/task1_review.csv` (Claude's review decision, 16 rows: `word_id, trad, vi, vi_check_task1, vi_check_review, gloss_vi_task2, reason`). Codex applies it as an overlay on the task-1 output when building tasks 2-4 (the content files stay as generated):

- `vi_check` becomes `same_word` for the 16 words (task 3/4 eligibility uses the corrected value);
- the 16 are always task-2 items, sent with `vi`; `gloss_vi` kept for `keep` and empty for `blank`; task 2 returns their Vietnamese meaning and `false_friend` judgment (its validator already needs one `meanings` entry per language with a reading);
- task 3: a Vietnamese word is linkable when `vi_check=same_word` and (`confidence=high` or `low_reason=ko_rare`): `ko_rare` is about the Korean reading and now excludes 176 good Vietnamese words (7-28 per level at levels 1-6, 84 at level 7);
- Codex 4e (merge) applies the same overlay and takes `meaning_ja__vi` of the 16 from task 2.

## 6. Loop notes (non-blocking)

- Some meanings carry commentary in parentheses (受傷 KO 「負傷すること（まれ、受賞と同音）」); harmless, but loop 3 (content) may want a style rule.
- `meanings_differ` is broad (1,419, 17%); task 2 size grows accordingly (about 3,940 items, 79 requests).
- The 9 multi-character `unsure` (創意 sáng ý, 白白, 親身 thân thân …) go to the step-6 list with the 30 above.
