# Stage 4 gate part 4: task 5 (usage check) — Claude, 2026-11-07

Scripts: `docs/review_scripts/stage4d_part4_reference.py` (fresh input build, validator rerun, merged table), `docs/review_scripts/stage4d_part4_effects.py` (app effect after the overlay). Decision: **D68**. User sample: **`docs/TASK5_USER_SAMPLE.md`**.

## 1. Run integrity
- Offline `--status`: task 5 **103/104 validated, 1 failed (b055), 0 missing**. Ledger **$35.42644775** (task 5 = $13.18, inside D67's $7-16; room $64.57).
- The 104 input files are byte-identical to a fresh `build_task5_batches()`; the 103 outputs pass `validate_task5` again.
- Attempts: 74 batches first try, 24 needed 2, 6 needed 3. Causes: 6 transport disconnects (no cost) and **31 failures of the reason-script rule**: Gemini wrote a Hangul or Vietnamese word that is not the item's reading inside a review note (Korean reading + particle 기사는, 우수는; other words 심문, 계파, 사냥개; Vietnamese words bằng, chức, tiếng, cầu). These failed attempts cost $2.74.
- **b055 failed 3/3 on the same item** (w08581 기사 → 「기사는」). The failed output is not saved, so a rerun is needed. Reasons are review notes and are never merged into `data/final/` → **D68 item 1**: the script rule becomes a logged warning for task 5; b055 is rerun once (about $0.08-0.11).

## 2. Counts (103 batches, 10,300 items)
| check | used / common | rare / literary | wrong_meaning | unsure | not checked |
|---|---|---|---|---|---|
| ko (8,990) | 7,275 | 1,713 (1,478 card words + 235 ff rows) | 15 | 0 | — |
| ja (1,882) | 1,441 | 439 | 2 | 0 | — |
| vi (5,077) | 3,815 | 1,261 | — | 1 | — |

Korean `rare` is concentrated in the low HSK levels (level 1: 69 of 158 checked words), which are full of Chinese everyday words such as 今天 금천, 電視 전시, 起來 기래. That is expected: low-level Chinese is where Chinese and Korean vocabulary differ most.

## 3. False positives (user item 2): every HSK level 1-3 flag
All **335** `rare`/`wrong_meaning` flags on HSK words (`origin` hsk or both) at levels 1-3 were read: Korean 239, Japanese 96.

- **Clear false positives (6, 1.8%)**, corrected in `config/task5_review.csv`: Korean 推動 추동 (추동력), 具有 구유 (formal), 反正 반정 (인조반정; a real false friend of zh "anyway"), 初中 초중 (초중고); Japanese 具有 ぐゆう (両性具有), 好奇 こうき (好奇の目).
- **Right to drop the meaning, wrong class (3)**, set to `wrong_meaning` (reading shown without （ ）): 短信 단신 (news brief), 過年 과년 (a woman past marriageable age), 星星 성성 (greying hair).
- **Borderline (8)**, sent to the user (sample part B): Korean 那邊 나변, 其實 기실, 明年 명년; Japanese 應當 おうとう (応当日), 接受 せつじゅ (接受国), 慶祝 けいしゅく, 宣布 せんぷ; plus 3 from the samples below.
- The rest are right: Chinese everyday words with no Korean/Japanese use (半天 반천, 電視 전시/でんし, 謝謝 シェシェ), readings heard as another word (雞蛋 계단 = 階段, 一半 いっぱん = 一般, 知道 지도 = 地図), and dictionary-only entries (樓上 누상, 機場 はたば).

## 4. D66 item 7 samples (seeded)
| sample | n | wrong | notes |
|---|---|---|---|
| ko `rare` where task 1 was `high`, levels 4-7 (seed 1107) | 50 | 2 FP + 1 borderline | 效益 효익 (경제적 효익), 吩咐 분부 (a living word; Gemini argued about the hanja spelling); 立國 입국 borderline |
| ko `used` where task 1 said `ko_rare` (all) | 15 | **9 FN** | 東邊, 北邊, 秀美, 觸犯, 慘痛, 急劇, 海量, 注重 → `rare`; 管子 → `wrong_meaning` (all corrected) |
| ff rows ko `rare` (seed 1108) | 50 | 1 FP + 2 borderline | 異狀 이상 (spelling argument again); 開演 개연, 第一聲 제일성 borderline |
| ko `used` (seed 1109) | 50 | 0 | |
| ja `rare`, levels 4-7 (seed 1110) | 50 | 1 FP + 3 borderline | 上市 じょうし (pharma term); 霍亂 (鬼の霍乱), 必定, 會同 borderline |
| ja `used` (seed 1111) | 40 | 0 | |
| ja `wrong_meaning` (all) | 2 | 1 | 兩棲 りょうせい is a valid spelling → `used` |
| vi `literary`/`common` multi + single (seeds 5-7) | 60 | 0 blocking | sensible (飛機 phi cơ class); data only in this run |
| all `unsure` | 1 | — | 奔 hợp: Gemini spotted the known Stage 3 data error (Kaikki reading of 合); loop 1 |

False-positive rate over the flags read (335 + 152 sampled flags): **11 clear / 487 = 2.3%**, plus 13 borderline cases for the user. Recurrent cause: Gemini sometimes calls a word `rare` because Korean writes it with a variant hanja (吩咐/分付, 異狀/異常); the overlay fixes the ones found. No batch shows a concentration (at most 2 corrections in any batch).

## 5. Held-out cases (user item 2; not in the prompt)
- **Should be rare (13):** 10 caught (誠信, 事宜, 差數, 王牌, 小羊, 幾度, 世相, 奇麗, 嫩葉, 浴衣). Missed: 折中 절중, 疑義 의의 → corrected to `rare`; 會意 회의 judged `used`, defensible (its given meaning includes the 六書 term 회의문자).
- **Should be used (8):** 用意 용의, 唯獨 유독, 文件 문건, 教書 교서, 上場 상장, 臨床 임상, 告白 고백, 言論 언론 — **8/8 `used`**.
- **User's five:** 同事 동사, 不大 부대, 順路 순로, 調度 조도 `rare`; 研究生 연구생 `wrong_meaning` — **5/5**. 同事 どうじ also `rare`.
- **Real false friends must stay used:** 工夫 공부, 愛人 애인, 汽車 기차, 小心 소심/しょうしん, 東西 동서, 大丈夫 대장부, 新聞 신문, 自己 자기 — all `used`. 勉強 면강 is `rare`, but 勉強 is static content (D67 item 5) and keeps 韓「（普通は 공부 と言う）」.
- **Every Korean trap of task 2** (58 after `task2_review.csv`): 52 `used`; 洞 is a single character (not checked); the other 5 are right to go: 接手 접수 `wrong_meaning` (= 接受), 小卒 소졸, 洞房 동방, 大變 대변, 浪花 낭화 `rare`. Each of them keeps a Chinese trap, so no entry is lost.

## 6. Effect on the app (user item 5), 103 batches, after the overlay
- **Cards (8,554 `card_eligible`):** Korean reading in （ ） on **1,479** cards; Japanese in （ ） on **436**; both 239, either 1,676. `wrong_meaning` (meaning dropped, reading plain): Korean 18, Japanese 1 (強勢 ごうせい).
- **偽の友達 (1,245 entries from task 2 + static):** **276 entries change**: 227 Korean rows and 81 Japanese rows show the fixed note instead of a meaning (D68 item 3), 8 Korean rows are dropped (`wrong_meaning`). **2 entries leave the view** (孫子, 內衣: no trap left once the Japanese baseline is gone, §6a); the old D67 baseline would have removed 131.
- **Vietnamese:** `literary` **1,261** of 5,077 checked words (788 multi-character, 473 single characters), `common` 3,815, `unsure` 1. Data only (UX_BACKLOG #5).
- b055 (100 words, w08573-w08749) is not in these numbers; expect about +15 Korean and +5 Japanese （ ）.

## 6a. Entries whose Japanese baseline is dropped (D67 item 2)
82 task-2 entries have a Japanese reading judged `rare` (all read). Their traps were judged against the Japanese meaning. Where Korean stays in use, Korean becomes the baseline: 放學 (ko 방학 is no longer a trap; zh stays), 藥方 (ko 약방 "pharmacy" is the baseline, so zh "prescription" becomes the trap), 孫子 and 內衣 (Korean, Chinese and Vietnamese all mean the same: no trap left, the entry leaves). These 8 trap flags go to **`config/task2_retrap.csv`** (4e only; D68 item 4). 應當 waits for the user's answer to B7 (if おうとう is rare, Korean 응당 and Chinese agree and the entry leaves). 師長 ko 사장 was a missed `rare` (heard as 社長) → overlay row 26. The other entries keep a valid trap against Korean or are judged against both notes (D68 item 3).

## 7. Result
**Accepted: 103 batches** (all except b055) with `config/task5_review.csv` (26 rows). Two items are open before Codex 4e: the b055 rerun and its check, and the user's answers to `docs/TASK5_USER_SAMPLE.md` (D67 item 6), which Claude adds to the overlay. If the user finds more than 2 of the 40 "not used" flags in part A wrong, Claude re-opens the class before 4e.

## 8. Part 4b (D68 follow-up), 2026-11-07 — decision **D69**
Script: `docs/review_scripts/stage4d_part4b_reference.py` (reads the accepted layout, checks with the runner's own `batch_state`, applies `task5_review.csv`, `task2_review.csv`, `task2_retrap.csv` fail-closed, prints the effect).

**b055 rerun.** User run, first attempt, $0.077528; ledger **$35.50397575** (= sum of `content/cost_log.csv`), room $64.50. Inputs of all 104 batches equal a fresh build; 104/104 validate. `reason_warnings`: 18, all in b055 (the 103 earlier logs predate the field): 17 Vietnamese everyday alternatives in `vi_reason` (*cầu nguyện*, *mùi vị*, *hợp đồng*, *vũ khí*, *di chuyển*, *chì*, *cha mẹ ruột*, *cần cù*, *chăm chỉ*, *mát mẻ*, *tâm tình*) and 1 Korean (그간 for 其間). Review-note text only; no data effect.

b055 = 100 card words (w08573-w08749, level 7): ko 25 `rare` / 62 `used`, ja 8 `rare` / 29 `used`, vi 16 `literary` / 33 `common`. All 33 flags and all `used` checks read:
| word | lang | generated | review | why |
|---|---|---|---|---|
| 欠缺 | ja けんけつ | rare | **used** | standard legal term (意思の欠缺) |
| 親生 | ko 친생 | rare | **used** | 친생자, 친생부모 (law, news) |
| 輕型 | ko 경형 | rare | **used** | official vehicle class (경형 자동차) |
| 青春期 | ko 청춘기 | rare | **used** | borderline: literary but current |
| 氣味 | ko 기미 | used | **rare** | heard as 幾微 / freckles; the meaning mixes 幾微 in |

The other 29 flags are right (欺詐 기사/ぎさ, 其後 기후, 棋子 기자, 前輩 전배, 前夕 전석, 情人 じょうじん, ...). 5 corrections / 100 items: not above 5% → **accepted**. No b055 false-friend entry has a Japanese reading judged `rare`; 氣味 and 強項 get a Korean fixed-note row, their Chinese traps stay.

**User's answers** (recorded in `docs/TASK5_USER_SAMPLE.md`): A all agreed (0 of 40 "not used" flags wrong → class not re-opened, D68 item 2); C all 26 agreed; B: B1, B2, B6, B8-B13 `used` (9 overlay rows), B3, B4, B5, B7 `rare` (= generated). `config/task5_review.csv`: **40 rows** (24 `used`, 12 `rare`, 4 `wrong_meaning`).

**§6a follow-up.** 應當: おうとう `rare` (B7), Korean 응당 "should, naturally" = Chinese → no trap left; 2 rows in `config/task2_retrap.csv` (10 rows; entries re-based: 放學, 藥方; leaving: 孫子, 內衣, 應當). Other B changes against task 2: 霍亂 (zh コレラ) and 會同 (vi 評議会) get their Japanese baseline back, traps valid; 第一聲 shows Korean 제일성 again, zh tone trap stays; 那邊 keeps なへん `rare`, so Korean 나변 ("where") is now its baseline and the Chinese trap (あちら) still holds. Note for loop 3: 那邊's task-2 Korean meaning 「あちら、どのあたり」 mixes in the Chinese sense (나변 = どこ). 開演 has no trap; the rest are not task-2 entries.

**Final counts (104 batches, after both overlays).**
| check | used / common | rare / literary | wrong_meaning | unsure |
|---|---|---|---|---|
| ko (9,090) | 7,337 | 1,734 (1,500 card words + 234 ff rows) | 19 | 0 |
| ja (1,919) | 1,481 | 437 | 1 | 0 |
| vi (5,126) | 3,848 | 1,277 (800 multi-character) | — | 1 |

App effect: Korean （ ） on **1,500** cards, Japanese **437** (both 241, either 1,696); `wrong_meaning` (meaning dropped, reading plain) Korean 18, Japanese 1. 偽の友達: **275 of 1,245** entries change (227 Korean and 76 Japanese fixed-note rows, 8 Korean rows dropped), **3 leave** (孫子, 內衣, 應當), 1,242 remain.

**Accepted layout.** Outputs, logs and inputs moved with `git mv` to `content/accepted/task5/` (+ `inputs/`); 87 non-rebuild tests pass. Launcher `-Status` after the move: tasks 1-4 86/86, 79/79, 14/14, 5/5; **task 5 `0/104 validated, 0 failed, 104 missing`**, because `run_status` still reads task 5 from `content/generated/task5/` (only tasks 1-4 were switched in 4c-prep4). The same check at the accepted paths gives 104/104. Codex 4e item 0 switches task 5; until then `-Tasks 5` must not be run (it would regenerate all 104 batches).

**Result: task 5 accepted in full (104/104).**
