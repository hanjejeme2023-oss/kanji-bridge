"""Apply the proposed rule A2 filter to English-Wiktionary pairs, then re-measure.
Usage: python -I filter_measure.py <repo> <outdir>
Rule A2 (proposed): a Kaikki English-Wiktionary Vietnamese entry whose etymology is
`vi-etym-sino` / "Sino-Vietnamese word from <Han>"; Han form = trad (2+ chars: else simp);
syllables = characters; excluded: pos name/romanization, alt-of/abbreviation entries,
given-name/surname glosses. Fills only words whose vi is still empty after A and B.
"""
import csv
import random
import sys
from collections import defaultdict, Counter

sys.stdout.reconfigure(encoding="utf-8")
repo, out = sys.argv[1:3]
TONES = "̣̀́̃̉"


def iy(v):
    """Comparison key only: D44 item 3 i/y variants (kì = kỳ, lí = lý) count as the same word."""
    import re
    import unicodedata
    out_ = []
    for s in v.split():
        d = unicodedata.normalize("NFD", s)
        tones = "".join(c for c in d if c in TONES)
        base = unicodedata.normalize("NFC", "".join(c for c in d if c not in TONES))
        if re.fullmatch(r"[bcdđghklmnpqrstvx]+i", base) and base != "gi":
            base = base[:-1] + "y"
        out_.append(base + "/" + tones)
    return " ".join(out_)

pairs = defaultdict(list)
dropped = Counter()
for r in csv.DictReader(open(f"{out}/enwikt_pairs.csv", encoding="utf-8")):
    tags = set(r["tags"].split(";"))
    g = r["gloss"].lower()
    if r["pos"] in ("name", "romanization"):
        dropped["pos_" + r["pos"]] += 1
        continue
    if tags & {"alt-of", "abbreviation"}:
        dropped["alt_of"] += 1
        continue
    if "given name" in g or "surname" in g:
        dropped["name_gloss"] += 1
        continue
    pairs[r["form"]].append(r)
print("dropped pairs:", dict(dropped))
with open(f"{out}/enwikt_pairs_a2.csv", "w", encoding="utf-8", newline="") as fh:
    rows = [p for v in pairs.values() for p in v]
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

chars = {r["char_id"]: r for r in csv.DictReader(open(f"{repo}/data/final/chars.csv", encoding="utf-8"))}
wc = defaultdict(list)
for r in csv.DictReader(open(f"{repo}/data/final/word_chars.csv", encoding="utf-8")):
    wc[r["word_id"]].append(r)
words = list(csv.DictReader(open(f"{repo}/data/final/words.csv", encoding="utf-8")))
amb = {r["word_id"]: r for r in csv.DictReader(open(f"{repo}/data/final/vi_ambiguous.csv", encoding="utf-8"))}


def char_check(w, vi):
    """every syllable is in the linked chars row's vi_all (verified) -> 'verified';
    in vi_all only when that row is unihan_unverified -> 'unverified'; else 'outside'"""
    rows = sorted(wc[w["word_id"]], key=lambda r: int(r["position"]))
    sy = vi.split()
    status = "verified"
    for r, s in zip(rows, sy):
        c = chars.get(r["char_id"], {})
        allv = {iy(x) for x in c.get("vi_all", "").split(";") if x}
        if iy(s) not in allv:
            return "outside"
        if c.get("source_vi") == "unihan_unverified":
            status = "unverified"
    return status


res = {"hsk": defaultdict(list), "vi_freq": defaultdict(list)}
for w in words:
    scope = "hsk" if w["origin"] in ("hsk", "both") else ("vi_freq" if w["origin"] == "vi_freq" else None)
    if scope is None:
        continue
    forms = [w["trad"]] + ([w["simp"]] if len(w["trad"]) >= 2 and w["simp"] and w["simp"] != w["trad"] else [])
    cands = []
    for f in forms:
        cands = [p for p in pairs.get(f, []) if len(p["vi"].split()) == len(w["trad"])]
        if cands:
            break
    if not cands:
        continue
    vis = sorted({p["vi"] for p in cands}, key=lambda v: (iy(v), not v.split()[-1][-1:] in "yỳýỷỹỵ"))
    keys = sorted({iy(v) for v in vis})
    if w["vi"]:
        known = {iy(w["vi"])} | {iy(x) for x in w["vi_alt"].split(";") if x}
        res[scope]["overlap"].append((w, vis, bool(known & set(keys))))
    elif len(keys) == 1:
        res[scope]["gain"].append((w, vis[0], cands, char_check(w, vis[0])))
    else:
        res[scope]["multi"].append((w, vis))

n_hsk = sum(1 for w in words if w["origin"] in ("hsk", "both"))
have = sum(1 for w in words if w["origin"] in ("hsk", "both") and w["vi"])
for scope in ("hsk", "vi_freq"):
    r = res[scope]
    ov = r["overlap"]
    ag = sum(o[2] for o in ov)
    print(f"== {scope}: overlap {len(ov)}, agree {ag} ({ag / max(1, len(ov)):.2%}); gain {len(r['gain'])}; "
          f"several {len(r['multi'])}")
ov = res["hsk"]["overlap"]
samp = random.Random(36).sample(ov, 200)
print(f"HSK overlap seeded sample (seed 36, n=200): agree {sum(o[2] for o in samp)}")
multi_ov = [o for o in ov if len(o[0]['trad']) >= 2]
print(f"HSK overlap 2+ chars: {len(multi_ov)}, agree {sum(o[2] for o in multi_ov)}")
g = res["hsk"]["gain"]
print(f"HSK gain {len(g)} -> coverage {have + len(g)}/{n_hsk} = {(have + len(g)) / n_hsk:.2%} "
      f"(+{len(g) / n_hsk * 100:.2f} pp); by length {Counter(min(len(x[0]['trad']), 3) for x in g)}")
print("gain char check:", Counter(x[3] for x in g))
print("gain by level:", dict(sorted(Counter(x[0]['level'] for x in g).items())))
print("gain card_eligible already (ja or ko):", sum(1 for x in g if x[0]['ja'] or x[0]['ko']),
      "; all four after gain:", sum(1 for x in g if x[0]['ja'] and x[0]['ko']))
print("gain words that are in vi_ambiguous now:", sum(1 for x in g if x[0]['word_id'] in amb),
      [(x[0]['trad'], x[1], amb[x[0]['word_id']]['reason']) for x in g if x[0]['word_id'] in amb])
tags = Counter()
for x in g:
    t = set(";".join(p["tags"] for p in x[2]).split(";"))
    for k in ("obsolete", "archaic", "rare", "dated", "literary"):
        if k in t:
            tags[k] += 1
print("gain words with usage tags:", dict(tags))
with open(f"{out}/a2_gain.csv", "w", encoding="utf-8", newline="") as fh:
    wr = csv.writer(fh)
    wr.writerow(["word_id", "trad", "pinyin", "level", "new_vi", "char_check", "pos", "tags", "gloss", "etymology"])
    for w, v, c, chk in g:
        wr.writerow([w["word_id"], w["trad"], w["pinyin"], w["level"], v, chk, c[0]["pos"],
                     ";".join(sorted({p["tags"] for p in c} - {""})), c[0]["gloss"], c[0]["ety"][:150]])
spot = random.Random(36).sample(g, 30)
with open(f"{out}/a2_spotcheck30.csv", "w", encoding="utf-8", newline="") as fh:
    wr = csv.writer(fh)
    wr.writerow(["word_id", "trad", "pinyin", "level", "new_vi", "char_check", "pos", "tags", "gloss", "etymology"])
    for w, v, c, chk in sorted(spot, key=lambda x: x[0]["word_id"]):
        wr.writerow([w["word_id"], w["trad"], w["pinyin"], w["level"], v, chk, c[0]["pos"],
                     ";".join(sorted({p["tags"] for p in c} - {""})), c[0]["gloss"], c[0]["ety"][:150]])
test = ["學", "國", "茶", "行", "生", "樂", "經濟", "大學", "勉強", "手紙", "銀行", "發展", "歷史", "博士", "新聞",
        "注意", "主義", "學習", "心理", "越南"]
print("test words:", [(t, sorted({p['vi'] for p in pairs.get(t, [])})) for t in test])
