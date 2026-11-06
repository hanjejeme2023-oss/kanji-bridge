"""Extract Sino-Vietnamese word pairs and chữ Hán character readings from the
Kaikki English-Wiktionary Vietnamese JSONL. Scratch measurement only (D36).
Usage: python -I extract_enwikt.py <jsonl> <repo> <outdir>
"""
import collections
import csv
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
jsonl, repo, outdir = sys.argv[1:4]
sys.path.insert(0, repo)
from pipeline.common import normalize_vietnamese, nfc  # noqa: E402

HAN = r"[㐀-䶿一-鿿豈-﫿\U00020000-\U0003ffff]"
HAN_RE = re.compile(f"^{HAN}+$")
ETY_RE = re.compile(f"Sino-Vietnamese word from ({HAN}+)")
CHAR_GLOSS_RE = re.compile(r"^(chữ Hán|Nôm|chữ Nôm) form of (.+?)(?: \(|$)")

pairs = []  # word-level
chars = []  # character-level
gloss_kinds = collections.Counter()
for line in open(jsonl, encoding="utf-8"):
    e = json.loads(line)
    if e.get("lang_code") != "vi":
        continue
    word = e.get("word", "")
    pos = e.get("pos", "")
    senses = e.get("senses", [])
    first_gloss = ""
    tags = set()
    for s in senses:
        tags.update(s.get("tags") or [])
        if not first_gloss and s.get("glosses"):
            first_gloss = s["glosses"][0]
    if pos == "character":
        for s in senses:
            for g in s.get("glosses") or []:
                m = CHAR_GLOSS_RE.match(g)
                if m:
                    gloss_kinds[m.group(1)] += 1
                    for reading in re.split(r",\s*", m.group(2)):
                        chars.append({"char": word, "kind": m.group(1),
                                      "vi": normalize_vietnamese(reading.strip("“”\" "))})
                else:
                    gloss_kinds["other:" + g[:25]] += 1
        continue
    forms = set()
    via = []
    for t in e.get("etymology_templates") or []:
        if t.get("name") == "vi-etym-sino":
            args = t.get("args", {})
            odd = [args[k] for k in sorted((k for k in args if k.isdigit() and int(k) % 2 == 1), key=int)]
            cand = "".join(nfc(x) for x in odd)
            if cand and HAN_RE.match(cand):
                forms.add(cand)
                via.append("vi-etym-sino")
    m = ETY_RE.search(e.get("etymology_text") or "")
    if m:
        forms.add(nfc(m.group(1)))
        via.append("ety_text")
    for f in forms:
        pairs.append({"form": f, "vi": normalize_vietnamese(word), "word_raw": word, "pos": pos,
                      "tags": ";".join(sorted(tags)), "gloss": first_gloss[:120],
                      "via": ";".join(sorted(set(via))),
                      "ety": (e.get("etymology_text") or "")[:200]})

with open(f"{outdir}/enwikt_pairs.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(pairs[0]))
    w.writeheader()
    w.writerows(pairs)
with open(f"{outdir}/enwikt_chars.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["char", "kind", "vi"])
    w.writeheader()
    w.writerows(chars)
print("pairs", len(pairs), "distinct forms", len({p["form"] for p in pairs}))
print("char readings", len(chars), collections.Counter(c["kind"] for c in chars))
print("gloss kinds (top)", gloss_kinds.most_common(12))
