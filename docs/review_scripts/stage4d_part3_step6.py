"""Step 6 (D57 Q1, D64 item 5): write the user-confirmed Vietnamese clears (Claude, 2026-11-07).

User answer 2026-11-07: "All as proposed. A27: clear." -> group A: clear 37 (keep A20 低迷, A36 預算);
group B: clear all 28. Prints what it would write; with --write appends the rows (refuses duplicates).
Run: python docs/review_scripts/stage4d_part3_step6.py [--write]
One-shot: it checks the pre-step-6 build (commit 2da3e9b) and was run once with --write on 2026-11-07;
afterwards its value asserts fail by design (the values are cleared).
"""
import csv, glob, json, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.stage4 import builders  # noqa: E402
sys.stdout.reconfigure(encoding="utf-8")
KW = dict(dtype=str, keep_default_na=False, encoding="utf-8")
W = pd.read_csv(ROOT / "data/final/words.csv", **KW).set_index("word_id", drop=False)

# group A, in VI_CLEAR_SHORTLIST.md order: (no, trad, vi value on the list)
A = [("A1", "姐姐", "thư thư"), ("A2", "星期", "tinh kỳ"), ("A3", "手指", "thủ chỉ"), ("A4", "信封", "tín phong"),
     ("A5", "大型", "đại hình"), ("A6", "期中", "kỳ trung"), ("A7", "童年", "đồng niên"), ("A8", "自制", "tự chế"),
     ("A9", "消防", "tiêu phòng"), ("A10", "依法", "y pháp"), ("A11", "中斷", "trung đoạn"), ("A12", "創意", "sáng ý"),
     ("A13", "傷口", "thương khẩu"), ("A14", "一行", "nhất hạng"), ("A15", "案件", "yên kiện"), ("A16", "白白", "bạch bạch"),
     ("A17", "標示", "tiêu thị"), ("A18", "波瀾", "ba lan"), ("A19", "低調", "đê điều"), ("A21", "地步", "địa bộ"),
     ("A22", "更改", "canh cải"), ("A23", "公事", "công sự"), ("A24", "海盜", "hải đạo"), ("A25", "荷花", "hà hoa"),
     ("A26", "進出", "tấn xuất"), ("A27", "境界", "cảnh giới"), ("A28", "領略", "lĩnh lược"), ("A29", "平價", "bình giá"),
     ("A30", "親身", "thân thân"), ("A31", "傷痕", "thương ngân"), ("A32", "時空", "thời không"), ("A33", "手勢", "thủ thế"),
     ("A34", "推移", "suy di"), ("A35", "液體", "giá thể"), ("A37", "真假", "chân giả"), ("A38", "蓮步", "liên bộ"),
     ("A39", "季女", "quý nữ")]
KEEP = {"低迷", "預算"}
B = ["上達", "不詳", "中堅", "主因", "再建", "器物", "奇数", "巡礼", "市立", "帰化", "手紙", "敬老", "旗標", "東経", "植樹",
     "清流", "網羅", "越冬", "雨季", "青色", "食材", "飼主", "高揚", "鮮烈", "観客", "文教", "新作", "新規"]

# the candidate set the list was drawn from must be exactly A + KEEP
t1 = builders.apply_task1_review([json.loads(l) for p in sorted(glob.glob(str(ROOT / "content/accepted/task1/b*.jsonl")))
                                  for l in open(p, encoding="utf-8")])
cand = {o["word_id"] for o in t1 if o["vi_check"] == "different_word" or (o["vi_check"] == "unsure" and len(W.loc[o["word_id"]].trad) > 1)}
assert {W.loc[k].trad for k in cand} == {t for _, t, _ in A} | KEEP, "candidate set changed"
assert len(cand) == 39
rows_a = []
for no, trad, vi in A:
    (wid,) = [k for k in cand if W.loc[k].trad == trad]
    w = W.loc[wid]
    assert w.vi == vi, (no, trad, w.vi, vi)
    rows_a.append(["words", f"x|{w.trad}" if w.origin == "vi_freq" else f"{w.trad}|{w.pinyin}", "vi", "", f"D64/D65 VI_CLEAR_SHORTLIST {no}: {vi} is a different word (user-confirmed 2026-11-07)"])

ff = pd.read_csv(ROOT / "data/staging/ff_candidates.csv", **KW)
t2 = {json.loads(l)["key"]: json.loads(l) for p in sorted(glob.glob(str(ROOT / "content/accepted/task2/b*.jsonl"))) for l in open(p, encoding="utf-8")}
rows_b = []
for k, form in enumerate(B, 1):
    hit = ff[(ff.form == form) | (ff.trad == form)]
    assert len(hit) == 1, (form, len(hit))
    key = hit.iloc[0].form
    o = t2[key]
    (m,) = [m for m in o["meanings"] if m["lang"] == "vi"]
    rows_b.append([key, "vi", "clear_vi", m["meaning_ja"], str(m["is_trap"]).lower(), "",
                   ";".join(l for l in o["false_friend"] if l != "vi"),
                   f"D64/D65 VI_CLEAR_SHORTLIST B{k}: vi {hit.iloc[0].vi} is a different word or a place name (user-confirmed 2026-11-07)"])

for r in rows_a + rows_b:
    print(r)
print(len(rows_a), "override rows,", len(rows_b), "clear_vi rows")
if "--write" in sys.argv:
    ov = pd.read_csv(ROOT / "pipeline/overrides.csv", **KW)
    assert not set(ov.key[ov.column == "vi"]) & {r[1] for r in rows_a}, "override rows already present"
    rv = pd.read_csv(ROOT / "config/task2_review.csv", **KW)
    assert not set(rv.key[rv.action == "clear_vi"]) & {r[0] for r in rows_b}, "clear_vi rows already present"
    for path, rows in ((ROOT / "pipeline/overrides.csv", rows_a), (ROOT / "config/task2_review.csv", rows_b)):
        raw = path.read_bytes()
        nl = "\r\n" if b"\r\n" in raw else "\n"
        with open(path, "a", encoding="utf-8", newline="") as f:
            if not raw.endswith(nl.encode()):
                f.write(nl)
            csv.writer(f, lineterminator=nl).writerows(rows)
    print("written")
