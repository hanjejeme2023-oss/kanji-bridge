"""Stage 4 gate part 1 (task 1) reference checks, Claude 2026-11-07. Read-only.

Run: python docs/review_scripts/stage4d_task1_reference.py
Prints: validator rerun, input == fresh build, token-format modes per batch,
vi_check x source table, every different_word with the D62 character check
(each character named in vi_check_reason must have the vi syllable in chars.vi_all;
'?' = character not in chars), the 50-item random sample (seed 20261106) and the
user's 10 words (seed 1107).
"""
import glob, json, os, re, sys, unicodedata
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.stage4 import builders, validators  # noqa: E402

rows, logs = [], []
for p in sorted(glob.glob(str(ROOT / "content/generated/task1/b*.jsonl"))):
    b = os.path.basename(p)[:4]
    out = [json.loads(l) for l in open(p, encoding="utf-8")]
    inp = [json.loads(l) for l in open(ROOT / f"content/inputs/task1/{b}.jsonl", encoding="utf-8")]
    validators.validate(1, out, inp)
    om = {o["word_id"]: o for o in out}
    rows += [{**i, **{k: v for k, v in om[i["word_id"]].items() if k != "word_id"}, "batch": b} for i in inp]
    lg = json.load(open(ROOT / f"content/generated/task1/{b}.log.json", encoding="utf-8"))
    logs.append({"batch": b, "attempts": len(lg["attempts"]), "out": lg["usage"]["output_tokens"],
                 "stored_chars": len(open(p, encoding="utf-8").read())})
df, L = pd.DataFrame(rows), pd.DataFrame(logs)
print("items", len(df), "unique", df.word_id.is_unique, "validator OK on all", len(L), "batches")
fresh = builders.build_task1_batches()
print("inputs == fresh build:", all(builders.jsonl_text(fb) == open(ROOT / f"content/inputs/task1/b{i+1:03d}.jsonl", encoding="utf-8").read() for i, fb in enumerate(fresh)))
L["tok_per_char"] = (L.out / L.stored_chars).round(3)
print("compact-format batches (<0.42 tokens/char):", list(L.batch[L.tok_per_char < 0.42]))
print("mixed (0.42-0.5):", list(L.batch[(L.tok_per_char >= 0.42) & (L.tok_per_char < 0.5)]))
v = df[df.vi != ""]
print(pd.crosstab(v.source_vi, v.vi_check, margins=True))

ch = pd.read_csv(ROOT / "data/final/chars.csv", dtype=str, keep_default_na=False)
yi = lambda s: unicodedata.normalize("NFC", s.lower()).translate(str.maketrans("ýỳỷỹỵy", "íìỉĩịi"))
vimap = {}
for _, r in ch.iterrows():
    for k in {r.trad, r.key_char, r.simp, r.jp} - {""}:
        vimap.setdefault(k, set()).update(yi(x) for x in r.vi_all.split(";") if x)
CJK = re.compile(r"[㐀-鿿豈-﫿]+")
review = pd.read_csv(ROOT / "config/task1_review.csv", dtype=str, keep_default_na=False).set_index("word_id")
print("\ndifferent_word (check per named form; R = corrected in config/task1_review.csv)")
for _, r in df[df.vi_check == "different_word"].iterrows():
    syl = [yi(x) for x in r.vi.split()]
    named = dict.fromkeys(c for c in CJK.findall(r.vi_check_reason) if len(c) == len(r.trad) and c != r.trad)
    marks = [c + ":" + "".join("?" if ci not in vimap else ("y" if s in vimap[ci] else "N") for ci, s in zip(c, syl)) for c in named]
    print(("R " if r.word_id in review.index else "  ") + f"{r.batch} {r.word_id} {r.trad} [{r.vi}] {r.source_vi} | {r.gloss_vi[:50]} || {' '.join(marks)}")

def show(r):
    print(f"{r.batch} {r.word_id} {r.trad} L{r.level} ja={r.ja} ko={r.ko} py={r.pinyin} vi={r.vi} | JA:{r.meaning_ja__ja} | KO:{r.meaning_ja__ko} | ZH:{r.meaning_ja__zh} | VI:{r.meaning_ja__vi} | differ={r.meanings_differ} {r.vi_check} {r.confidence} {r.low_reason[:30]}")
print("\nrandom 50 (seed 20261106)")
df.sample(50, random_state=20261106).apply(show, axis=1)
print("\nuser 10 (seed 1107)")
df.sample(10, random_state=1107).apply(show, axis=1)
