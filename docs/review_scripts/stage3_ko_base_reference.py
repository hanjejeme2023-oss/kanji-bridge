import sys, collections
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250, "display.max_columns", 60, "display.max_rows", 800, "display.max_colwidth", 70)
from pathlib import Path
R = str(Path(__file__).resolve().parents[2])
rd = lambda p: pd.read_csv(f"{R}/{p}", encoding="utf-8", keep_default_na=False, dtype=str)
w = rd("data/final/words.csv"); c = rd("data/final/chars.csv"); wc = rd("data/final/word_chars.csv")
m = wc.merge(c[["char_id", "key_char", "ko", "ko_all"]], how="left", on="char_id", validate="m:1").merge(w[["word_id", "trad", "ko", "ko_alt", "source_ko"]].rename(columns={"trad": "wtrad", "ko": "wko", "ko_alt":"wko_alt"}), how="left", on="word_id", validate="m:1")
for ch in ["旅", "流", "老", "歷", "連", "領", "輯", "嫦", "異"]:
    s = m[m.key_char == ch]
    print(ch, "ko", s.ko.iloc[0], "all", s.ko_all.iloc[0])
    print("  by (position1?, syl, base):", s[s.ko_syllable != ""].groupby([s.position == "1", "ko_syllable", "ko_base"]).size().to_dict())
    print("  sample", s[s.ko_syllable != ""][["wtrad", "wko", "wko_alt", "ko_syllable", "ko_base"]].head(5).values.tolist())

# Independent recomputation of the D39 mapping, ko
CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
IOT = {2, 3, 6, 7, 12, 17, 20}  # ㅑㅒㅕㅖㅛㅠㅣ (ㅑ=2,ㅒ=3,ㅕ=6,ㅖ=7,ㅛ=12,ㅠ=17,ㅣ=20)
def parts(s):
    o = ord(s) - 0xAC00
    return o // 588, (o % 588) // 28, o % 28
def compose(i, v, f): return chr(0xAC00 + i * 588 + v * 28 + f)
N, R_, O = 2, 5, 11
def base_at1(s, allv):
    i, v, f = parts(s)
    if i == O and v in IOT:
        for ci in (R_, N):
            b = compose(ci, v, f)
            if b in allv: return b
    if i == N and v not in IOT:
        b = compose(R_, v, f)
        if b in allv: return b
    return s
def base_later(s, prev, allv):
    i, v, f = parts(s)
    pf = parts(prev)[2] if prev else None
    if s in ("열", "율") and (pf == 0 or pf == 4):
        b = "렬" if s == "열" else "률"
        if b in allv: return b
    return s
wc2 = m[m.ko_syllable != ""].copy()
wc2["pos"] = wc2.position.astype(int)
wc2 = wc2.sort_values(["word_id", "pos"])
prev = wc2.groupby("word_id").ko_syllable.shift(1).fillna("")
bases = []
for r, p in zip(wc2.itertuples(), prev):
    allv = set(r.ko_all.split(";"))
    if r.ko_syllable in ("숫", "찻") or (r.ko_syllable == "란" and r.wtrad == "困難"):
        bases.append(r.ko_base); continue
    bases.append(base_at1(r.ko_syllable, allv) if r.pos == 1 else base_later(r.ko_syllable, p, allv))
wc2["my_base"] = bases
diff = wc2[wc2.my_base != wc2.ko_base]
print("\nko_base differs from independent D39 calc:", len(diff), "rows;", diff.key_char.nunique(), "chars")
print(diff.groupby(["key_char", "ko_syllable", "ko_base", "my_base"]).size().sort_values(ascending=False).head(50).to_string())

# Evidence definition: words with no ko_alt (one candidate) or single char with no alt
ev = wc2[wc2.wko_alt == ""]
cnt = ev.groupby(["key_char", "my_base"]).size().rename("n").reset_index()
out = []
for r in c.itertuples():
    s = cnt[cnt.key_char == r.key_char]
    allv = r.ko_all.split(";")
    s = s[s.my_base.isin(allv)]
    if s.empty: continue
    top = s.n.max(); tops = s[s.n == top].my_base.tolist()
    out.append((r.key_char, r.ko, sorted(tops, key=lambda x: allv.index(x))[0] if True else None, top, tops))
o = pd.DataFrame(out, columns=["key_char", "built", "recalc", "top", "tops"])
d = o[o.built != o.recalc]
print("\nprimary differs from independent D39 (evidence=no ko_alt):", len(d))
print(d.to_string())
print(c[c.key_char.isin(d.key_char)].level.value_counts().sort_index().to_dict())
