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
