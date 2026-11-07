"""Stage 4 gate part 4 (task 5) reference script (Claude, 2026-11-07).

Offline. Rebuilds the task-5 inputs, compares them with the inputs sent,
re-validates every generated batch, and writes a merged review table
(inputs + outputs + words columns) to the path given as argv[1].
"""
import glob, json, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.stage4 import builders, validators  # noqa: E402

def main(out_path: str) -> None:
    fresh = builders.build_task5_batches()
    sent = sorted(glob.glob(str(ROOT / "content/inputs/task5/b*.jsonl")))
    assert len(fresh) == len(sent) == 104, (len(fresh), len(sent))
    same = sum(builders.jsonl_text(b) == Path(p).read_text(encoding="utf-8") for b, p in zip(fresh, sent))
    print(f"inputs equal to a fresh build: {same}/104")
    rows, bad = [], []
    for p in sent:
        name = Path(p).stem
        items = builders.read_jsonl_files([Path(p)])
        outp = ROOT / "content/generated/task5" / f"{name}.jsonl"
        if not outp.exists():
            bad.append((name, "no output"))
            continue
        out = builders.read_jsonl_files([outp])
        try:
            validators.validate_task5(out, items)
        except Exception as exc:  # noqa: BLE001
            bad.append((name, str(exc)))
        om = {o["key"]: o for o in out}
        for it in items:
            r = dict(it)
            r["checks"] = ",".join(it["checks"])
            r["batch"] = name
            r.update({k: v for k, v in om.get(it["key"], {}).items() if k != "key"})
            rows.append(r)
    print("validator failures:", bad)
    df = pd.DataFrame(rows)
    words = pd.read_csv(ROOT / "data/final/words.csv", dtype=str, keep_default_na=False)
    w = words.set_index("word_id")[["level", "origin", "ja_common", "card_eligible", "jp", "simp"]]
    df = df.join(w, on="key")
    df["is_row"] = ~df["key"].str.match(r"^w\d{5}$")
    df.to_pickle(out_path)
    print(len(df), "items")

if __name__ == "__main__":
    main(sys.argv[1])
