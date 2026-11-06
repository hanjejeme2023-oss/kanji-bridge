# Vietnamese finalization (D55): short list for the user

**Status: proposed by Claude on 2026-11-06, waiting for the user. Nothing is written to `pipeline/overrides.csv` and `config/vi_sources.json` stays `false` until the user confirms.**

Built from commit `4919d5b` (repeat Stage 3 gate, attempt 2: PASS). Every replacement value below is a dictionary candidate the build accepts (an A2 / 7C value for the word's form, or a candidate listed in `vi_ambiguous.csv`). "Clear" means an empty `vi` override with a reason (D55 a): the value leaves the card and is listed in `vi_ambiguous.csv` as `override_cleared`. It does not go to `vi_alt`. Evidence: `docs/review_scripts/d55_vi_shortlist_reference.py` (items 1, 2, 6), the switched-on build for item 5 (not committed), and `docs/D36_VI_SOURCE_SEARCH.md`.

**How to answer:** "all as proposed", or name the rows to drop or change (e.g. "keep R3; E2 yes; Q1 b"). Questions Q1-Q3 at the end need an answer.

## Summary
| Group | D55 item | Rows | Proposed |
|---|---|---|---|
| R. A/B value vs English Wiktionary (A2) | 1 | 17 | **replace 8**, keep 9 |
| C. Rule-B values that are a different Vietnamese word | 2, 4, 6 | 39 + 3 from the samples | **clear 24**, keep 18 |
| O. `obsolete_only` words | 3 | 8 | keep all 8 empty (as built) |
| E. 7C character readings | 5 | 139 characters, 33 words | **switch on**; clear 5 new word values |
| M. Other open items | — | 調, 馴 | keep 調 điệu; **馴 → thuần** |
| S. Seeded sample of 50 words | 6 | 50 | 48 / 50 = **96%** (target 98%); both errors are in group C; after C: 49 / 50 = 98% |

New overrides if all are confirmed: 9 replacements + 29 clears = **38** (81 → 119 rows).

## R. Rule A/B value vs English Wiktionary (item 1)
A2 never overwrites A/B (D53), so these 17 disagreements are still in the build. The A2 entry gives the Han form explicitly; A/B gave the other value.

| # | Word (key) | L | Built (source) | 7C (A2) | Proposed | Why |
|---|---|---|---|---|---|---|
| R1 | 一 `一\|yī` | 1 | nhứt (Kaikki-vi rule A) | nhất | **nhất** | Kaikki-vi's own gloss: "(obsolete) Southern Vietnam form of nhất"; `chars.vi` is nhất |
| R2 | 詞 `詞\|cí` | 2 | tờ (rule A) | từ | **từ** | tờ is the Nôm word "sheet of paper" (gloss: "Tấm giấy phẳng mỏng"); 詞 = từ (từ điển) |
| R3 | 累 `累\|lèi` | 1 | lũy (rule B) | lụy | **lụy** | lèi "tired; to strain" = lụy (liên lụy 連累); lũy is lěi "accumulate" (tích lũy) |
| R4 | 圈 `圈\|quān` | 4 | quyển (rule B) | khuyên | **khuyên** | quān "circle, ring" = khuyên; quyển is juàn "pen" (R16) and the classifier for books (卷) |
| R5 | 祝福 `祝福\|zhùfú` | 4 | chúc phước (rule B) | chúc phúc | **chúc phúc** | standard form; 福 itself is already overridden to phúc (V5) |
| R6 | 服從 `服從\|fúcóng` | 5 | phục tòng (rule B) | phục tùng | **phục tùng** | standard modern form |
| R7 | 拖 `拖\|tuō` | 6 | đà (rule B) | tha | **tha** | 拖 = tha; the rule-B gloss is "log rolled under a load" (a Nôm word) |
| R8 | 拄 `拄\|zhǔ` | 7 | chủ (rule B) | trụ | **trụ** | 拄 = trụ; chủ is 主 (gloss "owner") |
| R9 | 幹 `幹\|gàn` | 1 | cán | can | keep **cán** | 幹 = cán (cán bộ 幹部); 7C can is 干 "to concern" |
| R10 | 關 `關\|guān` | 1 | quan | loan | keep **quan** | loan is a different word from the same etymon |
| R11 | 中 `中\|zhōng` | 1 | trung | trúng | keep **trung** | trúng is zhòng |
| R12 | 週 `週\|zhōu` | 2 | chu | châu | keep **chu** | chu (chu kỳ 週期) |
| R13 | 散 `散\|sàn` | 4 | tán | tản | keep **tán** | both are readings; sàn "scatter" = tán (giải tán) |
| R14 | 散 `散\|sǎn` | 5 | tán | tản | keep **tán** | tản (tản mạn) also fits sǎn; tán is the common reading, either is acceptable |
| R15 | 藏 `藏\|cáng` | 6 | tàng | tạng | keep **tàng** | cáng "hide" = tàng; tạng is zàng (Tây Tạng) |
| R16 | 圈 `圈\|juàn` | 7 | quyển | khuyên | keep **quyển** | juàn "pen" |
| R17 | 經 `經\|jīng` | 7 | kinh | canh | keep **kinh** | canh "warp thread" is a different word |

## C. Rule-B values that are a different Vietnamese word (items 2, 4, 6)
Rule B (D24) composes a reading from the characters and accepts it if Kaikki-vi has that headword. For these words the headword is a **different word written with other characters** (English Wiktionary gives its Han form), so the card would teach a wrong word. A card with the correct Vietnamese word cannot be built from the sources, so the proposal is to clear the value. The Hán-Việt syllables stay in `word_chars` (they are not wrong as syllables).

**Clear (24):**
| # | Word (key) | L | Built | Vietnamese word is | Meaning of the Vietnamese word |
|---|---|---|---|---|---|
| C1 | 老是 `老是\|lǎoshì` | 2 | lão thị | 老視 | presbyopia |
| C2 | 行人 `行人\|xíngrén` | 2 | hạnh nhân | 杏仁 | almond |
| C3 | 燈光 `燈光\|dēngguāng` | 4 | đăng quang | 登光 | to be crowned |
| C4 | 長假 `長假\|chángjià` | 6 | trưởng giả | 長者 | bourgeois |
| C5 | 嘆氣 `嘆氣\|tànqì` | 6 | thán khí | 碳氣 | carbon dioxide |
| C6 | 忠心 `忠心\|zhōngxīn` | 6 | trung tâm | 中心 | centre |
| C7 | 報酬 `報酬\|bàochou` | 7 | báo thù | 報讎 | revenge |
| C8 | 解讀 `解讀\|jiědú` | 7 | giải độc | 解毒 | to detoxify |
| C9 | 綠地 `綠地\|lǜdì` | 7 | lục địa | 陸地 | continent |
| C10 | 尚未 `尚未\|shàngwèi` | 7 | thượng vị | 上位 | upper position |
| C11 | 食用 `食用\|shíyòng` | 7 | thực dụng | 實用 | pragmatic |
| C12 | 無償 `無償\|wúcháng` | 7 | vô thường | 無常 | impermanence |
| C13 | 友情 `友情\|yǒuqíng` | 7 | hữu tình | 有情 | charming, evocative |
| C14 | 評定 `評定\|píngdìng` | 7 | bình định | 平定 | to pacify |
| C15 | 小型 `小型\|xiǎoxíng` | 4 | tiểu hình | 小刑 | petty punishment |
| C16 | 外行 `外行\|wàiháng` | 7 | ngoại hạng | 外項 | top-class |
| C17 | 登陸 `登陸\|dēnglù` | 7 | đăng lục | 登錄 | to register |
| C18 | 公里 `公里\|gōnglǐ` | 2 | công lý | 公理 | justice |
| C19 | 設想 `設想\|shèxiǎng` | 5 | thiết tưởng | 竊想 | "I humbly think" |
| C20 | 電器 `電器\|diànqì` | 6 | điện khí | 電氣 | electricity |
| C21 | 原型 `原型\|yuánxíng` | 7 | nguyên hình | 原形 | original (true) form |
| C22 | 生詞 `生詞\|shēngcí` | 2 | sinh từ | 生祠 | shrine to a living official (Kaikki-vi gloss) |
| C23 | 重型 `重型\|zhòngxíng` | 7 | trọng hình | 重刑 | heavy punishment (Kaikki-vi gloss) |
| C24 | 因為 `因為\|yīnwèi` | 2 | nhân vị | (no Han form given) | "for the good of people" (Kaikki-vi gloss); 因為 is "vì" |

C1-C21 come from the D36 list of 38 rule-B values that English Wiktionary files under other characters (plus 公里, which the current build adds). C22-C24 come from the samples in item 6 (below) and cannot be found by any source comparison.

**Keep (18):** the same word in another spelling, or a homograph that is the right word.
| Word | Value | Why keep |
|---|---|---|
| 清明 | thanh minh | 7C files it under 聲明 "to clarify", but Tết Thanh minh is 清明 |
| 外援 | ngoại viện | 援 = viện (viện trợ); 7C files the hospital sense 外院 |
| 周旋 | chu toàn | Kaikki-vi glosses "chu toàn" as "see chu tuyền" (周旋) |
| 工夫, 秘密, 情景, 辭典, 模仿, 沉思, 環球, 家境, 廉政, 收復 | công phu, bí mật, tình cảnh, từ điển, mô phỏng, trầm tư, hoàn cầu, gia cảnh, liêm chính, thu phục | same word, variant spelling (功夫, 祕密, 情境, 詞典, 摸仿, 沈思, 寰球, 家景, 廉正, 收服) |
| 想象, 以往, 振動, 激勵, 言辭 | (already overridden, V12, V15-V17, V19) | confirmed at Stage 3 |
| 變革 | biến cách | Kaikki-vi's gloss is the grammar sense (變格), but 變革 biến cách "great change" is a Hán-Việt word; keep, Stage 4 checks the meaning |

## O. `obsolete_only` words (item 3)
7C has only an obsolete or archaic entry, so the build leaves these empty (D53). Proposal: **keep all empty**; a card would teach a word a Vietnamese speaker no longer uses.
| Word | 7C candidate | Modern Vietnamese |
|---|---|---|
| 新聞 xīnwén (test word) | tân văn | tin tức |
| 戲劇 xìjù | hý kịch | kịch |
| 伯父 bófù | bá phụ | bác |
| 不宜 bùyí | bất nghi | không nên |
| 岳父 yuèfù | nhạc phụ | bố vợ (nhạc phụ survives in formal speech) |
| 岳母 yuèmǔ | nhạc mẫu | mẹ vợ (as above) |
| 聘 pìn | sính | (sính lễ, only in compounds) |
| 隧道 suìdào | tụy đạo | đường hầm |
Optional alternative: 岳父 nhạc phụ and 岳母 nhạc mẫu are still understood; say so if you want them on cards.

## E. Character readings from 7C (item 5, D55 b)
Measured with one build where `config/vi_sources.json` was `true` (not committed; the committed build is unchanged).

- **Characters:** 139 rows change source; **0 `ko` changes**; `vi` primary changes only for 棟 (chống, a Nôm reading → **đống**). 45 Unihan-unverified characters are confirmed, 36 characters without any Vietnamese reading get one, 52 `unihan_hvsyl` rows are relabelled `kaikki_en_char`, 6 verified rows gain a second reading (比 tỉ, 子 tí, 司 ti, 曾 tằng, 否 bĩ, 未 mùi). `vi_final` changes in 16 rows.
- **Precision check (all 81 confirmed or new readings, not a sample):** 80 / 81 are the standard Hán-Việt reading (new: 爸 ba, 餓 ngạ, 歲 tuế, 笑 tiếu, 雨 vũ, 剩 thặng, 癌 nham, 禪 thiền, 龜 quy, 卵 noãn, 隧 toại ...; confirmed: 買 mãi, 早 tảo, 黑 hắc, 夜 dạ, 皮 bì, 盆 bồn ...). The exception is 乾 **kiền** for gān "dry" (that sense is can; kiền is the trigram), which is already the built primary and has no `can` in `vi_all`, so an override cannot fix it (loop 1). **98.8% ≥ 95%: the D55 bar is met.**
- **Words:** HSK `vi` 4,239 → **4,271**, all four 3,362 → **3,381**. 33 words get or change `vi`, all through rule B. 28 are right (乾淨 kiền tịnh "clean", 歲月 tuế nguyệt, 日夜 nhật dạ, 罷免 bãi miễn, 凝聚 ngưng tụ, 富翁 phú ông, 欺詐 khi trá ...). 剩 shèng changes thừa → **thặng** (thặng dư; thừa is the everyday word from the same character, both are acceptable). **5 are wrong and are proposed for clearing:**

| # | Word (key) | L | New value | Kaikki-vi gloss of that headword |
|---|---|---|---|---|
| E1 | 爸爸 `爸爸\|bàba` | 1 | ba ba | softshell turtle |
| E2 | 大爺 `大爺\|dàye` | 4 | đại gia | a rich person (大家) |
| E3 | 飼養 `飼養\|sìyǎng` | 7 | tự dưỡng | autotrophic (自養) |
| E4 | 飼料 `飼料\|sìliào` | 7 | tự liệu | to manage on one's own |
| E5 | 薪水 `薪水\|xīnshui` | 6 | tân thủy | a commune name |

**Proposal:** switch `kaikki_en_char_readings` on, together with E1-E5.

## M. Other open items from the repeat gates
| # | Word | Built | Proposed | Why |
|---|---|---|---|---|
| M1 | 調 `調\|diào` | điệu (A2; the D44 count tied) | keep **điệu** | diào "tune, tone" = điệu (giọng điệu); 調 tiáo stays điều |
| M2 | 馴 `馴\|xùn` | empty (`several_candidates` tuần; thuần) | **thuần** | thuần hóa "to tame" is the HSK sense; tuần lộc (馴鹿) is a fixed word |
| M3 | 自己 zìjǐ | tự kỷ (7C: "autistic") | no change | the reading is right; the meaning differs, so Stage 4 task 2 must judge it as a false friend |
| M4 | VI-only 複合 phức hợp / HSK 復合; VI-only 凶悪 / HSK 兇惡 | both present | see Q3 | the D46 variant check cannot see 復/複 or the shinjitai 悪 |

Known side effect (gate note): `vi_alt` of 馴 still holds tuần;thuần and `vi_alt` of 調 diào holds điều;điệu, so `judge()` accepts those too. Overrides do not change `vi_alt`; see Q3.

## S. Seeded sample of 50 words with `vi` (item 6)
`DataFrame.sample(50, random_state=20261106)` over the 5,440 words with `vi` (38 HSK + 12 VI-only; 23 rule B, 18 rule A, 9 A2). **48 / 50 correct (96%), below the 98% target.** Errors: 因為 nhân vị (C24) and 食用 thực dụng (C11), both rule-B words where Kaikki-vi's headword is a different word. Correct, e.g.: 點 điểm, 停 đình, 行 háng hàng, 合理 hợp lý, 計算 kế toán (reading right; the Vietnamese meaning is "accounting", a Stage 4 false friend), 沉重 trầm trọng, 指示 chỉ thị, 鳳凰 phượng hoàng, 崛起 quật khởi, 欄杆 lan can, 美化 mỹ hóa, 秩序 trật tự, 義父 nghĩa phụ, 埃及 ai cập, 網膜 võng mạc, 植物學 thực vật học, 檢定 kiểm định, 地盤 địa bàn. With group C applied the sample is 49 / 50.

**Sizing the cause (extra seeded sample, `random_state=55055`, 60 of the 1,328 multi-character rule-B words):** 4 clearly wrong (生詞 C22, 重型 C23, 忠心 C6, 小型 C15), 1 doubtful (變革, kept). That is about **7% of multi-character rule-B words**, roughly 90 words, of which this list clears 24. Single-character rule-B values are character readings and were all right in both samples. The cause is rule B itself (D24, D51): a composed reading that happens to be a headword is accepted, and only some of the false matches can be detected from the sources (Kaikki-vi rule A for D51, 7C for group C). This is the rule-level cause D55 says must go to the user before the freeze (Q1).

## Questions for the user
**Q1. The remaining rule-B false matches (about 70 after group C).**
- **(a) Recommended: overrides now, Stage 4 finds the rest.** Apply groups C and E now. In the Stage 4 assignment, task 1 gets a field that flags a word whose Vietnamese value means something else than the Han word (Gemini sees `gloss_vi`, which for these words shows the other meaning, as for 生詞 and 重型). Claude reviews every flag and clears confirmed ones through overrides before Stage 5, as a separate short list for you. No Codex round before the freeze. Cost: the flagged words get Stage 4 content first, and the content for a cleared Vietnamese value is dropped.
- (b) Codex round before the freeze: extend the D51 conflict filter to 7C Han forms, with an exception for D43 variant forms. For this data it removes the same values as group C (the keep list would come back as overrides), so it adds a Codex and a gate round without finding new errors.
- (c) Group C only; accept the rest as a known limit.

**Q2. 7C character readings (group E): switch on together with E1-E5?** Recommended: yes.

**Q3. Two small pipeline items (M4 and the `vi_alt` note).** (a) Recommended: record them for loop 1 (two duplicated VI-only words; two words whose `vi_alt` accepts an extra reading). (b) Send them to Codex before the freeze: a VI-only exclusion for a form whose `vi` and `ko` equal an HSK word's, and `vi_alt` cleared when the D44 count ties. This needs a Codex round and a gate recheck.

**After your answer:** Claude writes the confirmed overrides (and the switch), rebuilds, and rechecks: tests, rebuild identical, D52 tie rule against `4919d5b` (clearing 24 rule-B words removes D39 evidence, so a primary may flip; any flip comes back to you), all overrides apply. Then the word list freezes (D46, D55), the documentation consolidation follows, and Claude writes the Stage 4 assignment.
