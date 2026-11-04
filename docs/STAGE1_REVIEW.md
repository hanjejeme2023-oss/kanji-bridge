# STAGE 1 REVIEW (Claude, 2026-11-04)

Evidence behind DECISIONS D23–D33. Numbers come from the reference scripts in `docs/review_scripts/` run on the checksum-locked `raw/` files. Those scripts are exploration, not pipeline code; Codex re-implements the rules (with tests) in Stage 2/3.

## 1. Licence confirmations

| Source | Finding | Verdict |
|---|---|---|
| Unicode/Unihan | Unicode License v3 | Use. Keep notice. |
| KANJIDIC2, JMdict | EDRDG: "Creative Commons Attribution-ShareAlike Licence (V4.0)" (checked in the saved licence page) | Use. Share-alike. |
| CC-CEDICT | "CC BY-SA 4.0" (checked) | Use. Share-alike. |
| libhangul `hanja.txt` | The data file's own comment header is BSD 3-Clause (Choe Hwanjin, 2005/2006), identical text to the extracted licence copy. The LGPL-2.1 applies to the library code, not this file. BSD-3 is permissive; a CC BY-SA 4.0 dataset may include BSD-licensed data if the notice and disclaimer are kept. | **Accepted.** Reproduce the BSD notice in README/data licence file. |
| ivankra/hsk30 | MIT (copyright Krasilnikov / Shawky / Pleco). README itself says the data is derived from MIT-labelled repos that copy a PRC Ministry of Education list, and that its copyright status is "somewhat questionable… might be public domain". The content used is a list of words + pinyin + levels (facts and a standard word list). It is the only HSK 3.0 machine-readable source and is the backbone (D2). | **Accepted with recorded risk** (D23); confirmed by the user (D35). |
| Kaikki / Vietnamese Wiktionary | Saved page says "both CC-BY-SA and GFDL", version not stated. Wikimedia projects use CC BY-SA 4.0 for text since 2023; the extract is from a 2026-10 dump. | **Accepted**, used under CC BY-SA 4.0 (the same licence as the dataset). |
| FrequencyWords | README: "MIT License for code. CC-by-sa-4.0 for content." | Accepted for frequency counts, CC BY-SA 4.0. |
| OpenCC | Apache 2.0 | Accepted as mapping data; keep the licence and mark the derived mapping. |
| ryanphung/hanviet-cognates | No licence, missing input provenance | Excluded (D21), unchanged. |

**Share-alike consequence:** every copyleft input is CC BY-SA 4.0 (EDRDG ×2, CC-CEDICT, Kaikki, FrequencyWords); BSD, MIT, Unicode and Apache are permissive. They combine cleanly. `data/final/*` is therefore released under **CC BY-SA 4.0**; app code may carry a separate licence (decided at Final Delivery).

## 2. Vietnamese data

### 2.1 What the two candidates can give
**Kaikki / Vietnamese Wiktionary** (`lang_code=vi`, 44,871 entries). Hán-Việt entries state their Han spelling in the first etymology line, in three forms (Vietnamese text, parsed conservatively):
- `Âm Hán-Việt của chữ Hán <H>.` — single Han form for the headword (3,609 + variants): **explicit word pairs**, 3,366 distinct Han forms with a reading.
- `… của chữ Hán <H1> (“gloss”) và <H2> (“gloss”).` — component characters in syllable order: **character-level pairs**.
- `Âm phi Hán-Việt … (HV: x)` — non-HV reading, ignored as a source of HV readings.
Kaikki's single-character entries (`mul`/`zh`/`unknown`) carry **no** Hán-Việt reading (rendered by templates, not in the extract).
Aligned character readings derived from the explicit pairs: **1,743 characters**.

**FrequencyWords** is a list of 50,000 syllable *tokens* with counts, not words.

### 2.2 Cross-check of 200 Unihan `kVietnamese` readings (seed 20261104, sample of characters having `kVietnamese`)
Tone-mark spelling was normalized to the modern style first (D25); without it 始 `thuỷ` vs `thủy` looks like a conflict.

| Measure | Result |
|---|---|
| Unihan characters with `kVietnamese` | 8,306 (8,655 readings) |
| Sample of 200 covered by Kaikki-aligned readings | 31 (15.5%) |
| …of which Unihan agrees | 29 / 31 (93.5%) |
| Disagreements in the sample | 擴 Unihan `quẳng` vs `khuếch`/`khoáng`; 斥 `xịch` vs `xích` — both are **Nôm/colloquial readings listed by Unihan** |
| Whole overlap (all Unihan∩Kaikki characters) | 1,439 chars; any-reading agreement 1,267 (88.0%); first-reading agreement 1,244 (86.4%) |
| Typical disagreements (whole overlap) | 主 `chúa`/`chủ`, 二 `nhì`/`nhị`, 乳 `vú`/`nhũ`, 例 `lề`/`lệ`, 別 `biết`/`biệt`, 低 `đây`/`đê` |

**Finding:** Unihan `kVietnamese` mixes Hán-Việt and Nôm/colloquial readings, and for common characters (the ones HSK uses) the first listed reading is often the Nôm one. It is usable only with a verification step. The measurable character-level coverage of the licensed cross-check source is 1,743 characters, enough to verify 61% of the HSK character list but not all of it.

### 2.3 Hán-Việt syllable set and verification
A syllable is "attested Hán-Việt" if it is the (normalized) headword syllable of a Kaikki entry whose etymology says `Âm Hán-Việt…` (1,231 distinct syllables). Of the 3,000 HSK characters (first traditional form):
- 1,535 have a Kaikki-aligned reading (**verified**)
- 300 more have a Unihan reading whose syllable is attested Hán-Việt (**plausible**)
- 457 have only Unihan readings that fail the test (**unverified**)
- 708 have no Unihan `kVietnamese`

→ 1,835 / 3,000 (61.2%) HSK characters get a Hán-Việt reading with evidence.

### 2.4 Word-level Vietnamese: coverage and precision of the proposed rule (HSK 3.0, 11,092 rows)
Rule (D24): (A) explicit Kaikki Han-form pair; else (B) the single combination of per-character readings (kaikki-aligned, or Unihan ∩ attested-HV syllables) that is also a Kaikki Vietnamese headword; if more than one combination exists, leave empty and report.

| Measure | Result |
|---|---|
| Rows resolved | 3,832 (34.6%); ambiguous (≥2 candidates, left empty) 98 |
| By HSK level | L1 44%, L2 46%, L3 58%, L4 44%, L5 41%, L6 38%, L7–9 24% |
| By word length | 1 char 59%, 2 chars 34%, 3–4 chars ≈ 3–4% |
| Precision of B against A, where both exist | 1,723 / 1,724 agree (the one difference: 惡 `ác` vs `ác tâm`, a Kaikki entry-form artefact) |
| Spot check, 30 random B-only words | all plausible Hán-Việt compounds (e.g. 管理 quản lý, 例外 lệ ngoại, 情報 tình báo, 會診 hội chẩn); B is a Hán-Việt *form* match, meaning is checked in Stage 4/loop audits |
| Known weakness | Compounds that Vietnamese does not use as Hán-Việt but happen to exist as an unrelated headword. Gemini's per-language meanings and loop audits catch these; `source_vi` marks the rule used |

**Ceiling:** with the licensed sources available, about 35% of HSK words get a Vietnamese reading. HSK words with all 4 languages will be below that. This is a measured source ceiling (METRICS "report the ceiling"), not a pipeline defect. A further licensed Vietnamese source will be searched after Stage 3 and before Stage 4 (D36, user decision); it is not a Stage 2/3 blocker.

### 2.5 FrequencyWords
50,000 tokens, 2,589 duplicate tokens (case/orthography variants; sum after normalization). Compounds have no rank. Proxy rule in D26.

## 3. Shinjitai ↔ traditional (D28)

- OpenCC `JPShinjitaiCharacters.txt` is keyed by the Japanese form, values are the old/Chinese forms. Inverting it gives trad → jp.
- Result on the 16 character pairs in the prototype's own GLYPHS (the approved ground truth): **16 / 16** (經→経 發→発 氣→気 樂→楽 歷→歴 實→実 賣→売 讀→読 廣→広 對→対 學→学 國→国 會→会, 電 話 語 unchanged).
- On the 3,000 HSK characters: 304 change form; 6 traditional characters have two candidate shinjitai: 畫→画/畵, 鬥→闘/鬪, 鹽→塩/䀋, 鋪→舗/舖, 莊→荘/庄, 驅→駆/駈.
- Unihan variants are Chinese simplification (經→经, not 経) so they cannot do this job; KANJIDIC2 variants are cross-reference codes. Both rejected as primary methods; KANJIDIC2 is used to *validate* candidates (jp must be a KANJIDIC2 literal) and to break ties.
- 45 HSK traditional characters are neither in KANJIDIC2 nor in the OpenCC map (e.g. 娛, 腳, 啟, 夠): they stay without a Japanese form and are reported (`no_jp_form`).
- The OpenCC file contains a comment line `# Format: key value(s)…` which a loader must skip.

## 4. hsk30 facts confirmed
- `hsk30-chars.csv`: 3,000 characters, per-character `Level` (1–6: 300 each; "7-9": 1,200). Used for `chars.level` (D29).
- `hsk30.csv` has a `CEDICT` column giving matching CC-CEDICT keys (`trad|simp[pin1yin1]`), so the CC-CEDICT join does not need to be guessed. 11,092 rows, duplicate `ID`: 0.
- 29 characters in the list are outside the word list.
