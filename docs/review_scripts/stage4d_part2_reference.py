"""Stage 4 gate part 2 (tasks 2-4) reference checks, Claude 2026-11-07. Read-only.

Run: python docs/review_scripts/stage4d_part2_reference.py [section ...]
Sections: integrity, task4drop, tokens, d63, sample2, sample3, sample4, low, fixed, user, clears
(no argument = all). Seeds: task-2 sample 20261107, task-4 sample 20261107,
user's 10 false friends 1107, user's passages 1108.
"""
import glob, json, os, random, re, sys, unicodedata
from collections import Counter
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.stage4 import builders, validators  # noqa: E402

SECTIONS = set(sys.argv[1:]) or {"integrity", "task4drop", "tokens", "d63", "sample2", "sample3",
                                 "sample4", "low", "fixed", "user", "clears"}
G, I = ROOT / "content/generated", ROOT / "content/inputs"
jl = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]


def load_task1():
    out = []
    for p in sorted(glob.glob(str(G / "task1/b*.jsonl"))):
        out += jl(p)
    return out


T1RAW = load_task1()
T1 = builders.apply_task1_review(T1RAW)
T1M = {o["word_id"]: o for o in T1}
T1RAWM = {o["word_id"]: o for o in T1RAW}
W = pd.read_csv(ROOT / "data/final/words.csv", dtype=str, keep_default_na=False).set_index("word_id", drop=False)
REVIEW = pd.read_csv(ROOT / "config/task1_review.csv", dtype=str, keep_default_na=False)


def batches(task):
    res = []
    for p in sorted(glob.glob(str(G / f"task{task}/b*.jsonl"))):
        b = os.path.basename(p)[:4]
        res.append((b, jl(p), jl(I / f"task{task}/{b}.jsonl"),
                    json.load(open(G / f"task{task}/{b}.log.json", encoding="utf-8")), p))
    return res


B = {t: batches(t) for t in (2, 3, 4)}

if "integrity" in SECTIONS:
    print("== integrity")
    for t in (2, 3, 4):
        fresh = builders.task_batches(t, T1RAW)
        same = len(fresh) == len(B[t]) and all(
            builders.jsonl_text(fb) == open(I / f"task{t}/{b}.jsonl", encoding="utf-8").read()
            for fb, (b, *_rest) in zip(fresh, B[t]))
        for b, out, inp, lg, _ in B[t]:
            validators.validate(t, out[0] if t == 3 else out, inp)
        n_in = sum(len(inp) for _, _, inp, _, _ in B[t])
        n_out = sum(len(out) if t != 3 else len(out[0]["passages"]) for _, out, _, _, _ in B[t])
        att = Counter(len(lg["attempts"]) for *_x, lg, _p in B[t])
        ops = Counter(a.get("operation", "") + ":" + str(a.get("validation_ok")) for *_x, lg, _p in B[t] for a in lg["attempts"])
        st = {(lg["model"], lg["location"], lg["prompt_sha256"][:8], lg["settings"]["temperature"]) for *_x, lg, _p in B[t]}
        th = sum(lg["usage"]["thinking_tokens"] for *_x, lg, _p in B[t])
        un = sum(lg["usage"]["unreported_tokens"] for *_x, lg, _p in B[t])
        ok = all(lg["validation"]["ok"] for *_x, lg, _p in B[t])
        print(f"task{t}: batches {len(B[t])} items_in {n_in} outputs {n_out} validator-rerun OK, logs ok={ok}, inputs==fresh {same}")
        print(f"   settings {st} thinking {th} unreported {un} attempts {dict(att)}")
        print(f"   attempt kinds {dict(ops)}")
        for b, out, inp, lg, _ in B[t]:
            if len(lg["attempts"]) > 1:
                print("   multi-attempt", b, [(a.get("operation"), a.get("validation_ok"), a.get("error", "")[:90], round(a["usd"], 4)) for a in lg["attempts"]])
    cl = pd.read_csv(ROOT / "content/cost_log.csv", dtype=str, keep_default_na=False)
    cl["usd"] = cl["usd"].astype(float)
    print(cl.groupby("task")["usd"].agg(["sum", "count"]), "total", round(cl.usd.sum(), 8))
    t2 = [o for _, out, *_r in B[2] for o in out]
    print("task2 items", len(t2), "with false_friend", sum(bool(o["false_friend"]) for o in t2),
          "low", sum(o["confidence"] == "low" for o in t2),
          "ff langs", Counter(l for o in t2 for l in o["false_friend"]))
    keys2 = {i["key"] for _, _, inp, _, _ in B[2] for i in inp}
    ffc = pd.read_csv(ROOT / "data/staging/ff_candidates.csv", dtype=str, keep_default_na=False)
    differ = {k for k, o in T1M.items() if o.get("meanings_differ") is True}
    print("task2 covers: ff_candidates", set(ffc.form) <= keys2, len(ffc), "| meanings_differ", differ <= keys2, len(differ),
          "| 自己", set(W.word_id[W.trad == "自己"]) <= keys2, "| D63 16", set(REVIEW.word_id) <= keys2)
    for _, out, inp, _, _ in B[3]:
        c = inp[0]
        ps = out[0]["passages"]
        lvl = Counter(next((w["level"] for w in c["words"] if w["word_id"] == tk.get("word_id")), None) for p in ps for tk in p["tokens"] if "word_id" in tk)
        at_level = sum(any(tk.get("word_id") in {w["word_id"] for w in c["words"] if w["level"] == c["level"]} for tk in p["tokens"]) for p in ps)
        print(f"   task3 {c['language']} L{c['level']}: words {len(c['words'])} passages {len(ps)} linked/passage {[sum('word_id' in tk for tk in p['tokens']) for p in ps]} passages with a level-{c['level']} word {at_level}")
    t4 = [o for _, out, *_r in B[4] for o in out]
    print("task4 notes", len(t4), "max len", max(len(o["note_ja"]) for o in t4))

if "task4drop" in SECTIONS:
    print("\n== task 4: 234 -> 212")
    before = builders.build_task4_items()
    after = builders.build_task4_items(task1_outputs=T1)
    after_raw = builders.build_task4_items(task1_outputs=T1RAW)
    bm, am = {i["word_id"]: i for i in before}, {i["word_id"]: i for i in after}
    print("before", len(before), "after (with D63)", len(after), "after (raw task 1, no D63)", len(after_raw))
    dropped = [bm[k] for k in bm if k not in am]
    bad = []
    for it in dropped:
        langs = {d["lang"] for d in it["differences"]}
        chk = T1M.get(it["word_id"], {}).get("vi_check", "NO_TASK1")
        ok = langs == {"vi"} and chk != "same_word"
        bad += [] if ok else [it["word_id"]]
        print(f"  {it['word_id']} {it['trad']} vi={it['vi']} langs={sorted(langs)} vi_check={chk} card={W.loc[it["word_id"]].card_eligible}")
    print("dropped", len(dropped), "all = only-vi differences of non-same_word words:", not bad, bad)
    print("vi_check of dropped:", Counter(T1M.get(i["word_id"], {}).get("vi_check", "NO_TASK1") for i in dropped))
    shrunk = [k for k in am if len(am[k]["differences"]) < len(bm[k]["differences"])]
    print("kept but lost a vi difference:", [(k, bm[k]["trad"], T1M.get(k, {}).get("vi_check", "NO_TASK1")) for k in shrunk])
    print("added:", [k for k in am if k not in bm])
    for _, r in REVIEW.iterrows():
        if r.word_id in bm:
            print(f"  D63 {r.word_id} {r.trad}: in 234 yes, in 212 {'yes' if r.word_id in am else 'NO'}, diffs {[(d['char'], d['lang'], d['reading_here'], d['primary']) for d in am.get(r.word_id, bm[r.word_id])['differences']]}")
    print("D63 words with a task-4 difference:", sum(REVIEW.word_id.isin(bm)), "kept", sum(REVIEW.word_id.isin(am)),
          "| would be dropped without D63:", [k for k in REVIEW.word_id if k in bm and k not in {i['word_id'] for i in after_raw}])
    noncheck_kept = [(k, am[k]["trad"]) for k in am if any(d["lang"] == "vi" for d in am[k]["differences"]) and T1M.get(k, {}).get("vi_check") != "same_word"]
    print("kept vi differences of non-same_word words (expect none):", noncheck_kept)

if "tokens" in SECTIONS:
    print("\n== task 2 output tokens")
    rows = []
    for b, out, inp, lg, p in B[2]:
        txt = open(p, encoding="utf-8").read()
        ms = [m for o in out for m in o["meanings"]]
        rows.append({"b": b, "items": len(out), "in": lg["usage"]["input_tokens"], "out": lg["usage"]["output_tokens"],
                     "chars": len(txt), "tpc": lg["usage"]["output_tokens"] / len(txt),
                     "mlen": sum(len(m["meaning_ja"]) for m in ms) / len(ms), "langs": len(ms) / len(out),
                     "ff": sum(bool(o["false_friend"]) for o in out), "lowr": sum(len(o["low_reason"]) for o in out),
                     "words": sum(not i.get("source") for i in inp)})
    D = pd.DataFrame(rows)
    D["mode"] = pd.cut(D.tpc, [0, 0.43, 0.60, 2], labels=["compact", "medium", "wide"])
    pd.set_option("display.width", 200)
    print(D.groupby("mode", observed=True)[["items", "in", "out", "chars", "tpc", "mlen", "langs", "ff", "lowr", "words"]].mean().round(3))
    print(D.groupby("mode", observed=True).b.apply(list))
    print("output tokens: min", D.out.min(), "max", D.out.max(), "| stored chars: min", D.chars.min(), "max", D.chars.max())
    full = D[D["items"] == 50]
    print("corr(out, chars)", round(full.out.corr(full.chars), 3), "corr(out, in)", round(full.out.corr(full["in"]), 3))
    rate = lambda d: d.tpc.median()
    pad = D[D["mode"] != "compact"]
    extra = (pad.out - pad.chars * rate(D[D["mode"] == "compact"])).sum()
    print(f"extra output tokens in padded batches ~{extra:,.0f} -> ~${extra * 10 / 1e6:.2f} at the November Argon output rate $10/M")
    for t in (3, 4):
        r = [(b, lg["usage"]["output_tokens"], len(open(p, encoding='utf-8').read()), round(lg["usage"]["output_tokens"] / len(open(p, encoding='utf-8').read()), 3)) for b, out, inp, lg, p in B[t]]
        print(f"task{t} out/chars", r)

if "d63" in SECTIONS:
    print("\n== D63 words in task 2")
    t2 = {o["key"]: (o, b) for b, out, *_r in B[2] for o in out}
    i2 = {i["key"]: i for _, _, inp, _, _ in B[2] for i in inp}
    for _, r in REVIEW.iterrows():
        o, b = t2[r.word_id]
        vi = [m for m in o["meanings"] if m["lang"] == "vi"]
        inp = i2[r.word_id]
        print(f"{b} {r.word_id} {r.trad} vi={inp['vi']} gloss_vi_sent={'yes' if inp['gloss_vi'] else 'blank'}({r.gloss_vi_task2}) "
              f"| VI: {vi[0]['meaning_ja'] if vi else 'MISSING'} | trap={vi[0]['is_trap'] if vi else '-'} | ff={o['false_friend']} {o['confidence']} {o['low_reason'][:60]}")
        others = " / ".join(f"{m['lang']}:{m['meaning_ja']}" for m in o["meanings"] if m["lang"] != "vi")
        print("      ", others)


def show2(o, inp, b):
    src = "FF " if inp.get("source") else "W  "
    hdr = f"{b} {src}{o['key']} {inp.get('trad')} ja={inp.get('ja','')} ko={inp.get('ko','')} py={inp.get('pinyin','')} vi={inp.get('vi','')}"
    ms = " | ".join(f"{m['lang']}{'*' if m['is_trap'] else ''}:{m['meaning_ja']}" for m in o["meanings"])
    print(hdr, "\n     ", ms, f"|| ff={o['false_friend']} {o['confidence']} {o['low_reason'][:80]}")
    g = f"en={inp.get('gloss_en','')[:70]} | ja_en={inp.get('gloss_ja_en','')[:50]} | vi={inp.get('gloss_vi','')[:60]} | ko={inp.get('gloss_ko','')[:30]}"
    print("      gl:", g)


ALL2 = [(o, i, b) for b, out, inp, _, _ in B[2] for o, i in zip(sorted(out, key=lambda x: x["key"]), sorted(inp, key=lambda x: x["key"]))]
if "sample2" in SECTIONS:
    print("\n== task 2 random 50 (seed 20261107)")
    for o, i, b in random.Random(20261107).sample(ALL2, 50):
        show2(o, i, b)
if "low" in SECTIONS:
    lows = [(o, i, b) for o, i, b in ALL2 if o["confidence"] == "low"]
    print(f"\n== task 2 low confidence ({len(lows)})")
    for x in lows:
        show2(*x)
if "fixed" in SECTIONS:
    print("\n== task 2 fixed items")
    for o, i, b in ALL2:
        if i.get("trad") in {"自己", "手紙", "大丈夫", "勉強", "工夫", "新聞", "博士", "裝置"} or o["key"] in {"手紙", "大丈夫"}:
            show2(o, i, b)


def passage_text(p, lang):
    s = ""
    for tk in p["tokens"]:
        t = tk["t"]
        if lang == "vi" and s and not tk.get("punct"):
            s += " "
        s += t
    return s


if "sample3" in SECTIONS:
    print("\n== task 3 all passages")
    for b, out, inp, lg, _ in B[3]:
        c = inp[0]
        wm = {w["word_id"]: w for w in c["words"]}
        for k, p in enumerate(out[0]["passages"]):
            links = ", ".join(f"{tk['t']}=L{wm[tk['word_id']]['level']}:{wm[tk['word_id']]['meaning_ja'][:12]}" for tk in p["tokens"] if "word_id" in tk)
            gl = ", ".join(f"{tk['t']}={tk['gloss_ja']}" for tk in p["tokens"] if "gloss_ja" in tk)
            print(f"{b} {c['language']} L{c['level']} #{k+1}: {passage_text(p, c['language'])}\n    JA: {p['translation_ja']}\n    linked: {links}\n    gloss: {gl}")

if "sample4" in SECTIONS:
    print("\n== task 4 random 50 (seed 20261107)")
    t4 = [(o, i, b) for b, out, inp, _, _ in B[4] for o, i in zip(sorted(out, key=lambda x: x["word_id"]), sorted(inp, key=lambda x: x["word_id"]))]
    for o, i, b in random.Random(20261107).sample(t4, 50):
        d = "; ".join(f"{x['char']} {x['lang']} here={x['reading_here']} prim={x['primary']} exP={[e['trad'] for e in x['examples_primary']]} exH={[e['trad'] for e in x['examples_here']]}" for x in i["differences"])
        print(f"{b} {i['word_id']} {i['trad']} ko={i['ko']} vi={i['vi']} || {d}\n     {o['note_ja']}")

if "user" in SECTIONS:
    print("\n== user: 10 random false friends (seed 1107)")
    ffs = [x for x in ALL2 if x[0]["false_friend"]]
    for x in random.Random(1107).sample(ffs, 10):
        show2(*x)
    print("\n== user: passages (seed 1108): 1 zh, 2 vi")
    rng = random.Random(1108)
    zh = [(b, inp[0], p) for b, out, inp, _, _ in B[3] if inp[0]["language"] == "zh" for p in out[0]["passages"]]
    vi = [(b, inp[0], p) for b, out, inp, _, _ in B[3] if inp[0]["language"] == "vi" for p in out[0]["passages"]]
    for b, c, p in rng.sample(zh, 1) + rng.sample(vi, 2):
        wm = {w["word_id"]: w for w in c["words"]}
        print(f"{b} {c['language']} L{c['level']}: {passage_text(p, c['language'])}\n    JA: {p['translation_ja']}")
        for tk in p["tokens"]:
            if "word_id" in tk:
                w = W.loc[tk["word_id"]]
                print(f"      {tk['t']} = {w.trad} ({w.word_id}, L{w.level}) {wm[tk['word_id']]['meaning_ja']}")
            elif "gloss_ja" in tk:
                print(f"      {tk['t']} = {tk['gloss_ja']}")

if "clears" in SECTIONS:
    print("\n== step 6 candidates: different_word + multi-character unsure (after D63)")
    ch = pd.read_csv(ROOT / "data/final/chars.csv", dtype=str, keep_default_na=False)
    vimap = {}
    for _, r in ch.iterrows():
        for k in {r.trad, r.key_char, r.simp, r.jp} - {""}:
            vimap.setdefault(k, set()).update(x for x in r.vi_all.split(";") if x)
    t2 = {o["key"]: o for o, _, _ in ALL2}
    for k, o in T1M.items():
        if o["vi_check"] == "different_word" or (o["vi_check"] == "unsure" and len(W.loc[k].trad) > 1):
            w = W.loc[k]
            per = " ".join(f"{c}:{'/'.join(sorted(vimap.get(c, {'?'})))}" for c in w.trad)
            vi2 = [m["meaning_ja"] for m in t2.get(k, {"meanings": []})["meanings"] if m["lang"] == "vi"]
            print(f"{k} {w.trad} vi=[{w.vi}] {o['vi_check']} src={w.source_vi} L{w.level} pinyin={w.pinyin} card={w.card_eligible}\n"
                  f"     chars: {per}\n     gloss_vi: {w.gloss_vi[:160]}\n     JA meaning: {o['meaning_ja__ja'] or o['meaning_ja__ko']} | ZH: {o['meaning_ja__zh']} | VI(task1): {o['meaning_ja__vi']} | VI(task2): {vi2}\n"
                  f"     reason: {o['vi_check_reason'][:200]}")
