"""Repeat Stage 3 gate after D53 (Claude, 2026-11-05). Evidence only, not pipeline.

Compares the committed outputs with the Stage 3 PASS build (git commit 7827546):
  1. D52 tie rule: chars.ko / chars.vi primary changes and evidence ties created or broken.
  2. HSK `vi` values that changed although they were non-empty at the baseline (R2).
  3. A2 (`kaikki_en_han`) values that are not literally a 7C value for the word's form (i/y respelling).
  4. `ff_candidates.csv` rows whose form is also in `words` (D47).
  5. VI-only churn: kept / added / dropped, with seeded samples.
Run from anywhere: python docs/review_scripts/stage3_repeat_gate_reference.py [baseline_commit]
"""
import collections
import io
import subprocess
import sys
import unicodedata
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_rows", 400, "display.max_colwidth", 50)
ROOT = Path(__file__).resolve().parents[2]
BASE = sys.argv[1] if len(sys.argv) > 1 else "7827546"
KW = dict(dtype=str, keep_default_na=False, encoding="utf-8")


def new(path):
    return pd.read_csv(ROOT / path, **KW)


def old(path):
    blob = subprocess.run(["git", "-C", str(ROOT), "show", f"{BASE}:{path}"], capture_output=True, check=True).stdout
    return pd.read_csv(io.StringIO(blob.decode("utf-8")), **KW)


def strip_tones(value):
    return "".join(ch for ch in unicodedata.normalize("NFD", value) if unicodedata.category(ch) != "Mn")


nc, oc = new("data/final/chars.csv"), old("data/final/chars.csv")
nw, ow = new("data/final/words.csv"), old("data/final/words.csv")
nwc, owc = new("data/final/word_chars.csv"), old("data/final/word_chars.csv")

# 1. D52 tie rule ----------------------------------------------------------------------------
print("== 1. primary changes against", BASE)
both = oc.merge(nc, on="char_id", how="inner", suffixes=("_o", "_n"), validate="1:1")
for lang in ["ko", "vi"]:
    changed = both[both[f"{lang}_o"] != both[f"{lang}_n"]]
    for row in changed.itertuples():
        print(f"  {lang} {row.trad_n}: {getattr(row, lang + '_o')} -> {getattr(row, lang + '_n')}")
    sets = (both[f"{lang}_all_o"].map(lambda s: frozenset(s.split(";")))
            != both[f"{lang}_all_n"].map(lambda s: frozenset(s.split(";")))).sum()
    print(f"  {lang}_all set differences: {sets}")


def evidence_counts(chars, words, word_chars):
    """Approximation of D39 evidence: words with no alternative candidate."""
    frame = (word_chars.merge(chars[["char_id", "key_char", "ko_all", "vi_all"]], on="char_id", validate="m:1")
             .merge(words[["word_id", "ko_alt", "vi_alt"]], on="word_id", validate="m:1"))
    out = {}
    for lang, col in [("ko", "ko_base"), ("vi", "vi_syllable")]:
        sub = frame[(frame[col] != "") & (frame[f"{lang}_alt"] == "")]
        sub = sub[[b in a.split(";") for b, a in zip(sub[col], sub[f"{lang}_all"])]]
        counts = collections.defaultdict(dict)
        for (key, reading), n in sub.groupby(["key_char", col]).size().items():
            counts[key][reading] = n
        out[lang] = counts
    return out


def top(counts):
    if not counts:
        return ()
    best = max(counts.values())
    return tuple(sorted(k for k, v in counts.items() if v == best))


oe, ne = evidence_counts(oc, ow, owc), evidence_counts(nc, nw, nwc)
print("== 1b. ties created or broken (evidence approximated)")
for lang in ["ko", "vi"]:
    for key in sorted(set(oe[lang]) | set(ne[lang])):
        a, b = oe[lang].get(key, {}), ne[lang].get(key, {})
        if a != b and (len(top(a)) > 1) != (len(top(b)) > 1):
            print(f"  {lang} {key}: {a} -> {b}")

# 2. R2 -----------------------------------------------------------------------------------------
print("== 2. HSK vi non-empty at baseline and different now")
hsk_o, hsk_n = ow[ow.origin != "vi_freq"], nw[nw.origin != "vi_freq"]
m = hsk_o.merge(hsk_n, on="word_id", suffixes=("_o", "_n"), validate="1:1")
print(m[(m.vi_o != "") & (m.vi_o != m.vi_n)][["trad_n", "pinyin_n", "vi_o", "vi_n", "vi_alt_n", "source_vi_n"]].to_string(index=False))

# 3. A2 respelling ------------------------------------------------------------------------------
print("== 3. A2 values that are not a 7C value for trad/simp")
src = collections.defaultdict(set)
for row in new("data/staging/kaikki_en.csv").itertuples():
    src[row.han].add(unicodedata.normalize("NFC", row.vi.strip().lower()))
a2 = nw[nw.source_vi == "kaikki_en_han"].copy()
a2["source_values"] = [";".join(sorted(src.get(t, set()) | src.get(s, set()))) for t, s in zip(a2.trad, a2.simp)]
a2["literal"] = [v in s.split(";") for v, s in zip(a2.vi, a2.source_values)]
respelled = a2[~a2.literal & (a2.source_values != "")]
respelled = respelled[[any(strip_tones(x).replace("y", "i") == strip_tones(v).replace("y", "i") for x in s.split(";"))
                       for v, s in zip(respelled.vi, respelled.source_values)]]
print(f"  A2 words {len(a2)}; respelled i->y {len(respelled)} (HSK {(respelled.origin != 'vi_freq').sum()})")
pairs = collections.Counter()
for row in respelled.itertuples():
    for got, raw in zip(row.vi.split(), row.source_values.split(";")[0].split()):
        if got != raw:
            pairs[strip_tones(raw) + "->" + strip_tones(got)] += 1
print("  ", pairs.most_common())
print(respelled.sample(min(20, len(respelled)), random_state=1)[["trad", "vi", "source_values", "origin", "level"]].to_string(index=False))

# 4. ff_candidates vs words ---------------------------------------------------------------------
print("== 4. ff_candidates rows whose form is in words")
ff = new("data/staging/ff_candidates.csv")
forms = set(nw.trad) | set(nw.simp) | set(nw.jp[nw.jp != ""])
hit = ff[ff.form.isin(forms) | ff.trad.isin(forms)]
print(f"  rows {len(ff)}; in words {len(hit)}; of which VI-only trad {ff.trad.isin(nw[nw.origin == 'vi_freq'].trad).sum()}")

# 5. VI-only churn ------------------------------------------------------------------------------
print("== 5. VI-only churn")
vo_n, vo_o = nw[nw.origin == "vi_freq"], ow[ow.origin == "vi_freq"]
added, dropped = vo_n[~vo_n.word_id.isin(vo_o.word_id)], vo_o[~vo_o.word_id.isin(vo_n.word_id)]
kept = vo_n[vo_n.word_id.isin(vo_o.word_id)]
for name, frame in [("kept", kept), ("added", added), ("dropped", dropped)]:
    print(f"  {name} {len(frame)}: ja_common {(frame.ja_common == 'true').sum()}, levels {frame.level.value_counts().sort_index().to_dict()}, "
          f"source_vi {frame.source_vi.value_counts().to_dict()}")
cols = ["word_id", "trad", "vi", "ko", "ja", "level", "ja_common"]
print("  added sample (seed 55)\n", added.sample(15, random_state=55)[cols].to_string(index=False))
print("  dropped sample (seed 55)\n", dropped.sample(15, random_state=55)[cols].to_string(index=False))
