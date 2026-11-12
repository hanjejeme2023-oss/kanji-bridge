# Stage 4 task 6: gate review (Claude, 2026-11-12)

Decision **D74**. Design `docs/TASK6_DESIGN.md` (D72), pilot `docs/TASK6_PILOT_REVIEW.md` (D73). Full run by the user overnight 2026-11-12 01:20-10:27 UTC. Scripts: `docs/review_scripts/task6_gate_reference.py` (integrity, diagnosis, pre-screen, extracts), `docs/review_scripts/task6_gate_write.py` (writes the overlay, the rerun list and the user sample). No request was sent by Claude.

## 1. Integrity

| Check | Result |
|---|---|
| Inputs | all 224 committed input batches equal a fresh `build_task6_batches()` |
| Logs | every log's `input_sha256`, `model` (`gemini-4-argon`) and `prompt_sha256` match: zh/vi = v2 prompts (`3e111ced…` / `848d4d90…`), notes = v1 (`4ccdb3e8…`) |
| Re-validation | every stored output re-validates with the current validator (0 errors); for each partial batch the missing keys = the log's `failed_keys` |
| State | zh **85 validated + 42 partial** (56 failed keys), vi **84/84**, notes **13/13**; 11,108 of 11,164 items stored |
| Cost | full run **$16.788226** (636 cost-log rows: 408 repair requests, 5 unbilled transport errors); ledger **$52.46134575**; room under $200: $147.54 |

## 2. The 42 partial zh batches: two validator bugs, not model errors

All 56 failed keys (`failed.tsv` from the reference script) carry one of two messages: `pinyin does not align with the characters` (55) or `pinyin contains an invalid character or notation` (1, 惯例). The runner does **not** store the model's answer for a failed item (only the message), so the last answers cannot be shown; the cause is proven from the validator code and from the 6,287 validated sentences instead.

| Group | Keys | Cause | Evidence |
|---|---:|---|---|
| **A. Missing syllables** | 42 whose target contains 然/燃/染/让/壤/绕/扰 (自然, 当然, 突然, 然后, 让步, 污染, 围绕, 土壤 …) + 13 whose target does not (破坏, 奇妙, 谦虚, 措手不及, 霍乱, 景观, 亲近, 受苦, 停电, 通风, 赞美, 窒息, 让 ff) | `PINYIN_SYLLABLES` (`pipeline/stage4/validators.py:49`) has no **ran, rang, rao** (the r-row is `re ren reng ri rong rou ru rua ruan rui run ruo`). Every sentence containing 然 燃 染 让 壤 嚷 攘 扰 绕 饶 fails alignment, whatever the model writes. The 13 "context" keys most likely used such a character elsewhere in the sentence (让, 然后, 虽然 are very common) | `chars.pinyin_all` syllables not in the inventory: `ran` 然燃染, `rang` 让壤攘嚷, `rao` 扰绕饶挠, `kei` 刻 (`kēi`, colloquial); **0 of 6,287 validated zh sentences contain any of 然 燃 染 让 壤 嚷 攘 扰 绕 饶** |
| **B. No capital tone-marked vowels** | 1 (惯例) + part of the 13 above | `ZH_PINYIN_RE` (`validators.py:39`) allows `A-Za-z` and lower-case `āáǎà…ǜ` only. The prompt says to capitalise the first letter of the sentence and proper nouns, so a sentence starting with 按/爱/安/二/阿/欧/饿/恶 (`Ànzhào guànlì…`) or containing 欧洲 `Ōuzhōu`, 澳大利亚 `Àodàlìyà` is rejected as "invalid character" | **0 of 6,287 validated zh sentences have pinyin starting with a vowel** (the repairs pushed the model away from them) |

**Decision: both are validator bugs (rules too strict by mistake).** Exact fix for Codex: D74 item 1. The model is not at fault, so no prompt change and no `review_feedback`.

**But the failed items still need a request.** Because the failed answers were never stored, fixing the validator cannot turn them into passes offline. After the fix, `-Tasks 6` resumes exactly the 56 failed keys in 42 small repair requests (resume logic exists: same model, prompt and input SHA → only `failed_keys` are sent). Estimate ≈ 42 × $0.006 ≈ **$0.25-0.40**, ≈ 15-20 minutes. The user must not rerun before Codex's fix (it would fail the same way).

Side effect on the 6,287 validated zh items: the bug made the model avoid those characters and vowel-initial sentences in repairs. The sentences that passed are still correct and natural (§3); no rerun is needed for them.

Smaller runner findings (fixed in D74 item 1 too): the log keeps only the last attempt's requests and no answer for failed keys; `rerun_task6()` does not skip already validated rerun batches, so a launcher retry after a partial rerun would regenerate them; the translation check accepts non-Latin foreign scripts (3 translations contain stray Arabic letters, §3).

## 3. Content review (D72 §8)

Read in full: every zh and vi card item at level 1-3, every false-friend item, every note, every `no_sentence`/`low` item, every warning; seeded samples (seed **20261112**) of 150 zh + 150 vi card items at level 4-7 and 100 zh + 100 vi trap card items. Pinyin was also checked by script for **all** 6,287 zh sentences: word-level against `words.pinyin` (392 flags, nearly all segmentation artefacts such as 都+会 or accepted neutral-tone variants such as xuésheng) and syllable-level with tones against `chars.pinyin_all` (11 flags; 绩/迹 jì and 没 mò are correct, the table holds old readings).

**3,934 distinct items read; 48 errors = 1.22%** (+5 pinyin errors found only by the script).

| Kind | Read | Errors | Rate |
|---|---:|---:|---:|
| zh card | 1,392 | 16 | 1.1% |
| zh ff | 564 | 6 | 1.1% |
| vi card | 1,213 | 15 | 1.2% |
| vi ff | 142 | 6 | 4.2% |
| notes | 623 | 5 | 0.8% |

Error classes (53 items in total):
| Class | Items | Action |
|---|---:|---|
| zh pinyin slip outside the target (今年 jīnniān ×4, 气温 qīwēn ×3, 发展 fǎzhǎn, 穿过 chuāngguò, 当天/当晚 dāng-) | 11 | rerun with the correct syllable named |
| zh sentence unnatural or wrong (非常谢谢, 这件事件, 被老师挨了…, 急用 only inside 应急用, 王储's wife called 王妃, …) | 8 | rerun |
| vi forced archaic word, wrong word or wrong sense (trên mã thượng, buổi xuân tiết, đáo để as "sharp-tongued", ngũ giác = pentagon, tẩu tán, cứu cánh, nhân số …) | 16 | 6 rerun, 10 drop (9 of them the model marked `low` itself) |
| Japanese translation wrong or unnatural (3 with stray Arabic letters, 「向かえに行く」, 「十分な資金が不足」, tòa sứ = 公使館 …) | 13 | `set_translation_ja` |
| note wording (切 claims thiết means "cut", garbled 潑, extra reading `cheng` in 盛, …) | 5 | `set_note_ja` |

**No kind reaches 5% and no class is systematic** → no prompt v3; every batch is accepted subject to the 56 resumed keys and rerun round 1 (25 items). Overlay `config/task6_review.csv` (28 rows: 10 `drop`, 13 `set_translation_ja`, 5 `set_note_ja`), rerun list `config/task6_rerun.csv` (round 1, 25 keys: 19 zh, 6 vi, each with `review_feedback`).

### Watch list (D73 item 6)
1. **Forced archaic vi:** rare. `no_sentence` for literary card words 142/831 = 17% (pilot 24% on a literary-heavy sample) and 157/4,193 = 3.7% overall; every `no_sentence` read: all justified (dictionary-only words and calques: điện não, đồ thư quán, tông giáo, tân gia ba …). Forced cases: 13 vi `ok/low` items (9 dropped) plus 6 high-confidence ones (reruns). The model's own `low` flag is a good signal.
2. **Subject words:** written calmly and factually (sát nhân, tử hình, khủng bố, 屠杀, 炸药, 枪, đặc công). None refused for its subject.
3. **Trap evidence:** every trap read (all ff items, level 1-3, 200 trap cards): evident in all but the reruns above (王妃 is a factual error, not a trap failure). cố nhân now "met again after twenty years".
4. **Gloss-copy translations:** not seen as a class (爱人 → 妻). 13 translation fixes are one-offs.
5. **Extra readings in notes:** 2 of 623 (乾 "gān": correct and useful, kept; 盛 "cheng" without tone: fixed). 42 notes are empty by choice (no useful addition), as the prompt allows.

Other observations: single-syllable vi false-friend targets are often met by a compound (cương trực, giao phó, phiền muộn); that is fine where the compound carries the meaning shown and was dropped where it does not (tẩu tán, ngũ giác, cứu cánh). 1,004 zh pinyin strings have a space before punctuation (`chéngshì .`): cosmetic, to be normalised by the app-phase merge (D74 item 5). Data findings for loop 1 (not task 6): `chars.pinyin_all` 绩 jī / 迹 jī are pre-1985 readings (standard jì).

## 4. User sample

`docs/TASK6_USER_SAMPLE.md`: 30 items (12 zh, 12 vi, 6 notes; seed 20261112; items touched by the overlay or rerun excluded). The user judges only the Japanese (○ / △ / ×).

## 5. Next steps and schedule (deadline for every request 2026-11-16 08:00 UTC)

| When | Who | What |
|---|---|---|
| 11-12 | Codex | D74 item 1 (validator + runner fixes, offline, tests); prove no stored output changes state |
| 11-13 morning | User | `-Tasks 6` (resumes the 56 keys, ≈ 20 min, ≈ $0.3) then `-Tasks 6 -RerunRound 1` (25 items, 1-2 requests + repairs, ≈ 5 min, ≈ $0.1); answers `TASK6_USER_SAMPLE.md` any time |
| 11-13 evening | Claude | re-check: read all 81 new answers + user's sample answers; accept; move task 6 to `content/accepted/task6/` |
| 11-14 | User, Claude | spare day: rerun round 2 only if the re-check finds errors; decision point (upgrade) no longer expected to be needed |
| by 11-15 | User | revoke and disable (part H) once Claude has accepted task 6 |

## 6. Re-check (Claude, 2026-11-12, D75): task 6 accepted

The user ran VERTEX_SETUP G7 on 2026-11-12 after Codex's fix (`0ab24a6`): `-Tasks 6` resumed the 56 failed zh keys (all 42 partial batches now validated), then `-Tasks 6 -RerunRound 1` (rerun b001 zh 19/19, b002 vi 6/6, both first attempt). Script `docs/review_scripts/task6_recheck.py` (offline; base commit `0ab24a6`). No request was sent by Claude.

| Check | Result |
|---|---|
| States | zh **127/127**, vi **84/84**, notes **13/13** validated; rerun1 b001/b002 validated |
| Integrity | every log (main + rerun1): model, input SHA = committed input = fresh build, prompt SHA = zh/vi v2, notes v1; every stored output re-validates; rerun inputs = main item + `review_feedback` only; rerun keys = `task6_rerun.csv` round 1 exactly |
| Resume added only the failed keys | for every batch the new keys = the `failed_keys` of the log at `0ab24a6` (56 in total); **no answer stored before changed** |
| Cost | resume + rerun $0.301874 (rerun $0.039168); task 6 total **$17.25865**; ledger **$52.76321975** (ceiling $200) |
| Tone-aware pinyin check (every syllable with its tone mark against `chars.pinyin_all` of the simplified character) | all **81 new answers: 0 toned mismatches** (only ordinary neutral tones: 们 men, 个 ge, 欢 huan …). Full zh set: the same 11 distinct flags as the gate (绩/迹 jì, 没 mò, 刹 chà, 横 hèng, 剥 bāo, 懒洋洋 yāng, 好好 hāo are correct; 年/气/穿 are the rerun items, now fixed) |

**56 resumed answers (read in full): 0 errors.** 42 contain 然/燃/染/让/壤/扰/绕 (the validator gap), 惯例 starts `Ànzhào` (the capital-vowel gap), the 13 "context" items use 让/然后/虽然/自然 elsewhere, as diagnosed. All natural, in the shown meaning, pinyin correct; traps evident (奇妙, 居然, 霍乱 コレラ vs 日射病, 猛然, 漠然 冷淡 vs ぼんやり, 骚扰 迷惑電話, 让 ～させる); Japanese natural.

**25 rerun answers: 24 fix their `review_feedback`, 1 dropped.**
- zh pinyin (11): 今年 jīnnián ×4, 气温 qìwēn ×2 (水管 now avoids 气温), 发展 fāzhǎn, 穿过 chuānguò; 当天/当晚 avoided (温习, 查证 rewritten; 查证 trap vs ビザ evident).
- zh sentences (8): 谢谢你今天来帮我; 我对中国古代的历史很感兴趣; 这么多年过去了，你还认得他吗; 这一事件; 太不讲理、太过分了; 他因为迟到挨了老师一顿批评; 这笔钱你先留着急用; 王妃: 「国王的正妻是王后，地位比王妃更高」. *Correction to the gate:* the gate's feedback "the wife of a crown prince is not a 王妃" was too strict: Chinese also calls a prince's / crown prince's wife 王妃 (戴安娜王妃), which the shown meaning 「皇太子妃」 includes. The new sentence is correct and shows the trap (Japanese 王妃 = the king's wife) better, so it is accepted.
- vi (6): mã thượng → 「tinh thần mã thượng」 (current sense); xuân tiết → `no_sentence` (allowed by the feedback: not used today in that meaning); đáo để → 「khó đáo để」; đường đường → 「đường đường chính chính」; bách tính alone; **thành nhân → 「khán giả đã thành nhân」 is still forced** (today người trưởng thành / trên 18 tuổi; thành nhân lives in lễ thành nhân, học để thành nhân) → **`drop`** in `config/task6_review.csv` (row 29), no round 2: the card simply shows no Vietnamese example, as for `no_sentence`.

**User sample** (`docs/TASK6_USER_SAMPLE.md`): **30/30 ○** (Japanese natural, no problem) → no further Japanese change.

**Decision: task 6 accepted** (224/224 batches + rerun1). Moved with `git mv`/`mv` to `content/accepted/task6/` (`b001-b224.{jsonl,log.json}`, `inputs/b001-b224.jsonl`, `rerun1/`, `inputs/rerun1/`); SHA-256 of all 452 output/log files and 226 input files identical before/after. Overlay `config/task6_review.csv` **29 rows** (11 `drop`, 13 `set_translation_ja`, 5 `set_note_ja`), every `generated` equal to the effective answer (rerun answer where one exists). Merge expectation: **10,367 `examples`** (zh card 5,783, zh ff 560, vi card 3,909, vi ff 115) and **581 `char_notes`**. The 134 non-rebuild tests pass after the move. The pilot (`content/generated/pilot_task6/`) is never merged and stays.

**No further request is needed:** the user revokes the login and disables the API now (VERTEX_SETUP part H). Next: the app phase (`docs/APP_PHASE.md`).
