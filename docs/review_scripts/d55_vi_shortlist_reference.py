"""D55 Vietnamese finalization: evidence for docs/VI_SHORTLIST.md (Claude, 2026-11-06). Evidence only, not pipeline.

Reads the committed outputs (git HEAD) and data/staging/kaikki_en.csv, kaikki.csv (a local rebuild).
  1  A/B values that disagree with every A2 (7C) value for the same form (i/y treated as equal, D44)
  2  rule-B (composed_attested) values that 7C files under a different Han form
  6  fresh seeded sample of 50 words with `vi` (seed 20261106)
  +  per-character readings for every listed word, for the reviewer
Run: python docs/review_scripts/d55_vi_shortlist_reference.py > out.txt
"""
import collections
import io
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 300, "display.max_columns", 40, "display.max_rows", 500, "display.max_colwidth", 70)
ROOT = Path(__file__).resolve().parents[2]
KW = dict(dtype=str, keep_default_na=False, encoding="utf-8")


def at(path, commit="HEAD"):
    blob = subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{path}"], capture_output=True, check=True).stdout
    return pd.read_csv(io.StringIO(blob.decode("utf-8")), **KW)


def iy(value):
    """i/y-insensitive key: a syllable-final y after a consonant counts as i."""
    out = []
    for syl in unicodedata.normalize("NFC", value.strip().lower()).split():
        nfd = unicodedata.normalize("NFD", syl)
        nfd = re.sub(r"(?<=[bcdghklmnpqrstvxđ])y(?=[̀-ͯ]*$)", "i", nfd)
        out.append(unicodedata.normalize("NFC", nfd))
    return " ".join(out)


w, c = at("data/final/words.csv"), at("data/final/chars.csv")
k7 = pd.read_csv(ROOT / "data/staging/kaikki_en.csv", **KW)
by_han = collections.defaultdict(list)
by_vi = collections.defaultdict(list)
for r in k7.itertuples():
    if len(r.vi.split()) != len(r.han):
        continue
    by_han[r.han].append(r)
    by_vi[iy(r.vi)].append(r)
cvi = dict(zip(c.trad, c.vi_all))


def chars_of(trad):
    return " ".join(f"{ch}[{cvi.get(ch, '?')}]" for ch in trad)


# 1 ---------------------------------------------------------------------------------------------
print("== 1. A/B vs A2 disagreements")
rows = []
for r in w[w.source_vi.isin(["kaikki_han", "composed_attested"])].itertuples():
    pairs = by_han.get(r.trad, []) + ([] if r.simp == r.trad else by_han.get(r.simp, []))
    if not pairs:
        continue
    a2 = {iy(p.vi) for p in pairs if p.obsolete_only != "true"} or {iy(p.vi) for p in pairs}
    mine = {iy(r.vi)} | {iy(x) for x in r.vi_alt.split(";") if x}
    if not (mine & a2):
        rows.append(dict(word_id=r.word_id, trad=r.trad, pinyin=r.pinyin, level=r.level, origin=r.origin, vi=r.vi,
                         source_vi=r.source_vi, a2=";".join(sorted({p.vi for p in pairs})),
                         a2_gloss=" | ".join(f"{p.vi}: {p.gloss_vi}" for p in pairs)[:160],
                         gloss_vi=r.gloss_vi[:60], chars=chars_of(r.trad)))
print(pd.DataFrame(rows).to_string(index=False))

# 2 ---------------------------------------------------------------------------------------------
print("== 2. rule-B values that 7C files under another Han form")
rows = []
for r in w[w.source_vi == "composed_attested"].itertuples():
    own = {iy(p.vi) for p in by_han.get(r.trad, []) + by_han.get(r.simp, [])}
    other = [p for p in by_vi.get(iy(r.vi), []) if p.han not in (r.trad, r.simp)]
    if other and iy(r.vi) not in own:
        rows.append(dict(word_id=r.word_id, trad=r.trad, pinyin=r.pinyin, level=r.level, origin=r.origin, vi=r.vi,
                         other=";".join(sorted({p.han for p in other})),
                         other_gloss=" | ".join(f"{p.han}: {p.gloss_vi}" for p in other)[:120],
                         gloss_en=r.gloss_en[:50]))
print(pd.DataFrame(rows).to_string(index=False))

# 6 ---------------------------------------------------------------------------------------------
print("== 6. seeded sample of 50 words with vi (seed 20261106)")
s = w[w.vi != ""].sample(50, random_state=20261106).sort_values("word_id")
s["chars"] = s.trad.map(chars_of)
print(s[["word_id", "trad", "pinyin", "level", "origin", "vi", "source_vi", "gloss_en", "gloss_vi", "chars"]]
      .assign(gloss_en=lambda d: d.gloss_en.str[:40], gloss_vi=lambda d: d.gloss_vi.str[:50]).to_string(index=False))
print("source mix:", s.source_vi.value_counts().to_dict(), "origin:", s.origin.value_counts().to_dict())
