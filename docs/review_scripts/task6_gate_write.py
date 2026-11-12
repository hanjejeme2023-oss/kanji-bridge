"""Task-6 gate decisions (Claude, 2026-11-12). Offline; no request.

Writes config/task6_review.csv, config/task6_rerun.csv (round 1) and
docs/TASK6_USER_SAMPLE.md from the decisions below. Every `generated` value is
copied from the stored output and must exist, so the overlay is fail-closed.
Usage: python -X utf8 docs/review_scripts/task6_gate_write.py
"""
from __future__ import annotations

import csv
import glob
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = 20261112

# --- rerun round 1: the sentence (or its pinyin) is wrong; Claude never writes zh/vi text
PINYIN = "Pinyin error outside the target: {0}. Keep the sentence if it is natural; write the dictionary pinyin."
RERUN = {
    "w00064:zh:card": PINYIN.format("今年 is jīnnián, not jīnniān") + " Also prefer a more natural sentence (她今年上大学了 style).",
    "w00099:zh:card": PINYIN.format("今年 is jīnnián, not jīnniān"),
    "w00432:zh:card": PINYIN.format("今年 is jīnnián, not jīnniān"),
    "w10550:zh:card": PINYIN.format("今年 is jīnnián, not jīnniān"),
    "w07513:zh:card": PINYIN.format("气温 is qìwēn, not qīwēn"),
    "w08563:zh:card": PINYIN.format("气温 is qìwēn, not qīwēn"),
    "w09251:zh:card": PINYIN.format("气温 is qìwēn, not qīwēn"),
    "w01990:zh:card": PINYIN.format("发展 is fāzhǎn, not fǎzhǎn"),
    "w07028:zh:card": PINYIN.format("穿过 is chuānguò, not chuāngguò"),
    "w09720:zh:card": PINYIN.format("当天 'that same day' is dàngtiān, not dāngtiān"),
    "w13069:zh:ff": PINYIN.format("当晚 'that same evening' is dàngwǎn, not dāngwǎn"),
    "w00418:zh:card": "非常谢谢 is unnatural; write a natural sentence with 谢谢 (e.g. 谢谢你帮我…).",
    "w01521:zh:card": "这件东西有很长的古代历史 is unnatural Chinese; write a natural sentence using 古代 as 'ancient times'.",
    "w01855:zh:card": "年头太多了，你认得他吗 is unnatural; write a natural sentence with 认得 'to recognize, know'.",
    "w01914:zh:card": "这件事件 is redundant; use 这一事件/这个事件 or another natural sentence.",
    "w02521:zh:card": "The sentence is redundant (太过了…太过于过分了); write one natural sentence with 过分.",
    "w04280:zh:ff": "被老师挨了一顿批评 is ungrammatical; 挨 takes the hardship as object (他挨了老师一顿批评).",
    "w13035:zh:ff": "The sentence contains 应急 + 用, not the word 急用; write a sentence where 急用 itself is the word (留着急用).",
    "w12480:zh:ff": "The wife of a crown prince (王储) is not a 王妃; write a factually correct sentence about a king's consort.",
    "w00232:vi:card": "'trên mã thượng' is not Vietnamese. Use the current sense that matches 堂々とした: generous, chivalrous (tinh thần mã thượng, thái độ mã thượng), or return no_sentence.",
    "w00589:vi:card": "'buổi xuân tiết' is not idiomatic. Write a sentence only if xuân tiết is really used today in the meaning given; otherwise return no_sentence.",
    "w01408:vi:card": "The sentence uses đáo để as 'sharp-tongued', but the meaning shown is 'extremely, thoroughly' (khó đáo để, ghét đáo để). Use that meaning.",
    "w12232:vi:card": "'phong thái rất đường đường' is unnatural. Use a real pattern (đường đường là…, đường đường chính chính) or return no_sentence.",
    "w02310:vi:card": "'nên người thành nhân' is redundant and forced. Write a natural formal sentence with thành nhân (an adult), or return no_sentence.",
    "w11344:vi:card": "'trăm họ bách tính' repeats the same meaning. Write a sentence with bách tính alone.",
}

# --- overlay rows: (key, action, field, review text or '', reason)
OVERLAY = [
    # forced archaic / wrong word: the model was unsure itself (low) or the syllable is another word
    ("w00962:vi:card", "drop", "sentence", "", "nhân số is not used for 人数 (low; Vietnamese: số người, nhân sự)"),
    ("w03919:vi:card", "drop", "sentence", "", "số mục is archaic in this sense (low)"),
    ("w03941:vi:card", "drop", "sentence", "", "năm tháng tuế nguyệt is redundant and forced (low)"),
    ("w03963:vi:card", "drop", "sentence", "", "đề khởi is archaic (low); today đề xuất / khởi xướng"),
    ("w04261:vi:card", "drop", "sentence", "", "tư sản means bourgeois today, not 私有財産 (low)"),
    ("w04626:vi:card", "drop", "sentence", "", "quốc sản is not current (low)"),
    ("w04649:vi:card", "drop", "sentence", "", "hòa hài is a rare inversion of hài hòa (low)"),
    ("w00500:vi:ff", "drop", "sentence", "", "tẩu tán is another word (hide assets), not 走る/逃げる (low)"),
    ("w04713:vi:ff", "drop", "sentence", "", "ngũ giác means pentagon; five senses is ngũ quan / năm giác quan"),
    ("w07626:vi:ff", "drop", "sentence", "", "chân tướng cứu cánh is not Vietnamese (low)"),
    # Japanese translation fixes (zh/vi text unchanged)
    ("w01358:zh:card", "set_translation_ja", "translation_ja", "木になっているりんごはもう熟している。", "「の」 lost the word 木"),
    ("w00980:zh:card", "set_translation_ja", "translation_ja", "今日はとても寒い。", "「天気がとても寒い」 is not natural Japanese"),
    ("w01400:zh:card", "set_translation_ja", "translation_ja", "うちはこの建物の三号ユニット（三番目の階段口）にあります。", "单元 is a stairwell section, not 棟; 「私の家は…に住んでいる」 is not Japanese"),
    ("w01365:zh:card", "set_translation_ja", "translation_ja", "彼女は未来への希望に満ちあふれている。", "「未来に希望で満ちあふれている」 is ungrammatical"),
    ("w02101:zh:card", "set_translation_ja", "translation_ja", "私は空港へ友人を迎えに行く。", "typo 向かえ"),
    ("w02209:zh:card", "set_translation_ja", "translation_ja", "私たちの会社は今、十分な資金がない。", "「十分な資金が不足している」 is contradictory"),
    ("w12786:zh:ff", "set_translation_ja", "translation_ja", "あの大先輩はずっと熱心に若手を引き立てている。", "stray Arabic letters in the translation"),
    ("w13097:zh:ff", "set_translation_ja", "translation_ja", "現代中国語では、普通の女性俳優を「女优」とは呼ばない。", "the old translation was confusing"),
    ("w01383:vi:card", "set_translation_ja", "translation_ja", "前世紀の初め頃、その老人は地元のフランス理事官府に勤めていたことがある。", "tòa sứ is the French Résident's office, not 公使館"),
    ("w12241:vi:card", "set_translation_ja", "translation_ja", "封建時代、郷試の三場まで合格した者は「生徒」という称号で呼ばれた。", "make clear 生徒 is a title"),
    ("w00200:vi:ff", "set_translation_ja", "translation_ja", "先生が生徒に口頭試問をしている。", "stray Arabic letters in the translation"),
    ("w00768:vi:ff", "set_translation_ja", "translation_ja", "先生が生徒に授業で説明している。", "stray Arabic letters in the translation"),
    ("w03385:vi:ff", "set_translation_ja", "translation_ja", "今週末、友人にごちそうするために鍋料理を作るつもりだ。", "「友人を振る舞う」 is not Japanese"),
    # note wording (Chinese/Vietnamese words unchanged)
    ("c00772:note", "set_note_ja", "note_ja", "ベトナム語で「切る」は普通 cắt と言う", "thiết does not mean 切る in Vietnamese"),
    ("c00558:note", "set_note_ja", "note_ja", "中国語では「1億」を一亿と日常的に言う。ベトナム語では một trăm triệu と言う", "「（百百万）」 was confusing"),
    ("c00764:note", "set_note_ja", "note_ja", "ベトナム語で「りんご」は普通 táo と言う", "bom is dated"),
    ("c01370:note", "set_note_ja", "note_ja", "ベトナム語で水を「かける・まく」は普通 hắt や tạt と言う", "garbled Japanese (「普通泼に相当する」)"),
    ("c01700:note", "set_note_ja", "note_ja", "中国語ではご飯などを「よそう・盛る」意味でも日常的に使う（読みは別）", "extra reading 'cheng' without tone (prompt rule)"),
]


def load(pattern: str) -> dict[str, dict]:
    data = {}
    for path in sorted(glob.glob(str(ROOT / pattern))):
        for line in open(path, encoding="utf-8"):
            value = json.loads(line)
            data[value["key"]] = value
    return data


def main() -> None:
    outputs = load("content/generated/task6/b*.jsonl")
    inputs = load("content/inputs/task6/b*.jsonl")
    assert not set(RERUN) & {row[0] for row in OVERLAY}
    for key in RERUN:
        assert key in outputs and outputs[key].get("status") == "ok", key
    rows = []
    for key, action, field, review, reason in OVERLAY:
        generated = outputs[key][field]
        assert generated, key
        if action != "drop":
            assert review and len(review) <= 60 and review != generated, key
        rows.append({"key": key, "action": action, "generated": generated, "review": review, "reason": reason})
    with open(ROOT / "config/task6_review.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ["key", "action", "generated", "review", "reason"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    with open(ROOT / "config/task6_rerun.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ["round", "key", "reason"], lineterminator="\n")
        w.writeheader()
        for key, reason in RERUN.items():
            w.writerow({"round": "1", "key": key, "reason": reason})
    print("task6_review.csv", len(rows), "task6_rerun.csv", len(RERUN))

    # --- user sample: 12 zh, 12 vi, 6 notes; validated ok items not touched by the gate
    touched = set(RERUN) | {row[0] for row in OVERLAY}
    rng = random.Random(SEED)
    pick = lambda pool, n: sorted(rng.sample(sorted(pool), n))  # noqa: E731
    zh = pick([k for k, v in outputs.items() if ":zh:" in k and v["status"] == "ok" and k not in touched], 12)
    vi = pick([k for k, v in outputs.items() if ":vi:" in k and v["status"] == "ok" and k not in touched], 12)
    nt = pick([k for k, v in outputs.items() if k.endswith(":note") and v["note_ja"] and k not in touched], 6)
    lines = [
        "# 例文タスク（task 6）：日本語のサンプル確認（30項目）",
        "",
        "Claude, 2026-11-12. 決定 **D74**。所要 10 分ほど。",
        "",
        "**確認するのは日本語だけです。** 中国語・ベトナム語の文は Claude が確認済みなので、判断は不要です（読めなくて構いません）。",
        "各項目の「日本語訳」または「メモ」が、日本語として自然で、学習者に役立つかを見てください。",
        "",
        "- ○ = 自然で問題なし　△ = 少し不自然（ひとこと理由を）　× = おかしい／誤解を招く",
        "- 答え方：表の「判定」欄に ○ / △ / × を書き、△・× には短いコメントを添えてください（Claude への貼り付けでも構いません）。",
        f"- 抽出：seed {SEED}、Claude が修正・再生成の対象にした項目は除外。",
        "",
        "## A. 中国語の例文（12）",
        "",
        "| # | 単語 | 意味（アプリの表示） | 文 | 日本語訳 | 判定 | コメント |",
        "|---|---|---|---|---|---|---|",
    ]
    n = 0
    for key in zh:
        n += 1
        i, o = inputs[key], outputs[key]
        lines.append(f"| A{n} | {i['target']} | {i['meaning_ja']} | {o['sentence']} | {o['translation_ja']} |  |  |")
    lines += ["", "## B. ベトナム語の例文（12）", "",
              "| # | 単語（漢字） | 意味（アプリの表示） | 文 | 日本語訳 | 判定 | コメント |",
              "|---|---|---|---|---|---|---|"]
    n = 0
    for key in vi:
        n += 1
        i, o = inputs[key], outputs[key]
        lines.append(f"| B{n} | {i['target']}（{i['trad']}） | {i['meaning_ja']} | {o['sentence']} | {o['translation_ja']} |  |  |")
    lines += ["", "## C. 字体の使われ方メモ（6）", "",
              "| # | 字 | 中国語 / ベトナム語の読み | メモ | 判定 | コメント |",
              "|---|---|---|---|---|---|"]
    n = 0
    for key in nt:
        n += 1
        i, o = inputs[key], outputs[key]
        lines.append(f"| C{n} | {i['char']} | {i['pinyin']} / {i['vi']} | {o['note_ja']} |  |  |")
    lines += ["", "## 回答", "", "（ここに記入、または Claude に「A3 △ …」の形で貼り付け）", ""]
    (ROOT / "docs/TASK6_USER_SAMPLE.md").write_text("\n".join(lines), encoding="utf-8")
    print("user sample", len(zh), len(vi), len(nt))


if __name__ == "__main__":
    main()
