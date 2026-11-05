from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


class WordTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.words = pd.read_csv(
            ROOT / "data" / "final" / "words.csv", encoding="utf-8",
            keep_default_na=False, dtype=str,
        )
        cls.chars = pd.read_csv(
            ROOT / "data" / "final" / "chars.csv", encoding="utf-8",
            keep_default_na=False, dtype=str,
        )
        cls.word_chars = pd.read_csv(
            ROOT / "data" / "final" / "word_chars.csv", encoding="utf-8",
            keep_default_na=False, dtype=str,
        )

    def row(self, trad: str, pinyin: str = "") -> pd.Series:
        rows = self.words.loc[self.words["trad"] == trad]
        if pinyin:
            rows = rows.loc[rows["pinyin"] == pinyin]
        self.assertEqual(len(rows), 1, (trad, pinyin, len(rows)))
        return rows.iloc[0]

    def test_hsk_shape_and_keys(self) -> None:
        hsk = self.words.loc[self.words["source_level"] == "hsk30"]
        self.assertEqual(len(hsk), 11028)
        self.assertFalse(hsk.duplicated(["trad", "pinyin"]).any())
        self.assertFalse(self.words["word_id"].duplicated().any())
        self.assertEqual(len(self.word_chars), self.words["trad"].str.len().sum())
        self.assertFalse(self.word_chars.duplicated(["word_id", "position"]).any())

    def test_fixed_multichar_words(self) -> None:
        expected = {
            "經濟": ("経済", "けいざい", "경제", "kinh tế"),
            "大學": ("大学", "だいがく", "대학", "đại học"),
            "勉強": ("勉強", "べんきょう", "면강", "miễn cưỡng"),
            "銀行": ("銀行", "ぎんこう", "은행", "ngân hàng"),
            "發展": ("発展", "はってん", "발전", "phát triển"),
            "歷史": ("歴史", "れきし", "역사", "lịch sử"),
            "新聞": ("新聞", "しんぶん", "신문", ""),
            "注意": ("注意", "ちゅうい", "주의", "chú ý"),
            "主義": ("主義", "しゅぎ", "주의", "chủ nghĩa"),
            "學習": ("学習", "がくしゅう", "학습", "học tập"),
            "心理": ("心理", "しんり", "심리", "tâm lý"),
        }
        for trad, values in expected.items():
            with self.subTest(trad=trad):
                row = self.row(trad)
                self.assertEqual(tuple(row[["jp", "ja", "ko", "vi"]]), values)

    def test_single_character_fallbacks(self) -> None:
        expected = {"國": ("こく", "くに"), "電": ("でん", "いなずま"), "海": ("かい", "うみ"), "手": ("しゅ", "て")}
        for trad, (reading, alt) in expected.items():
            row = self.row(trad)
            self.assertEqual(row["ja"], reading)
            self.assertEqual(row["source_ja"], "kanjidic2_on")
            self.assertIn(alt, row["ja_alt"].split(";"))

    def test_vi_seed_and_false_friend_candidates(self) -> None:
        vietnam = self.row("越南")
        self.assertEqual(tuple(vietnam[["origin", "ja", "ko", "pinyin", "vi"]]), ("vi_freq", "えつなん", "월남", "yuènán", "việt nam"))
        ff = pd.read_csv(
            ROOT / "data" / "staging" / "ff_candidates.csv", encoding="utf-8",
            keep_default_na=False, dtype=str,
        )
        self.assertGreaterEqual(len(ff), 2500)
        self.assertLessEqual(len(ff), 3300)
        self.assertIn("手紙", set(ff["form"]))
        self.assertIn("大丈夫", set(ff["form"]))
        self.assertNotIn("手紙", set(self.words["trad"]))

    def test_d39_character_primaries(self) -> None:
        by_key = self.chars.set_index("key_char")
        self.assertIn(by_key.loc["樂", "ko"], {"락", "악"})
        self.assertNotEqual(by_key.loc["樂", "ko"], "낙")
        self.assertEqual(by_key.loc["歷", "ko"], "력")
        self.assertEqual(by_key.loc["怒", "ko"], "노")
        self.assertEqual(by_key.loc["行", "ko"], "행")
        self.assertIn(by_key.loc["茶", "ko"], {"다", "차"})

    def test_card_eligibility_formula(self) -> None:
        recomputed = (
            (self.words["level"] != "")
            & ((self.words["ja"] != "") | (self.words["ko"] != ""))
            & ((self.words["pinyin"] != "") | (self.words["vi"] != ""))
            & (self.words["origin"] != "ff_only")
        )
        self.assertTrue((recomputed == (self.words["card_eligible"] == "true")).all())


if __name__ == "__main__":
    unittest.main()
