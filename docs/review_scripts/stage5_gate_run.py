"""Stage 5 gate (Claude, 2026-11-12), extended in R1 (2026-11-14, RELEASE_PLAN §4.3).

Runs the real app offline in headless Chrome/Edge: copies ``app/`` alone to a
temporary folder (proves the folder runs standalone), adds
``stage5_gate_harness.js`` to a *copy* of ``index.html`` (``harness.html``),
blocks every network host name, opens the page and prints the harness JSON:
console errors, rendered "undefined"/"NaN"/"null" per view state, failed
checks, counts and a few in-app timings. ``app/`` itself is not changed.

Modes (R1): ``file`` opens ``file://…/harness.html`` (a learner who double-clicks
``app/index.html``); ``http`` serves the copy with Python's ``http.server`` on
``http://127.0.0.1:<port>/`` (a secure context like GitHub Pages' https);
``both`` (default) runs both. The browser is driven over the DevTools protocol
(``tests/app_browser.py``), so script exceptions and ``console.error`` calls are
caught by the browser as well as by the in-page capture.

Usage (repository root):
    python -X utf8 docs/review_scripts/stage5_gate_run.py [--mode file|http|both]
Exit code 1 when any mode reports an error, a failed check or bad text.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))

from app_browser import APP, app_url, browser_page, find_browser, wait_for  # noqa: E402

HARNESS = Path(__file__).with_name("stage5_gate_harness.js")
CAPTURE = (
    "<script>window.__errs=[];window.addEventListener('error',e=>window.__errs.push("
    "String(e.message)+' @'+e.lineno));const __ce=console.error;console.error=(...a)=>"
    "{window.__errs.push('console.error: '+a.join(' '));__ce(...a)};</script>"
)


def harness_page() -> str:
    page = (APP / "index.html").read_text(encoding="utf-8")
    if page.count("<head>") != 1 or page.count("</body>") != 1:
        raise SystemExit("unexpected index.html structure")
    page = page.replace("<head>", "<head>" + CAPTURE, 1)
    return page.replace("</body>", "<script>" + HARNESS.read_text(encoding="utf-8") + "</script></body>", 1)


def run_mode(mode: str) -> dict:
    with app_url(mode, "harness.html", {"harness.html": harness_page()}) as (url, work):
        with browser_page(work) as page:
            page.navigate(url)
            wait_for(page, "document.title==='HARNESS DONE'", timeout=600, interval=0.5)
            text = page.evaluate("document.getElementById('harness-out').textContent")
            result = json.loads(text)
            result["mode"] = mode
            result["url_scheme"] = url.split(":", 1)[0]
            result["browser_errors"] = page.errors
            result["network_failures"] = sorted(set(page.network_failures))
            return result


def failed(result: dict) -> bool:
    return bool(result.get("errors") or result.get("fail") or result.get("bad")
                or result.get("exception") or result.get("browser_errors"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["file", "http", "both"], default="both")
    args = parser.parse_args()
    if find_browser() is None:
        print("Chrome or Edge not found")
        return 2
    modes = ["file", "http"] if args.mode == "both" else [args.mode]
    results = [run_mode(mode) for mode in modes]
    print(json.dumps(results if len(results) > 1 else results[0], ensure_ascii=False, indent=1))
    summary = {r["mode"]: "FAIL" if failed(r) else "PASS" for r in results}
    print("SUMMARY", json.dumps(summary))
    return 1 if any(failed(r) for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
