"""Task-6 re-check (Claude, 2026-11-12, D75). Offline; no request.

Usage: python -X utf8 docs/review_scripts/task6_recheck.py BASE_COMMIT OUT_DIR

1. Integrity: every batch log (main + rerun1) matches its input/prompt SHA and model;
   every stored output re-validates; batch states; outputs stored at BASE_COMMIT are
   unchanged (the resume only added the failed keys); ledger.
2. The 56 resumed keys (= failed_keys of the logs at BASE_COMMIT) and the 25 rerun-1
   answers, with their review_feedback, as one review extract (new_answers.tsv).
3. Tone-aware pinyin check of every new zh sentence: each aligned syllable, with its
   tone mark, against chars.pinyin_all of that simplified character (neutral tone
   listed separately). Also run over the full zh set to compare with the gate's 11.
"""
from __future__ import annotations

import collections
import csv
import json
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd  # noqa: E402

from pipeline.stage4 import builders, runner  # noqa: E402
from pipeline.stage4 import validators as V  # noqa: E402

GEN = ROOT / "content" / "generated" / "task6"
INP = ROOT / "content" / "inputs" / "task6"


def git_show(commit: str, rel: str) -> str:
    return subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=ROOT, capture_output=True,
                          check=True).stdout.decode("utf-8")


def tone_flags(v: dict, py_by_simp: dict[str, set[str]]) -> list[tuple[str, str, str]]:
    han = V.HAN_RE.findall(v["sentence"])
    al = V._pinyin_alignments(v["sentence"], v["pinyin"].replace("’", "'"))
    if not al:
        return [("?", "", "NO ALIGNMENT")]
    out = []
    for left, right, marked, base in al[0]:
        ch = han[left]
        known = py_by_simp.get(ch)
        if not known:
            continue
        m = unicodedata.normalize("NFC", marked.casefold())
        if m.endswith("r") and right - left == 2:
            m = m[:-1]
        if m in known:
            continue
        if V._tone_count(m) == 0 and any(V._toneless(k) == m for k in known):
            out.append((ch, marked, "neutral"))
        elif ch in "一不":
            continue  # validator already forces yī/bù
        else:
            out.append((ch, marked, "/".join(sorted(known))))
    return out


def main(base: str, out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    batches = builders.build_task6_batches()
    items_by_key, kind_by_key, outputs = {}, {}, {}
    states = collections.Counter()
    resumed: list[str] = []
    changed_old = []
    for name, kind, items in batches:
        assert builders.read_jsonl_files([INP / f"{name}.jsonl"]) == items, name
        log = json.loads((GEN / f"{name}.log.json").read_text(encoding="utf-8"))
        assert log["input_sha256"] == builders.sha256_text(builders.ordered_jsonl_text(items)), name
        assert log["prompt_sha256"] == builders.sha256_text(runner.prompt_text(6, items)), name
        assert log["model"] == runner.MODEL_ID, name
        states[(kind, log["validation"]["state"])] += 1
        values = builders.read_jsonl_files([GEN / f"{name}.jsonl"])
        _, errs, _ = V.validate_task6_items(values, items if len(values) == len(items) else
                                            [i for i in items if i["key"] in {x["key"] for x in values}], kind)
        assert not errs, (name, errs)
        old_log = json.loads(git_show(base, f"content/generated/task6/{name}.log.json"))
        old_vals = {x["key"]: x for x in (json.loads(l) for l in git_show(base, f"content/generated/task6/{name}.jsonl").splitlines() if l.strip())}
        new_vals = {x["key"]: x for x in values}
        for k, x in old_vals.items():
            if new_vals.get(k) != x:
                changed_old.append((name, k))
        assert set(new_vals) - set(old_vals) == set(old_log["failed_keys"]), name
        resumed.extend(old_log["failed_keys"])
        for i in items:
            items_by_key[i["key"]] = i
            kind_by_key[i["key"]] = kind
        outputs.update(new_vals)
    print("batch states:", dict(states))
    print("outputs:", len(outputs), "| resumed keys:", len(resumed), "| old outputs changed:", changed_old or "none")

    # rerun round 1
    rerun_rows = list(csv.DictReader(open(ROOT / "config" / "task6_rerun.csv", encoding="utf-8")))
    feedback = {r["key"]: r["reason"] for r in rerun_rows if r["round"] == "1"}
    rerun_out, rerun_in = {}, {}
    for log_path in sorted((GEN / "rerun1").glob("*.log.json")):
        log = json.loads(log_path.read_text(encoding="utf-8"))
        name = log_path.name.split(".")[0]
        items = builders.read_jsonl_files([INP / "rerun1" / f"{name}.jsonl"])
        assert log["input_sha256"] == builders.sha256_text(builders.ordered_jsonl_text(items)), name
        assert log["prompt_sha256"] == builders.sha256_text(runner.prompt_text(6, items)), name
        assert log["model"] == runner.MODEL_ID
        values = builders.read_jsonl_files([GEN / "rerun1" / f"{name}.jsonl"])
        _, errs, _ = V.validate_task6_items(values, items, log["kind"])
        assert not errs, errs
        print(f"rerun1 {name}: {log['kind']} {log['validation']['state']} items={len(values)} requests={len(log['requests'])} usd={log['usd']:.6f}")
        for i in items:
            rerun_in[i["key"]] = i
            base_item = dict(items_by_key[i["key"]])
            diff = {k for k in set(i) | set(base_item) if i.get(k) != base_item.get(k)}
            assert diff <= {"review_feedback"}, (i["key"], diff)
        rerun_out.update({x["key"]: x for x in values})
    assert set(rerun_out) == set(feedback), set(rerun_out) ^ set(feedback)
    print("rerun1 keys:", len(rerun_out))

    rows = list(csv.DictReader(open(ROOT / "content" / "cost_log.csv", encoding="utf-8")))
    print("ledger $%.8f; task 6 $%.8f" % (sum(float(r["usd"]) for r in rows),
                                          sum(float(r["usd"]) for r in rows if r["task"] == "6")))

    # tone-aware pinyin check
    chars = pd.read_csv(ROOT / "data/final/chars.csv", dtype=str, keep_default_na=False)
    py_by_simp: dict[str, set[str]] = collections.defaultdict(set)
    for _, r in chars.iterrows():
        for p in r["pinyin_all"].split(";"):
            if p:
                py_by_simp[r["simp"]].add(unicodedata.normalize("NFC", p.casefold()))
    full = collections.Counter()
    for k, v in outputs.items():
        if kind_by_key[k] == "zh" and v["status"] == "ok":
            for f in tone_flags(v, py_by_simp):
                full["neutral" if f[2] == "neutral" else "tone"] += 1
    print("full zh set (incl. new) tone flags:", dict(full))

    def line(k: str, v: dict, tag: str) -> str:
        i = items_by_key[k]
        kind = kind_by_key[k]
        trap = f"TRAP vs「{i['contrast_meaning_ja']}」" if i.get("is_trap") else ""
        py = v.get("pinyin", "") if kind == "zh" else i.get("vi_use", "")
        flags = ""
        if kind == "zh" and v["status"] == "ok":
            flags = " ".join(f"{c}={m}≠{e}" for c, m, e in tone_flags(v, py_by_simp))
        fb = f"\tFEEDBACK: {feedback[k]}" if k in feedback else ""
        return (f"{tag}\t{k}\tL{i['level']}\t{i['target']}\t{i['meaning_ja']}\t{trap}\t"
                f"{v['status']}/{v['confidence']}\t{v['sentence']}\t{py}\t=「{v['translation_ja']}」\t"
                f"{v['review_note']}\tTONE[{flags}]{fb}")

    with open(out / "new_answers.tsv", "w", encoding="utf-8") as f:
        for k in resumed:
            f.write(line(k, outputs[k], "resumed") + "\n")
        for k in feedback:
            f.write(line(k, rerun_out[k], "rerun1") + "\n")
            f.write(line(k, outputs[k], "  old") + "\n")
    n_flag = sum(1 for k in resumed + list(feedback)
                 for v in [rerun_out.get(k) or outputs[k]]
                 if kind_by_key[k] == "zh" and v["status"] == "ok" and
                 any(e != "neutral" for _, _, e in tone_flags(v, py_by_simp)))
    print("new zh answers with a toned mismatch:", n_flag)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
