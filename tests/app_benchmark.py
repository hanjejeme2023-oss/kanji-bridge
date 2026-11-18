"""Benchmark the real ``app/index.html`` in headless Chrome/Edge (R1, RELEASE_PLAN §1.4).

Replaces the old ``tests/stage5_benchmark.py`` (which measured pre-Part-B
adapters). Runs a copy of ``app/`` offline (every host blocked) from
``file://`` or ``http://127.0.0.1`` and measures the same keys as the HANDOFF
"Speed check" console snippet, in the same order:

    load, ff, ffOpen, ffClose, glyphList, glyphAll, glyphQuiz, glyphLevel1, cards

Each key = milliseconds from the click until the browser has laid out the
result (``document.body.offsetHeight``), exactly like the snippet. For views
that finish rendering in idle time, ``<key>Settled`` is the time until the view
stops changing (last DOM mutation), so deferred work is reported, not hidden.
``loadParts`` splits the page load (fetch of ``data.js``, its evaluation, the
data adapters, the first render).

Prints the median of ``--runs`` runs (default 3; a fresh browser profile per
run) as JSON. Does not fail on time (machine load varies) but exits 1 on a
console error or an exception.

Usage (repository root):
    python -X utf8 tests/app_benchmark.py [--mode file|http] [--runs 3]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app_browser import APP, app_url, browser_page, find_browser, wait_for  # noqa: E402

KEYS = ["load", "ff", "ffOpen", "ffClose", "glyphList", "glyphAll", "glyphQuiz", "glyphLevel1", "cards"]

# Instrumented copy: performance marks around the two scripts and the first render.
MARKS = [
    ('<script src="data.js"></script>',
     '<script>performance.mark("kb-data-start")</script><script src="data.js"></script>'
     '<script>performance.mark("kb-data-end")</script>'),
    ("/* ---------- data adapters (Stage 5) ---------- */",
     'performance.mark("kb-adapters-start");/* ---------- data adapters (Stage 5) ---------- */'),
    ("const $=s=>document.querySelector(s);",
     'performance.mark("kb-adapters-end");const $=s=>document.querySelector(s);'),
    ("\nrender();\n</script>",
     '\nperformance.mark("kb-render-start");render();performance.mark("kb-render-end");\n</script>'),
]

SCRIPT = r"""
(async()=>{
const q=s=>document.querySelector(s),nav=v=>q(`#nav button[data-v="${v}"]`).click();
const T=f=>{const t=performance.now();f();void document.body.offsetHeight;return performance.now()-t};
// settle: time until the DOM under the view stops changing (300 ms quiet), incl. layout
const S=(f,root)=>new Promise(resolve=>{let last=null;const t=performance.now();
  const obs=new MutationObserver(()=>{last=performance.now()});obs.observe(q(root),{childList:true,subtree:true,attributes:true});
  f();void document.body.offsetHeight;const sync=performance.now()-t;
  const check=()=>{const now=performance.now(),quiet=now-(last===null?t+sync:last);
    if(quiet>=300){obs.disconnect();void document.body.offsetHeight;resolve({sync,settled:last===null?sync:Math.max(sync,last-t)})}
    else setTimeout(check,50)};setTimeout(check,50)});
const r={},nv=performance.getEntriesByType('navigation')[0];
r.load=nv.loadEventEnd;
const m=n=>{const e=performance.getEntriesByName(n);return e.length?e[0].startTime:null};
const span=(a,b)=>m(a)!==null&&m(b)!==null?m(b)-m(a):null;
const res=performance.getEntriesByType('resource').find(e=>/data\.js$/.test(e.name));
r.loadParts={dataJsFetch:res?res.responseEnd-res.startTime:null,dataJsEval:span('kb-data-start','kb-data-end'),
  adapters:span('kb-adapters-start','kb-adapters-end'),firstRender:span('kb-render-start','kb-render-end'),
  domContentLoaded:nv.domContentLoadedEventEnd};
const step=async(key,f,root)=>{const x=await S(f,root);r[key]=x.sync;r[key+'Settled']=x.settled};
await step('ff',()=>nav('ff'),'#v-ff');
await step('ffOpen',()=>q('#fflist .tile').click(),'#v-ff');
await step('ffClose',()=>q('#fflist .tile').click(),'#v-ff');
await step('glyphNav',()=>nav('glyph'),'#v-glyph');
await step('glyphList',()=>q('#gfilter button[data-p="diff"]').click(),'#v-glyph');
await step('glyphAll',()=>q('#gfilter button[data-p="all"]').click(),'#v-glyph');
await step('glyphQuiz',()=>q('#gmode button[data-g="quiz"]').click(),'#v-glyph');
await step('glyphLevel1',()=>q('#gfilter button[data-p="level-1"]').click(),'#v-glyph');
await S(()=>{q('#gfilter button[data-p="all"]').click();q('#gmode button[data-g="list"]').click()},'#v-glyph');
await step('cards',()=>nav('cards'),'#v-cards');
return r})()
"""


def instrumented_page(source: Path = APP) -> str:
    text = (source / "index.html").read_text(encoding="utf-8")
    for old, new in MARKS:
        if text.count(old) != 1:
            raise SystemExit(f"benchmark mark not found once: {old!r}")
        text = text.replace(old, new, 1)
    return text


def run_once(mode: str, source: Path = APP) -> tuple[dict, list[str]]:
    with app_url(mode, "bench.html", {"bench.html": instrumented_page(source)}, source) as (url, work):
        with browser_page(work) as page:
            page.navigate(url)
            # like the user: wait until the card shows and the page is idle
            wait_for(page, "!!document.querySelector('#cardbox > *')", timeout=120)
            page.evaluate("new Promise(r=>setTimeout(r,1500))")
            result = page.evaluate(SCRIPT)
            return result, page.errors


def median_of(runs: list[dict]) -> dict:
    out: dict = {}
    for key in runs[0]:
        values = [run[key] for run in runs]
        if isinstance(values[0], dict):
            out[key] = median_of(values)
        elif all(isinstance(v, (int, float)) for v in values):
            out[key] = round(statistics.median(values))
        else:
            out[key] = values[0]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["file", "http"], default="file")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--app-dir", type=Path, default=APP,
                        help="folder with index.html + data.js (default app/; e.g. an older version for before/after)")
    args = parser.parse_args()
    if find_browser() is None:
        print("Chrome or Edge not found")
        return 2
    runs, errors = [], []
    for _ in range(args.runs):
        result, errs = run_once(args.mode, args.app_dir)
        runs.append(result)
        errors.extend(errs)
    median = median_of(runs)
    snippet_keys = {key: median[key] for key in KEYS}
    print(json.dumps({"mode": args.mode, "runs": args.runs, "median": snippet_keys,
                      "settled": {k: median[k + "Settled"] for k in KEYS if k + "Settled" in median},
                      "glyphNav": median.get("glyphNav"), "loadParts": median["loadParts"],
                      "errors": errors}, ensure_ascii=False, indent=1))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
