# Vertex AI setup for Stage 4 (for the user)

Why: Stage 4 uses Gemini through **Vertex AI**, because your Free Trial credit ($300, expires **2026-12-28**) does not pay for the Gemini API in AI Studio (DECISIONS D58).

**Login method: Google Cloud CLI sign-in through your browser.** You never create, copy or paste a key. Google's `gcloud` tool keeps the sign-in in your Windows user profile (not in the project folder). The script picks it up automatically, and you can cancel it with one command when Stage 4 is over.

**Never paste anything secret into a chat, a file or a command** (keys, tokens, passwords). Nothing in this guide asks you to.

Time: about 20 minutes, done once.

**Task 6 (2026-11-12 to 11-15): go straight to part G.** Parts A-F were done for tasks 1-5; part F switched everything off afterwards.

---

## Do you have to upgrade the Free Trial to a paid account?

**No, not as far as Google's rules say.** Google's Free Trial page lists only two AI exclusions: the Gemini API in AI Studio, and partner (non-Google) models. Gemini on Vertex AI is not excluded. The first test request (part E) shows whether it really works on your account.

Only if Google refuses that request with a billing or Free-Trial message do you need to upgrade (part E explains how). If you upgrade:
- your unused credit stays and can be used until 2026-12-28;
- any use after the credit runs out or expires is charged to your card. So the budget alert in part B is **required** then, and part F must be done when Stage 4 ends.

Set the budget alert in part B anyway, even without upgrading. It costs nothing.

## Will the credit be enough?

Estimated from the frozen word list (D58):

| Task | Items | Estimate |
|---|---|---|
| 1 Meanings in 4 languages | 8,555 words | about $10-25 |
| 2 False friends | about 5,000 words and candidates | about $5-12 |
| 3 Reading passages | 84 passages | about $2 |
| 4 Notes on other readings | 302 words | under $1 |
| Pilot, retries, reruns | | included |
| **Total** | | **about $20-45** |

That is less than a sixth of $300. The script also has a **hard stop at $100** and will not go past it. A short trial run (the pilot) measures the real cost before the full run, and Claude checks that number.

---

## A. Check your project and credit (5 minutes)

1. Open https://console.cloud.google.com and sign in with the Google account that has the Free Trial.
2. At the top of the page, click the project picker (next to "Google Cloud"). Note the **Project ID** (the ID, not the name; it looks like `kanji-bridge-123456`). If you have no project, click **New project**, name it `kanji-bridge`, create it, and then note its ID.
3. Open the menu (☰) → **Billing**. Check that this project is linked to your Free Trial billing account. If Billing says the project has no billing account, choose **Link a billing account** and pick the Free Trial one.
4. Billing → **Credits**: you should see the Free Trial credit, its remaining amount and **2026-12-28** as the end date.

## B. Set a budget alert (5 minutes)

1. Billing → **Budgets & alerts** → **Create budget**.
2. **Name:** `kanji-bridge Stage 4`.
3. **Scope:** Projects = your project; Services = all.
4. **Credits:** **untick** the box for promotions (the Free Trial credit is a promotion). If it stays ticked, the credit is subtracted first and the alert would always see $0.
5. **Amount:** "Specified amount", **$100**.
6. **Thresholds:** 50%, 90%, 100% (actual spend). Keep "Email alerts to billing admins and users" on.
7. **Finish.**

A budget alert only sends emails. It does not stop spending, which is why the script has its own $100 stop.

## C. Install the Google Cloud CLI and sign in (10 minutes)

1. Download the Windows installer from https://cloud.google.com/sdk/docs/install (`GoogleCloudSDKInstaller.exe`) and run it with the default options. At the end, leave **"Run `gcloud init`"** ticked.
2. **`gcloud init`** opens a terminal and then your browser. Choose your Google account and click **Allow**. Back in the terminal, pick your project ID from part A. If asked about a default region, you can skip it.
3. Open a **new PowerShell window** and run these lines one at a time. Replace `YOUR_PROJECT_ID` with your ID. The project ID is not a secret.
   ```powershell
   gcloud config set project YOUR_PROJECT_ID
   gcloud services enable aiplatform.googleapis.com
   gcloud auth application-default login
   gcloud auth application-default set-quota-project YOUR_PROJECT_ID
   ```
   - The third line opens your browser again: choose the same account and click **Allow**. The terminal then shows "Credentials saved to file: [...application_default_credentials.json]". This is normal. That file is your sign-in. It sits in your Windows profile, not in the project. **Do not move, copy or share it.**
4. Tell the script which project and region to use. These are settings, not secrets:
   ```powershell
   setx GOOGLE_CLOUD_PROJECT "YOUR_PROJECT_ID"
   setx GOOGLE_CLOUD_LOCATION "global"
   setx GOOGLE_GENAI_USE_VERTEXAI "True"
   ```
   Then **close every terminal and restart Codex**, so they see the new settings.
5. Make sure no old AI Studio key is set (it would send requests to AI Studio, which the credit does not pay for):
   ```powershell
   echo $env:GEMINI_API_KEY
   echo $env:GOOGLE_API_KEY
   ```
   Both lines should print nothing. If one prints something, remove it with `[Environment]::SetEnvironmentVariable("GEMINI_API_KEY", $null, "User")` (or `"GOOGLE_API_KEY"`). Do **not** copy what it printed anywhere. If you created a key in AI Studio earlier, delete it there (https://aistudio.google.com → API keys).

## D. Check the price (2 minutes)

Open https://cloud.google.com/vertex-ai/generative-ai/pricing and find **Gemini 3.8 Flash**. Note the price per 1 million **input** tokens and per 1 million **output** tokens. The estimate above assumes $0.75 and $3.75 (Google's rate until 2026-12-31). If the page shows different numbers, tell Codex when you start it. They go into the script's price file.

## E. First test (together with Codex)

Start Codex for Stage 4a as usual. When its script is ready, it runs `--check`: one tiny request that costs a fraction of a cent. What you might see:
- **Success:** model name and a token count. Nothing else to do.
- **A billing or "Free Trial" refusal:** upgrade. Billing → **Overview** → **Activate full account / Upgrade** → confirm. Your remaining credit stays. Make sure part B is done, then ask Codex to run `--check` again.
- **"API not enabled":** repeat the `gcloud services enable` line in C3.
- **"Model not found" for location `global`:** run `setx GOOGLE_CLOUD_LOCATION "us-central1"`, restart the terminals and Codex, and try again.
- **"Could not find default credentials" / "reauthentication needed":** repeat `gcloud auth application-default login`.

## E2. Running the full generation yourself (Stage 4c, D62/D67)

*(Tasks 1-5 are done; for task 6 use part G, which reuses steps 1-3 below.)* You start the long runs, not an agent. Tasks 1-4 are accepted and the launcher now refuses to regenerate them (D65). The remaining sitting is **task 5** (about 1.5-2 hours, about $7-16). Only start it when `docs/HANDOFF.md` says **"Next: User — run `-Tasks 5`"**. It must finish before the **evening of 2026-11-30** (the script refuses Argon requests from 2026-12-01 00:00 UTC, which is 7 pm on 30 November in US Eastern time).

**Before each sitting (2 minutes)**
1. Plug in the charger. Keep the laptop lid **open** (closing it can put the PC to sleep).
2. Settings → **System** → **Power & battery** → **Screen, sleep & hibernate timeouts** → "When plugged in, put my device to sleep after" → **Never**. Remember the old value. (The screen may still turn off; that is fine. The script also asks Windows to stay awake, so this is a second safety.)
3. Settings → **Windows Update** → **Pause updates** (1 week), so Windows does not restart in the middle.

**Start (1 minute)**
4. Open a **new** PowerShell window from the Start menu. Do not use an old window or Codex's terminal: only a new window has the settings from part C4.
5. Type these two lines, pressing Enter after each:
   ```powershell
   cd "<project folder>"
   powershell -ExecutionPolicy Bypass -File pipeline\stage4\run_stage4.ps1 -Tasks 5
   ```
6. Leave the window open. About every 1-2 minutes a line like `task=5 batch=b007 ok ...` appears. At the end the script prints a summary such as `task 5: 104/104 validated, 0 failed`, and the amount spent.

**If something interrupts it** (window closed, PC restarted or asleep, Wi-Fi lost, an error): open a new window and do steps 4-5 again. Batches that are already finished are skipped (`skipped=validated`) and are not paid again; only the one request that was running is lost. Never run two windows at the same time (the script refuses).
- If the error mentions **credentials**, **401**, **reauthentication** or **login**: run `gcloud auth application-default login`, choose your account in the browser, click **Allow**, then step 5 again.
- If the summary still shows **failed** batches after the script's own retries: run step 5 once more. If they fail again, stop and tell Claude or Codex what the last lines say.
- To see progress at any time without sending anything to Google: `powershell -ExecutionPolicy Bypass -File pipeline\stage4\run_stage4.ps1 -Status`

**After each sitting:** set the sleep setting back to its old value, then start Claude ("Read PROMPT.md. You are Claude. …"). You do not need to commit anything; Claude does.

## F. When Stage 4 is finished (Claude will say so)

Run these lines to remove the sign-in and switch off the API, so nothing can use the account by accident:
```powershell
gcloud auth application-default revoke
gcloud services disable aiplatform.googleapis.com
```
If you upgraded to a paid account, also check Billing → **Reports** after 2026-12-28. You can close the billing account if you no longer need Google Cloud.

## G. Task 6: switch Vertex AI back on (from 2026-11-12, D72)

Why: task 6 (example sentences and character notes, `docs/TASK6_DESIGN.md`) needs Gemini again. After Stage 4 you revoked the sign-in and switched the API off (part F), so they must be switched back on first.

**Deadline.** Google wrote that from **2026-11-16** the Free Trial credit no longer pays for Gemini/Vertex unless the account is upgraded. Every request must therefore be sent before **2026-11-15 23:59 US Pacific time = 2026-11-16 08:00 UTC = 2026-11-16 17:00 Japan/Korea time**. From that moment the script refuses to send anything, unless it is started with `-AllowAfterCreditDeadline`. Use that switch **only** if you have upgraded to a paid account and HANDOFF says so.

**G1. Credit and budget (3 minutes).** In https://console.cloud.google.com: Billing → **Credits**: the Free Trial credit is still active and has money left. Billing → **Budgets & alerts** → `kanji-bridge Stage 4` → change the amount from $100 to **$200** (the script's own stop is now $200, D71).

**G2. Sign in and switch the API on (5 minutes).** Open a **new** PowerShell window from the Start menu and run these lines one at a time (replace `YOUR_PROJECT_ID` with your project ID from part A):
```powershell
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable aiplatform.googleapis.com
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```
`gcloud auth login` and `gcloud auth application-default login` each open your browser: choose the same Google account and click **Allow**.

**G3. Check the settings (1 minute).** In the same window:
```powershell
echo $env:GOOGLE_CLOUD_PROJECT
echo $env:GOOGLE_CLOUD_LOCATION
echo $env:GOOGLE_GENAI_USE_VERTEXAI
echo $env:GEMINI_API_KEY
echo $env:GOOGLE_API_KEY
```
The first three lines should print your project ID, `global` and `True`; the last two should print **nothing**. If the first three are empty, repeat part C4 (`setx …`) and open a new window. If one of the last two prints something, remove it as in part C5 and do not copy it anywhere.

**G4. Test request (1 minute; only after HANDOFF says Codex's task-6 support is done):**
```powershell
cd "<project folder>"
powershell -ExecutionPolicy Bypass -File pipeline\stage4\run_stage4.ps1 -Check
```
Success shows the model name and a token count. For errors, see part E.

**G5. Pilot (11-12, about 5 minutes, about $0.40):**
```powershell
powershell -ExecutionPolicy Bypass -File pipeline\stage4\run_stage4.ps1 -Pilot6
```
Three requests (Chinese, Vietnamese, notes). Then start Claude for the pilot review.

**G6. Full run (11-13 morning, only when HANDOFF says "Next: User — run `-Tasks 6`").** Do steps 1-3 of part E2 (charger, sleep "Never", pause updates), then in a new window:
```powershell
cd "<project folder>"
powershell -ExecutionPolicy Bypass -File pipeline\stage4\run_stage4.ps1 -Tasks 6
```
About **6.5-7 hours**, 224 requests: Chinese batches b001-b127 first (about 4 hours), then Vietnamese b128-b211, then notes b212-b224. Lines like `task=6 batch=b007 ok …` appear every 1-2 minutes; a batch may also show `repair` (only the few failing sentences are sent again). If anything interrupts it, run the same two lines again: finished batches are skipped and not paid again. Progress and time left before the deadline, without sending anything: `… run_stage4.ps1 -Status`. When the Chinese batches are done you may start Claude for gate part A while the run continues in its own window.

**G6-night. Running it overnight (D73; the pilot measured about 4.5 hours, allow 6.5).**
*Before you start (5 minutes):*
1. **Charger** plugged in and the plug switched on. Laptop on a hard surface (not a bed), **lid open**.
2. Settings → **System** → **Power & battery** → **Screen, sleep & hibernate timeouts**. For **"When plugged in"**, set **both** "Turn off my screen after" and "Put my device to sleep after" to **Never** (on many laptops a screen that turns off can let the PC drop into standby). Write down the old values. Turn the brightness down instead.
3. Settings → **Windows Update** → **Pause updates** (1 week), so Windows does not restart at night.
4. Close other heavy programs. Do not shut down, sign out, restart, close the lid or press the power button. Leave Wi-Fi on.
*Start:* open a **new** PowerShell window from the Start menu and type:
```powershell
cd "<project folder>"
powershell -ExecutionPolicy Bypass -File pipeline\stage4\run_stage4.ps1 -Tasks 6
```
Wait until the first line `task=6 batch=b001 ok …` appears (about 1-2 minutes). Then leave the window open and go to sleep. The script itself retries API errors and, if it stops, restarts itself up to two more times (2-minute wait).
*In the morning:* look at the last lines of the window.
- **`task 6 zh: 127/127 validated … vi: 84/84 … note: 13/13`** → done. Put the sleep and screen settings back, then start Claude (task-6 gate). You do not commit anything.
- **The summary still shows `failed`, `partial` or `missing` batches**, or the window says `still failed after 3 launcher attempts` → run the same two lines once more (finished batches are skipped and not paid again). If the same batches fail again, stop and start Claude; copy the last 20 lines into the chat (they contain no secret).
- **The window is gone, the PC restarted or was asleep** → open a new window and run the same two lines. Only the request that was running is lost.
- **The error mentions credentials, 401, reauthentication or login** → `gcloud auth application-default login` (browser → same account → Allow), then the two lines again.
- **The error mentions the $200 ceiling or the credit deadline** → stop and start Claude. Do not use `-AllowAfterCreditDeadline`.
- Never run two windows at the same time (the script refuses). To see progress without sending anything: `powershell -ExecutionPolicy Bypass -File pipeline\stage4\run_stage4.ps1 -Status`.
There is time to spare: even if the run has to be restarted tomorrow, it ends long before the deadline (2026-11-16 08:00 UTC).

**G7. Reruns (11-14 / 11-15, only when HANDOFF says so):**
```powershell
powershell -ExecutionPolicy Bypass -File pipeline\stage4\run_stage4.ps1 -Tasks 6 -RerunRound 1
```

**G8. If the script refuses with "credit deadline":** stop and start Claude. Do not use `-AllowAfterCreditDeadline` unless you have upgraded.

## H. After task 6 is accepted (Claude will say so)

```powershell
gcloud auth application-default revoke
gcloud auth revoke --all
gcloud services disable aiplatform.googleapis.com
```
The first line removes the script's sign-in, the second the `gcloud` sign-in from G2, the third switches the API off. A few days after 2026-11-16, check Billing → **Reports** that no Gemini cost appears after that date.

---
Sources (read 2026-11-06): Google Cloud Free Trial page https://docs.cloud.google.com/free/docs/free-cloud-features ("The $300 credit can't pay for Gemini API in AI Studio costs"; remaining credit stays after an upgrade until 90 days from sign-up); Google's Vertex AI model list https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models (Gemini 3.8 Flash generally available); Gemini price table https://aistudio.google.com/docs/pricing (Developer API rates, used for the estimate because the Vertex price page could not be read).
