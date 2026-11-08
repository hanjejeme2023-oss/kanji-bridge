from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from pipeline import build_app, export_app_data


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "index.html"
PROTOTYPE = ROOT / "prototype" / "index.html"
DATA_JS = ROOT / "data" / "final" / "data.js"


def load_data_js() -> dict:
    text = DATA_JS.read_text(encoding="utf-8")
    prefix = "window.KB_DATA = "
    if not text.startswith(prefix) or not text.endswith(";\n"):
        raise AssertionError("data.js is not one window.KB_DATA statement")
    return json.loads(text[len(prefix) : -2])


def reference_due(deck, srs, introduced, target, now):
    def target_ok(word):
        if target == "vi":
            return bool(word.get("v"))
        if target == "zh":
            return bool(word.get("p"))
        return bool(word.get("v") and word.get("p"))

    eligible = [word for word in deck if target_ok(word)]
    reviews = [word for word in eligible if word["id"] in srs and srs[word["id"]]["due"] <= now]
    pending = [word for word in eligible if word["id"] not in srs and word["id"] in introduced]
    slots = max(0, 20 - len(introduced))
    fresh = [word for word in eligible if word["id"] not in srs and word["id"] not in introduced][:slots]
    return reviews + pending + fresh


class Stage5DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data_js()

    def test_data_js_is_reduced_and_has_no_nulls(self):
        data = self.data
        self.assertEqual(data["meta"]["counts"]["words"], 12508)
        self.assertEqual(data["meta"]["counts"]["glyphs"], 1246)
        self.assertEqual(len(data["words"]), 12508)
        self.assertEqual(len(data["chars"]), 1246)
        self.assertEqual(len(data["passages"]), 80)
        self.assertEqual(len(data["ff_meanings"]), 4044)

        def visit(value):
            self.assertIsNotNone(value)
            if isinstance(value, dict):
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
            elif isinstance(value, str):
                self.assertNotIn(value, {"undefined", "NaN", "None", "null"})

        visit(data)

    def test_words_omit_missing_values_and_vi_alt_without_vi(self):
        for word in self.data["words"]:
            if "vi" not in word:
                self.assertNotIn("vi_alt", word)
            self.assertIn("word_id", word)
            self.assertRegex(word["word_id"], r"^w\d{5}$")

    def test_rules_have_primary_aligned_unique_examples(self):
        chars = {
            row["key_char"]: row
            for row in export_app_data.read_csv(ROOT / "data" / "final" / "chars.csv")
        }
        for rule in self.data["rules"]:
            self.assertGreaterEqual(len(rule["ex"]), 4)
            self.assertLessEqual(len(rule["ex"]), 8)
            self.assertEqual(len({example[0] for example in rule["ex"]}), len(rule["ex"]))
            for key_char, ko, ja, vi, pinyin in rule["ex"]:
                char = chars[key_char]
                self.assertEqual([ko, ja, vi, pinyin], [char["ko"], char["ja_on"], char["vi"], char["pinyin"]])
                self.assertEqual(char["ko_final"], rule["kr"])
                self.assertIn(char["vi_final"], rule["vi"])

    def test_glyphs_use_ko_base_all(self):
        chars = {row["key_char"]: row for row in self.data["chars"]}
        self.assertEqual(chars["歷"]["ko_base_all"], "력")
        self.assertTrue(chars["樂"]["ko_base_all"].startswith("락;악"))


class Stage5AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = APP.read_text(encoding="utf-8")
        cls.prototype = PROTOTYPE.read_text(encoding="utf-8")

    def test_app_is_current_reproducible_build(self):
        self.assertEqual(self.app, build_app.build())
        self.assertNotIn("KB_DATA", self.prototype)
        self.assertNotIn("../data/final/data.js", self.prototype)

    def test_app_uses_local_script_and_no_fetch(self):
        self.assertIn('<script src="../data/final/data.js"></script>', self.app)
        self.assertNotIn("fetch(", self.app)
        self.assertIn("const KB=window.KB_DATA", self.app)

    def test_ids_are_used_for_srs_custom_and_false_friends(self):
        self.assertNotRegex(self.app, r"srs\[[^\]]+\.h\]")
        self.assertIn("srs[cur.id]", self.app)
        self.assertIn("custom.push(w.id)", self.app)
        self.assertIn("ffopen.has(f.id)", self.app)
        self.assertIn('data-w="${f.id}"', self.app)

    def test_daily_new_limit_reviews_unlimited_and_target_first(self):
        self.assertIn("let newToday=S.get('kb_newtoday'", self.app)
        self.assertIn("const slots=Math.max(0,20-introduced.size)", self.app)
        self.assertIn("const reviews=d.filter(w=>srs[w.id]&&srs[w.id].due<=now)", self.app)
        self.assertIn("const pending=d.filter(w=>!srs[w.id]&&introduced.has(w.id))", self.app)
        self.assertIn("fresh=d.filter(w=>!srs[w.id]&&!introduced.has(w.id)).slice(0,slots)", self.app)

        deck = [
            {"id": f"w{i:05d}", "v": "vi" if i != 29 else "", "p": "py"}
            for i in range(1, 31)
        ]
        srs = {f"w{i:05d}": {"due": 1} for i in range(21, 26)}
        due = reference_due(deck, srs, set(), "vi", now=2)
        self.assertEqual(sum(word["id"] in srs for word in due), 5)
        self.assertEqual(sum(word["id"] not in srs for word in due), 20)

        introduced = {f"w{i:05d}" for i in range(1, 20)}
        due = reference_due(deck, srs, introduced, "vi", now=2)
        self.assertEqual(sum(word["id"] in srs for word in due), 5)
        self.assertEqual(sum(word["id"] not in srs and word["id"] not in introduced for word in due), 1)
        self.assertNotIn("w00029", {word["id"] for word in due})

    def test_missing_values_and_approved_exceptions(self):
        self.assertIn("x.jp||x.trad", self.app)
        self.assertIn("x.pinyin||''", self.app)
        self.assertIn("x.vi||''", self.app)
        self.assertIn("pair.ko_syllable", self.app)
        self.assertIn("replace(/[（）()]/g,'')", self.app)
        self.assertIn("#psel{flex-wrap:wrap}", self.app)
        self.assertEqual(self.app.count("w.note?"), 1)

    def test_hardcoded_prototype_arrays_are_gone(self):
        for marker in ("{h:'經濟'", "{w:'勉強'", "{id:'v1'", "['経','經','经'"):
            self.assertNotIn(marker, self.app)
        self.assertIsNone(re.search(r"const (WORDS|RULES|FF|PASSAGES|GLYPHS)=\[", self.app))


if __name__ == "__main__":
    unittest.main()
