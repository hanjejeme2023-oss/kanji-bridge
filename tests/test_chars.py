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
        cls.by_trad = cls.chars.drop_duplicates("trad").set_index("trad")
        cls.by_key = cls.chars.set_index("key_char")

    def test_shape_keys_and_ids(self) -> None:
        self.assertEqual((self.chars["in_hsk_chars"] == "true").sum(), 3000)
        self.assertGreater(len(self.chars), 3000)
        self.assertEqual(self.chars["key_char"].duplicated().sum(), 0)
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

    def test_shared_trad_rows_keep_source_character_readings(self) -> None:
        wearing = self.by_key.loc["着"]
        author = self.by_key.loc["著"]
        self.assertEqual(
            [wearing.name, *wearing[["trad", "simp", "jp", "ko", "level"]].tolist()],
            ["着", "著", "着", "着", "착", "1"],
        )
        self.assertIn("ちゃく", wearing["ja_on_all"].split(";"))
        self.assertEqual(
            [author.name, *author[["trad", "simp", "jp", "ko", "level"]].tolist()],
            ["著", "著", "著", "著", "저", "4"],
        )
        self.assertIn("ちょ", author["ja_on_all"].split(";"))

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

    def test_fixed_characters_have_source_backed_primary_readings(self) -> None:
        expected = {
            "學": ["学", "がく", "학", "xué", "học"],
            "國": ["国", "こく", "국", "guó", "quốc"],
            "茶": ["茶", "ちゃ", "차", "chá", "trà"],
            "行": ["行", "こう", "행", "xíng", "hành"],
            "生": ["生", "せい", "생", "shēng", "sinh"],
            "樂": ["楽", "がく", "락", "lè", "lạc"],
        }
        for key_char, values in expected.items():
            with self.subTest(key_char=key_char):
                self.assertEqual(
                    self.by_key.loc[key_char, ["jp", "ja_on", "ko", "pinyin", "vi"]].tolist(),
                    values,
                )

    def test_korean_readings_have_no_unihan_source_suffixes(self) -> None:
        self.assertFalse(self.chars["ko"].str.contains(":", regex=False).any())
        self.assertFalse(self.chars["ko_all"].str.contains(":", regex=False).any())

    def test_expected_stage2_sanity_ranges(self) -> None:
        base = self.chars.loc[self.chars["in_hsk_chars"] == "true"]
        jp_missing = int((base["jp"] == "").sum())
        # kaikki_en_char is a verified tag since D55 b / D57 (7C character readings switched on):
        # Stage 2 measured about 1,835 verified; 7C confirms 45 and adds readings, giving about 1,913.
        verified_vi = int(base["source_vi"].isin(["kaikki_aligned", "kaikki_en_char", "unihan_hvsyl"]).sum())
        self.assertGreaterEqual(jp_missing, 35)
        self.assertLessEqual(jp_missing, 55)
        self.assertGreaterEqual(verified_vi, 1880)
        self.assertLessEqual(verified_vi, 1950)


if __name__ == "__main__":
    unittest.main()
