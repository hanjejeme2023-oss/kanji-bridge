# Stage 3 gate, attempt 2: review short list (D50 item 4)

Claude proposes these picks. **Nothing is written to `pipeline/overrides.csv` until the user confirms.** Every value is already a dictionary candidate for that word (from `ko_multi_candidates.csv`, `ja_multi_candidates.csv` or `vi_ambiguous.csv`), or is in that character's `*_all` list. The build rejects any other value (D43 item 7). Built from the commit `e18e7e0` outputs.

**How to answer:** "all as proposed", or list the row numbers to drop or change (e.g. "drop K12, J7; group C no").

## Short list scope and counts
| List | Rows in file | On short list | Proposed change | Keep as built |
|---|---|---|---|---|
| `ko_multi_candidates.csv` | 136 | 76 (46 multi-character + 30 single at L1-3) | 23 | 53 |
| `ja_multi_candidates.csv` | 149 | 115 (39 multi-character + 76 single at L1-3) | 14 | 101 |
| `vi_ambiguous.csv` | 47 | 47 (11 several-candidate, 24 HSK/VI-only rule-B conflicts, 12 `ff_candidates` rule-B conflicts) | 19 | 28 stay empty or unchanged |
| `chars` (D39 primaries) | — | 茶, 寧, plus 13 `ko_law_form_suspect` rows (group C) | 2 + 13 | — |

Rows not on the short list (single characters at levels 4-7) go to loop 1, as GATES check 9 says.

## A. Words, Korean (`table=words`, column `ko`)
| # | Word (key) | Built | Proposed | Why |
|---|---|---|---|---|
| K1 | 茶 `茶\|chá` | 다 | **차** | User decision D39/D50: 茶 = 차 |
| K2 | 紅茶 `紅茶\|hóngchá` | 홍다 | **홍차** | the Korean word is 홍차 |
| K3 | 綠茶 `綠茶\|lǜchá` | 녹다 | **녹차** | the Korean word is 녹차 |
| K4 | 喝 `喝\|hē` | (empty) | **갈** | 喝 = 꾸짖을 갈; 애 is a rare reading |
| K5 | 句 `句\|jù` | (empty) | **구** | 句 = 글귀 구 |
| K6 | 台 `台\|tái` | (empty) | **대** | tái "platform" = 대 (臺) |
| K7 | 更 `更\|gèng` | 경 | **갱** | gèng "more, again" = 다시 갱; 경 is gēng "change" |
| K8 | 更新 `更新\|gēngxīn` | 경신 | **갱신** | "renew, update" = 갱신; 경신 is mainly a record being broken |
| K9 | 一切 `一切\|yīqiè` | 일절 | **일체** | "all, everything" = 일체; 일절 means "not at all" |
| K10 | 寶貝 `寶貝\|bǎobèi` | 보패 | **보배** | 보배 is the Korean word |
| K11 | 議論 `議論\|yìlùn` | 의론 | **의논** | "discuss" = 의논 |
| K12 | 編輯 `編輯\|biānjí` | 편즙 | **편집** | the Korean word is 편집 |
| K13 | 編輯 `編輯\|biānji` | 편즙 | **편집** | same |
| K14 | 藏匿 `藏匿\|cángnì` | 장익 | **장닉** | 匿 = 닉 after the first syllable (은닉) |
| K15 | 粗暴 `粗暴\|cūbào` | 조폭 | **조포** | dictionary word 조포; 조폭 is slang for gangsters |
| K16 | 復活 `復活\|fùhuó` | 복활 | **부활** | the Korean word is 부활 |
| K17 | 復興 `復興\|fùxīng` | 복흥 | **부흥** | the Korean word is 부흥 |
| K18 | 滑稽 `滑稽\|huájī` | 활계 | **골계** | 滑稽 is read 골계 |
| K19 | 省略 `省略\|shěnglüè` | 성략 | **생략** | the Korean word is 생략 |
| K20 | 喜怒哀樂 `喜怒哀樂\|xǐnùāilè` | 희노애락 | **희로애락** | standard spelling 희로애락 |
| K21 | 車駕 `x\|車駕` | 차가 | **거가** | dictionary word 거가 |
| K22 | 行伍 `x\|行伍` | 행오 | **항오** | 行 "rank, file" = 항 |
| K23 | 寂寥 `x\|寂寥` | 적료 | **적요** | standard reading 적요 |

Kept as built (53), including: 北 북, 不 불, 車 차, 讀 독, 乾 건, 乾淨 건정, 火車 화차, 見 견, 十 십, 說 설, 洗 세, 下車 하차, 行 xíng 행, 行 háng 행 (as in 銀行 은행), 著 착, 場 장, 車輛 차량, 度 도, 畫 화, 省 성, 數 수, 數字 숫자, 停車 정차, 調 조 (both), 金 금, 困難 곤란, 樂 락, 屬 속, 糖 당, 跳 도, 員 원, 節省 절성, 說服 설복, 電車 전차, 同行 동행, 一行 일행, 拜見 배견, 茶道 다도 (the Korean word), 車間 찻간, 車輪 차륜, 車軸 차축, 行列 행렬, 懶惰 나타, 失戀 실연, 跳躍 도약, 暴行 폭행, 動力學 동력학, 行文 행문, 惡鬼 악귀, 原狀 원상, 句法 구법, 頻數 빈수.

## B. Words, Japanese (`table=words`, column `ja`)
Single characters follow D50 item 2 (on'yomi first). I change only two whose on'yomi is the wrong one for the meaning.
| # | Word (key) | Built | Proposed | Why |
|---|---|---|---|---|
| J1 | 畫 `畫\|huà` | え | **が** | 画 alone is が/かく; え is a rare go-on reading |
| J2 | 直 `直\|zhí` | じき | **ちょく** | じき means "soon"; zhí "straight, direct" = ちょく |
| J3 | 出來 `出來\|chūlái` | しゅったい | **でき** | a native reader reads 出来 as でき |
| J4 | 身體 `身體\|shēntǐ` | からだ | **しんたい** | standard reading of 身体; shows the cognate |
| J5 | 心中 `心中\|xīnzhōng` | しんじゅう | **しんちゅう** | "in one's heart" = しんちゅう; しんじゅう (double suicide) stays in `ja_alt` for Stage 4 |
| J6 | 故鄉 `故鄉\|gùxiāng` | ふるさと | **こきょう** | on reading, equally common |
| J7 | 市場 `市場\|shìchǎng` | いちば | **しじょう** | economics "market", the main HSK sense |
| J8 | 今日 `今日\|jīnrì` | こんにち | **きょう** | "today" is きょう |
| J9 | 明日 `明日\|míngrì` | みょうにち | **あした** | "tomorrow" is あした in normal use |
| J10 | 一行 `一行\|yīxíng` | いちぎょう | **いっこう** | "party, delegation" = いっこう; いちぎょう is "one line" |
| J11 | 內幕 `內幕\|nèimù` | うちまく | **ないまく** | "inside story" = ないまく |
| J12 | 氣質 `氣質\|qìzhì` | かたぎ | **きしつ** | "temperament" = きしつ |
| J13 | 相對 `相對\|xiāngduì` | あいたい | **そうたい** | "relative(ly)" = そうたい (noted at attempt 1) |
| J14 | 一一 `一一\|yīyī` | じゅういち | **いちいち** | じゅういち is "eleven" |

Kept as built (101), including the D50 single-character on'yomi values (國 こく, 年 ねん, 人 じん, 月 がつ, 家 け, 下 げ, 背 はい, 雞 けい ...), 半年 はんとし, 重複 ちょうふく, 出生 しゅっしょう, 大家 たいか, 取得 しゅとく, 主人 しゅじん, 分別 ぶんべつ, 目標, 目前, 左右, 的確, 黃金, 博士 はかせ, 上下, 詩歌, 唯一, 情緒, 一時, 分泌, 空地 あきち, 牧場, 氣味, 人事, 下手 へた (false-friend trap, left for Stage 4), 忠實, 假名 かめい, 草木.

## C. Characters (`table=chars`, column `ko`)
| # | Char | Built | Proposed | Why |
|---|---|---|---|---|
| C1 | 茶 | 다 | **차** | User decision (D39, D50). With K1-K3 the counts also give 차 |
| C2 | 寧 | 령 | **녕** | D39's literal mapping sends 영 to 령 because 령 is in `ko_all`; 寧 is 편안할 녕 (안녕) |

**Group C3 (optional, one yes/no):** 13 characters with no evidence word keep Unihan's first value, which is the 두음 form (`ko_law_form_suspect=true`). Propose the dictionary base form for each: 拉 랍, 懶 라, 爐 로, 廊 랑, 勒 륵, 寥 료, 聾 롱, 虜 로, 魯 로, 碌 록, 縷 루, 卵 란, 裸 라. All are levels 2-7 and every value is in its `ko_all`. This matches D50 item 3 (base form) for characters the word evidence cannot reach.

## D. Vietnamese (`table=words`, column `vi`)
**Several candidates (11):** pick the Hán-Việt reading that goes with the word's pinyin.
| # | Word | Proposed | Why |
|---|---|---|---|
| V1 | 份 `份\|fèn` | **phần** | "portion" |
| V2 | 更 `更\|gèng` | **cánh** | gèng; canh is gēng |
| V3 | 過 `過\|guo` | **quá** | Hán-Việt reading of 過 |
| V4 | 占 `占\|zhàn` | **chiếm** | zhàn "occupy"; chiêm is zhān |
| V5 | 福 `福\|fú` | **phúc** | standard; phước is the southern form |
| V6 | 行 `行\|háng` | **hàng** | háng (test table accepts hàng) |
| V7 | 濕 `濕\|shī` | **thấp** | "wet" |
| V8 | 應 `應\|yīng` | **ưng** | yīng "should"; ứng is yìng |
| V9 | 將 `將\|jiāng` | **tương** | jiāng; tướng is jiàng |
| V10 | 與 `與\|yǔ` | **dữ** | yǔ; dự is yù |
| V11 | 瓷 `瓷\|cí` | **từ** | Hán-Việt reading; sứ is the native word |

**Rule-B conflicts on words (24):** restore 8 values where Kaikki's other Han form is only a variant spelling of the same word.
| # | Word | Proposed | Kaikki writes it | Why |
|---|---|---|---|---|
| V12 | 想象 `想象\|xiǎngxiàng` | **tưởng tượng** | 想像 | same word, variant 象/像 |
| V13 | 贊助 `贊助\|zànzhù` | **tán trợ** | 讚助 | variant 贊/讚 |
| V14 | 模糊 `模糊\|móhu` | **mô hồ** | 模胡 | variant |
| V15 | 以往 `以往\|yǐwǎng` | **dĩ vãng** | 已往 | same word |
| V16 | 振動 `振動\|zhèndòng` | **chấn động** | 震動 | same word, variant 振/震 |
| V17 | 激勵 `激勵\|jīlì` | **khích lệ** | 激厲 | variant |
| V18 | 兇惡 `兇惡\|xiōng'è` | **hung ác** | 凶悪 | shinjitai spelling of the same word |
| V19 | 言辭 `言辭\|yáncí` | **ngôn từ** | 言詞 | variant 辭/詞 |

Stay empty (true homophones, D51): 不行 bất hạnh (不幸), 食物 / 實物 thực vật (植物), 只是 chỉ thị (指示), 創建 sáng kiến (創見), 父女 phụ nữ (婦女), 定為 định vị (定位), 敢情 cảm tình (感情), 公用 công dụng (功用), 警官 cảnh quan (景觀), 路面 lộ diện (露面), 視角 thị giác (視覺), 合約 hiệp ước (協約). Unchanged because the word already has a correct value and only an extra candidate was dropped: 長城 trường thành, 容易 dung dị, 激動 khích động.

**Rule-B conflicts on `ff_candidates.csv` (12):** 3 are correct (難民 nạn dân, 淡泊 đạm bạc, 政治犯 chính trị phạm); 9 are homophones (學園 học viên, 機體 cơ thể, 原人 nguyên nhân, 正體 chính thể, 先行 tiến hành, 直角 trực giác, 風土 phong độ, 首位 thú vị, 浮游 phù du). **Proposed: leave all 12 empty.** The override code supports only `table=words` and `table=chars`, these rows are not cards, and Stage 4 judges them without a Vietnamese value. (Alternative: Codex adds `table=ff_candidates` overrides for the 3.)

## Proposed `pipeline/overrides.csv` rows (written only after confirmation)
```
table,key,column,value,reason
words,茶|chá,ko,차,D50 user decision; Stage 3 short list K1
words,紅茶|hóngchá,ko,홍차,Stage 3 short list K2
words,綠茶|lǜchá,ko,녹차,Stage 3 short list K3
words,喝|hē,ko,갈,Stage 3 short list K4
words,句|jù,ko,구,Stage 3 short list K5
words,台|tái,ko,대,Stage 3 short list K6
words,更|gèng,ko,갱,Stage 3 short list K7
words,更新|gēngxīn,ko,갱신,Stage 3 short list K8
words,一切|yīqiè,ko,일체,Stage 3 short list K9
words,寶貝|bǎobèi,ko,보배,Stage 3 short list K10
words,議論|yìlùn,ko,의논,Stage 3 short list K11
words,編輯|biānjí,ko,편집,Stage 3 short list K12
words,編輯|biānji,ko,편집,Stage 3 short list K13
words,藏匿|cángnì,ko,장닉,Stage 3 short list K14
words,粗暴|cūbào,ko,조포,Stage 3 short list K15
words,復活|fùhuó,ko,부활,Stage 3 short list K16
words,復興|fùxīng,ko,부흥,Stage 3 short list K17
words,滑稽|huájī,ko,골계,Stage 3 short list K18
words,省略|shěnglüè,ko,생략,Stage 3 short list K19
words,喜怒哀樂|xǐnùāilè,ko,희로애락,Stage 3 short list K20
words,x|車駕,ko,거가,Stage 3 short list K21
words,x|行伍,ko,항오,Stage 3 short list K22
words,x|寂寥,ko,적요,Stage 3 short list K23
words,畫|huà,ja,が,Stage 3 short list J1
words,直|zhí,ja,ちょく,Stage 3 short list J2
words,出來|chūlái,ja,でき,Stage 3 short list J3
words,身體|shēntǐ,ja,しんたい,Stage 3 short list J4
words,心中|xīnzhōng,ja,しんちゅう,Stage 3 short list J5
words,故鄉|gùxiāng,ja,こきょう,Stage 3 short list J6
words,市場|shìchǎng,ja,しじょう,Stage 3 short list J7
words,今日|jīnrì,ja,きょう,Stage 3 short list J8
words,明日|míngrì,ja,あした,Stage 3 short list J9
words,一行|yīxíng,ja,いっこう,Stage 3 short list J10
words,內幕|nèimù,ja,ないまく,Stage 3 short list J11
words,氣質|qìzhì,ja,きしつ,Stage 3 short list J12
words,相對|xiāngduì,ja,そうたい,Stage 3 short list J13
words,一一|yīyī,ja,いちいち,Stage 3 short list J14
words,份|fèn,vi,phần,Stage 3 short list V1
words,更|gèng,vi,cánh,Stage 3 short list V2
words,過|guo,vi,quá,Stage 3 short list V3
words,占|zhàn,vi,chiếm,Stage 3 short list V4
words,福|fú,vi,phúc,Stage 3 short list V5
words,行|háng,vi,hàng,Stage 3 short list V6
words,濕|shī,vi,thấp,Stage 3 short list V7
words,應|yīng,vi,ưng,Stage 3 short list V8
words,將|jiāng,vi,tương,Stage 3 short list V9
words,與|yǔ,vi,dữ,Stage 3 short list V10
words,瓷|cí,vi,từ,Stage 3 short list V11
words,想象|xiǎngxiàng,vi,tưởng tượng,rule_b_conflict variant spelling (想像); V12
words,贊助|zànzhù,vi,tán trợ,rule_b_conflict variant spelling (讚助); V13
words,模糊|móhu,vi,mô hồ,rule_b_conflict variant spelling (模胡); V14
words,以往|yǐwǎng,vi,dĩ vãng,rule_b_conflict same word (已往); V15
words,振動|zhèndòng,vi,chấn động,rule_b_conflict variant spelling (震動); V16
words,激勵|jīlì,vi,khích lệ,rule_b_conflict variant spelling (激厲); V17
words,兇惡|xiōng'è,vi,hung ác,rule_b_conflict shinjitai spelling (凶悪); V18
words,言辭|yáncí,vi,ngôn từ,rule_b_conflict variant spelling (言詞); V19
chars,茶,ko,차,D39/D50 user decision; C1
chars,寧,ko,녕,D39 literal mapping gave 령; C2
```
Group C3, if confirmed, adds 13 `chars` rows (`chars,爐,ko,로,...` and so on).

## After confirmation (Claude)
Write the confirmed rows, run `run_all.py` and all tests, update the one test that pins 茶 = 다 (`tests/test_stage3_gate_fixes.py`) to 차, recheck the changed rows, then record the gate result.
