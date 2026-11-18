"""Release part R1 (RELEASE_PLAN §1, §2.5, §2.6; D78): one test per fix.

Data checks read the rebuilt ``data/final`` tables and ``data.js``; the overlay,
exclusion and refresh-check functions are also tested on synthetic inputs so a
fail-closed path is proven without a rebuild.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

import download  # noqa: E402
import load_kaikki  # noqa: E402
import refresh_check  # noqa: E402
from pipeline import build_app  # noqa: E402
from pipeline.export_app_data import _first_three_words  # noqa: E402
from pipeline.merge_stage4 import apply_task1_meaning_review, apply_task2_reviews  # noqa: E402

FINAL = ROOT / "data" / "final"


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(FINAL / name, dtype=str, keep_default_na=False)


def data_js() -> dict:
    text = (FINAL / "data.js").read_text(encoding="utf-8")
    return json.loads(text[len("window.KB_DATA = "):-2])


class R1DataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.words = read("words.csv").set_index("word_id")
        cls.chars = read("chars.csv")
        cls.chars_by_key = cls.chars.set_index("key_char")
        cls.ff = read("ff_meanings.csv")
        cls.kb = data_js()
        cls.kb_chars = {row["char_id"]: row for row in cls.kb["chars"]}

    # §1.1 使われ方 duplicates
    def test_usage_lists_each_word_once(self) -> None:
        for char_id, zh, vi in self.kb["usage"]:
            for lang, rows in (("zh", zh), ("vi", vi)):
                ids = [row[0] for row in rows]
                self.assertEqual(len(ids), len(set(ids)), f"{char_id} {lang}: {ids}")
                self.assertLessEqual(len(rows), 3)
        ba = self.chars_by_key.loc["爸", "char_id"]
        usage = next(row for row in self.kb["usage"] if row[0] == ba)
        self.assertEqual([row[0] for row in usage[1]].count("w00004"), 1)  # 爸爸 once
        self.assertEqual(usage[1][0][1], 1)  # first position kept

    def test_first_three_words_gives_freed_slot_to_next_candidate(self) -> None:
        candidates = [
            ((1, "w2"), ["w2", 2, "b"]), ((1, "w2"), ["w2", 1, "a"]),
            ((2, "w3"), ["w3", 1, "c"]), ((3, "w4"), ["w4", 1, "d"]), ((4, "w5"), ["w5", 1, "e"]),
        ]
        self.assertEqual(_first_three_words(candidates), [["w2", 1, "a"], ["w3", 1, "c"], ["w4", 1, "d"]])

    # §1.3 吧: no Nôm reading on the card or in 字体
    def test_ba_has_no_nom_reading(self) -> None:
        self.assertEqual(self.words.loc["w00006", "trad"], "吧")
        self.assertEqual(self.words.loc["w00006", "vi"], "")
        self.assertEqual(self.words.loc["w00006", "source_vi"], "")
        self.assertEqual(self.chars_by_key.loc["吧", "source_vi"], "unihan_unverified")
        ba = self.chars_by_key.loc["吧", "char_id"]
        self.assertNotIn("vi_all", self.kb_chars[ba])
        glyph = next(row for row in self.kb["glyphs"] if row[0] == ba)
        self.assertEqual(glyph[4], [])
        staging = pd.read_csv(ROOT / "data" / "staging" / "kaikki_char_readings.csv", dtype=str, keep_default_na=False)
        self.assertTrue(staging.loc[staging["char"] == "吧"].empty)

    # §1.3 錯 and every unihan_unverified character
    def test_unverified_readings_never_reach_glyph_rows(self) -> None:
        unverified = set(self.chars.loc[self.chars["source_vi"] == "unihan_unverified", "char_id"])
        glyph_ids = {row[0] for row in self.kb["glyphs"]}
        shown = [cid for cid in glyph_ids & unverified if self.kb_chars[cid].get("vi_all")]
        self.assertEqual(shown, [])
        self.assertEqual(len(glyph_ids & unverified), 290)  # 289 before R1 + 吧
        cuo = self.chars_by_key.loc["錯", "char_id"]
        self.assertEqual(self.chars_by_key.loc["錯", "vi"], "thó")  # kept in chars.csv, flagged
        self.assertNotIn("vi_all", self.kb_chars[cuo])
        for row in self.kb["glyphs"]:
            if row[0] in unverified and not row[1]:
                self.assertEqual(row[4], [], row[0])

    # §1.3 荷 痕 瀾 蓮
    def test_no_evidence_report_marks_character_source_evidence(self) -> None:
        report = read("char_primary_no_evidence.csv")
        vi = report.loc[report["lang"] == "vi"].set_index("key_char")
        for char in "荷痕瀾蓮":
            self.assertEqual(vi.loc[char, "char_source_evidence"], "true", char)
        self.assertEqual(vi.loc["錯", "char_source_evidence"], "false")
        self.assertTrue((report.loc[report["lang"] == "ko", "char_source_evidence"] == "false").all())

    # §1.3 review overlays 那邊 / 器械
    def test_korean_meaning_overlays_reach_every_table(self) -> None:
        expected = {"w00262": "どこ、どのあたり", "w08625": "器具、器械"}
        kb_words = {row["word_id"]: row for row in self.kb["words"]}
        for word_id, meaning in expected.items():
            self.assertEqual(self.words.loc[word_id, "meaning_ja__ko"], meaning)
            rows = self.ff.loc[(self.ff["word_id"] == word_id) & (self.ff["lang"] == "ko")]
            self.assertEqual(rows["meaning_ja"].tolist(), [meaning])
            self.assertEqual(rows["is_trap"].tolist(), ["false"])
            kb_rows = [row for row in self.kb["ff_meanings"] if row["word_id"] == word_id and row["lang"] == "ko"]
            self.assertEqual([row["meaning_ja"] for row in kb_rows], [meaning])
            self.assertEqual(kb_words[word_id].get("false_friend"), self.words.loc[word_id, "false_friend"])
        self.assertEqual(self.words.loc["w00262", "false_friend"], "zh")  # the Chinese trap stays
        self.assertEqual(self.words.loc["w08625", "false_friend"], "vi")


class R1OverlayTest(unittest.TestCase):
    words = pd.DataFrame([{"word_id": "w1", "trad": "那邊"}])
    review = pd.DataFrame([{
        "word_id": "w1", "trad": "那邊", "lang": "ko", "meaning_ja_generated": "あちら",
        "meaning_ja_review": "どこ", "reason": "test",
    }])

    def test_task1_meaning_overlay_applies_once_and_fails_closed(self) -> None:
        outputs = {"w1": {"word_id": "w1", "meaning_ja__ko": "あちら"}}
        self.assertEqual(apply_task1_meaning_review(outputs, self.words, self.review)["w1"]["meaning_ja__ko"], "どこ")
        self.assertEqual(outputs["w1"]["meaning_ja__ko"], "あちら")  # input untouched
        with self.assertRaises(ValueError):  # generated text changed upstream
            apply_task1_meaning_review({"w1": {"meaning_ja__ko": "別"}}, self.words, self.review)
        with self.assertRaises(ValueError):  # duplicate row
            apply_task1_meaning_review(outputs, self.words, pd.concat([self.review, self.review]))
        with self.assertRaises(ValueError):  # unknown word
            apply_task1_meaning_review({}, self.words, self.review)

    def test_task2_set_meaning_keeps_trap_flags(self) -> None:
        outputs = {"w1": {"key": "w1", "false_friend": ["zh"], "meanings": [
            {"lang": "ko", "meaning_ja": "あちら", "is_trap": False},
            {"lang": "zh", "meaning_ja": "向こう", "is_trap": True}]}}
        empty = pd.DataFrame(columns=["key", "lang", "meaning_ja_generated", "is_trap_generated",
                                      "is_trap_review", "false_friend_review"])
        row = {"key": "w1", "lang": "ko", "action": "set_meaning", "meaning_ja_generated": "あちら",
               "is_trap_generated": "false", "meaning_ja_review": "どこ", "false_friend_review": "zh", "reason": "t"}
        result, _ = apply_task2_reviews(outputs, pd.DataFrame([row]), empty)
        self.assertEqual(result["w1"]["meanings"][0]["meaning_ja"], "どこ")
        self.assertTrue(result["w1"]["meanings"][1]["is_trap"])
        with self.assertRaises(ValueError):  # would turn ko into a trap
            apply_task2_reviews(outputs, pd.DataFrame([{**row, "false_friend_review": "ko;zh"}]), empty)


class R1Task6InputReviewTest(unittest.TestCase):
    def test_reviewed_task6_inputs_restore_exactly_and_fail_closed(self) -> None:
        from pipeline import merge_task6

        def fresh(value: str, use: str = "", reason: str = "vi_no_examples"):
            return [("b002", "zh", [{"key": "w00262:zh:card", "contrast_meaning_ja": value}]),
                    ("b212", "note", [{"key": "c00004:note", "vi_single_use": use, "reason": reason}])]

        batches = fresh("どこ、どのあたり")
        merge_task6._restore_reviewed_inputs(batches)
        self.assertEqual(batches[0][2][0]["contrast_meaning_ja"], "あちら、どのあたり")
        self.assertEqual(batches[1][2][0], {"key": "c00004:note", "vi_single_use": "literary",
                                            "reason": "vi_single_literary"})
        with self.assertRaises(ValueError):  # the fresh value is not the reviewed current value
            merge_task6._restore_reviewed_inputs(fresh("別の意味"))
        with self.assertRaises(ValueError):  # a listed key is missing from the fresh build
            merge_task6._restore_reviewed_inputs(fresh("どこ、どのあたり")[:1])

    def test_ba_has_no_stale_vietnamese_usage(self) -> None:
        words = read("words.csv")
        self.assertEqual(((words["vi"] == "") & (words["vi_use"] != "")).sum(), 0)
        kb_ba = next(row for row in data_js()["words"] if row["word_id"] == "w00006")
        self.assertNotIn("lit", kb_ba)


class R1LoaderAndRefreshTest(unittest.TestCase):
    def test_kaikki_exclusions_fail_closed(self) -> None:
        self.assertEqual(len(load_kaikki.load_exclusions()), 1)
        original = load_kaikki.EXCLUSIONS
        try:
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "x.csv"
                path.write_text("word,etymology,reason\ncả và,Âm Hán-Việt của X,\n", encoding="utf-8")
                load_kaikki.EXCLUSIONS = path
                with self.assertRaises(ValueError):  # no reason
                    load_kaikki.load_exclusions()
        finally:
            load_kaikki.EXCLUSIONS = original

    def test_download_only_is_limited_to_known_sources_with_refresh(self) -> None:
        self.assertEqual(download.parse_only("kanjidic2, jmdict", True), {"kanjidic2", "jmdict"})
        self.assertIsNone(download.parse_only(None, False))
        with self.assertRaises(RuntimeError):
            download.parse_only("kanjidic2", False)
        with self.assertRaises(RuntimeError):
            download.parse_only("kanjidic2,edict", True)

    def test_refresh_check_fails_on_id_change_and_reports_japanese_changes(self) -> None:
        words = pd.DataFrame([
            {"word_id": "w1", "trad": "學", "simp": "学", "pinyin": "xué", "jp": "学", "ja": "がく",
             "ja_alt": "", "ja_common": "true", "source_ja": "jmdict"}])
        ids = pd.DataFrame([{"kind": "word", "key": "學|xué", "id": "w1"}])
        chars = pd.DataFrame([{"char_id": "c1", "trad": "學", "jp": "学", "ja_on": "がく", "ja_on_all": "がく"}])
        changed = words.assign(ja="まな")
        errors, report = refresh_check.compare(words, changed, ids, ids, chars, chars)
        self.assertEqual(errors, [])
        self.assertEqual(report[["id", "column", "before", "after"]].values.tolist(), [["w1", "ja", "がく", "まな"]])
        new_word = pd.concat([words, words.assign(word_id="w2")])
        errors, _ = refresh_check.compare(words, new_word, ids, ids, chars, chars)
        self.assertTrue(any("added" in error for error in errors))
        errors, _ = refresh_check.compare(words, words.assign(pinyin="xuè"), ids, ids, chars, chars)
        self.assertTrue(any("pinyin changed" in error for error in errors))
        errors, _ = refresh_check.compare(words, words, ids, ids.assign(id="w9"), chars, chars)
        self.assertTrue(any("id_map" in error for error in errors))


class R1AppTest(unittest.TestCase):
    def test_title_and_about_panel(self) -> None:
        app = (ROOT / "app" / "index.html").read_text(encoding="utf-8")
        prototype = (ROOT / "prototype" / "index.html").read_text(encoding="utf-8")
        self.assertIn("<title>漢字ブリッジ（試作版）</title>", prototype)  # frozen prototype unchanged
        self.assertIn("<title>漢字ブリッジ</title>", app)
        self.assertEqual(app.count('id="about"'), 1)
        self.assertEqual(app.count("このアプリについて"), 3)  # link, panel heading, aria-label
        for text in (
            "These files are the property of the Electronic Dictionary Research and Development Group",
            "例文と一部の意味は AI（Google Gemini）が作ったもので、誤りを含むことがある。",
            "データは集めていない。学習の記録はこのブラウザの中だけに保存される。",
            'href="https://github.com/hanjejeme2023-oss/kanji-bridge"',
        ):
            self.assertIn(text, app)
        self.assertIn("e.key==='Escape'", app)
        self.assertEqual(app, build_app.build())

    def test_chunked_renderers_are_used_for_long_lists(self) -> None:
        app = (ROOT / "app" / "index.html").read_text(encoding="utf-8")
        self.assertIn("renderChunked('glyph'", app)
        self.assertIn("renderChunked('ff'", app)
        self.assertIn("function toggleFFTile(id)", app)
        self.assertIn("function render(){cancelChunks();", app)


if __name__ == "__main__":
    unittest.main()
