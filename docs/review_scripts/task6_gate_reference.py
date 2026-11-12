"""Task-6 gate reference (Claude, 2026-11-12). Offline; no request.

Usage: python -X utf8 docs/review_scripts/task6_gate_reference.py OUT_DIR

1. Integrity: committed inputs == a fresh build; log input/prompt SHA, model; outputs
   re-validate with the current validator; ledger.
2. Diagnosis of partial items: failed keys + validator messages; validator inventory gaps.
3. Pre-screen: warnings, no_sentence, low, word-level pinyin check against words.csv.
4. Review extracts (text files in OUT_DIR) and the seeded samples (seed 20261112).
"""
from __future__ import annotations

import collections
import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd  # noqa: E402

from pipeline.stage4 import builders, runner  # noqa: E402
from pipeline.stage4 import validators as V  # noqa: E402

SEED = 20261112
GEN = ROOT / "content" / "generated" / "task6"
INP = ROOT / "content" / "inputs" / "task6"


def main(out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    batches = builders.build_task6_batches()
    sha_v2 = {k: builders.sha256_text(runner.prompt_text(6, [{"key": f"x:{k}:card"}] if k != "note" else [{"key": "c:note"}])) for k in ("zh", "vi", "note")}
    items_by_key: dict[str, dict] = {}
    kind_by_key: dict[str, str] = {}
    outputs: dict[str, dict] = {}
    batch_of: dict[str, str] = {}
    states = collections.Counter()
    failed: dict[str, str] = {}
    warnings: list[dict] = []
    revalidation_errors = []
    for name, kind, items in batches:
        committed = builders.read_jsonl_files([INP / f"{name}.jsonl"])
        assert committed == items, f"{name}: committed input differs from a fresh build"
        log = json.loads((GEN / f"{name}.log.json").read_text(encoding="utf-8"))
        assert log["input_sha256"] == builders.sha256_text(builders.ordered_jsonl_text(items)), name
        assert log["prompt_sha256"] == builders.sha256_text(runner.prompt_text(6, items)), name
        assert log["model"] == runner.MODEL_ID, name
        states[(kind, log["validation"]["state"])] += 1
        values = builders.read_jsonl_files([GEN / f"{name}.jsonl"])
        present = {v["key"] for v in values}
        sub = [i for i in items if i["key"] in present]
        _, errs, warns = V.validate_task6_items(values, sub, kind)
        if errs:
            revalidation_errors.append((name, errs))
        warnings.extend(warns)
        failed.update(log["failed_errors"])
        missing = {i["key"] for i in items} - present
        assert missing == set(log["failed_keys"]), name
        for i in items:
            items_by_key[i["key"]] = i
            kind_by_key[i["key"]] = kind
            batch_of[i["key"]] = name
        for v in values:
            outputs[v["key"]] = v
    print("prompt SHA used (current files):", {k: v[:12] for k, v in sha_v2.items()})
    print("batch states:", dict(states))
    print("re-validation errors:", revalidation_errors or "none")
    print("outputs:", len(outputs), "failed keys:", len(failed))
    rows = list(csv.DictReader(open(ROOT / "content" / "cost_log.csv", encoding="utf-8")))
    print("ledger total $%.8f; task 6 $%.8f; task-6 requests %d" % (
        sum(float(r["usd"]) for r in rows), sum(float(r["usd"]) for r in rows if r["task"] == "6"),
        sum(r["task"] == "6" for r in rows)))

    # 2. diagnosis
    chars = pd.read_csv(ROOT / "data/final/chars.csv", dtype=str, keep_default_na=False)
    words = pd.read_csv(ROOT / "data/final/words.csv", dtype=str, keep_default_na=False)
    gaps = collections.defaultdict(set)
    for _, r in chars.iterrows():
        for p in r["pinyin_all"].split(";"):
            if p and V._toneless(p) not in V.PINYIN_SYLLABLES:
                gaps[V._toneless(p)].add(r["simp"])
    print("inventory gaps (chars.pinyin_all):", {k: "".join(sorted(v)) for k, v in gaps.items()})
    gap_chars = set().union(*gaps.values())
    zh_ok = [v for k, v in outputs.items() if kind_by_key[k] == "zh" and v["status"] == "ok"]
    print("validated zh ok sentences:", len(zh_ok),
          "| containing a gap character:", sum(bool(set(v["sentence"]) & gap_chars) for v in zh_ok),
          "| pinyin starting with a vowel:", sum(V._toneless(v["pinyin"].lstrip('"“('))[:1] in "aeiou" for v in zh_ok))
    with open(out / "failed.tsv", "w", encoding="utf-8") as f:
        for k, m in sorted(failed.items()):
            i = items_by_key[k]
            cause = "gap_in_target" if set(i["target"]) & gap_chars else ("invalid_notation" if "notation" in m else "context")
            f.write("\t".join([batch_of[k], k, i["target"], i["target_pinyin"], i["level"], cause, m.split(": ", 1)[-1]]) + "\n")

    # 3. word-level pinyin check: longest words.simp match (>= 2 chars) inside each sentence
    dict_py = collections.defaultdict(set)
    for _, r in words.iterrows():
        if r["simp"] and r["pinyin"] and len(r["simp"]) >= 2:
            for p in r["pinyin"].split(";"):
                dict_py[r["simp"]].add(p.casefold().replace("'", "").replace(" ", ""))
    maxlen = 8
    py_flags = []
    for v in zh_ok:
        han = V.HAN_RE.findall(v["sentence"])
        al = V._pinyin_alignments(v["sentence"], v["pinyin"].replace("’", "'"))[0]
        syl = {left: marked for left, right, marked, _ in al}
        pos = 0
        s = "".join(han)
        while pos < len(s):
            hit = None
            for n in range(min(maxlen, len(s) - pos), 1, -1):
                if s[pos:pos + n] in dict_py:
                    hit = n
                    break
            if not hit:
                pos += 1
                continue
            got = "".join(syl.get(j, "") for j in range(pos, pos + hit)).casefold()
            if all(j in syl for j in range(pos, pos + hit)) and got not in dict_py[s[pos:pos + hit]]:
                exp = sorted(dict_py[s[pos:pos + hit]])
                # ignore pure neutral-tone/tone-mark-only differences on the last syllable? keep all; read.
                py_flags.append((v["key"], s[pos:pos + hit], got, "/".join(exp), v["sentence"]))
            pos += hit
    with open(out / "pinyin_flags.tsv", "w", encoding="utf-8") as f:
        for row in py_flags:
            f.write("\t".join(row) + "\n")
    print("word-level pinyin differences:", len(py_flags))

    # status counts
    st = collections.Counter((kind_by_key[k], v.get("status", "note"), v["confidence"]) for k, v in outputs.items())
    print("status/confidence:", dict(st))
    wc = collections.Counter((kind_by_key[w["key"]], w["warning"]) for w in warnings)
    print("warnings:", dict(wc))
    json.dump(warnings, open(out / "warnings.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)

    # 4. extracts
    def line(k: str) -> str:
        i, v = items_by_key[k], outputs.get(k)
        kind = kind_by_key[k]
        if v is None:
            return f"{k}\tFAILED"
        if kind == "note":
            ex_zh = ",".join(e["simp"] for e in i["zh_examples"])
            ex_vi = ",".join(e["vi"] + ("*" if e["literary"] else "") for e in i["vi_examples"])
            return f"{k}\t{i['char']}/{i['simp']}/{i['jp']}\t{i['pinyin']}\t{i['vi']}\t{i['reason']}\tzh:{ex_zh}\tvi:{ex_vi}\tsingle:{i['vi_single_use']}\t>> {v['note_ja']}\t[{v['confidence']}] {v['review_note']}"
        trap = f"TRAP vs「{i['contrast_meaning_ja']}」" if i["is_trap"] else ""
        extra = f"\t{i.get('vi_use', '')}" if kind == "vi" else ""
        py = f"\t{v['pinyin']}" if kind == "zh" and v["status"] == "ok" else ""
        return (f"{k}\tL{i['level']}\t{i['target']}\t{i['meaning_ja']}\t{trap}{extra}\t"
                f"{v['status']}/{v['confidence']}\t{v['sentence']}{py}\t=「{v['translation_ja']}」\t{v['review_note']}")

    def write(name: str, keys: list[str]) -> None:
        with open(out / name, "w", encoding="utf-8") as f:
            for k in keys:
                f.write(line(k) + "\n")
        print(f"{name}: {len(keys)}")

    order = [i["key"] for _, _, items in batches for i in items]
    lvl = lambda k: items_by_key[k]["level"]  # noqa: E731
    write("zh_card_L1-3.tsv", [k for k in order if k.endswith(":zh:card") and lvl(k) in {"1", "2", "3"}])
    write("vi_card_L1-3.tsv", [k for k in order if k.endswith(":vi:card") and lvl(k) in {"1", "2", "3"}])
    write("zh_ff.tsv", [k for k in order if k.endswith(":zh:ff")])
    write("vi_ff.tsv", [k for k in order if k.endswith(":vi:ff")])
    write("notes.tsv", [k for k in order if k.endswith(":note")])
    write("no_sentence_low.tsv", [k for k in order if k in outputs and (outputs[k].get("status") == "no_sentence" or outputs[k]["confidence"] == "low")])
    rng = random.Random(SEED)
    for lang in ("zh", "vi"):
        hi = [k for k in order if k.endswith(f":{lang}:card") and lvl(k) not in {"1", "2", "3"}]
        trap_cards = [k for k in order if k.endswith(f":{lang}:card") and items_by_key[k]["is_trap"]]
        write(f"{lang}_sample_L4-7.tsv", sorted(rng.sample(hi, 150), key=order.index))
        write(f"{lang}_sample_trapcard.tsv", sorted(rng.sample(trap_cards, min(100, len(trap_cards))), key=order.index))
    warn_keys = sorted({w["key"] for w in warnings if w["warning"] != "empty_note_ja"}, key=order.index)
    write("warned.tsv", warn_keys)


if __name__ == "__main__":
    main(sys.argv[1])
