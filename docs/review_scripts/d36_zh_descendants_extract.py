"""Stream the Kaikki English-Wiktionary Chinese JSONL from stdin and keep Vietnamese
descendants (Sino-Xenic) of Chinese words. Usage: curl ... | python -I extract_zh_desc.py <repo> <out.csv>"""
import csv
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
repo, out = sys.argv[1:3]
sys.path.insert(0, repo)
from pipeline.common import normalize_vietnamese, nfc  # noqa: E402

HAN_RE = re.compile(r"^[㐀-䶿一-鿿豈-﫿\U00020000-\U0003ffff]+$")
rows = []
n = 0


def walk(descs, form, path):
    for d in descs or []:
        if d.get("lang_code") == "vi" and d.get("word"):
            rows.append({"form": form, "vi": normalize_vietnamese(d["word"]), "word_raw": d["word"],
                         "tags": ";".join(d.get("tags") or []), "raw_tags": ";".join(d.get("raw_tags") or []),
                         "path": path})
        walk(d.get("descendants"), form, path + ">" + (d.get("lang_code") or "?"))


for line in sys.stdin.buffer:
    n += 1
    e = json.loads(line)
    if e.get("lang_code") != "zh":
        continue
    form = nfc(e.get("word", ""))
    if not HAN_RE.match(form):
        continue
    walk(e.get("descendants"), form, "zh")
with open(out, "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["form", "vi", "word_raw", "tags", "raw_tags", "path"])
    w.writeheader()
    w.writerows(rows)
print("lines", n, "vi descendant rows", len(rows), "forms", len({r["form"] for r in rows}))
