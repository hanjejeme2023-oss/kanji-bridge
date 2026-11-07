# Stage 4 gate part 2: tasks 2, 3, 4 review (Claude, 2026-11-07)

Input: `content/inputs/task{2,3,4}/`, `content/generated/task{2,3,4}/`, run by the user on 2026-11-07 (sitting 2, D62); `content/cost_log.csv`. Reference script: `docs/review_scripts/stage4d_part2_reference.py` (read-only; sections `integrity task4drop tokens d63 sample2 low fixed sample3 sample4 user clears`; seeds 20261107, 1107, 1108).

**Result (D64):** task 2 **all 79 batches accepted** with a review overlay; task 3 **Chinese b001-b007 accepted, Vietnamese b008-b014 rejected** (prompt v3, rerun); task 4 **all 5 batches accepted** with a review overlay. Vietnamese clear list for step 6: `docs/VI_CLEAR_SHORTLIST.md` (39 words + 28 false-friend forms).

## 1. Done-when and run integrity

| Check | Evidence | Result |
|---|---|---|
| Validator rerun by Claude | `validators.validate` on every output file of tasks 2-4: 0 failures; 79 + 14 + 5 logs `validation.ok` | OK |
| Inputs = fresh build | every `content/inputs/task{2,3,4}/bNNN.jsonl` byte-identical to `builders.task_batches(t, task-1 output)` (D63 overlay applied) | OK |
| Settings | one prompt SHA per task (task2_v2 `c750a410`, task3_v2 `c77d9809`, task4_v1 `2fafe282`); `gemini-4-argon`, `global`, 0.3; thinking 0, unreported 0 | OK |
| Attempts | every batch validated on its first attempt (79 + 14 + 5); no transport failure | OK |
| Task 2 coverage | 3,937 items = 1,419 `meanings_differ` + 自己 + the 16 D63 words (1,433 words) + all 2,504 `ff_candidates.csv` rows; 1,272 with a false friend (zh 961, vi 513, ko 64); 9 `low` | OK |
| Task 3 coverage | 14 cells × 6 passages = 84 (target ≥ 5 per cell); every passage links ≥ 4 words and at least one at the cell's level; all tokens resolve (validator) | OK (content: §4) |
| Task 4 coverage | 212 notes, longest 69 characters (limit 80) | OK |
| No reading in content | outputs have no reading field; task-3 tokens and task-4 Hangul/Latin tokens are checked against the input by the validator | OK |
| Frozen data | `git diff HEAD -- data config pipeline/overrides.csv` empty before this review; `id_map.csv` line endings only | OK |
| Cost | ledger **$21.87953175** (sitting 2: $7.51; task 2 $6.74, task 3 $0.84, task 4 $0.23 incl. their pilot rows); room under the ceiling $78.12 | OK |

## 2. User questions

**Q1. Task 4: 234 → 212.** All 22 dropped items have **only Vietnamese differences** and no `same_word` check, so D59 item 5 drops them; no item lost a Korean difference and none was added. But the cause is not only `vi_check`: **13** are task-1 words whose `vi_check` is not `same_word` (6 `different_word`: 中斷, 一行, 案件, 更改, 進出, 液體; 7 single-character `unsure`: 重, 應, 將, 拖, 奔, 損, 拄), and **9 are not `card_eligible`** (學分, 長度, 厲害, 田徑, 穿過, 激活, 看台, 可惡, 造福): they have no task-1 result, so no `vi_check` at all, and the builder treats "no check" as "not `same_word`". Nothing is lost: `note_ja` is shown only in the 読解 word detail, and 読解 links only task-3-linkable words, which all have a task-1 result. **D63 words:** only 2 of the 16 have a reading difference (複製 phục/phức, 最少 thiểu/thiếu); both are kept, and both would have been dropped without D63 (raw task 1 gives 210 items). The other 14 never were task-4 items.

**Q2. Task 2 output tokens: formatting only.** The stored content per batch is the same size in every group (mean 13,005 vs 12,959 characters; 1,427 vs 1,606 characters of meaning text), but output tokens per stored character fall into **three** fixed levels: 0.33-0.37 (18 batches, compact JSON), 0.53-0.56 (31) and 0.63-0.68 (30) (indented layouts). The "5,000 vs 9,000" pairs are b001-b029 (word items, about 8,500 input tokens: they carry the task-1 meanings) at the compact vs the widest level; b030-b079 (`ff_candidates` rows, about 4,800 input) show the same three levels at 3,800-8,800. As in task 1, the same content at fixed token rates can only be response layout. The padding cost about 204,000 output tokens, **about $2.05** at the November Argon rate ($10 per 1M). No action.

**Q3. D63 words in task 2:** all 16 got a Vietnamese meaning and a judgment, `gloss_vi` withheld exactly for the 4 `blank` rows. Vietnamese is the trap for 7: 聲明 (釈明する), 符號 (バッジ), 複製 (修復する), 裝置 (装飾する), 開場 (始業式; zh trap as well), 證紙 (証明書), 不勤 (無頓着な). Not a trap for 9 with fitting meanings (公正, 財力, 團圓, 響應, 商賣, 最少, 和諧, 色彩 ニュアンス, 精細 繊細); 色彩 and 精細 are borderline but defensible. 0 errors.

**Q4.** Ten false friends and three passages: see the end of this file.

**Q5.** `docs/VI_CLEAR_SHORTLIST.md`.

## 3. Task 2 (false friends): ACCEPT all 79, with `config/task2_review.csv`

| Set | Size | Errors | Notes |
|---|---|---|---|
| Fixed items | 自己, 手紙, 大丈夫, 勉強, 新聞, 工夫, 博士, 裝置 | 1 | 自己 VI 自閉症の, vi trap (as expected); 大丈夫 ko/zh/vi traps, `ja` never a trap; 勉強 zh/vi; 工夫 ko/zh/vi; 新聞 zh; 博士 vi. **手紙:** zh trap right, but the vi trap (村の顔役) comes from a different word (B11) |
| Random | 50 (seed 20261107) | 0 (1 debatable) | 私服 zh "private server" only: CC-CEDICT's gloss; modern Chinese also uses 私服 for "one's own clothes" (loop 3) |
| `low` | all 9 | 7 | the model's own doubts were right: 不詳, 中堅, 主因, 再建, 奇數 (Vietnamese gloss of a homophone), 歸化 (place name) → group B; 濃淡 (Korean 농담 = 弄談 "joke") → overlay. 天理, 體勢 OK |
| Word items, vi traps | 25 of 445 | 0 | these `vi` values passed task 1's `vi_check` |
| **ff rows, vi traps** | **all 68** | **25** | §3.1 |
| ff rows, vi not a trap | 238, scanned for place-name or "同音" glosses | 3 | 文教, 新作, 新規: Vietnamese meaning = "a commune name" |
| **Korean traps** | **all 64** | **6** | §3.2 |

### 3.1 Vietnamese values of `ff_candidates.csv` rows (new error class)

The 306 `ff_candidates` rows with a `vi` never went through task 1, so the rule-B false matches that D57 Q1 sends to `vi_check` were never checked for them. Task 2 judged the gloss it was given and marked a different word as a Vietnamese false friend: 敬老 "reading glasses" (kính lão = 鏡老), 食材 "real talent" (實才), 巡禮 "a week" (旬禮), 網羅 / 東經 / 雨季 "a commune". **25 of the 68 Vietnamese traps** in these rows are such errors (5 of them `low`), plus 3 non-trap rows whose Vietnamese meaning is a place name. The other 43 traps are real (亡命 vong mạng, 勤務 cần vụ, 教頭 giáo đầu, 楊柳 dương liễu = casuarina, 合意 hợp ý …). These 28 forms are **group B** of the step-6 list; a confirmed clear becomes a `clear_vi` row in `config/task2_review.csv` that 4e applies.

### 3.2 Korean homophones (6)

With no Korean gloss, the model sometimes took the meaning of a more common Korean word with the same sound: 質素 → 窒素 "nitrogen", 定規 → 正規, 商談 → 相談, 濃淡 → 弄談 "joke", 等身 → 等神 "fool", 修業 → 授業. In each the Korean word written with these characters means what the Japanese word means. `config/task2_review.csv` (Claude's review decision, 6 rows, action `same_as_ja`): the Korean meaning becomes the Japanese meaning, Korean is removed from `false_friend`; the generated value is recorded so the overlay fails closed if the output changes.

### 3.3 Per-batch rate and why no batch is rejected

31 errors in 3,937 items (0.8%). Two batches have 3 of 50 (6%): b031 (不詳, 中堅, 主因, all marked `low` by the model) and b047 (巡禮, 市立, 歸化). Strictly that is above the 5% line. They are accepted because every error in them belongs to the class in §3.1, whose cause is the **input** (a `vi` value that is a different word) and which Claude has reviewed completely: a rerun gets the same input and can only repeat the judgment, while removing the wrong Vietnamese entry gives exactly the result a rerun with corrected input would give, at no cost (D63 precedent). The next largest is 2 of 50 (b041, b073, b077, b078, b079).

## 4. Task 3 (passages): ACCEPT zh b001-b007, REJECT vi b008-b014

All 84 passages read. **Chinese (42): natural, level-appropriate, complete translations;** minor stiffness only (b006 #4 资料与账, #3 于城市的仓库开设). Accept.

**Vietnamese (42): about 1 in 5 passages forces a literary or archaic Sino-Vietnamese word where Vietnamese uses another word, and one has a wrong word**, although prompt v2 already said not to: b008 L1 `bộ điện ảnh` for one film (bộ phim), `Bên ngoại đang có nhiều gió` (*ngoại* = the mother's side; "outside" is *bên ngoài*), `phi cơ`, `địa đồ`, `viết hán tự`; b010 L3 `lão sư` (giáo viên), `chủng tử` (hạt giống), `túc cầu`; b011 L4 `nghiêm cách`, `thục luyện văn pháp`, `miêu tả tiên minh`; b014 L7 `xuất sinh`, `quan tài phán` (*quan tài* alone = coffin; judge = thẩm phán), `hậu quả hạn`. A learner would copy these. Every Vietnamese cell has at least one such passage, so with 6 passages per batch every vi batch is above 5%. Cause: the linkable lists contain many correct but literary Sino-Vietnamese readings (老師 lão sư), and the rules "link at least one word at the level" and "link every supplied Sino word" push the model towards them.

**Fix:** `content/prompts/task3_v3.md` (Vietnamese cells only): a supplied word is only a candidate; use it only where an educated speaker would; otherwise write the everyday word as a gloss token; named examples of what not to write; "three natural links are better than more forced ones"; check tone and vowel marks (ngoài / ngoại). The level-word rule becomes "when one fits naturally". Rerun: 7 requests, about $0.45. Chinese cells keep v2 and stay accepted (runner change, HANDOFF).

## 5. Task 4 (other-reading notes): ACCEPT all 5, with `config/task4_review.csv`

50 random notes (seed 20261107) read against their input: every note states the supplied primary, example and reading correctly; 0 model errors. Data-side remarks that come from the frozen primaries, not from the notes (loop 1): 當 "usually đáng" (D52 tie 6:6), 激 "usually khích (例：激動)" (激動 is usually kích động), 難 "usually nạn".

**Builder defect (5 notes):** `examples_primary` / `examples_here` give a Korean example with `word_chars.ko_base`, which for 두음 and 율/열 positions is not the written syllable (D62 item 6 fixed only `reading_here`). 7 of the examples are affected and 5 notes quote one: 「效率」 as an example of 률 (written 효율) in 率先, 表率, 坦率, 輕率, and 「戀愛」 as an example of 련 (written 연애) in 失戀. `config/task4_review.csv` (5 rows) replaces 「效率」 with 「能率」 (능률, another supplied example) and removes the 戀愛 example; each corrected note passes `validate_task4`. Per batch: b002 2/50, b003 2/50, b005 1/12 (8%, accepted for the same reason as §3.3: input-caused, fully enumerated by script, corrected by the overlay). Builder fix → loop 1 (it would change task-4 inputs now).

## 6. Material for the user (Q4)

**Ten random false friends** (seed 1107, from the 1,272 items with a non-empty `false_friend`; `*` = trap): all 10 correct in my review.

| Word | Readings | Meanings (Japanese baseline first) |
|---|---|---|
| 錄取 | ja ろくしゅ · zh lùqǔ | ja 録取、記録し選び取ること · **zh\*** （試験の合格者を）採用する、入学を許可する |
| 體格 | ja たいかく · ko 체격 · zh tǐgé · vi thể cách | ja からだつき、体格 · ko 同 · zh 体格、健康状態 · **vi\*** （手続きなどの）様式、形式、やり方 |
| 乃至 | ja ないし · ko 내지 · zh nǎizhì | ja 〜から〜まで、あるいは · ko 同 · **zh\*** ひいては、〜にまで至る |
| 小結 | ja こむすび · zh xiǎojié | ja 大相撲の三役の一つ · **zh\*** 小規模なまとめ、要約 |
| 研究生 | ja けんきゅうせい · ko 연구생 · zh yánjiūshēng · vi nghiên cứu sinh | ja 研究生（非正規の研究課程生） · ko 研究生、大学院生 · **zh\*** 大学院生 · **vi\*** 博士課程の大学院生 |
| 秀才 | ja しゅうさい · ko 수재 · zh xiùcai · vi tú tài | ja 学問や才能が優れた人 · ko 同 · zh 科挙の合格者、知識人 · **vi\*** 科挙の郷試合格者、現在は高校卒業資格（バカロレア） |
| 同事 | ja どうじ · ko 동사 · zh tóngshì · vi đồng sự | ja 同じ事柄 · ko 同僚、同じ事柄 · **zh\*** 同僚 · **vi\*** 同僚、共に働くこと |
| 不大 | ko 부대 · zh bùdà | ko 大きくないこと · **zh\*** あまり〜ない |
| 順路 | ja じゅんろ · ko 순로 · zh shùnlù | ja 決まった道順 · ko 同 · **zh\*** 通り道である、ついでに |
| 調度 | ja ちょうど · ko 조도 · zh diàodù · vi điều độ | ja 身の回りの道具や家具 · ko 物品の調達 · **zh\*** （車両や人員を）手配する、配車する · **vi\*** （業務を）調整する、配分する |

**Three passages** (seed 1108):

1. **zh L3 (b003, accepted):** 这家书店的杂志和文学作品很受读者欢迎，价钱也不高。作者在文章里谈了不少自身的经验，留下了深刻的印象。 — この本屋の雑誌や文学作品は読者にとても人気があり、値段も高くありません。作者は記事の中で多くの自身の経験について語り、深い印象を残しました。 Linked: 书店, 杂志, 和, 文学, 作品, 读者, 欢迎, 价钱, 高, 作者, 在, 文章, 里, 谈, 不少, 自身, 经验, 深刻, 印象.
2. **vi L7 (b014, rejected):** Cơ quan chấp pháp đã công tố kẻ phạm tội xâm hại tài sản tư hữu sau khi nhân chứng ra làm chứng công khai. Phán quyết nghiêm của quan tài phán đã trừ khử thủ đoạn xấu, giữ quy củ yên ổn cho khu phố. — 法を執行する機関は、証人が公の場で証言したのち、個人の財産を侵害した犯罪者を公訴した。裁判官の厳格な判決は犯罪の悪辣な手段を取り除き、地域の平穏な秩序を守った。 *My note:* grammatical, but legal jargon throughout; `quan tài phán` is not how one says "judge" (thẩm phán), and *quan tài* alone means "coffin".
3. **vi L6 (b013, rejected batch; this passage is fine):** Hành trình vượt qua vùng sơn cốc gặp nhiều chướng ngại nhưng không ai bỏ cuộc. Mọi người đã đồng tâm vượt khó và cuối cùng cũng đến được hòn đảo san hô mỹ lệ. — 山と谷を越える旅の道のりは多くの障害にぶつかったが、誰一人として諦めなかった。みんなは心を一つにして困難を乗り越え、ついに美しい珊瑚の島に着いた。 *My note:* natural; `sơn cốc` and `mỹ lệ` are literary but used.

## 7. Loop notes (non-blocking)

- 私服 zh (CC-CEDICT gives only the gaming sense); `meanings_differ` breadth (task 2 has many "same" judgments, harmless).
- Task-4 builder: Korean examples must use the written syllable (§5); task-4 notes are invisible for words not linked in 読解 (by design, D59).
- Data primaries questioned by the notes (§5); 水平 thủy bằng.
- `ff_candidates` rows with a `vi` that is not a trap may still carry a homophone value (only place-name/"同音" glosses were scanned); a fuller check belongs to loop 3.
