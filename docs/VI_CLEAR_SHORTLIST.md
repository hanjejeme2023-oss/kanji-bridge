# Vietnamese clear short list (D57 Q1, HANDOFF step 6) — for the user to confirm

Prepared by Claude, 2026-11-07, after Stage 4 gate part 2. Evidence script: `docs/review_scripts/stage4d_part2_reference.py clears`.

## What you decide

Each row is a Vietnamese value that our dictionary pipeline attached to a Han word, where the Vietnamese dictionary entry describes **a different word that only sounds the same** (written with other Han characters, or a place name, or a native Vietnamese word). If such a value stays, a card or the false-friend view would teach you a Vietnamese word that does not mean this.

- **Clear** = the word keeps its Japanese, Korean and Chinese data but shows **no Vietnamese** (we never invent a replacement, Global Rule 2).
- **Keep** = the Vietnamese value stays.

Reply with **"All as proposed"**, or list exceptions by number (e.g. "A27 keep, B25 keep").

## How to check a row yourself

1. Open the link in the "Dictionary" column. Rows marked *vi* go to Vietnamese Wiktionary (the source of our Vietnamese glosses); rows marked *en* go to English Wiktionary.
2. Read the first definition; the table quotes it with an English translation.
3. Ask: does that definition match the meaning of the Han word on the left? The "Belongs to" column names the word the definition really describes, and "Everyday Vietnamese" gives what a Vietnamese speaker says for the Han word's meaning (my explanation only; it does not enter the data).

## Group A: 39 words on cards (30 `different_word` + 9 multi-character `unsure` from task 1)

Proposed: **clear 36, keep 2 (A20, A36), your call on A27 (I lean clear).**

| # | Word (level) | Vietnamese value | Dictionary | What the dictionary says | Belongs to | Everyday Vietnamese for the word's meaning | Proposal |
|---|---|---|---|---|---|---|---|
| A1 | 姐姐 elder sister (1) | thư thư | [vi](https://vi.wiktionary.org/wiki/thư_thư) | "Thư, ngh. 2." = only "see *thư*, sense 2"; no definition | not a word for "sister" (as a native word *thư thư* means "slowly, at ease") | chị, chị gái | **clear** |
| A2 | 星期 week (1) | tinh kỳ | [vi](https://vi.wiktionary.org/wiki/tinh_kỳ) | "Cờ." = "a flag" | 旌旗 (banners) | tuần, tuần lễ; weekday = thứ | **clear** |
| A3 | 手指 finger (3) | thủ chỉ | [vi](https://vi.wiktionary.org/wiki/thủ_chỉ) | "Người cường hào đứng đầu một làng thời phong kiến…" = "the strongman who headed a village in feudal times" | another old word, not 手指 | ngón tay | **clear** |
| A4 | 信封 envelope (3) | tín phong | [vi](https://vi.wiktionary.org/wiki/tín_phong) | "Xem gió tín phong" = "see *trade wind*" | 信風 (trade wind) | phong bì | **clear** |
| A5 | 大型 large-scale (4) | đại hình | [vi](https://vi.wiktionary.org/wiki/đại_hình) | "Các vụ án về trọng tội…" = "serious criminal cases" | 大刑 | cỡ lớn, quy mô lớn | **clear** |
| A6 | 期中 mid-term (4) | kỳ trung | [vi](https://vi.wiktionary.org/wiki/kỳ_trung) | "Thực ra bên trong là." = "in fact, inside it is…" | 其中 (among them) | giữa kỳ | **clear** |
| A7 | 童年 childhood (4) | đồng niên | [vi](https://vi.wiktionary.org/wiki/đồng_niên) | "Cùng tuổi với nhau." = "the same age as each other" | 同年 | tuổi thơ, thời thơ ấu | **clear** |
| A8 | 自制 self-control (4) | tự chế | [en](https://en.wiktionary.org/wiki/tự_chế#Vietnamese) | "to make or innovate something by oneself; to DIY" | 自製 (home-made) | tự kiềm chế, tự chủ | **clear** |
| A9 | 消防 fire fighting (5) | tiêu phòng | [vi](https://vi.wiktionary.org/wiki/tiêu_phòng) | "Buồng của vợ vua có trát hột hạt tiêu lên vách" = "the queen's room, walls plastered with pepper" | 椒房 | phòng cháy chữa cháy, cứu hỏa | **clear** |
| A10 | 依法 according to law (5) | y pháp | [vi](https://vi.wiktionary.org/wiki/y_pháp) | "Chuyên khoa dùng kiến thức y học phục vụ cho luật pháp…" = "the medical specialty that serves the law" (forensic medicine) | 醫法 | theo pháp luật | **clear** |
| A11 | 中斷 interrupt (5) | trung đoạn | [vi](https://vi.wiktionary.org/wiki/trung_đoạn) | "Đoạn thẳng góc vạch từ tâm của một đa giác đều tới một cạnh" = "the perpendicular from the centre of a regular polygon to a side" (geometry) | a geometry term, not 中斷 | gián đoạn, ngắt quãng | **clear** |
| A12 | 創意 creative idea (6) | sáng ý | [vi](https://vi.wiktionary.org/wiki/sáng_ý) | "Thông minh, chóng hiểu." = "clever, quick to understand" | native *sáng* (bright) + ý | sáng kiến, ý tưởng sáng tạo | **clear** |
| A13 | 傷口 wound (6) | thương khẩu | [vi](https://vi.wiktionary.org/wiki/thương_khẩu) | "Như thương cảng" = "same as *trading port*" | 商口 | vết thương | **clear** |
| A14 | 一行 a party; a line (6) | nhất hạng | [vi](https://vi.wiktionary.org/wiki/nhất_hạng) | "Hơn hết." = "above all, the most" | another word (一項) | một đoàn; một dòng | **clear** |
| A15 | 案件 legal case (7) | yên kiện | [vi](https://vi.wiktionary.org/wiki/yên_kiện) | "Một xã thuộc huyện Đoan Hùng, tỉnh Phú Thọ" = "a commune in Phú Thọ province" (place name only; 案 is normally *án*) | a place name | vụ án, vụ việc | **clear** |
| A16 | 白白 in vain (7) | bạch bạch | [vi](https://vi.wiktionary.org/wiki/bạch_bạch) | "Từ mô phỏng tiếng… các vật mềm… vỗ đập vào nhau" = "a sound word for soft things slapping together" | a native sound word | uổng công, phí công | **clear** |
| A17 | 標示 to mark, sign (7) | tiêu thị | [vi](https://vi.wiktionary.org/wiki/tiêu_thị) | "Bêu đầu để thị chúng…" = "displaying a cut-off head to warn the people" | 梟示 | đánh dấu, biển báo | **clear** |
| A18 | 波瀾 big waves; turmoil (7) | ba lan | [vi](https://vi.wiktionary.org/wiki/Ba_Lan) | "Một quốc gia ở châu Âu… Cộng hòa Ba Lan" = Poland | 波蘭 | sóng gió, biến cố | **clear** |
| A19 | 低調 low-key (7) | đê điều | [vi](https://vi.wiktionary.org/wiki/đê_điều) | "Xem đê." = "see *dike*" | dikes (堤條) | kín tiếng, khiêm tốn | **clear** |
| A20 | 低迷 slump (7) | đê mê | [vi](https://vi.wiktionary.org/wiki/đê_mê) | "Có cảm giác say sưa, thích thú đến tê dại…" = "enraptured, intoxicated with pleasure" | **低迷 itself**: the Wiktionary entry gives these characters. Same written word, different meaning = a real false friend; task 2 already marks Vietnamese as the trap (うっとりする) | — | **keep** |
| A21 | 地步 extent; plight (7) | địa bộ | [vi](https://vi.wiktionary.org/wiki/địa_bộ) | "Xem địa bạ" = "see *land register*" | 地簿 | mức độ, nông nỗi | **clear** |
| A22 | 更改 to change (7) | canh cải | [vi](https://vi.wiktionary.org/wiki/canh_cải) | "Canh rau cải (nói tắt)" = "mustard-green soup (short form)" | native *canh* soup + *cải* greens | thay đổi, sửa đổi | **clear** |
| A23 | 公事 official business (7) | công sự | [vi](https://vi.wiktionary.org/wiki/công_sự) | "…các công trình quân sự… như hầm, hào" = "military field works: bunkers, trenches" | 工事 | việc công | **clear** |
| A24 | 海盜 pirate (7) | hải đạo | [vi](https://vi.wiktionary.org/wiki/hải_đạo) | "Đường biển." = "sea route" | 海道 | cướp biển, hải tặc | **clear** |
| A25 | 荷花 lotus flower (7) | hà hoa | [vi](https://vi.wiktionary.org/wiki/hà_hoa) | "Cửa khẩu tại thôn Hải Khẩu, xã Kỳ Hoa…" = a border gate (place name) | a place name | hoa sen | **clear** |
| A26 | 進出 to go in and out (7) | tấn xuất | [vi](https://vi.wiktionary.org/wiki/tấn_xuất) | "…trừng phạt… đối với các nhà sư…" = "a punishment expelling a Buddhist monk" | 擯出 | ra vào, xuất nhập | **clear** |
| A27 | 境界 boundary (7) | cảnh giới | [vi](https://vi.wiktionary.org/wiki/cảnh_giới) | "Canh gác, tuần phòng ở phía ngoài để phát hiện địch" = "keep watch to detect the enemy" | 警戒. **But** *cảnh giới* is also a literary/Buddhist word for 境界 "realm, state" (cảnh giới Niết bàn). Keeping it needs one small paid request for its Vietnamese meaning | ranh giới, biên giới | **your call** (I lean clear: the boundary sense is the one on the card) |
| A28 | 領略 to grasp, appreciate (7) | lĩnh lược | [vi](https://vi.wiktionary.org/wiki/lĩnh_lược) | "Vâng lời người trên." = "obey one's superiors" | another word | lĩnh hội, cảm nhận | **clear** |
| A29 | 平價 fair price (7) | bình giá | [vi](https://vi.wiktionary.org/wiki/bình_giá) | "Bàn bạc, đánh giá để quyết định giá cả (trong hợp tác xã…)" = "discuss and assess to set prices (old farm cooperatives)" | 評價 | giá rẻ, giá phải chăng | **clear** |
| A30 | 親身 in person (7) | thân thân | [vi](https://vi.wiktionary.org/wiki/thân_thân) | "Hơi thân." = "somewhat close (friendly)" | native reduplication of *thân* | tự mình, đích thân | **clear** |
| A31 | 傷痕 scar (7) | thương ngân | [vi](https://vi.wiktionary.org/wiki/thương_ngân) | "Người đi buôn (cũ)." = "a trader (old)" | a trade word (商…) | vết sẹo | **clear** |
| A32 | 時空 space-time (7) | thời không | [vi](https://vi.wiktionary.org/wiki/thời_không) | "Lúc thế giới hoàn toàn chết…" = "the time when the world is completely dead" | a different (religious) sense; the physics word is *không–thời gian* | không–thời gian | **clear** |
| A33 | 手勢 gesture (7) | thủ thế | [vi](https://vi.wiktionary.org/wiki/thủ_thế) | "Giữ miếng để kẻ địch khỏi đánh được mình" = "a guard stance so the enemy cannot hit you" | 守勢 | cử chỉ, điệu bộ | **clear** |
| A34 | 推移 to change over time (7) | suy di | [vi](https://vi.wiktionary.org/wiki/suy_di) | "Thay đổi theo chiều hướng kém trước (cũ)" = "change for the worse (old)" | 衰移 | thay đổi, chuyển biến | **clear** |
| A35 | 液體 liquid (7) | giá thể | [vi](https://vi.wiktionary.org/wiki/giá_thể) | "…vật liệu giúp… cho sự phát triển của cây trồng" = "growing medium for plants" | a farming word; known source error (the right reading *dịch thể* is not in our sources, so we may not add it) | chất lỏng | **clear** |
| A36 | 預算 budget (7) | dự toán | [vi](https://vi.wiktionary.org/wiki/dự_toán) | "Bản." = only a cut-off fragment ("a copy/sheet") | **預算 itself**: *dự toán* is the normal Vietnamese word for a cost estimate / budget plan (*dự toán ngân sách*); the gloss is just truncated | — | **keep** |
| A37 | 真假 true and false (7) | chân giả | [vi](https://vi.wiktionary.org/wiki/chân_giả) | "Phần lồi của chất nguyên sinh…" = "pseudopod" (native *chân* leg + *giả* false; also "artificial leg") | a biology word | thật giả | **clear** |
| A38 | 蓮步 a lady's dainty steps (7) | liên bộ | [vi](https://vi.wiktionary.org/wiki/liên_bộ) | "Hai hay nhiều bộ phối hợp với nhau" = "two or more ministries working together" | 聯部 | — | **clear** |
| A39 | 季女 youngest daughter (7) | quý nữ | [en](https://en.wiktionary.org/wiki/quý_nữ#Vietnamese) | "synonym of *ái nữ* ('only daughter')" | 貴女 (someone's precious daughter) | con gái út | **clear** |

## Group B: 28 forms that appear only in the false-friend list (`ff_candidates.csv`)

New in part 2. These forms never went through task 1, so nobody checked their Vietnamese value. Task 2 then turned the wrong gloss into a "false friend": for example it would teach that 敬老 in Vietnamese means "reading glasses" (*kính lão* = 鏡老, kính = glasses) and that 網羅 is a village name. The task-2 model itself marked 7 of them low confidence. **Proposed: clear all 28** (B25 is the least certain).

| # | Form | Vietnamese value | Dictionary | What the dictionary says | Belongs to |
|---|---|---|---|---|---|
| B1 | 上達 | thượng đạt | [vi](https://vi.wiktionary.org/wiki/thượng_đạt) | "Một xã thuộc huyện Nam Sách, tỉnh Hải Dương" = a commune (place name) | place name |
| B2 | 不詳 | bất tường | [vi](https://vi.wiktionary.org/wiki/bất_tường) | "Không lành, gở" = "inauspicious" | 不祥 |
| B3 | 中堅 | trung kiên | [vi](https://vi.wiktionary.org/wiki/trung_kiên) | "Trung thành và bền bỉ" = "loyal and steadfast" | 忠堅 |
| B4 | 主因 | chủ nhân | [vi](https://vi.wiktionary.org/wiki/chủ_nhân) | "người có quyền lực ra lệnh cho người khác" = "a person who gives orders; owner" | 主人 |
| B5 | 再建 | tái kiến | [vi](https://vi.wiktionary.org/wiki/tái_kiến) | "Lại thấy nhau, gặp nhau (cũ)" = "to meet again (old)" | 再見 |
| B6 | 器物 | khí vật | [vi](https://vi.wiktionary.org/wiki/khí_vật) | "Vật bỏ đi." = "a thing thrown away" | 棄物 |
| B7 | 奇数 | cơ số | [vi](https://vi.wiktionary.org/wiki/cơ_số) | "Số dùng làm cơ sở…" = "the base of a number system" | 基數 |
| B8 | 巡礼 | tuần lễ | [vi](https://vi.wiktionary.org/wiki/tuần_lễ) | "Khoảng thời gian bảy ngày…" = "a week" | 旬禮 |
| B9 | 市立 | thị lập | [vi](https://vi.wiktionary.org/wiki/thị_lập) | "Đứng chầu." = "to stand in attendance at court" | 侍立 |
| B10 | 帰化 | quy hóa | [vi](https://vi.wiktionary.org/wiki/quy_hóa) | "Một xã thuộc huyện Minh Hoá, tỉnh Quảng Bình" = a commune | place name |
| B11 | 手紙 | thủ chỉ | [vi](https://vi.wiktionary.org/wiki/thủ_chỉ) | "Người cường hào đứng đầu một làng…" = "a village strongman" (same entry as A3) | another old word |
| B12 | 敬老 | kính lão | [vi](https://vi.wiktionary.org/wiki/kính_lão) | "Kính đeo dành cho người có tuổi" = "glasses for older people" | 鏡老 (kính = glasses) |
| B13 | 旗標 | kỳ tiêu | [vi](https://vi.wiktionary.org/wiki/kỳ_tiêu) | "Tên một ngọn núi… ở Trung Quốc" = name of a mountain in China | place name |
| B14 | 東経 | đông kinh | [vi](https://vi.wiktionary.org/wiki/đông_kinh) | "Một phường thuộc thành phố Lạng Sơn" = a ward | place name |
| B15 | 植樹 | thực thụ | [vi](https://vi.wiktionary.org/wiki/thực_thụ) | "Có một chức vụ đã được chính thức hóa" = "holding a confirmed official post" | 實授 |
| B16 | 清流 | thanh lưu | [vi](https://vi.wiktionary.org/wiki/thanh_lưu) | "Một xã thuộc huyện Thanh Liêm, tỉnh Hà Nam" = a commune | place name |
| B17 | 網羅 | võng la | [vi](https://vi.wiktionary.org/wiki/võng_la) | "Một xã thuộc huyện Đông Anh, tp. Hà Nội" = a commune | place name |
| B18 | 越冬 | việt đông | [vi](https://vi.wiktionary.org/wiki/việt_đông) | "Chỉ tỉnh Quảng Đông (Trung Quốc)…" = Guangdong province | 粵東 |
| B19 | 雨季 | vũ quý | [vi](https://vi.wiktionary.org/wiki/vũ_quý) | "Một xã thuộc huyện Kiến Xương, tỉnh Thái Bình" = a commune | place name (rainy season = mùa mưa) |
| B20 | 青色 | thanh sắc | [vi](https://vi.wiktionary.org/wiki/thanh_sắc) | "Âm nhạc và sắc đẹp của phụ nữ" = "music and women's beauty" | 聲色 |
| B21 | 食材 | thực tài | [vi](https://vi.wiktionary.org/wiki/thực_tài) | "Tài năng thực có" = "real talent" | 實才 |
| B22 | 飼主 | tự chủ | [vi](https://vi.wiktionary.org/wiki/tự_chủ) | "Tự điều hành, quản lí mọi công việc của mình…" = "self-governing" | 自主 |
| B23 | 高揚 | cao dương | [vi](https://vi.wiktionary.org/wiki/cao_dương) | "Tên gọi các xã thuộc h. Thanh Oai…" = names of communes | place name |
| B24 | 鮮烈 | tiên liệt | [vi](https://vi.wiktionary.org/wiki/tiên_liệt) | "Người có công trạng ở đời trước đã hy sinh vì việc nước" = "earlier heroes who died for the country" | 先烈 |
| B25 | 観客 | quan khách | [vi](https://vi.wiktionary.org/wiki/quan_khách) | "khách mời đến dự lễ" = "invited guests at a ceremony" | probably 官客 (honoured guests); audience = khán giả. Least certain row |
| B26 | 文教 | văn giáo | [vi](https://vi.wiktionary.org/wiki/văn_giáo) | "Một xã thuộc huyện Tịnh Biên, tỉnh An Giang" = a commune | place name |
| B27 | 新作 | tân tác | [vi](https://vi.wiktionary.org/wiki/tân_tác) | "Một xã thuộc huyện Văn Lãng, tỉnh Lạng Sơn" = a commune | place name |
| B28 | 新規 | tân quy | [vi](https://vi.wiktionary.org/wiki/tân_quy) | "Một phường thuộc quận 7, TP Hồ Chí Minh" = a ward | place name |

B1-B25 are Vietnamese "traps" in the task-2 output; B26-B28 are not traps, but task 2 wrote "a commune name" as their Vietnamese meaning.

## What happens after you confirm

Claude, in its next session (after the task-3 rerun, see HANDOFF):
- **Group A:** one `pipeline/overrides.csv` row per cleared word (`words`, `vi` → empty; reason = this list), rebuild, tests, rebuild identical, D52 tie check, all overrides apply. A word you keep stays as it is (A20 and A36 already have a Vietnamese meaning).
- **Group B:** `overrides.csv` cannot target `ff_candidates.csv` (Stage 3 gate attempt 2, note 4), so each cleared form becomes a `clear_vi` row in `config/task2_review.csv`; Codex 4e then drops its Vietnamese reading and meaning when it adds the form to `words`.
- Codex 4e drops any task-1/task-2 meaning and false-friend entry for a language whose reading is empty after these clears.
