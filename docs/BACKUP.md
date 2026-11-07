# Backing up the project to a private GitHub repository (D67 item 8)

Checked 2026-11-07: no credential, key or token file is tracked or anywhere in the git history; `.gitignore` excludes `raw/`, staging files, `.env*`, `*credentials*.json`, `*-key.json`, `service-account*.json` and the Stage 4 lock. The repository is about 36 MB; the largest file (`data/final/words.json`) is 11 MB, below GitHub's 100 MB per-file limit. `raw/` is not backed up on purpose: `python pipeline/download.py` recreates it.

## Once

1. In the browser, sign in to github.com → **+** (top right) → **New repository**.
   - Name: `kanji-bridge`. Visibility: **Private**. Do **not** tick "Add a README", ".gitignore" or "license" (the repository must be empty).
   - Click **Create repository** and copy the HTTPS address it shows, e.g. `https://github.com/YOUR-NAME/kanji-bridge.git`.
2. Open PowerShell and run (replace the address):
   ```powershell
   cd "<project folder>"
   git remote add origin https://github.com/YOUR-NAME/kanji-bridge.git
   git push -u origin master
   ```
   The first push opens a browser window (Git Credential Manager) to sign in to GitHub; approve it. No password or token goes into any project file.
3. Check on github.com that the files are there and that the repository shows **Private**.

## After every agent session

```powershell
cd "<project folder>"
git push
```

Agents commit but do not push. Never push while a Stage 4 run is in progress (wait until the launcher has finished).
