"""Stage 5 gate (Claude, 2026-11-12): run the real app offline in headless Chrome/Edge.

Copies ``app/`` alone to a temporary folder (proves the folder runs standalone),
adds ``stage5_gate_harness.js`` to a *copy* of ``index.html`` (``harness.html``),
blocks every network host, loads the page from ``file://`` and prints the
harness JSON: console errors, rendered "undefined"/"NaN"/"null" per view state,
failed checks, counts and a few in-app timings. ``app/`` itself is not changed.

Usage (repository root):
    python -X utf8 docs/review_scripts/stage5_gate_run.py
Exit code 1 when the harness reports an error, a failed check or bad text.
"""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = Path(__file__).with_name("stage5_gate_harness.js")
BROWSERS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
]
CAPTURE = (
    "<script>window.__errs=[];window.addEventListener('error',e=>window.__errs.push("
    "String(e.message)+' @'+e.lineno));const __ce=console.error;console.error=(...a)=>"
    "{window.__errs.push('console.error: '+a.join(' '));__ce(...a)};</script>"
)


def main() -> int:
    browser = next((path for path in BROWSERS if path.exists()), None)
    if browser is None:
        print("Chrome or Edge not found")
        return 2
    with tempfile.TemporaryDirectory(prefix="kb-stage5-gate-") as tmp:
        work = Path(tmp)
        app = work / "copied" / "app"
        shutil.copytree(ROOT / "app", app)
        page = (app / "index.html").read_text(encoding="utf-8")
        if page.count("<head>") != 1 or page.count("</body>") != 1:
            raise SystemExit("unexpected index.html structure")
        page = page.replace("<head>", "<head>" + CAPTURE, 1)
        page = page.replace("</body>", "<script>" + HARNESS.read_text(encoding="utf-8") + "</script></body>", 1)
        (app / "harness.html").write_text(page, encoding="utf-8")
        command = [
            str(browser), "--headless=new", "--disable-gpu", "--no-first-run",
            f"--user-data-dir={work / 'profile'}",
            "--host-resolver-rules=MAP * ~NOTFOUND",  # offline: no host resolves
            "--virtual-time-budget=20000", "--dump-dom",
            (app / "harness.html").resolve().as_uri(),
        ]
        dom = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=300).stdout
    # last match: the harness source itself mentions the marker in a comment
    matches = re.findall(r'<pre id="harness-out">(.*?)</pre>', dom, re.S)
    match = matches[-1] if matches else None
    if not match:
        print("harness produced no output")
        return 1
    result = json.loads(html.unescape(match))
    print(json.dumps(result, ensure_ascii=False, indent=1))
    bad = result.get("errors") or result.get("fail") or result.get("bad") or result.get("exception")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
