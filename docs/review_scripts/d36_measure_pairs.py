"""Measure a candidate word-pair file (form, vi, ...) against data/final/words.csv.
Usage: python -I measure_words.py <repo> <pairs.csv> <outdir> <label>
Pairs need columns: form, vi (D25-normalized); other columns are kept as evidence.
"""
import csv
import re
import random
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
repo, pairs_path, outdir, label = sys.argv[1:5]
SEED = 36


def iy(v):
    # comparison key only: D44 item 3 i/y variants (kì = kỳ, lí = lý, mĩ = mỹ) count as the same word
    import unicodedata
    out = []
    for s in v.split():
        d = unicodedata.normalize("NFD", s)
        tones = "".join(c for c in d if c in "̣̀́̃̉")
        base = unicodedata.normalize("NFC", "".join(c for c in d if c not in "̣̀́̃̉"))
        if re.fullmatch(r"[bcdđghklmnpqrstvx]+i", base) and base != "gi":
            base = base[:-1] + "y"
        out.append(base + "/" + tones)
    return " ".join(out)


pairs = defaultdict(list)
for r in csv.DictReader(open(pairs_path, encoding="utf-8")):
    pairs[r["form"]].append(r)

words = list(csv.DictReader(open(f"{repo}/data/final/words.csv", encoding="utf-8")))
hsk = [w for w in words if w["origin"] in ("hsk", "both")]
n_hsk = len(hsk)
have = sum(1 for w in hsk if w["vi"])

overlap, gain, gain_multi, no_hit = [], [], [], 0
for w in hsk:
    forms = [w["trad"]] + ([w["simp"]] if len(w["trad"]) >= 2 and w["simp"] and w["simp"] != w["trad"] else [])
    cands = []
    for f in forms:
        cands = [p for p in pairs.get(f, []) if len(p["vi"].split()) == len(w["trad"])]
        if cands:
            break
    if not cands:
        no_hit += 1
        continue
    vis = sorted({iy(p["vi"]) for p in cands})
    if w["vi"]:
        known = {iy(w["vi"])} | {iy(x) for x in w["vi_alt"].split(";") if x}
        overlap.append((w, vis, cands, bool(known & set(vis)), iy(w["vi"]) in vis))
    elif len(vis) == 1:
        gain.append((w, vis[0], cands))
    else:
        gain_multi.append((w, vis, cands))

agree_any = sum(o[3] for o in overlap)
agree_primary = sum(o[4] for o in overlap)
rng = random.Random(SEED)
sample = rng.sample(overlap, min(200, len(overlap)))
s_agree = sum(o[3] for o in sample)
print(f"[{label}] HSK words {n_hsk}; with vi now {have} ({have / n_hsk:.2%})")
print(f"overlap (existing vi and candidate): {len(overlap)}; agree (vi or vi_alt in cands) {agree_any} "
      f"({agree_any / max(1, len(overlap)):.2%}); primary in cands {agree_primary}")
print(f"seeded sample (seed {SEED}, n={len(sample)}): agree {s_agree} ({s_agree / max(1, len(sample)):.2%})")
print(f"gain (empty vi -> exactly one candidate): {len(gain)}; several candidates: {len(gain_multi)}")
print(f"new coverage if single-candidate gains are taken: {have + len(gain)} ({(have + len(gain)) / n_hsk:.2%}, "
      f"+{len(gain) / n_hsk * 100:.2f} pp)")
tagcount = defaultdict(int)
for w, v, c in gain:
    t = set(";".join(p.get("tags", "") for p in c).split(";")) - {""}
    for k in ("obsolete", "archaic", "rare", "dated", "literary"):
        if k in t:
            tagcount[k] += 1
print("gain words whose entry carries tags:", dict(tagcount))
levels = defaultdict(int)
for w, v, c in gain:
    levels[w["level"]] += 1
print("gain by level:", dict(sorted(levels.items())))

with open(f"{outdir}/{label}_disagree.csv", "w", encoding="utf-8", newline="") as fh:
    wr = csv.writer(fh)
    wr.writerow(["word_id", "trad", "pinyin", "vi_now", "source_vi", "vi_alt", "candidates", "evidence"])
    for w, vis, c, a, p in overlap:
        if not a:
            wr.writerow([w["word_id"], w["trad"], w["pinyin"], w["vi"], w["source_vi"], w["vi_alt"], ";".join(vis),
                         " | ".join((x.get("gloss", "") + " [" + x.get("tags", "") + "]") for x in c)[:300]])
with open(f"{outdir}/{label}_gain.csv", "w", encoding="utf-8", newline="") as fh:
    wr = csv.writer(fh)
    wr.writerow(["word_id", "trad", "pinyin", "level", "new_vi", "tags", "gloss", "evidence"])
    for w, v, c in gain:
        wr.writerow([w["word_id"], w["trad"], w["pinyin"], w["level"], v,
                     ";".join(sorted({p.get("tags", "") for p in c} - {""})),
                     c[0].get("gloss", ""), c[0].get("ety", c[0].get("evidence", ""))[:160]])
spot = random.Random(SEED).sample(gain, min(30, len(gain)))
with open(f"{outdir}/{label}_spotcheck30.csv", "w", encoding="utf-8", newline="") as fh:
    wr = csv.writer(fh)
    wr.writerow(["word_id", "trad", "pinyin", "level", "new_vi", "tags", "gloss", "evidence"])
    for w, v, c in spot:
        wr.writerow([w["word_id"], w["trad"], w["pinyin"], w["level"], v,
                     ";".join(sorted({p.get("tags", "") for p in c} - {""})),
                     c[0].get("gloss", ""), c[0].get("ety", c[0].get("evidence", ""))[:160]])
