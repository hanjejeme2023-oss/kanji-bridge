"""Repeat Stage 3 gate after D53, attempt 2 (Claude, 2026-11-06). Evidence only, not pipeline.

Reads committed outputs from git (default HEAD), compares with the attempt-1 build (0d581fa) and the
Stage 3 PASS build (7827546). Needs data/staging/kaikki_en.csv from a local rebuild (7C pairs).
  G1  A2 spelling: every kaikki_en_han value = 7C value with only the D56 h/k/l/m/t + i -> y change;
      no invented consonant+y syllable in words.vi / ff_candidates.vi outside rule A/B values.
  G2  ff_candidates rows whose form/trad/simp is in words (trad, simp, jp).
  G3  VI-only churn against 0d581fa; bands; ID reuse.
  R2  HSK vi non-empty at 7827546 and different now.
  R5  chars.ko / chars.vi primary changes and evidence ties against 0d581fa.
  R6  every overrides.csv row equals the output value.
Run: python docs/review_scripts/stage3_repeat_gate_attempt2_reference.py [head] [prev] [base]
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
pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_rows", 400, "display.max_colwidth", 60)
ROOT = Path(__file__).resolve().parents[2]
HEAD, PREV, BASE = (sys.argv[1:4] + ["HEAD", "0d581fa", "7827546"][len(sys.argv[1:4]):])
KW = dict(dtype=str, keep_default_na=False, encoding="utf-8")


def at(commit, path):
    blob = subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{path}"], capture_output=True, check=True).stdout
    return pd.read_csv(io.StringIO(blob.decode("utf-8")), **KW)


def strip_tones(value):
    return "".join(ch for ch in unicodedata.normalize("NFD", value) if unicodedata.category(ch) != "Mn")


def a2_spell(value):
    """D56 item 2, written independently of the pipeline."""
    out = []
    for syl in value.split():
        base = strip_tones(syl).replace("đ", "d")
        if re.fullmatch(r"[hklmt]i", base):
            nfd = unicodedata.normalize("NFD", syl)
            nfd = nfd.replace("i", "y", 1)
            syl = unicodedata.normalize("NFC", nfd)
        out.append(syl)
    return " ".join(out)


nw, pw, bw = (at(c, "data/final/words.csv") for c in (HEAD, PREV, BASE))
nc, pc = at(HEAD, "data/final/chars.csv"), at(PREV, "data/final/chars.csv")
nwc, pwc = at(HEAD, "data/final/word_chars.csv"), at(PREV, "data/final/word_chars.csv")
ff, pff = at(HEAD, "data/staging/ff_candidates.csv"), at(PREV, "data/staging/ff_candidates.csv")
idn, idp = at(HEAD, "pipeline/id_map.csv"), at(PREV, "pipeline/id_map.csv")
ov = at(HEAD, "pipeline/overrides.csv")

# G1 --------------------------------------------------------------------------------------------
print("== G1 A2 spelling")
src = collections.defaultdict(set)
k7 = pd.read_csv(ROOT / "data/staging/kaikki_en.csv", **KW)
for row in k7.itertuples():
    if str(getattr(row, "obsolete_only", "")).lower() != "true":
        src[row.han].add(unicodedata.normalize("NFC", row.vi.strip().lower()))
a2 = nw[nw.source_vi == "kaikki_en_han"].copy()
a2["src"] = [sorted(src.get(t, set()) | src.get(s, set())) for t, s in zip(a2.trad, a2.simp)]
a2["ok"] = [v in {a2_spell(x) for x in s} for v, s in zip(a2.vi, a2.src)]
a2["nosrc"] = [not s for s in a2.src]
print(f"  A2 words {len(a2)} (HSK {(a2.origin != 'vi_freq').sum()}); equal to a2_spell(7C): {a2.ok.sum()}; "
      f"no 7C pair under trad/simp (variant form): {a2.nosrc.sum()}")
bad = a2[~a2.ok & ~a2.nosrc]
print(bad[["word_id", "trad", "vi", "src", "origin"]].to_string(index=False) if len(bad) else "  mismatches: 0")
print("  variant-form A2 words:\n", a2[a2.nosrc][["word_id", "trad", "simp", "vi", "origin"]].to_string(index=False))
ychanged = a2[[v != " ".join(s[0].split()) if s else False for v, s in zip(a2.vi, a2.src)]]
print(f"  A2 words where a syllable got y (D56 exception): {len(ychanged)} (HSK {(ychanged.origin != 'vi_freq').sum()})")
FORBID = re.compile(r"^(b|ch|d|gh|kh|ng|ngh|nh|ph|s|th|tr|v|x|đ|g|n|r|p|c|q)y$")
for name, frame in [("words", nw), ("ff_candidates", ff)]:
    hits = frame[[any(FORBID.match(strip_tones(s)) for s in v.split()) for v in frame.vi]]
    print(f"  {name}: values with consonant+y outside h/k/l/m/t: {len(hits)};",
          hits.get("source_vi", pd.Series(["ff"] * len(hits))).value_counts().to_dict())
    if len(hits):
        print(hits[[c for c in ["word_id", "form", "trad", "vi", "source_vi"] if c in hits]].head(30).to_string(index=False))
    left = frame[[any(re.fullmatch(r"[hklmt]i", strip_tones(s)) for s in v.split()) for v in frame.vi]]
    print(f"  {name}: values with h/k/l/m/t + i:", left.get("source_vi", pd.Series(["ff"] * len(left))).value_counts().to_dict())
for t, want in [("皮膚", "bì phu"), ("移", "di"), ("支給", "chi cấp"), ("王妃", "vương phi"), ("胎兒", "thai nhi"),
                ("議程", "nghị trình"), ("自己", "tự kỷ"), ("分離", "phân ly"), ("美金", "mỹ kim"), ("禁忌", "cấm kỵ")]:
    got = nw.loc[nw.trad == t, "vi"].tolist() or ff.loc[ff.trad == t, "vi"].tolist()
    print(f"  {t}: {got} expected {want} {'OK' if want in got else 'MISSING (not in words?)'}")
mp = pw.merge(nw, on="word_id", suffixes=("_p", "_n"), validate="1:1")
ch = mp[mp.vi_p != mp.vi_n]
print(f"  words vi changed vs {PREV}: {len(ch)} (HSK {(ch.origin_n != 'vi_freq').sum()}); sources",
      ch.source_vi_n.value_counts().to_dict(), "; prev sources", ch.source_vi_p.value_counts().to_dict())
nonA2 = ch[(ch.source_vi_p != "kaikki_en_han") | (ch.source_vi_n != "kaikki_en_han")]
print("  changes not A2->A2:\n", nonA2[["trad_n", "vi_p", "vi_n", "source_vi_p", "source_vi_n"]].to_string(index=False))
print("  sample of changes:", list(zip(ch.trad_n, ch.vi_p, ch.vi_n))[:12])

# G2 --------------------------------------------------------------------------------------------
print("== G2 ff_candidates")
forms = set(nw.trad) | set(nw.simp) | set(nw.jp[nw.jp != ""])
print(f"  rows {len(ff)} (prev {len(pff)}); overlap form {ff.form.isin(forms).sum()}, trad {ff.trad.isin(forms).sum()}, "
      f"simp {ff.simp.isin(forms).sum()}; added vs prev {(~ff.form.isin(pff.form)).sum()}, "
      f"removed {(~pff.form.isin(ff.form)).sum()}; 手紙 {(ff.form == '手紙').any()}, 大丈夫 {(ff.form == '大丈夫').any()}")
removed = pff[~pff.form.isin(ff.form)]
print(f"  removed rows whose form/trad/simp is in words: {(removed.form.isin(forms) | removed.trad.isin(forms) | removed.simp.isin(forms)).sum()}")
dropped_vo = set(pw[pw.origin == "vi_freq"].trad) - set(nw[nw.origin == "vi_freq"].trad)
print("  dropped VI-only forms now in ff:", sorted(dropped_vo & set(ff.trad)), "not in ff:", sorted(dropped_vo - set(ff.trad)))
common = pff.merge(ff, on="form", suffixes=("_p", "_n"), validate="1:1")
vic = common[common.vi_p != common.vi_n]
print(f"  ff vi changed on kept rows: {len(vic)}", list(zip(vic.form, vic.vi_p, vic.vi_n))[:40])

# G3 / R4 ---------------------------------------------------------------------------------------
print("== G3/R4 VI-only")
vn, vp = nw[nw.origin == "vi_freq"], pw[pw.origin == "vi_freq"]
print(f"  rows {len(vn)}; levels {vn.level.value_counts().sort_index().to_dict()}; single chars {(vn.trad.str.len() == 1).sum()}; "
      f"HSK form repeats {vn.trad.isin(set(nw[nw.origin != 'vi_freq'].trad) | set(nw[nw.origin != 'vi_freq'].simp)).sum()}")
add, drop = vn[~vn.word_id.isin(vp.word_id)], vp[~vp.word_id.isin(vn.word_id)]
cols = ["word_id", "trad", "vi", "ko", "ja", "level", "ja_common", "source_vi"]
print("  added\n", add[cols].to_string(index=False), "\n  dropped\n", drop[cols].to_string(index=False))
rep = at(HEAD, "data/final/vi_only_report.csv")
print(f"  report selected {(rep.selected == 'true').sum()}; set equal {set(rep[rep.selected == 'true'].word_id) == set(vn.word_id)}")
merged_ids = idp.merge(idn, on=["kind", "key"], how="outer", suffixes=("_p", "_n"), indicator=True, validate="1:1")
print("  id_map:", merged_ids._merge.value_counts().to_dict(), "; changed ids:", (merged_ids.id_p != merged_ids.id_n)[merged_ids._merge == "both"].sum())
print(merged_ids[merged_ids._merge != "both"].to_string(index=False))
print("  every word_id equals id_map:", set(zip(nw.word_id)) <= set(zip(idn.id)), "; dup word_id", nw.word_id.duplicated().sum())

# R2 --------------------------------------------------------------------------------------------
print("== R2 vs", BASE)
mb = bw[bw.origin != "vi_freq"].merge(nw[nw.origin != "vi_freq"], on="word_id", suffixes=("_o", "_n"), validate="1:1")
print(mb[(mb.vi_o != "") & (mb.vi_o != mb.vi_n)][["trad_n", "pinyin_n", "vi_o", "vi_n", "source_vi_n"]].to_string(index=False))
hsk = nw[nw.origin != "vi_freq"]
four = (hsk.ja != "") & (hsk.ko != "") & (hsk.pinyin != "") & (hsk.vi != "")
print(f"  HSK {len(hsk)}: ja {(hsk.ja != '').sum()} ko {(hsk.ko != '').sum()} pinyin {(hsk.pinyin != '').sum()} vi {(hsk.vi != '').sum()} "
      f"all4 {four.sum()}; card_eligible HSK {(hsk.card_eligible == 'true').sum()} total {(nw.card_eligible == 'true').sum()}")

# R5 --------------------------------------------------------------------------------------------
print("== R5 primaries vs", PREV)
both = pc.merge(nc, on="char_id", how="outer", suffixes=("_o", "_n"), validate="1:1", indicator=True)
print("  chars merge:", both._merge.value_counts().to_dict())
print(both[both._merge != "both"][["char_id", "trad_o", "trad_n", "ko_n", "vi_n", "ko_all_n", "vi_all_n"]].to_string(index=False))
b = both[both._merge == "both"]
for col in ["ko", "vi", "ko_final", "vi_final", "ja_on", "pinyin", "simp", "jp"]:
    d = b[b[f"{col}_o"] != b[f"{col}_n"]]
    print(f"  {col} changed: {len(d)}", list(zip(d.trad_n, d[f"{col}_o"], d[f"{col}_n"]))[:20])
for col in ["ko_all", "vi_all", "ja_on_all", "pinyin_all", "ko_base_all"]:
    d = b[b[f"{col}_o"].map(lambda s: frozenset(s.split(";"))) != b[f"{col}_n"].map(lambda s: frozenset(s.split(";")))]
    print(f"  {col} set changed: {len(d)}", list(zip(d.trad_n, d[f"{col}_o"], d[f"{col}_n"]))[:20])
cpc, ppc = at(HEAD, "data/final/char_primary_changes.csv"), at(PREV, "data/final/char_primary_changes.csv")
t1, t0 = set(map(tuple, cpc.values)), set(map(tuple, ppc.values))
print(f"  char_primary_changes {len(ppc)} -> {len(cpc)}; added {sorted(t1 - t0)}; removed {sorted(t0 - t1)}")


def evidence(chars, words, wc):
    frame = (wc.merge(chars[["char_id", "key_char", "ko_all", "vi_all"]], on="char_id", validate="m:1")
             .merge(words[["word_id", "ko_alt", "vi_alt"]], on="word_id", validate="m:1"))
    out = {}
    for lang, col in [("ko", "ko_base"), ("vi", "vi_syllable")]:
        sub = frame[(frame[col] != "") & (frame[f"{lang}_alt"] == "")]
        sub = sub[[x in a.split(";") for x, a in zip(sub[col], sub[f"{lang}_all"])]]
        counts = collections.defaultdict(dict)
        for (key, reading), n in sub.groupby(["key_char", col]).size().items():
            counts[key][reading] = n
        out[lang] = counts
    return out


def top(c):
    if not c:
        return ()
    m = max(c.values())
    return tuple(sorted(k for k, v in c.items() if v == m))


oe, ne = evidence(pc, pw, pwc), evidence(nc, nw, nwc)
print("  evidence changes that create/break a tie or change the top (approximate D39 evidence):")
for lang in ["ko", "vi"]:
    for key in sorted(set(oe[lang]) | set(ne[lang])):
        a, c = oe[lang].get(key, {}), ne[lang].get(key, {})
        if a != c and (top(a) != top(c)):
            print(f"   {lang} {key}: {a} -> {c}")

# R6 --------------------------------------------------------------------------------------------
print("== R6 overrides")
wkey = dict(zip(idn[idn.kind == "word"].key, idn[idn.kind == "word"].id))
wid = nw.set_index("word_id")
cidx = nc.set_index("key_char")
fails = []
for row in ov.itertuples():
    if row.table == "words":
        got = wid.at[wkey[row.key], row.column] if row.key in wkey and wkey[row.key] in wid.index else "<missing>"
    else:
        got = cidx.at[row.key, row.column] if row.key in cidx.index else "<missing>"
    if got != row.value:
        fails.append((row.table, row.key, row.column, row.value, got))
print(f"  rows {len(ov)} ({ov.table.value_counts().to_dict()}); not applied: {fails}")
