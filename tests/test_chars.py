from __future__ import annotations

import re
import unicodedata
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CHARS_PATH = ROOT / "data" / "final" / "chars.csv"


class CharacterTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.chars = pd.read_csv(CHARS_PATH, encoding="utf-8", keep_default_na=False, dtype=str)
        cls.by_trad = cls.chars.set_index("trad")

    def test_shape_keys_and_ids(self) -> None:
        self.assertEqual(len(self.chars), 3000)
        self.assertEqual(self.chars["trad"].duplicated().sum(), 0)
        self.assertEqual(self.chars["char_id"].duplicated().sum(), 0)
        self.assertTrue(self.chars["char_id"].map(lambda value: bool(re.fullmatch(r"c\d{5}", value))).all())

    def test_all_text_is_nfc_and_has_no_missing_sentinels(self) -> None:
        for column in self.chars.columns:
            for value in self.chars[column]:
                self.assertEqual(value, unicodedata.normalize("NFC", value), (column, value))
                self.assertNotIn(value, {"NaN", "nan", "None", "undefined"})

    def test_multi_target_shinjitai_tie_breaks(self) -> None:
        expected = {"畫": "画", "鬥": "闘", "鹽": "塩", "鋪": "舗", "莊": "荘", "驅": "駆"}
        for traditional, japanese in expected.items():
            with self.subTest(traditional=traditional):
                self.assertEqual(self.by_trad.loc[traditional, "jp"], japanese)

    def test_prototype_glyph_pairs(self) -> None:
        expected = {
            "經": "経", "發": "発", "氣": "気", "樂": "楽", "歷": "歴", "實": "実",
            "賣": "売", "讀": "読", "廣": "広", "對": "対", "學": "学", "國": "国",
            "會": "会", "電": "電", "話": "話", "語": "語",
        }
        for traditional, japanese in expected.items():
            with self.subTest(traditional=traditional):
                self.assertEqual(self.by_trad.loc[traditional, "jp"], japanese)

    def test_fixed_characters(self) -> None:
        for char in ["學", "國", "茶", "行", "生", "樂"]:
            self.assertIn(char, self.by_trad.index)
        self.assertEqual(self.by_trad.loc["學", "ko"], "학")
        self.assertEqual(self.by_trad.loc["學", "vi"], "học")
        self.assertEqual(self.by_trad.loc["學", "pinyin"], "xué")
        self.assertEqual(self.by_trad.loc["國", "ko"], "국")
        self.assertEqual(self.by_trad.loc["國", "vi"], "quốc")
        self.assertEqual(self.by_trad.loc["國", "pinyin"], "guó")
        self.assertEqual(self.by_trad.loc["茶", "vi"], "trà")
        music = self.by_trad.loc["樂"]
        self.assertTrue({"lạc", "nhạc"}.issubset(set(music["vi_all"].split(";"))))
        self.assertTrue({"락", "악"}.issubset(set(music["ko_all"].split(";"))))
        self.assertTrue({"lè", "yuè"}.issubset(set(music["pinyin_all"].split(";"))))

    def test_expected_stage2_sanity_ranges(self) -> None:
        jp_missing = int((self.chars["jp"] == "").sum())
        verified_vi = int(self.chars["source_vi"].isin(["kaikki_aligned", "unihan_hvsyl"]).sum())
        self.assertGreaterEqual(jp_missing, 35)
        self.assertLessEqual(jp_missing, 55)
        self.assertGreaterEqual(verified_vi, 1800)
        self.assertLessEqual(verified_vi, 1870)


if __name__ == "__main__":
    unittest.main()
