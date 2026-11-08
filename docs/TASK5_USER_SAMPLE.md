# Task 5: native-speaker check (Stage 4 gate part 4, D67 item 6)

Gemini (task 5) judged whether Korean and Japanese speakers actually use each reading. **`rare`** = not used (the card will show the reading in （ ）, its meaning is removed, and in 偽の友達 the row shows 「（韓国語ではほぼ使わない）」 or 「（日本語ではほぼ使わない）」); **`wrong_meaning`** = the word is used, but not with the given meaning (meaning removed, reading shown normally); **`used`** = fine.

**How to answer:** reply in the chat with the numbers you disagree with and what is right, e.g. `A7 used, A23 wrong_meaning, B3 rare`. Anything you do not mention counts as agreed. Seeded random draw (seed 20261107), excluding the items Claude already corrected in part C.

Columns: *meaning* = the meaning the app would show for that language (from tasks 1-2); *reason* = Gemini's review note (never shown in the app).

## Answers (user, 2026-11-07; applied in gate part 4b, D69)
- **A:** all agreed (0 of 40 "not used" flags wrong; the class is not re-opened).
- **C:** all 26 corrections agreed.
- **B** (the user delegated the research; final decisions): B1 那邊 나변 **used**, B2 其實 기실 **used**, B3 明年 명년 rare, B4 立國 입국 rare, B5 開演 개연 rare, B6 第一聲 제일성 **used**, B7 應當 おうとう rare (user's own call), B8 接受 せつじゅ **used**, B9 慶祝 けいしゅく **used**, B10 宣布 せんぷ **used**, B11 霍亂 かくらん **used**, B12 必定 ひつじょう **used**, B13 會同 かいどう **used**. The 9 `used` answers are rows in `config/task5_review.csv`; 應當 leaves 偽の友達 (`config/task2_retrap.csv`).

## A. 50 random items (20 Korean and 20 Japanese "not used" flags, 10 "used", mixed)

| # | lang | word | reading | check | meaning | reason |
|---|---|---|---|---|---|---|
| A1 | 日 | 配偶 | はいぐう | rare | 取り合わせること、夫婦となること | 単独ではほぼ使わず「配偶者」と言う |
| A2 | 韓 | 地盤 | 지반 | used | 土地の土台、また勢力の基礎となる範囲 |  |
| A3 | 韓 | 小聲 | 소성 | rare | 小さな声 | 辞書のみの語。日常では固有語を使う。 |
| A4 | 韓 | 隨便 | 수편 | rare | 都合に任せること、気軽なこと | 辞書のみの中国語由来の語 |
| A5 | 日 | 粗略 | そりゃく | rare | 大まかなこと、ぞんざいなこと | 辞書のみの古風な語。そりゃくは通常「疎略」 |
| A6 | 日 | 出門 | しゅつもん | rare | 門を出ること、外出 | 日常的には「外出」などを使う。しゅつもんは主に仏教用語 |
| A7 | 日 | 自刎 | じふん | rare | 自刎、首をはねて自殺すること | 文語・歴史用語。通常は「自害」「自殺」を使う |
| A8 | 韓 | 足下 | 족하 | rare | 足元、貴下（二人称） | 辞書のみの古語。족하は通常、甥・姪を指す固有語に聞こえる |
| A9 | 韓 | 補考 | 보고 | rare | 追試験、再試験 | 보고は通常「報告」「宝庫」を指す。追試験には「再試験」などを使う |
| A10 | 日 | 名利 | めいり | rare | 名誉と利益 | 文語・辞書的な語。現代では「名誉と利益」などと言う |
| A11 | 日 | 城市 | じょうし | rare | 城下町、都市 | 辞書のみの語。日常では「都市」や「城下町」を使う |
| A12 | 韓 | 得到 | 득도 | rare | 悟りを開くこと | 韓国語では득도は「得道（悟りを開く）」と認識され、「得到」は使わない |
| A13 | 日 | 孵化 | ふか | used | 卵がかえること、孵化 |  |
| A14 | 韓 | 白紙 | 백지 | used | 白紙 |  |
| A15 | 韓 | 竹竿 | 죽간 | rare | 竹のさお | 固有語を使い、죽간は通常「竹簡」と認識される |
| A16 | 日 | 噴泉 | ふんせん | rare | 噴き出る泉、噴水 | 温泉の用語を除き、通常は「噴水」を使う |
| A17 | 韓 | 依舊 | 의구 | rare | 元のままであること、相変わらないこと | 文語・成語（依舊如前など）のみで、日常語は「依然」や固有語を使う |
| A18 | 日 | 一直 | いっちょく | rare | 一直、まっすぐなこと（野球のライナーなど） | 「一直線」としては使うが単独の「一直」は野球の記録用語などを除き稀 |
| A19 | 日 | 顯然 | けんぜん | rare | 顕然、はっきりしているさま | 現代語ではほぼ使わない文語。「明白」「明らか」を使う |
| A20 | 韓 | 臺上 | 대상 | rare | 台の上、舞台の上 | 韓国語では「舞台の上」などと言う。대상は通常「対象」「大賞」 |
| A21 | 日 | 忠君 | ちゅうくん | used | 忠君、主君に忠義を尽くすこと |  |
| A22 | 日 | 尺寸 | しゃくすん | rare | 長さ、またごくわずかなこと | 古風な文語。現代では「寸法」「サイズ」を使う |
| A23 | 韓 | 一剎那 | 일찰나 | rare | 一刹那、一瞬 | 韓国語では通常「刹那」または「一瞬」を使う |
| A24 | 日 | 牧民 | ぼくみん | rare | 人民を治め養うこと | 古典・歴史用語であり、現代語としては使わない |
| A25 | 韓 | 難道 | 난도 | rare | 険しい道 | 辞書のみの古語。난도は通常「難度」として認識される |
| A26 | 日 | 變性 | へんせい | used | 変性、性質が変わること（タンパク質の変性など） |  |
| A27 | 韓 | 富翁 | 부옹 | rare | 富翁、金持ち | 古風な語で、通常は「富者」や「富豪」を使う |
| A28 | 日 | 燕子 | えんし | rare | ツバメ | 漢詩文の語。日常では和語「つばめ」を使う |
| A29 | 韓 | 下地 | 하지 | rare | 下等の土地、基礎・下塗り | 辞書のみの語。現代語では하지は「夏至」や「下肢」と認識される |
| A30 | 韓 | 不成 | 불성 | rare | 物事が成就しないこと | 四字熟語以外ではほぼ使わない文語。単体では「不誠」などと紛らわしい |
| A31 | 日 | 電視臺 | でんしだい | rare | （中国語圏の）テレビ局 | 中国語の単語。日本語では「テレビ局」を使う |
| A32 | 日 | 平淡 | へいたん | rare | あっさりして穏やかなこと、簡素 | へいたんは通常「平坦」と書く |
| A33 | 韓 | 作客 | 작객 | rare | 客となること、他郷に滞在すること | 辞書のみの古語であり日常では使われない |
| A34 | 韓 | 半夜 | 반야 | rare | 真夜中、半夜 | 반야は通常仏教語の「般若」と聞き、「真夜中」の意では固有語を使う |
| A35 | 日 | 仁義 | じんぎ | used | 仁愛と正義、道徳上の務め |  |
| A36 | 日 | 演練 | えんれん | rare | 演練、訓練 | 現代日本語では使われず、「訓練」や「演習」を使う |
| A37 | 日 | 主攻 | しゅこう | rare | 主攻、主力による攻撃 | 中国語由来の語。日本語では「主力攻撃」などと言う |
| A38 | 韓 | 著落 | 저락 | rare | 落ち着く先、あて | 韓国語では使われない語。저락は通常「低落」 |
| A39 | 日 | 放肆 | ほうし | rare | 放肆、気ままで慎みがないこと | 現代語ではほぼ使われない漢籍語 |
| A40 | 韓 | 低落 | 저락 | rare | 相場や価値が下がること | 現代韓国語ではほとんど使われず、「下落」や「暴落」を使う |
| A41 | 韓 | 車號 | 차호 | rare | 車両の番号 | 차호は「次号」「借字」などを指す。車両番号には「車両番号」を使う |
| A42 | 日 | 猛然 | もうぜん | used | 猛然、勢いの激しいさま |  |
| A43 | 韓 | 愚癡 | 우치 | rare | 愚かで無知なこと | 現代では日常的に使われない仏教・文語的表現 |
| A44 | 韓 | 大路 | 대로 | used | 大路、大通り |  |
| A45 | 日 | 愛心 | あいしん | rare | 愛する心 | 現代日本語では使わない語 |
| A46 | 韓 | 政局 | 정국 | used | 政治の情勢や局面。 |  |
| A47 | 日 | 萬萬 | まんまん | rare | 数が多いさま、極めて | 「万々承知」などの決まり文句を除き、単独では古語的 |
| A48 | 日 | 高考 | こうこう | rare | 中国の全国統一大学入学試験 | 中国の制度の名称であり、日本語では通常中国語音で呼ぶ |
| A49 | 韓 | 規劃 | 규획 | rare | 企画・計画を立てること | 韓国語では「企画」や「計画」を使う |
| A50 | 韓 | 參政權 | 참정권 | used | 政治に参加する権利 |  |

## B. 13 borderline cases Claude could not decide (all currently `rare`)

Formal, literary or technical words count as **used** (task-5 prompt). Answer `used` or `rare` for each.

| # | lang | word | reading | check | meaning | Claude's question |
|---|---|---|---|---|---|---|
| B1 | 韓 | 那邊 | 나변 | rare | あちら、どのあたり | その表現は社説などの「저의가 나변에 있는가」で使う？ |
| B2 | 韓 | 其實 | 기실 | rare | 実際、実は | 書き言葉の副詞「기실」として使う？ |
| B3 | 韓 | 明年 | 명년 | rare | 来年 | 「명년」は古風だが通じる？ |
| B4 | 韓 | 立國 | 입국 | rare | 立国 | 「수출입국」「기술입국」の形で使う？ |
| B5 | 韓 | 開演 | 개연 | rare | 開演 | 劇場の「개연 시간」で使う？ |
| B6 | 韓 | 第一聲 | 제일성 | rare | 最初に発する言葉 | 報道の「취임 제일성」で使う？ |
| B7 | 日 | 應當 | おうとう | rare | 相当すること、当てはまること | 金融・保険の「応当日」で使う？ |
| B8 | 日 | 接受 | せつじゅ | rare | 接受、受け取ること | 外交用語「接受国」で使う？ |
| B9 | 日 | 慶祝 | けいしゅく | rare | 慶祝、祝うこと | 「慶祝行事」「慶祝式典」で使う？ |
| B10 | 日 | 宣布 | せんぷ | rare | 広く告げ知らせること、公布 | 法令・歴史の「宣布」で使う？ |
| B11 | 日 | 霍亂 | かくらん | rare | 日射病、暑気あたり | 慣用句「鬼の霍乱」で使う？ |
| B12 | 日 | 必定 | ひつじょう | rare | 必定、必ずそうなること | 「敗北は必定」のように使う？ |
| B13 | 日 | 會同 | かいどう | rare | 諸侯や人が一堂に会すること | 官庁の「検察長官会同」などで使う？ |

## C. Claude's corrections, already in `config/task5_review.csv` (veto any you disagree with)

| # | lang | word | reading | Gemini | Claude | why |
|---|---|---|---|---|---|---|
| C1 | 韓 | 推動 | 추동 | rare | **used** | 추동 is in active use in Korean writing (추동력; 변화를 추동하다) |
| C2 | 韓 | 具有 | 구유 | rare | **used** | 구유하다 is a formal word used in academic and legal Korean |
| C3 | 日 | 具有 | ぐゆう | rare | **used** | 具有 is used in formal Japanese (両性具有; 〜を具有する) |
| C4 | 韓 | 反正 | 반정 | rare | **used** | 반정 is the standard Korean history term (인조반정, 중종반정); a real false friend of zh "anyway" |
| C5 | 韓 | 初中 | 초중 | rare | **used** | 초중 is in everyday use as 초등+중등 (초중고, 초중등교육); the given meaning describes that use |
| C6 | 日 | 好奇 | こうき | rare | **used** | 好奇 is used on its own in Japanese (好奇の目, 好奇に満ちた) |
| C7 | 韓 | 效益 | 효익 | rare | **used** | 효익 is a standard accounting and economics term (경제적 효익, 비용 대비 효익) |
| C8 | 韓 | 吩咐 | 분부 | rare | **used** | 분부 is a living Korean word; the standard dictionary lists 分付/吩咐 for it |
| C9 | 韓 | 異狀 | 이상 | rare | **used** | 이상(異狀) "an abnormal state" is used (이상 없음); the reason argues only about the hanja spelling |
| C10 | 日 | 上市 | じょうし | rare | **used** | 上市 じょうし is the standard Japanese pharmaceutical term (新薬の上市) |
| C11 | 日 | 兩棲 | りょうせい | wrong_meaning | **used** | 両棲 りょうせい is a valid spelling of 両生 (両棲類); the meaning is right |
| C12 | 韓 | 短信 | 단신 | rare | **wrong_meaning** | 단신 is used, but as a short news item (단신 기사), not as a short letter or SMS |
| C13 | 韓 | 過年 | 과년 | rare | **wrong_meaning** | 과년 is used, but for a woman past marriageable age (과년한 딸), not for New Year |
| C14 | 韓 | 星星 | 성성 | rare | **wrong_meaning** | 성성하다 is used for greying hair (백발이 성성하다), not for stars |
| C15 | 韓 | 管子 | 관자 | used | **wrong_meaning** | the given meaning mixes the homophones 貫子 and 冠者; 管子 is only the historical person |
| C16 | 韓 | 東邊 | 동변 | used | **rare** | 동변 is a dictionary-only word; Korean says 동쪽 |
| C17 | 韓 | 北邊 | 북변 | used | **rare** | 북변 is a dictionary-only or historical word; Korean says 북쪽 |
| C18 | 韓 | 秀美 | 수미 | used | **rare** | 수미 for 秀美 is a dictionary-only word |
| C19 | 韓 | 觸犯 | 촉범 | used | **rare** | 촉범 is a dictionary-only word; Korean uses 저촉 or 위반 |
| C20 | 韓 | 慘痛 | 참통 | used | **rare** | 참통 is a dictionary-only word; Korean uses 비통 or 참담 |
| C21 | 韓 | 急劇 | 급극 | used | **rare** | 급극 is a dictionary-only word; Korean uses 급격 (急激) |
| C22 | 韓 | 海量 | 해량 | used | **rare** | 해량 is heard as 海諒 (forgiveness); 海量 is not used |
| C23 | 韓 | 注重 | 주중 | used | **rare** | 주중 is heard as 週中; 注重 is not used |
| C24 | 韓 | 折中 | 절중 | used | **rare** | held-out case: Korean uses 절충 (折衷); 절중 is not used |
| C25 | 韓 | 疑義 | 의의 | used | **rare** | held-out case: 의의 is heard as 意義; Korean uses 의문 or 이의 |
| C26 | 韓 | 師長 | 사장 | used | **rare** | 사장 is heard as 社長; Korean says 사단장 (師團長) for a division commander, 스승 for a teacher |
