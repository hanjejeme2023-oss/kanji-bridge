"""D55 apply check (Claude, 2026-11-06). Evidence only, not pipeline.

Compares the working-tree build with a commit (default 4919d5b, the repeat-gate build):
character primaries and *_all sets (D52 tie rule), word `vi` changes, every override applied, HSK coverage.
Optional second argument: a directory with another build's chars.csv/words.csv to diff against as well
(used for the switch-on-only build, to separate the effect of the overrides from the effect of the switch).
Run: python docs/review_scripts/d55_apply_check.py [commit] [other_build_dir]
"""
import io
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250, "display.max_rows", 300, "display.max_colwidth", 50)
ROOT = Path(__file__).resolve().parents[2]
BASE = sys.argv[1] if len(sys.argv) > 1 else "4919d5b"
KW = dict(dtype=str, keep_default_na=False, encoding="utf-8")


def at(path):
    blob = subprocess.run(["git", "-C", str(ROOT), "show", f"{BASE}:{path}"], capture_output=True, check=True).stdout
    return pd.read_csv(io.StringIO(blob.decode("utf-8")), **KW)


def cur(path):
    return pd.read_csv(ROOT / path, **KW)


def diff(label, oc, nc, ow, nw):
    print(f"== {label}")
    m = oc.merge(nc, on="char_id", how="outer", suffixes=("_o", "_n"), validate="1:1", indicator=True)
    print("  chars:", m._merge.value_counts().to_dict())
    m = m[m._merge == "both"]
    for col in ["ko", "vi", "ko_final", "vi_final", "ja_on", "pinyin"]:
        d = m[m[f"{col}_o"] != m[f"{col}_n"]]
        print(f"  {col} changed {len(d)}:", list(zip(d.trad_n, d[f"{col}_o"], d[f"{col}_n"]))[:60])
    for col in ["ko_all", "vi_all", "ko_base_all"]:
        d = m[m[f"{col}_o"] != m[f"{col}_n"]]
        print(f"  {col} changed {len(d)}:", list(zip(d.trad_n, d[f"{col}_o"], d[f"{col}_n"]))[:20])
    w = ow.merge(nw, on="word_id", how="outer", suffixes=("_o", "_n"), validate="1:1", indicator=True)
    print("  words:", w._merge.value_counts().to_dict())
    for col in ["vi", "ko", "ja", "card_eligible"]:
        d = w[(w._merge == "both") & (w[f"{col}_o"] != w[f"{col}_n"])]
        print(f"  words {col} changed {len(d)}")
        if col != "vi" or len(d) < 120:
            print(d[["word_id", "trad_n", "pinyin_n", f"{col}_o", f"{col}_n"]].to_string(index=False) if len(d) else "")


nc, nw = cur("data/final/chars.csv"), cur("data/final/words.csv")
diff(f"against {BASE}", at("data/final/chars.csv"), nc, at("data/final/words.csv"), nw)
if len(sys.argv) > 2:
    other = Path(sys.argv[2])
    diff(f"against {other}", pd.read_csv(other / "chars.csv", **KW), nc, pd.read_csv(other / "words.csv", **KW), nw)

print("== overrides")
ov = cur("pipeline/overrides.csv")
idm = cur("pipeline/id_map.csv")
wkey = dict(zip(idm[idm.kind == "word"].key, idm[idm.kind == "word"].id))
wid, cidx = nw.set_index("word_id"), nc.set_index("key_char")
bad = []
for r in ov.itertuples():
    got = (wid.at[wkey[r.key], r.column] if r.table == "words" else cidx.at[r.key, r.column])
    if got != r.value:
        bad.append((r.table, r.key, r.column, r.value, got))
print(f"  rows {len(ov)}; not applied {bad}")
cleared = ov[(ov.table == "words") & (ov.value == "")]
alt = wid.loc[[wkey[k] for k in cleared.key], "vi_alt"]
print(f"  cleared {len(cleared)}; with non-empty vi_alt: {(alt != '').sum()}", alt[alt != ""].to_dict())
amb = cur("data/final/vi_ambiguous.csv")
print("  vi_ambiguous:", amb.reason.value_counts().to_dict())
hsk = nw[nw.origin != "vi_freq"]
print(f"== HSK {len(hsk)}: ja {(hsk.ja != '').sum()} ko {(hsk.ko != '').sum()} pinyin {(hsk.pinyin != '').sum()} "
      f"vi {(hsk.vi != '').sum()} all4 {((hsk.ja != '') & (hsk.ko != '') & (hsk.vi != '')).sum()}; "
      f"card_eligible HSK {(hsk.card_eligible == 'true').sum()} total {(nw.card_eligible == 'true').sum()}; "
      f"words with vi {(nw.vi != '').sum()}")
cpc = cur("data/final/char_primary_changes.csv")
print("  char_primary_changes rows", len(cpc))
