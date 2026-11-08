"""Stage 4 gate part 4b (task 5, D68 follow-up) reference script (Claude, 2026-11-07).

Offline. Reads task 5 from the accepted layout (content/accepted/task5/{bNNN.jsonl,
bNNN.log.json,inputs/bNNN.jsonl}), checks the inputs against a fresh build, checks every
batch with the runner's own batch_state (the -Status rule) at the accepted paths, applies
config/task5_review.csv (fail-closed on check_generated) and, for 偽の友達, config/task2_review.csv
then config/task2_retrap.csv (fail-closed on generated meaning and trap), and prints the app
effect under D67/D68 (rare/unsure ja/ko -> （ ） on cards and a fixed-note row in 偽の友達;
wrong_meaning -> meaning and row dropped; an entry leaves only when false_friend is empty).
Usage: python docs/review_scripts/stage4d_part4b_reference.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.stage4 import builders, runner  # noqa: E402

ACC = ROOT / "content/accepted/task5"
NOT = {"rare", "unsure"}
STATIC = set("勉強 工夫 手紙 汽車 愛人 大丈夫 小心 東西 娘 新聞 先生 博士".split())


def load_table() -> pd.DataFrame:
    fresh = builders.build_task5_batches()
    assert len(fresh) == 104
    same, states, rows, warns = 0, Counter(), [], []
    for n, items in enumerate(fresh, 1):
        name = f"b{n:03d}"
        sent = (ACC / "inputs" / f"{name}.jsonl").read_text(encoding="utf-8")
        same += builders.jsonl_text(items) == sent
        states[runner.batch_state(5, name, items, ACC / f"{name}.jsonl", ACC / f"{name}.log.json")] += 1
        log = json.loads((ACC / f"{name}.log.json").read_text(encoding="utf-8"))
        warns += [dict(w, batch=name) for w in log.get("reason_warnings", [])]
        out = {o["key"]: o for o in builders.read_jsonl_files([ACC / f"{name}.jsonl"])}
        for it in items:
            r = dict(it, checks=",".join(it["checks"]), batch=name)
            r.update({k: v for k, v in out[it["key"]].items() if k != "key"})
            rows.append(r)
    print(f"inputs equal to a fresh build: {same}/104; batch_state at accepted paths: {dict(states)}")
    wf = Counter(w["field"] for w in warns)
    print(f"reason_warnings: {len(warns)} in {len({w['batch'] for w in warns})} batches {dict(wf)}"
          f"; b055: {sum(w['batch'] == 'b055' for w in warns)}")
    df = pd.DataFrame(rows)
    df["is_row"] = ~df["key"].str.match(r"^w\d{5}$")
    return df


def apply_task5_review(df: pd.DataFrame) -> pd.DataFrame:
    rev = pd.read_csv(ROOT / "config/task5_review.csv", dtype=str, keep_default_na=False)
    assert not rev.duplicated(["key", "lang"]).any()
    for _, r in rev.iterrows():
        m = df.key == r.key
        c = r.lang + "_check"
        assert m.sum() == 1, r.key
        assert df.loc[m, c].iloc[0] == r.check_generated, (r.key, r.lang)
        assert df.loc[m, "trad"].iloc[0] == r.trad and df.loc[m, r.lang].iloc[0] == r.reading, r.key
        df.loc[m, c] = r.check_review
    print(f"task5_review.csv: {len(rev)} rows applied {dict(rev.check_review.value_counts())}")
    return df


def task2_entries(df: pd.DataFrame) -> dict:
    t2 = {o["key"]: o for o in builders.read_accepted_outputs(2)}
    r2 = pd.read_csv(ROOT / "config/task2_review.csv", dtype=str, keep_default_na=False)
    for _, r in r2.iterrows():
        o = t2[r.key]
        if r.false_friend_review or r.action:
            o["false_friend"] = [x for x in r.false_friend_review.split(";") if x]
        if r.action == "clear_vi":
            o["meanings"] = [m for m in o["meanings"] if m["lang"] != "vi"]
    for o in t2.values():
        o["ff_before_retrap"] = list(o["false_friend"])
    rt = pd.read_csv(ROOT / "config/task2_retrap.csv", dtype=str, keep_default_na=False)
    for key, g in rt.groupby("key"):
        assert g.false_friend_review.nunique() == 1, key
        o = t2[key]
        for _, r in g.iterrows():
            m = next(x for x in o["meanings"] if x["lang"] == r.lang)
            assert m["meaning_ja"] == r.meaning_ja_generated and str(m["is_trap"]).lower() == r.is_trap_generated, (key, r.lang)
            m["is_trap"] = r.is_trap_review == "true"
        o["false_friend"] = [x for x in g.false_friend_review.iloc[0].split(";") if x]
    print(f"task2_retrap.csv: {len(rt)} rows, keys {sorted(rt.key.unique())}")
    return t2


def main() -> None:
    df = apply_task5_review(load_table())
    words, rows = df[~df.is_row], df[df.is_row]
    ko_not, ja_not = words.ko_check.isin(NOT), words.ja_check.isin(NOT)
    print(f"card words checked {len(words)}; Korean （ ） {ko_not.sum()}, Japanese （ ） {ja_not.sum()}, "
          f"both {(ko_not & ja_not).sum()}, either {(ko_not | ja_not).sum()}; wrong_meaning "
          f"ko {(words.ko_check == 'wrong_meaning').sum()}, ja {(words.ja_check == 'wrong_meaning').sum()}")
    print(f"ff rows: Korean not used {rows.ko_check.isin(NOT).sum()}, wrong_meaning {(rows.ko_check == 'wrong_meaning').sum()}")
    for lg in ("ko", "ja"):
        print(lg, dict(df[lg + "_check"].value_counts()))
    print("vi", dict(df.vi_use.value_counts()), "multi-char literary",
          ((df.vi_use == "literary") & (df.trad.str.len() > 1)).sum())

    t2 = task2_entries(df)
    chk = df.set_index("key")
    s = Counter()
    leave = []
    for k, o in t2.items():
        if not o["ff_before_retrap"]:
            continue
        ff = list(o["false_friend"])
        trad = chk.loc[k, "trad"] if k in chk.index else k
        if not ff:  # emptied by task2_retrap.csv
            s["entries_before"] += 1
            s["changed"] += 1
            leave.append(trad)
            continue
        s["entries_before"] += 1
        if trad in STATIC:
            s["entries_after"] += 1
            continue
        langs = {m["lang"] for m in o["meanings"]}
        changed = False
        x = chk.loc[k] if k in chk.index else None
        for lg in ("ja", "ko"):
            c = x[lg + "_check"] if x is not None else ""
            if lg in langs and c in NOT:
                s[lg + "_note"] += 1; changed = True
            elif lg in langs and c == "wrong_meaning":
                s[lg + "_dropped_wm"] += 1; changed = True
            if (c in NOT or c == "wrong_meaning") and lg in ff:
                ff.remove(lg)
        s["changed"] += changed
        if ff:
            s["entries_after"] += 1
        else:
            leave.append(trad)
    print(dict(s))
    print("entries that leave 偽の友達:", len(leave), leave)


if __name__ == "__main__":
    main()
