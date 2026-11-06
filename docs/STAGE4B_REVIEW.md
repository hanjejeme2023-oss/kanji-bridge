# Stage 4b — pilot review (Claude, 2026-11-06)

Inputs: `docs/STAGE4A_REPORT.md` (commit `1a2fdb5`), `content/inputs/pilot/`, `content/generated/pilot/` (Flash) and `content/generated/pilot/argon/` (Argon), `content/cost_log.csv`. Decision: **D60**. No full run was started.

## 1. Frozen data unchanged (user check 1)

- `pipeline/overrides.csv`: byte-identical to `03b3bf9` (MD5 `8c306278…`), **121 rows**. The backup Codex restored left no trace: no `*.bak`/backup file in `pipeline/`.
- `git diff 03b3bf9 -- . ':!content' ':!docs' ':!pipeline/stage4' ':!tests'` (working tree) lists only the two new files `pipeline/requirements-stage4.txt` and `pipeline/stage4_generate.py`. **No file under `data/` differs.**
- `pipeline/id_map.csv` shows as modified, but it is line endings only: CR-stripped MD5 is identical (`3a2c189e…`) for `03b3bf9` and the working tree.

## 2. Cause of the task-1 Vietnamese retries (user check 4)

The three failed attempts (Flash `w09582`, `w00131`; Argon `w01515`) all fail `meaning_ja__vi presence does not match vi`. Two causes:

1. **Field order.** The response schema has no `propertyOrdering`, and Vertex returns properties alphabetically (every saved output starts `confidence, low_reason, meaning_ja__ja, …` and ends `vi_check`). The model therefore writes or omits `meaning_ja__vi` **before** it decides `vi_check`, then decides `vi_check` inconsistently with it.
2. **Prompt gap.** v1 says "Vietnamese only when `vi` is non-empty and it is the same written Han word", which reads as "empty unless certain"; it never says that `unsure` keeps the meaning. The validator requires it for `unsure`.

Fix: `content/prompts/task1_v2.md` (vi_check first, an explicit presence table, `unsure` fills the meaning) + `propertyOrdering` in the task-1 and task-2 schemas (Codex). The validator rule stays as is.

## 3. Flash vs Argon on identical inputs (user check 2)

Identical prompt and input SHA-256 (task 1 `e0d78cd4…`; task 2 identical as well). Counts:

| | Flash | Argon |
|---|---:|---:|
| task 1 `different_word` | 10 | 8 |
| task 1 `meanings_differ=true` | 29 | 22 |
| task 1 `ko_rare` | 2 | 7 |
| task 1 low confidence | 12 | 15 |
| task 1 reasons in Japanese (as the prompt asks) | no (English) | yes |
| task 2 false friends / low | 9 / 0 | 10 / 1 |

23 of 100 task-1 items differ in `vi_check`, `meanings_differ`, `confidence` or Vietnamese meaning presence; 2 of 50 task-2 items differ in `false_friend`. My judgment of those 25:

- **`vi_check` (the D57 Q1 audit; errors here would put wrong clears on the user's short list):** Flash marks **國 quốc** and **茶 trà** (two of the 20 fixed test words) `different_word` because their Kaikki gloss is a given-name sense; Argon keeps both (correct). Flash marks **財源 tài nguyên** `different_word` "= 資源"; the Vietnamese word tài nguyên *is* 財源 with a shifted meaning ("natural resources"), which is what Argon says (a false friend, not a homophone; 資源 would be tư nguyên). Argon alone catches **平價 bình giá**, whose gloss ("to assess prices", co-operatives) is 評價. Score: Argon 4, Flash 0.
- **`meanings_differ`:** Argon is right on 容易 (vi dung dị = "plain, simple"), 的確 (zh "really"), 在家 (ja = lay Buddhist), 上級 (zh/vi = "superiors"), 小姐 (zh slang sense); Flash is right on 民工 (vi = corvée labourer) and arguably 生. Flash's other `true` values come from Vietnamese values it had just discarded (moot). Argon better.
- **`ko_rare` (D49):** both flag the prompt's own examples 小姐 소저 and 老公 노공; only Argon also flags 勉強 면강, 功課 공과, 精英 정영, 回來 회래 (all rare in Korean). Argon's 擋 당 flag is debatable. Argon better.
- **Task 2:** nearly identical. Argon marks 体勢 (CEDICT gloss "feature") low-confidence instead of inventing a Chinese meaning (better). On 手紙 Argon lists `ja` as a trap; Flash does not. But **both** list `ja` for 勉強 and 大丈夫, so this is a prompt problem (§5), not a model difference.
- **Shared weakness:** both mark the single characters 樂 lạc, 試 thí, 塗 đồ `different_word` although lạc, thí, đồ are the correct Hán-Việt readings of those characters (the gloss belongs to a native homophone); this would clear `vi` from the test word 樂. Both also mark 團圓 đoàn viên `different_word` because the gloss is 團員, although Vietnamese đoàn viên also means "reunion" (團圓). Fixed for single characters in task 1 v2 (`unsure`, never `different_word`); 團圓-type cases are what the user's short list (HANDOFF step 6) is for.

**Choice: Argon** for all four tasks (D60). Cost is not the deciding factor (user instruction).

## 4. Ten side-by-side examples (user check 3)

Readings are from the input tables. "F" = Flash, "A" = Argon. Meanings are copied verbatim from the outputs.

**1. 國** — ja こく, ko 국, zh guó, vi quốc (`kaikki_han`). gloss_vi: "Một tên dành cho nam từ tiếng Trung Quốc" (a male given name).
- F: vi_check **different_word** (would clear quốc) | ja 国、国家 | ko 国 | zh 国、国家 | vi —
- A: vi_check **same_word** | ja くに、国家 | ko くに、国家 | zh くに、国家 | vi くに、国家（また男性名）

**2. 財源** — ja ざいげん, ko 재원, zh cáiyuán, vi tài nguyên (`kaikki_han`). gloss_vi: "natural means that become wealth when used" (= natural resources).
- F: **different_word** "= 資源" | ja 財源、財産の出所 | ko 財源 | zh 財源、資金源 | vi —
- A: **same_word**, meanings_differ true | ja 財源、資金の出どころ | ko 財源 | zh 財源、資金源 | vi 天然資源、資源

**3. 平價** — ja へいか, ko 평가, zh píngjià, vi bình giá (`composed_attested`). gloss_vi: "discuss and assess in order to set prices (in former agricultural co-operatives)".
- F: **same_word** | ja 基準となる価格、平価 | ko 適正価格、平価 | zh 手頃な価格の、平価 | vi 協議して価格を定めること
- A: **different_word** "= 評價" | ja 平価、通貨の基準価値・通常の価格 | ko 平価 | zh 手頃な価格、安価、価格を抑える、平価 | vi —

**4. 容易** — ja ようい, ko 용이, zh róngyì, vi dung dị. gloss_vi: "Như bình dị" (= plain, simple).
- F: meanings_differ **false** | ja たやすい、平易 | ko 平易であること、容易 | zh 容易である、平易な、〜しやすい | vi 平易な、素朴な
- A: meanings_differ **true** | ja 容易、たやすいこと | ko 容易、たやすいこと | zh 容易な、簡単な、〜しやすい | vi 平易で親しみやすい、簡素な

**5. 的確** — ja てきかく, ko 적확, zh díquè, vi đích xác. gloss_en "really; indeed", gloss_ja_en "accurate".
- F: meanings_differ **false** | ja 的確、確かであること | ko 的確 | zh 確かに、本当に | vi 正真正銘、確かに
- A: meanings_differ **true** | ja 的確、間違いなく確かなさま | ko 的確、正確で間違いがないこと | zh 確かに、本当に | vi 正確な、事実と完全に一致した

**6. 在家** — ja ざいけ, ko 재가, zh zàijiā, vi tại gia. gloss_ja_en "layperson"; gloss_en "to be at home".
- F: meanings_differ **false** | ja 出家せず世俗にとどまること | ko 在宅、在家 | zh 在宅している、出家しない | vi 自宅にとどまること、在家
- A: meanings_differ **true** | ja 出家せず家庭にあって仏道を修行する人、在家 | ko 在家（出家せず家で仏道を修めること） | zh 家にいる、在宅する、在社している、在家である | vi 在家である（寺に出家せず自宅にいる）

**7. 勉強** — ja べんきょう, ko 면강, zh miǎnqiǎng, vi miễn cưỡng.
- F: confidence high | ja 学問や技芸を学ぶこと | ko 無理に励むこと | zh 無理をする、無理強いする、やっと | vi 無理に、気が進まないまま
- A: confidence **low, ko_rare** | ja 学習、勉強すること | ko 無理に努めること | zh 無理強いする、しぶしぶ行う、かろうじて | vi しぶしぶ行う、無理をしてやる

**8. 精英** — ko 정영, zh jīngyīng, vi tinh anh (no `ja`).
- F: confidence high | ko 精鋭、エリート | zh エリート、精華 | vi 精華、純粋で優れた部分
- A: confidence **low, ko_rare** | ko 精鋭、最も優れた部分 | zh エリート、精鋭、精華、粋 | vi 精髄、最も純粋で優れた部分

**9. 民工** (Flash better) — ja みんこう, zh míngōng, vi dân công (no `ko`). gloss_vi: "citizen doing compulsory manual labour for a set period".
- F: meanings_differ **true** | ja 農村からの出稼ぎ労働者 | zh 農民工、出稼ぎ労働者 | vi 労役に従事する民衆、人夫
- A: meanings_differ **false** | ja （中国の）農村からの出稼ぎ労働者 | zh 農村からの出稼ぎ労働者、公共事業の臨時労働者 | vi 一定期間の肉体労働義務に従事する市民（民工）

**10. 手紙** (task 2) — ja てがみ, zh shǒuzhǐ, vi thủ chỉ (no `ko`).
- F: false_friend **[zh, vi]** | ja 手紙、書簡 | zh★ トイレットペーパー、ちり紙 | vi★ 封建時代の村の頭役・有力者
- A: false_friend **[ja, zh, vi]** | ja★ 書状、レター | zh★ トイレットペーパー | vi★ 封建時代の村の有力者

(★ = `is_trap`.) Not in the ten, also differing: 茶 (like 國), 体勢 (task 2), 小姐, 上級, 生, 結, 外, 樂/團圓/傷口/自制/試/塗 (same `vi_check`, different `meanings_differ`), 擋 and 回來 (Argon `ko_rare`). Full dump: re-run `docs/review_scripts/stage4b_compare.py`.

## 5. Other findings

- **Task 2 trap perspective (both models).** The prototype's `FF` always treats Japanese as safe (勉強, 大丈夫, 手紙 → trap `中`). Both models list `ja` for 勉強 and 大丈夫, and SCHEMA §3.3 would then set `t='ja'`, so the word would appear under neither the 中国語 nor the ベトナム語 filter. Fixed in `task2_v2.md` (baseline Japanese, never a trap; Korean a trap only if common and different, as 工夫 in the prototype) + a validator rule (Codex).
- **Task 3 (Flash).** All tokens valid. Three zh translations leave a sentence untranslated (「行，请试。」「行，加油！」「一会儿回来」); the vi passages are stilted and use literary words to fit the list (nhiên hậu, giáo tài). `task3_v2.md` requires complete translations and natural modern sentences.
- **Task 4 (Flash).** Notes are well-formed and within 80 characters, but the input teaches two data artefacts as facts: **24 differences that are only i/y spellings** (離 li/ly, 理 lý/lí, 期 kỳ/kì, 自己 kỉ/kỷ) and **39 differences against a `unihan_unverified` primary**, mostly Nôm readings (庫 "usually kho", 誓 thề, 冷 lạnh, 豹 beo, 岸 ngàn, 臘 chạp). D24 already bars unverified readings from composition and rule pairs. Builder fix (D60): about 243 of 302 items remain. D59 item 5 (notes use only `vi` values task 1 marked `same_word`) also removes 案件 yên kiện / 奔 hợp-type values once full task 1 exists.
- **Low-confidence items.** All 12 Flash and 15 Argon low items are the `different_word` and `ko_rare` cases above; no other kind.

## 6. Cost (approved)

Spent so far (check + pilot): $0.70. Argon at November prices, from the pilot's measured tokens: tasks 1-2 about $19.5 with one attempt per batch (about $34 if every task-1 batch needed two); tasks 3-4 about $6; v2 re-pilot about $0.5. **Expected about $26-41**, under the $100 ceiling and the $300 credit. The same work at Argon's December price would be about $52-82, so the full run must finish by **2026-11-30** (D60).
