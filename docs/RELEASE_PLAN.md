# RELEASE PLAN (D78)

Written by Claude on 2026-11-14 for the user's decision of the same day. **The five Stage 6 learner loops are replaced** by: (1) one short pre-release fix pass, (2) a public, non-commercial release, then (3) improvements after release, driven by the user's own study. D78 in `docs/DECISIONS.md` records the decision. This file is the contract for the release. Where it differs from `PROMPT.md` Stage 6 and Final Delivery, this file wins.

No agent sends a Gemini/Vertex request for anything in this plan.

## 0. Order of work

| Step | Who | What | Waits for |
|---|---|---|---|
| R0 | User | Answer the questions in §8 and send the real-browser timings (§1.2). | n/a |
| R1 | Codex | Pre-release fix part (§1) plus the release files in the app and repo (§2.4, §4.3, §5.1). One session, offline, with tests. | R0 |
| R2 | Claude | Release check (a short gate, logged in GATES): R1 evidence, licence files, README, NOTICE, history re-scan (§3.1), Final Delivery items (§5). | R1 |
| R3 | User | Author/history choice (§3.2), make the repository public, switch on Pages (§4.2), first published check. | R2 |
| R4 | User | `VERTEX_SETUP.md` part H on or after **2026-11-16**, then check Billing → Reports a few days later (§7). | date |
| Then | All | Maintenance workflow (§6). | release |

## 1. Pre-release fixes (Codex part R1; with tests)

Scope rule (user, D78): fix only what a **public learner would notice**. Everything else goes to "Known gaps" in the README (§3.3) or to `UX_BACKLOG.md`. Fix at the root (loader, rule, overlay, `overrides.csv` with a reason), never by editing outputs. Every fix gets a test. Global Rules 2 and 10 still apply: no reading from an agent's own knowledge, and no layout change.

### 1.1 使われ方 duplicates of reduplicated words (D77 item 6a)
`build_usage()` in `pipeline/export_app_data.py` lists a reduplicated word once per position (爸爸 twice under 爸; 29 zh + 2 vi `usage` rows), so it uses two of the three example slots. Fix: one entry per `word_id` (first position); the freed slot goes to the next candidate by the existing order. Test: no `usage` row repeats a `word_id`; 爸 shows 爸爸 once; the counts before and after are reported.

### 1.2 Render time of 字体 すべて and 偽の友達 (D77 item 6c)
Headless reference: first 字体 すべて render ≈ 2.8–3.2 s, 偽の友達 tab ≈ 0.9–1.0 s, and every 偽の友達 tile toggle re-renders all 1,242 tiles.
**The user's real-browser numbers have not been received yet** (the request had a blank placeholder). The user runs the console snippet in HANDOFF ("Speed check") and puts the JSON in HANDOFF or `docs/LEARNER_FEEDBACK.md`.
Rule (user, D78): **fix only a measurement above about 1,000 ms** (`glyphAll`, `ff`, or a tile toggle). The fix changes rendering only, with the same DOM, layout, wording and behaviour, for example:
- toggle only the clicked tile instead of rebuilding the list;
- build the list once and re-use it, or render it in chunks (first screen at once, the rest in idle time) with the same final DOM.

Test: the final DOM equals the old renderer's DOM for すべて, a level filter and 間違えた字だけ, and for an open/closed 偽の友達 tile; the new benchmark (§1.4) shows the times before → after.

### 1.3 Known wrong data, fixable at the root without new API requests
| Item | Now | Source evidence (2026-11-14) | Required result |
|---|---|---|---|
| 吧 (w00006, single-character card, level 1) | `words.vi` = **và**, `source_vi` `composed_attested`; `chars.vi` và (`kaikki_aligned`, the only Kaikki reading) | Unihan `kVietnamese` = và only; no licensed source gives the Hán-Việt reading | A Nôm reading is not shown as the card's or 字体's Vietnamese. If no licensed source in `raw/` gives a Hán-Việt reading, **leave it empty** (Rule 2) and keep the item in the known-gaps list. Codex finds which rule let `composed_attested` produce it and fixes that rule, or adds a reasoned `overrides.csv` blank if the case is one-off. |
| 錯 (c00033) | `chars.vi` **thó** (`unihan_unverified`); word 錯 w00056 has empty `vi` | no other source reading | The 字体 row must not show an `unihan_unverified` reading (D76 item 1 already says so for character-only rows). Find why thó still shows (TASK6 pilot note) and fix it. Check the same path for every `unihan_unverified` character and report the count. |
| 怎 | `chars.vi` chẩn (`unihan_hvsyl`), flagged at the Stage 2 gate | no source gives another reading | Report only; no fix (the source agrees). Known gap. |
| 荷 hà, 痕 ngân, 瀾 lan, 蓮 liên | listed in `char_primary_no_evidence.csv` | the character-level readings **are** in Unihan `kVietnamese` (痕, 瀾) or Kaikki (荷, 蓮) | Not wrong data, so nothing changes. Codex marks these four in the report as "character-source evidence present" and does not flag them again. |
| 那邊 (w00262) Korean meaning | `meaning_ja__ko` 「あちら、どのあたり」 (tasks 1 and 2) mixes in the Chinese sense | Stage 4 part-4b review: 나변 = どこ | Review overlay (Claude, D78): **「どこ、どのあたり」** in every table that shows the Korean meaning (`words`, `ff_meanings`). The Chinese trap stays. |
| 器械 (w08625) Korean meaning | `meaning_ja__ko` 「機械、器具」 mixes in the homophone 機械 | Stage 4 part-4b review | Review overlay (Claude, D78): **「器具、器械」**. |

The two meaning corrections use the existing review-overlay route (`config/task2_review.csv` has `meaning_ja_review`; for the task-1 field Codex adds the same route to the task-1 overlay, fail-closed like the others). Codex does not write meaning text. Test: both values appear in `words` and `ff_meanings` and in `data.js`, and the overlay rows are applied exactly once.

Not in R1 (known gaps, §3.3): rule-B compositions that are a different word (人為 nhân vị, 手紙 thủ chỉ); 乾 kiền (can not in `vi_all`); 拖 đà / 拄 chủ; 液體 giá thể and 奔 hợp in `rules_examples.csv` (not reachable in the app); kì/kỳ source spellings; Vietnamese ties (D52); 두음 bases in `word_chars`; weak JMdict variant matches; `vi_alt` extras (調, 馴); VI-only duplicates 複合/復合 and 凶悪/兇惡; 季女 task-1 leftovers; press-register words in passages. Codex may fix any of these only if the fix is a one-line rule change with a test and no effect elsewhere, and must report what it did.

### 1.4 Replace the stale benchmark (D77 item 6b)
`tests/stage5_benchmark.py` measures pre-Part-B adapters. Replace it with a benchmark of the real `app/index.html` in headless Chrome/Edge, with the network blocked, on a copy of `app/`. It measures the same keys as the HANDOFF console snippet (`load, ff, ffOpen, ffClose, glyphList, glyphAll, glyphQuiz, glyphLevel1, cards`) and gives the median of 3 runs. Re-use `docs/review_scripts/stage5_gate_run.py` and its harness, or move them into `tests/`. It prints JSON. It does not fail on time (machine load varies) but does fail on console errors. Delete `.stage5-benchmark/` from the plan and `.gitignore` if nothing uses it any more.

### 1.5 Done when
All of §1.1–1.4 (and §2.4, §4.3, §5.1 below) are done; the full non-rebuild suite and the rebuild-determinism test pass; `stage5_gate_run.py` (or its successor) passes over **file://** and **http://localhost** (§4.3); HANDOFF lists counts before → after.

## 2. Licences for a public, non-commercial release

### 2.1 Per source (checked 2026-11-14 against `licenses/` and `SOURCES.md` §1)
| # | Source | Licence (own file) | Public non-commercial release | Duties |
|---|---|---|---|---|
| 1 | Unihan (Unicode) | Unicode License v3 (`UNICODE-LICENSE.txt`) | Yes | Ship the copyright and permission notice; name Unicode/Unihan. |
| 2 | KANJIDIC2 (EDRDG) | CC BY-SA 4.0 + EDRDG licence (`KANJIDIC2-EDRDG-LICENSE.html`) | Yes, **share-alike** | Acknowledge EDRDG in the docs **and on the website** (general acknowledgement is enough because the data are mixed with other sources). Ship or link the licence. **Keep an update procedure (§2.5).** |
| 5 | JMdict (EDRDG) | same (`JMDICT-EDRDG-LICENSE.html`) | Yes, **share-alike** | as #2 |
| 3 | ivankra/hsk30 | MIT (`HSK30-MIT-LICENSE.txt`) | Yes, **with the provenance risk accepted by the user (§2.3)** | Keep the MIT notice; credit `ivankra/hsk30`; state the upstream HSK 3.0 (PRC Ministry of Education) provenance. |
| 4 | CC-CEDICT | CC BY-SA 4.0 (`CC-CEDICT-LICENSE.html`, `CC-BY-SA-4.0.txt`) | Yes, **share-alike** | Credit CC-CEDICT and MDBG; link the source and licence; say the data were modified. |
| 6 | libhangul `hanja.txt` | BSD 3-Clause file header (`LIBHANGUL-HANJA-BSD-3-CLAUSE.txt`) | Yes | Keep the copyright, three conditions and disclaimer with the source and in the docs. |
| 7A | Kaikki / Vietnamese Wiktionary | CC BY-SA (and GFDL); used under CC BY-SA 4.0 | Yes, **share-alike** | Credit Wiktionary contributors and Kaikki/Wiktextract (Tatu Ylonen); link the source and licence; say the data were modified. |
| 7B | FrequencyWords (vi, OpenSubtitles 2018) | content CC BY-SA 4.0 | Yes, **share-alike** | Credit Hermit Dave / FrequencyWords and OpenSubtitles 2018; say the data were modified. |
| 7C | Kaikki / English Wiktionary (Vietnamese) | as 7A | Yes, **share-alike** | as 7A (English Wiktionary) |
| 8 | OpenCC | Apache 2.0 (`OPENCC-APACHE-2.0-LICENSE.txt`) | Yes | Ship the Apache licence; keep notices; say the tables were inverted and modified. |
| 7, 7D–7J | excluded sources | n/a | **Not used.** Nothing of them is in the repository (Stage 1, D53). | none |

Every used licence allows public redistribution. None is non-commercial-only, so a later commercial use would not be blocked by the dictionaries. It would be blocked only by the hsk30 provenance question and by this release's own choice.

### 2.2 Gemini-generated content (Google Cloud Vertex AI)
Read on 2026-11-14 (web-fetch; the page was too long to read in full, so the Generative AI section comes from an extracted summary, and **§8 Q6 asks to confirm it verbatim before release**): Google Cloud **Service Specific Terms** (dated April 2, 2026 per the summary), Generative AI section, and the **Generative AI Prohibited Use Policy** (last modified 2024-12-17).
- **Ownership:** generated output is treated as Customer Data. Google asserts no ownership rights in new IP in the output. The customer is responsible for the rights needed to use its Customer Data (Section 15, verbatim).
- **Publishing:** no general restriction on publishing or redistributing the output was found. The restriction found (Section 17, per the summary) bars the customer from using output to develop competing models. That binds the user, not people who later reuse the CC BY-SA dataset, and publishing a study dataset is not developing a model. The remaining risk is small, and the user accepts it in D78.
- **Disclosure:** the Use Policy forbids "misrepresenting the provenance of generated content by claiming it was created solely by a human, in order to deceive" (verbatim). The app's about section and the README say which content was generated by AI.
- **Accuracy:** the output may be inaccurate (no warranty). Hence the in-app sentence that it may contain errors.
- **Copyright status:** purely machine-generated text may not carry copyright in some countries. The CC BY-SA licence applies to the dataset to the extent rights exist. The selection, review and arrangement are human work.
- Models (from `content/cost_log.csv`): `gemini-4-argon` (main runs of tasks 1–6) and `gemini-3.8-flash` (pilots and checks). Every accepted batch was reviewed by Claude, and samples by the user (gates in `GATES.md`).

**R2 verbatim re-read (2026-11-17, D79 item 6; supersedes the section numbers above).** The page (https://cloud.google.com/terms/service-terms, "Last modified April 2, 2026") was read in full. The Generative AI section is **§20 "Generative AI Services"**, not 17: §20(a) "'Generated Output' means the data or content generated by a Generative AI Service prompted by Customer Data. Generated Output is Customer Data. As between Customer and Google, Google does not assert any ownership rights in any new intellectual property created in the Generated Output." §20(b) Generative AI Services "may provide inaccurate or offensive Generated Output". §20(c) the Prohibited Use Policy is incorporated into the AUP. **§20(d) "Customer will not, and will not allow End Users to, use a Generative AI Service as part of a website, Customer Application, or other online service that is directed towards or is likely to be accessed by individuals under the age of 18."** §20(e) healthcare; §20(h) storage of prompts/output; §20(i) Google's indemnity for unmodified output of indemnified paid services. **§17** (Use Restrictions for AI/ML Services): (a) not to use a service or Generated Output "to develop a similar or competing product or service"; (b) not to use output to substitute a Google Model or to "create or improve models similar to a Google Model"; (c) no reverse engineering. General **§15** (Customer Data): the customer is responsible for "securing and maintaining all applicable rights required for Customer's use of Customer Data" (it does not mention generated output). No clause restricts publishing or redistributing Generated Output or requires attribution or AI disclosure (the disclosure duty above comes from the Prohibited Use Policy). **Reading:** the published site and dataset contain stored, reviewed output; the site calls no Google service, so it is not "use of a Generative AI Service as part of a website" (§20(d)); a study app is not a product competing with Gemini (§17(a)). The user confirms or overrides this reading in R3 (D79 item 6).

### 2.3 hsk30 provenance risk (user, D78)
D35 accepted the risk of the hsk30 list (MIT grant clear; README says the underlying PRC Ministry of Education list's copyright is questionable/possibly public domain) for **personal** non-commercial use. **D78 extends the user's acceptance to the public, non-commercial release.** The README states the provenance. If a rights holder objects, the remedy is to remove the HSK level/list data from the published dataset (§6.4).

### 2.4 Licences of this project
| Part | Licence | File |
|---|---|---|
| Dataset: `data/final/`, `app/data.js`, `content/` (accepted and generated AI content), `config/` data overlays, `pipeline/id_map.csv`, `pipeline/overrides.csv` | **CC BY-SA 4.0** (required: share-alike sources #2, #4, #5, 7A, 7B, 7C) | `LICENSE-DATA` (pointer + `licenses/CC-BY-SA-4.0.txt`) |
| Code: `pipeline/*.py`, `tests/`, `docs/review_scripts/`, `app/index.html` (code; its data are in `data.js`), `prototype/index.html` | **MIT** (suggested; §8 Q3) | `LICENSE` |
| Documentation: `README.md`, `docs/`, `PROMPT.md` | **CC BY-SA 4.0** (the docs quote sample rows from share-alike sources) | covered by `LICENSE-DATA` |
| Third-party notices | as §2.1 | `NOTICE.md` (Claude, R2) + `licenses/` |

Copyright line in `LICENSE`: "Copyright (c) 2026 <name>". The name depends on §8 Q1.

### 2.5 EDRDG update procedure (licence §4)
EDRDG requires "a procedure for regular updating of the data from the most recent versions available" for any software or web server using the files. It names monthly updates for web dictionary servers. Kanji Bridge is a study app with mixed sources, not a dictionary server, so the plan is a documented, regular procedure (§6.3): `python pipeline/download.py --refresh` for the EDRDG sources (KANJIDIC2, JMdict), rebuild, tests, review the change report, publish. **Cadence: every 3 months, or sooner on a learner report** (§8 Q7; monthly is safer). R1 checks that `--refresh` can be limited to the EDRDG sources (add `--only kanjidic2,jmdict` if needed) and that a refresh changes no `word_id` (word list frozen, D46). Words whose Japanese form or reading changes are listed in a report, for Claude's check.

### 2.6 In-app credits/about section (Global Rule 10 exception approved by the user, D78)
The smallest possible addition. Exactly one small text link 「このアプリについて」 at the foot of the page, in the existing muted style. It opens a plain panel and closes with the same link or Esc, using existing styles only. No other view, control or wording changes. Codex adds it through `pipeline/build_app.py` (the prototype stays byte-unchanged). Text (Claude, static, like `config/rules.json`; the user approves the wording in §8 Q4):

> **このアプリについて**
> 漢字ブリッジは、日本語と韓国語を知っている人が中国語とベトナム語を学ぶための個人の非営利の学習ツール。
> **データ**：Unihan（Unicode, Inc.）、KANJIDIC2・JMdict（EDRDG、CC BY-SA 4.0）、CC-CEDICT（MDBG、CC BY-SA 4.0）、Wiktionary（Kaikki/Wiktextract 経由、CC BY-SA 4.0）、FrequencyWords（OpenSubtitles 2018、CC BY-SA 4.0）、libhangul hanja.txt（BSD-3-Clause）、ivankra/hsk30（MIT）、OpenCC（Apache 2.0）。
> This app uses the JMdict and KANJIDIC2 dictionary files. These files are the property of the Electronic Dictionary Research and Development Group, and are used in conformance with the Group's licence.
> データは CC BY-SA 4.0、プログラムは MIT ライセンスで公開している。詳しくは〔リポジトリへのリンク〕。
> 例文と一部の意味は AI（Google Gemini）が作ったもので、誤りを含むことがある。
> データは集めていない。学習の記録はこのブラウザの中だけに保存される。

The last line is accurate: the app sends nothing. The README adds that the host and Google Fonts receive ordinary web requests (§3.3). The repository link is filled in once §8 Q2 is answered. Offline, the link simply does not open.

## 3. Public GitHub repository (for job hunting)

### 3.1 History scan (Claude, 2026-11-14; repeated in R2 and right before the repository goes public)
61 commits on `master` (= `origin/master`, the private backup `hanjejeme2023-oss/kanji-bridge`); 1,780 tracked files; `.git` ≈ 70 MB (largest file 11 MB, below GitHub's 100 MB limit).
- **Secrets: none found.** No file with a credential-like name was ever added. 0 matches in the whole history for Google API keys (`AIza…`), private-key blocks, OAuth tokens (`ya29.`, `1//0…`), `sk-…`, GitHub tokens, `client_secret`, `refresh_token`, `access_token`, `password=`, bearer headers. The 3 `"private_key"` hits are the test description that checks for that pattern. Stage 4 logs hold model, location `global`, tokens and cost only (no project ID, account or request ID). `gcloud config set project` appears only as `YOUR_PROJECT_ID`.
- **Personal data found:**
  1. Commit author/committer of all 61 commits: the PC's user name with the user's Gmail address (removed for publication, D79); the same address in 32 lines of file text (D19, HANDOFF, docs).
  2. **An earlier personal e-mail address** in the text of D19 in `docs/DECISIONS.md` (present in the current files and in every commit since Stage 0; 4 history lines). Changing the author for future commits does **not** remove it. Only an edit (current files) plus a history rewrite or a fresh repository removes it from history (§3.2).
  3. The Windows profile path `C:\Users\<user name>\…` (R1: replaced by `<project folder>` / `<user folder>` in the docs) in 6 current files (`PROMPT.md`, `docs/BACKUP.md`, `docs/HANDOFF.md`, `docs/HANDOFF_ARCHIVE.md`, `docs/VERTEX_SETUP.md`, `pipeline/stage4/run_stage4.ps1`) and 57 history lines.
  4. The GitHub account name `hanjejeme2023-oss` becomes part of the public URL (§4).
  5. Not personal, kept: Google Cloud cost figures and the Free Trial story (`VERTEX_SETUP.md`, `cost_log.csv`), the user's sample answers (`TASK5/6_USER_SAMPLE.md`), and `jimbreen@gmail.com` (inside the EDRDG licence page, public).

### 3.2 Author and history: options (the user chooses, §8 Q1)
| Option | What it does | Risks / costs |
|---|---|---|
| **A. Keep** | Publish as is. | The Gmail address is public in every commit (GitHub shows it and spammers harvest it), and so is the earlier personal address in D19. The commit name is this PC's user name; employers see that name, not yours. Cheapest. |
| **B. New name/e-mail for future commits only** | `git config user.name "<your name>"`, `git config user.email "<id>+<user>@users.noreply.github.com"`; on GitHub tick *Keep my email addresses private* and *Block command line pushes that expose my email*. Edit D19 and the 6 files to remove the earlier address and the profile path. | The 61 old commits keep both addresses and the old name, readable by anyone in the public history. Commit graph mixes two identities. |
| **C. Rewrite history (recommended if the old addresses must not be public)** | After a backup clone: `git filter-repo` with `--mailmap` (old author → `<your name> <noreply address>`) and `--replace-text` (earlier address and profile path → placeholders). Force-push to `origin` **while it is still private**, then publish. | All 61 commit hashes change. Hashes quoted in the docs (`7351956`, `acba6ca`, …) no longer resolve; filter-repo writes `commit-map` (old → new), which is committed as `docs/COMMIT_MAP.csv`, and the docs keep their old hashes with a note. Needs `pip install git-filter-repo`. Any other clone (e.g. another PC) must be re-cloned. Do it before the repo is public, never after. Claude gives the exact commands in R2 and the user runs them (a destructive step stays with the user). |
| **D. Fresh public repository** | Keep the private repo as the full archive; publish a new repo with one initial commit of the cleaned tree. | Simplest and clean, but the public history of how the agents built it (the `[Claude]`/`[Codex]` commits) is lost. That history is a strong point for job hunting. |

Whatever the option: the current files are cleaned in R1/R2 (D19 text → "the user's earlier address (removed for publication)"; profile path → `<project folder>`), and `user.email` is checked before every commit (D19).

### 3.3 English README (Claude writes it in R2)
Sections: **What it is** (one paragraph; the Sino-Xenic bridge 學 → 학 / がく / xué / học; the five views) · **Screenshots** (one per view, `docs/screenshots/*.png`, taken by Codex in R1 in headless Chrome at 1280×800 from the real app) · **Try it** (the Pages link; or download/clone and double-click `app/index.html`; Chrome or Edge on a PC; progress is stored per browser and per address, so file:// and the website keep separate progress) · **Rebuild the data** (Python 3.12, `pip install -r pipeline/requirements.txt`, `python pipeline/download.py`, `python pipeline/run_all.py`; approx. times) · **Data sources and licences** (§2, from `SOURCES.md`; EDRDG acknowledgement; hsk30 provenance) · **AI-generated content** (which fields, which models, how it was reviewed; may contain errors) · **Privacy** (no data collected; progress in localStorage; GitHub Pages and Google Fonts receive ordinary requests) · **Known gaps** (§1.3 "not in R1" list in plain words, coverage numbers: 12,508 words, card deck 6,983, all-4-languages ceiling; `freq_vi` proxy; `hanja.txt` has no frequency) · **How it was built** (three agents through files: Claude as architect/reviewer, Codex as engineer, Gemini on Vertex AI as batch content generator; gates; `docs/` as the record; cost of generation ≈ $53) · **Licence** (code MIT, data and docs CC BY-SA 4.0) · **Reporting a problem** (§6.1).

## 4. Hosting

### 4.1 Comparison
| | GitHub Pages | Cloudflare Pages |
|---|---|---|
| Account | the same GitHub account as the repository | an extra Cloudflare account + GitHub app permission |
| Publish | GitHub Actions workflow uploads `app/` only, on every push to `master` | Cloudflare builds/uploads on every push |
| URL | `https://hanjejeme2023-oss.github.io/kanji-bridge/` (or the account chosen in §8 Q2) | `https://<name>.pages.dev` |
| https | automatic | automatic |
| Fit | static site of 2 files (6.7 MB); well inside the free limits | also fits; its extra speed and features are not needed |
| Terms | free for public repositories; non-commercial personal project is fine | free plan |

**Recommendation: GitHub Pages**: one account, one place, the published site follows the public repo the employer sees, and nothing new to sign up for. Cloudflare Pages is the fallback if Pages ever fails.

### 4.2 The user's steps (after R2, once the repository is public)
1. github.com → the repository → **Settings** → **General** → bottom "Danger Zone" → **Change visibility** → **Public** (only after §3.2 is done and Claude's R2 re-scan is clean).
2. **Settings** → **Pages** → "Build and deployment" → Source: **GitHub Actions**.
3. In PowerShell: `cd "<project folder>"` then `git push`. The workflow `.github/workflows/pages.yml` (added in R1) runs.
4. **Actions** tab → wait for the green tick of "Deploy app to Pages" (1–2 minutes).
5. Open `https://<account>.github.io/kanji-bridge/` in Chrome or Edge, check that the card shows, then check each tab once and 「このアプリについて」. Press F12 → Console, which should show no red errors.
6. Optional: **Settings** → **General** → Features: keep **Issues** on (for reports, §6.1).

### 4.3 https as well as file:// (Codex, R1)
Checked 2026-11-14: `app/index.html` loads `data.js` by relative `<script src>`, uses `localStorage` and `speechSynthesis`, has no `fetch()`, no `location`/protocol checks and no `http://` links (no mixed content); fonts come from `https://fonts.googleapis.com`. It should work unchanged over https. R1 proves it:
- `.github/workflows/pages.yml`: on push to `master` (and manual run), upload `app/` as the Pages artifact (`actions/upload-pages-artifact` with `path: app`) and deploy (`actions/deploy-pages`); permissions `pages: write`, `id-token: write`; pinned action versions.
- Extend `stage5_gate_run.py` (or its `tests/` successor) with an http mode: serve a copy of `app/` with `python -m http.server` on `127.0.0.1` and run the same harness (localhost is a secure context like https). Both modes: 0 console errors, 0 bad text.
- Note in the README: progress (localStorage) is per origin, so file:// and the website keep separate progress.

## 5. PROMPT Final Delivery: what still applies (D78)

| PROMPT item | Status after D78 |
|---|---|
| 1. Address every open item of the last learner review | No loops ran. Replaced by §1 (fixes) + "Known gaps" (README) + `UX_BACKLOG.md`; every HANDOFF open problem is placed in one of them (Claude, R2). |
| 2. Deliver `app/`, `data/final/`, `pipeline/` with `run_all.py`, `download.py`, **`pipeline/README.md`**, `config/`, `content/accepted/`, `licenses/` | Applies. `pipeline/README.md` does not exist yet → **Codex R1** (§5.1). |
| 3. `README.md`, Data sources section, `LICENSE` files | Applies → Claude R2 (§2.4, §3.3). |
| 4. docs: SCHEMA, DECISIONS, CHANGELOG, HANDOFF, GATES, SOURCES, SOURCE_PROFILES, METRICS, LEARNER_FEEDBACK, UX_BACKLOG, final audit | Applies, except: `METRICS.md` and loop audits do not exist (no loops; D78); the **release check** in GATES replaces the final audit; `LEARNER_FEEDBACK.md` starts as the post-release report log (§6.1). `SOURCES.md` §4 gets the final attribution (Claude R2). |
| 5. Short summary for the user | Applies → Claude R2 report. |
| Stage 6 loop setup (`tests/metrics.py`, METRICS) | **Dropped** (D78). |

### 5.1 R1 also writes
`pipeline/README.md` (what each script does, run order, times, `--skip-download`, `--refresh`); `docs/LEARNER_FEEDBACK.md` with a "Post-release reports" template (date · view · word/char · what looked wrong · expected); `.github/ISSUE_TEMPLATE/problem.md` with the same fields (if §8 Q5 = Issues on); screenshots (§3.3); the about section (§2.6); the Pages workflow and http test (§4.3); `--only` for `download.py` if needed (§2.5).

## 6. Maintenance after release

### 6.1 Reporting
The user (or a visitor, if Issues are on) reports a problem as a GitHub Issue (template fields above) or, offline, as a line in `docs/LEARNER_FEEDBACK.md` "Post-release reports". One problem per line; a screenshot helps.

### 6.2 Fixing
1. **Claude** (triage): reads the new reports, finds the root cause (source, rule, overlay, prompt, app code), classifies data / content / app / UX idea, and writes the assignment in HANDOFF (UX ideas → `UX_BACKLOG.md`; the user decides).
2. **Codex** fixes at the root with a test (PROMPT Stage 6 Step 3 rules still apply: no hand edits of outputs; one-offs in `overrides.csv` with a reason).
3. **Claude** checks: the item itself, the full non-rebuild suite, a rebuild-determinism run if the pipeline changed, `stage5_gate_run.py` in file:// and http modes, Global Rule 10. It logs a short entry in GATES and CHANGELOG.
4. **User** pushes (`git push`). Pages redeploys automatically. Check the site once and close the Issue.
5. Content that needs new Gemini output needs the user's decision first (cost; Vertex is switched off after part H). Until then, a wrong AI meaning is corrected only by a review overlay or removed.

### 6.3 Regular data update (EDRDG, §2.5)
Every 3 months (or as decided in §8 Q7): Codex runs `download.py --refresh --only kanjidic2,jmdict`, rebuilds, runs the tests and writes a change report. Claude checks the changed rows. The user pushes, and the CHANGELOG notes the EDRDG version dates. The other sources are refreshed only by decision (their licences require no updates, and a refresh may move readings).

### 6.4 Take-down
If a rights holder or source asks for removal, Claude records it in DECISIONS and Codex removes the data at the loader level, then it is republished. The hsk30 list is the known risk (§2.3).

## 7. Vertex AI clean-up (user)
On or after **2026-11-16**: `VERTEX_SETUP.md` part H (revoke both logins, disable `aiplatform.googleapis.com`). A few days later, check Billing → **Reports** for any Gemini cost after 11-16. The runner already refuses tasks 1–6. Nothing in this plan needs Vertex.

## 8. Questions the user must answer (R0)
1. **Author and history (§3.2):** A keep / B future only / C rewrite / D fresh repo? With which public name, and the GitHub noreply address? (Claude recommends **C**, done while the repo is still private.)
2. **Public account and URL:** publish under `hanjejeme2023-oss` (URL `hanjejeme2023-oss.github.io/kanji-bridge`) or move the repo to another account first (Settings → Transfer)?
3. **Code licence:** MIT (suggested) or another? Data stays CC BY-SA 4.0 (required).
4. **About-section text (§2.6):** approve as written, or give changes. Also: keep the window title 「漢字ブリッジ（試作版）」 or drop 「（試作版）」 for the release (a wording change, Global Rule 10)?
5. **Issues:** allow public Issues for reports, or only your own `LEARNER_FEEDBACK.md`?
6. **Google terms:** OK to rely on the summary in §2.2? Otherwise Claude re-reads the Generative AI section of the Service Specific Terms verbatim in R2 (no API request; one web page).
7. **EDRDG update cadence:** every 3 months (plan) or monthly?
8. **Speed:** your real-browser JSON from the HANDOFF snippet (the request had a blank placeholder). Without it, R1 uses the headless numbers (`glyphAll` ≈ 3 s → fixed; `ff` ≈ 1 s → fixed only if the new benchmark median is above 1,000 ms).
9. **Repository contents:** publish everything including `content/generated/` (raw and rejected Gemini output), `cost_log.csv` and the Vertex/Free-Trial notes (shows the process; plan default), or leave some out?
