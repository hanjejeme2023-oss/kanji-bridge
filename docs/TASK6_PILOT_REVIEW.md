# Stage 4 task 6: pilot review (Claude, 2026-11-11)

Decision **D73**. Design: `docs/TASK6_DESIGN.md` (D72). Pilot run by the user 2026-11-12 00:46-00:53 UTC (`-Check` + `-Pilot6`). No request was sent by Claude.

## 1. Integrity and cost

| Request | Items | Result | Input / output tokens | Cost | Wall time |
|---|---:|---|---:|---:|---:|
| `-Check` | | OK | 192 / 21 | $0.000594 | 3 s |
| pilot6-zh | 50 | validated; **1 item repaired** (w05424 安宁) in repair 1 | 6,418 / 5,470 | $0.067536 | 81 s |
| pilot6-vi | 50 | validated, no repair | 4,247 / 4,257 | $0.051064 | 54 s |
| pilot6-note | 50 | validated; **1 item repaired** (c00123 課) in repair 1 | 8,970 / 3,201 | $0.049950 | 61 s |
| **Total** | 150 | 150/150 valid | | **$0.169144** | |

- All three batches validated on the first attempt; two single-item repairs were needed (the batch totals the user quoted already include them). Thinking tokens 0; unreported tokens 0.
- Validator warnings: one, `target_multiple` for 自己 (自己的事情应该自己做, natural; kept). No pinyin warning.
- Output per item: zh 107 tokens (design assumed 150), vi 85 (120), notes 63 (80). **Projected full run ≈ $14-16** (zh ≈ $8.6, vi ≈ $4.6, notes ≈ $0.65, plus about 10% repairs/retries), below D72's $18 base. Offline dry-run with the v2 prompts: base estimate **$16.84** (+$0.13 for the longer prompts). Ledger after the pilot: **$35.67311975**; room under the $200 ceiling about $164.
- **Projected run time ≈ 4.5 h** (zh 127 × ≈ 80 s ≈ 2.9 h, vi 84 × ≈ 60 s ≈ 1.4 h, notes 13 × ≈ 60 s ≈ 0.2 h); allow up to 6.5 h for retries.

## 2. Chinese (50 items: 17 named words, 2 ff, 21 level 1, 10 level 7)

**All 50 sentences are natural, use the meaning the app shows, and have correct pinyin** (segmentation as a dictionary writes words, neutral tones correct: 朋友 péngyou, 时候 shíhou, 学生 xuésheng, 粮食 liángshi, 消息 xiāoxi; 一/不 in citation tone; erhua 一点儿 yīdiǎnr; apostrophe shí'èr). Lengths fit the levels (level 1: 7-12 characters; level 7: 13-20).

All **13 trap items make the trap evident**: 老师 年轻的女老师 (not "old master"), 手纸 洗手间里没有手纸了, 大丈夫 男子汉大丈夫不怕困难, 出来 太阳从东边出来了, 打开 请打开门, 不用 不用带伞, 案件 失窃案件, 爱惜 爱惜粮食, 别人, 半天, 白天, 不大, 打球.

Problems (all minor; no wrong sentence):
| # | Item | Problem | Class |
|---|---|---|---|
| 1 | 爱人 | 「配偶者と一緒に映画を見に行きました」: 配偶者 is copied from `meaning_ja`; natural Japanese is 妻／夫 | Japanese copies the gloss |
| 2 | 打球 | 「友達と球技をしに行きます」: stiff, copied from the gloss | Japanese copies the gloss |
| 3 | 北京 | pinyin `qù běijīng`: proper noun in lower case, because `target_pinyin` is lower case and the prompt said "exactly" (the validator compares case-insensitively) | pinyin capitalisation |
| – | 出去 | 「出かけて行きたくありません」 slightly wordy | acceptable |

## 3. Vietnamese (50 items: 16 named words, 7 ff, 17 literary fill, 10 `vi_freq`)

38 `ok`, 12 `no_sentence`. Sentences are natural with correct tone and vowel marks; every literary word sits in a formal, historical or written context (phi cơ in an aviation report, khảo thí 'the feudal examination system', thương điếm 'the old quarter once had many trading houses', bằng hữu, đồng học, hồi đáp 'a reply letter from the partner'), so the v1 literary rule works. Trap items 勉強 miễn cưỡng, 自己 tự kỷ (autism), 大丈夫 đại trượng phu, 數學 số học vs toán, 火車 hỏa xa are evident.

**Correct `no_sentence` (9):** biệt, cật, tòng, địa (single-character readings), địa đồ (bản đồ), điện não (máy tính), kiền tịnh, khai hội in the meeting sense (khai mạc / họp), danh tự (tên). The review notes give the everyday word, which helps the gate.

Errors:
| # | Item | Problem | Class |
|---|---|---|---|
| 1 | 殺人 sát nhân (common) | `no_sentence` with the reason "the task forbids violence": the v1 topic rule was applied to the target word itself. sát nhân is a common word (kẻ sát nhân, vụ án sát nhân) | **prompt-caused, systematic**: ≈ 180 vi and ≈ 130 zh items have crime/war/military/death/religion meanings (武器, 戰爭, 軍人, 犯罪, 自殺, 宗教, 死刑 …) |
| 2 | 半年 bán niên (literary) | `no_sentence` "always nửa năm": wrong; bán niên is current in finance (báo cáo tài chính bán niên) | false `no_sentence` for a formal-field word |
| 3 | 故人 cố nhân (trap; contrast 亡くなった人) | "ông lại bồi hồi nhớ về cố nhân": remembering fits the deceased reading too, so the trap is not evident; translation 「胸を揺らして」 is not Japanese | trap check + Japanese |
| – | 馬上 mã thượng | `no_sentence`; modern mã thượng means "chivalrous, magnanimous" (sports writing), which `meaning_ja` 「馬上、堂々とした様子」 only partly covers | borderline, not counted |
| – | 工夫 công phu | 'the dish was prepared very công phu': only the translation (手間をかけて) excludes the Japanese 工夫 reading | acceptable |
| – | lão sư, thư điếm, đại chiến, xướng ca | rare or slightly vague but defensible in the formal contexts chosen | acceptable |

**3 clear errors of 50 = 6% (> 5%)**, two of them from classes a prompt rule can fix (§8.5 of the design → v2).

## 4. Notes (50 items)

**50/50 non-empty; no factual error.** Each names the everyday word correctly: giúp đỡ, yêu, tám, trắng, trăm, nửa/rưỡi, cốc/ly, so sánh/hơn, khác/đừng, không, xe, ăn, mặc, giường, từ, sai/nhầm, đánh, đến/tới, đất, đợi/chờ, em trai, thứ, tiệm/cửa hàng, đều, đọc, đói, hai, gió, khô/sạch, bảo, anh, cái, với/cùng/theo, đóng/tắt, còn/vẫn, tốt/hay, uống, xấu/hỏng, lửa, thấy/gặp, gọi, cảm thấy/ngủ, chị, sạch, chín, xem/nhìn, bài học. The zh-side notes (餓 饿, 喝, 九, 就) are correct.
- One rule slip: 還 writes 「返す（huán）」, a reading not given in the input (correct, but against the rule). Fix at the gate with `set_note_ja` if it recurs.
- One awkward wording: 吧 「中国語の文末助詞（…）に当たり」.
- **Notes stay on prompt v1** (no class to fix).

Data finding (not task 6): the 字体 readings 錯 **thó** (`unihan_unverified`; usual Hán-Việt thác/thố) and 吧 **và** (`kaikki_aligned`; usual ba) look like Nôm readings → HANDOFF open problems (loop 1, accuracy).

## 5. Decision: prompt v2 for zh and vi; notes stay v1; no second pilot

`content/prompts/task6_zh_v2.md`, `task6_vi_v2.md` = v1 plus these rules (nothing removed; schema, fields and validator unchanged):

| Change | zh | vi | Fixes |
|---|:-:|:-:|---|
| The "no politics, religion or violence" rule is about the **topic the model chooses**; a target word about crime, war, the military, weapons, death, illness, politics or religion gets a calm factual sentence (news, history, textbook); never `no_sentence` for the word's subject | ✓ | ✓ | sát nhân; ≈ 310 items at risk |
| Trap self-check: read the sentence with `contrast_meaning_ja`; if it still makes sense, add ruling-out context (example: 老师 / cố nhân "met again after twenty years") | ✓ | ✓ | cố nhân |
| Japanese translation: `meaning_ja` is a gloss, do not copy its wording when Japanese says it differently (爱人 → 妻／夫, not 配偶者; bồi hồi → しみじみと, not 胸を揺らす) | ✓ | ✓ | 爱人, 打球, cố nhân |
| Capitalise proper nouns in the pinyin (Běijīng), also as target; the check ignores case | ✓ | | 北京 |
| Before `no_sentence`, consider today's formal fields (finance, law, administration, press, sport, medicine, education); a word current there counts as used (bán niên in báo cáo tài chính bán niên); `no_sentence` stays right for dictionary-only readings and calques (điện não); never invent a use | | ✓ | bán niên |

**Why no second pilot:** the changes clarify existing rules and add examples; output format, schema and validator are unchanged, so the run cannot break mechanically. The one change with a downside (fewer `no_sentence`, risk of forcing archaic words, as in task 3, D64) is bounded by "only dictionary/old texts/calques stay no_sentence" and "never invent a use", and the gate reads every `no_sentence`, every level 1-3 vi card item and every ff item; any forced item is dropped or rerun. A second pilot would need another Claude review and push the start past tonight with little to gain before the gate.

**Gate watch list (part A/B):** (1) forced archaic Vietnamese after the no_sentence change (compare the `no_sentence` rate with the pilot's 12/50 on a literary-heavy sample; expect fewer); (2) sensitive-meaning items: calm and factual, not avoided; (3) trap items whose sentence also fits the contrast meaning; (4) translations that copy the gloss; (5) notes that add a second reading.

**Wiring:** the runner selects task-6 prompts from the constant `TASK6_PROMPT_FILES` in `pipeline/stage4/runner.py`; Claude changed only its zh and vi paths to v2 (D73 item 3). The pilot logs keep the v1 prompt SHA (pilot output is never merged).
