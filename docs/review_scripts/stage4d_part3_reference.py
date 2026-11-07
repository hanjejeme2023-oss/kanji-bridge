"""Stage 4 gate part 3 (task-3 Vietnamese rerun) reference checks, Claude 2026-11-07. Read-only.

Run: python docs/review_scripts/stage4d_part3_reference.py [integrity] [passages]
"""
import glob, json, os, sys
from collections import Counter
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.stage4 import builders, validators, runner  # noqa: E402

SECTIONS = set(sys.argv[1:]) or {"integrity", "passages"}
G = ROOT / "content/accepted"  # D65 layout: taskN/bNNN.jsonl, taskN/inputs/bNNN.jsonl
jl = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
T1RAW = []
for p in sorted(glob.glob(str(G / "task1/b*.jsonl"))):
    T1RAW += jl(p)
W = pd.read_csv(ROOT / "data/final/words.csv", dtype=str, keep_default_na=False).set_index("word_id", drop=False)

B = []
for p in sorted(glob.glob(str(G / "task3/b*.jsonl"))):
    b = os.path.basename(p)[:4]
    B.append((b, jl(p), jl(G / f"task3/inputs/{b}.jsonl"), json.load(open(G / f"task3/{b}.log.json", encoding="utf-8"))))


def text(p, lang):
    s = ""
    for tk in p["tokens"]:
        if lang == "vi" and s and not tk.get("punct"):
            s += " "
        s += tk["t"]
    return s


if "integrity" in SECTIONS:
    fresh = builders.task_batches(3, T1RAW)
    print("inputs==fresh", len(fresh) == len(B) and all(
        builders.jsonl_text(fb) == open(G / f"task3/inputs/{b}.jsonl", encoding="utf-8").read() for fb, (b, *_r) in zip(fresh, B)))
    for b, out, inp, lg in B:
        validators.validate(3, out[0], inp)
        lang = inp[0]["language"]
        want = builders.sha256_text(runner.prompt_text(3, inp))
        n = len(out[0]["passages"])
        links = [sum("word_id" in t for t in p["tokens"]) for p in out[0]["passages"]]
        lvl = inp[0]["level"]
        wm = {w["word_id"]: w for w in inp[0]["words"]}
        atlvl = sum(any("word_id" in t and str(wm[t["word_id"]]["level"]) == str(lvl) for t in p["tokens"]) for p in out[0]["passages"])
        print(b, lang, "L", lvl, "passages", n, "links", links, "with-level-word", atlvl,
              "prompt", lg["prompt_sha256"][:8], "==current" if lg["prompt_sha256"] == want else "STALE",
              "ok", lg["validation"]["ok"], "attempts", len(lg["attempts"]), lg["model"], lg["settings"]["temperature"],
              "think", lg["usage"]["thinking_tokens"], "unrep", lg["usage"]["unreported_tokens"])
    cl = pd.read_csv(ROOT / "content/cost_log.csv", dtype=str, keep_default_na=False)
    cl["usd"] = cl["usd"].astype(float)
    print("total spend", round(cl.usd.sum(), 8), "rows", len(cl))

if "passages" in SECTIONS:
    for b, out, inp, lg in B:
        c = inp[0]
        if c["language"] != "vi":
            continue
        wm = {w["word_id"]: w for w in c["words"]}
        for k, p in enumerate(out[0]["passages"]):
            links = ", ".join(f"{t['t']}={W.loc[t['word_id']].trad}/L{wm[t['word_id']]['level']}:{wm[t['word_id']]['meaning_ja'][:14]}"
                              for t in p["tokens"] if "word_id" in t)
            gl = ", ".join(f"{t['t']}={t['gloss_ja']}" for t in p["tokens"] if "gloss_ja" in t)
            print(f"{b} L{c['level']} #{k+1}: {text(p, 'vi')}\n    JA: {p['translation_ja']}\n    linked: {links}\n    gloss: {gl}")


def apply_task3_review(batch, output, review):
    """Reference implementation of config/task3_review.csv (D65); fail-closed. Returns the kept passages."""
    passages = [dict(p, tokens=list(p["tokens"])) for p in output["passages"]]
    rows = review[review.batch == batch]
    drops, deletes = set(), {}
    for _, r in rows.iterrows():
        p = passages[int(r.passage) - 1]
        if r.action == "drop":
            assert p["translation_ja"] == r.generated, (batch, r.passage, "translation changed")
            drops.add(int(r.passage))
        elif r.action == "delete_token":
            assert p["tokens"][int(r.token_index)] == json.loads(r.generated), (batch, r.passage, r.token_index)
            deletes.setdefault(int(r.passage), []).append(int(r.token_index))
        elif r.action == "set_t":
            tk = p["tokens"][int(r.token_index)]
            assert tk["t"] == r.generated and "word_id" in tk, (batch, r.passage, r.token_index)
            p["tokens"][int(r.token_index)] = dict(tk, t=r.review)
        else:
            raise ValueError(r.action)
    for k, idx in deletes.items():
        for i in sorted(idx, reverse=True):
            del passages[k - 1]["tokens"][i]
    return [p for k, p in enumerate(passages, 1) if k not in drops]


if "overlay" in SECTIONS:
    import re
    rv = pd.read_csv(ROOT / "config/task3_review.csv", dtype=str, keep_default_na=False)
    for b, out, inp, lg in B:
        kept = apply_task3_review(b, out[0], rv)
        for p in kept:  # the validator wants six passages; check each kept passage on its own
            validators.validate_task3({"passages": [p] * 6}, inp)
        bad = [p["translation_ja"] for p in out[0]["passages"] if re.search(r"[가-힣a-zA-Z]", p["translation_ja"])]
        gl = [t["gloss_ja"] for p in out[0]["passages"] for t in p["tokens"] if "gloss_ja" in t and re.search(r"[가-힣]", t["gloss_ja"])]
        edited = [p for p in kept if p not in out[0]["passages"]]
        print(b, inp[0]["language"], "kept", len(kept), "edited", len(edited), "translations with Hangul/Latin", len(bad), bad[:1], "gloss with Hangul", gl)
        for p in edited:
            print("   edited:", text(p, inp[0]["language"]))
