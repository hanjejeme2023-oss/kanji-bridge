from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

from build_chars import kaikki_en_char_readings_enabled  # noqa: E402
from build_words import apply_word_overrides, prefer_existing_vi  # noqa: E402


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8", keep_default_na=False, dtype=str)


class Stage3D53Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.words = read_csv(ROOT / "data" / "final" / "words.csv")
        cls.chars = read_csv(ROOT / "data" / "final" / "chars.csv")
        cls.ambiguous = read_csv(ROOT / "data" / "final" / "vi_ambiguous.csv")
        cls.overrides = read_csv(ROOT / "pipeline" / "overrides.csv")

    def word(self, trad: str) -> pd.Series:
        rows = self.words.loc[self.words["trad"] == trad]
        self.assertFalse(rows.empty, trad)
        return rows.iloc[0]

    def test_a2_fills_only_empty_values(self) -> None:
        self.assertEqual(prefer_existing_vi("đã có", "mới"), "đã có")
        self.assertEqual(prefer_existing_vi("", "mới"), "mới")

    def test_a2_examples_and_iy_collapse(self) -> None:
        expected = {
            "豹": "báo",
            "唱歌": "xướng ca",
            "絕大多數": "tuyệt đại đa số",
            "自己": "tự kỷ",
        }
        for trad, vi in expected.items():
            with self.subTest(trad=trad):
                row = self.word(trad)
                self.assertEqual(row["vi"], vi)
                self.assertEqual(row["source_vi"], "kaikki_en_han")

    def test_obsolete_only_words_remain_empty_and_reported(self) -> None:
        expected = {"新聞", "戲劇", "伯父", "不宜", "岳父", "岳母"}
        for trad in expected:
            self.assertTrue((self.words.loc[self.words["trad"] == trad, "vi"] == "").all(), trad)
        reported = set(self.ambiguous.loc[self.ambiguous["reason"] == "obsolete_only", "trad"])
        self.assertTrue(expected.issubset(reported))

    def test_all_committed_overrides_apply(self) -> None:
        words = self.words.set_index("word_id", drop=False)
        word_key = {}
        for row in self.words.itertuples(index=False):
            key = f"{row.trad}|{row.pinyin}" if row.source_level == "hsk30" else f"x|{row.trad}"
            word_key[key] = row
        chars = self.chars.set_index("key_char")
        # 77 confirmed at the Stage 3 gate; repeat gate (D56): +6 chars, -2 VI-only words.
        self.assertEqual(len(self.overrides), 81)
        for override in self.overrides.itertuples(index=False):
            with self.subTest(table=override.table, key=override.key, column=override.column):
                if override.table == "words":
                    self.assertIn(override.key, word_key)
                    self.assertEqual(getattr(word_key[override.key], override.column), override.value)
                else:
                    self.assertEqual(chars.loc[override.key, override.column], override.value)

    def test_empty_vi_override_does_not_create_an_accepted_alt(self) -> None:
        words = pd.DataFrame([{
            "word_key": "測試|cèshì", "word_id": "w99999", "trad": "測試",
            "pinyin": "cèshì", "level": "7", "vi": "sai", "vi_alt": "đúng",
            "source_vi": "fixture", "gloss_vi": "fixture", "vi_evidence": True,
        }])
        overrides = pd.DataFrame([{
            "table": "words", "key": "測試|cèshì", "column": "vi", "value": "",
            "reason": "fixture clear",
        }])
        result, reports = apply_word_overrides(words, overrides, {}, {"測試|cèshì": []})
        self.assertEqual(result.iloc[0]["vi"], "")
        self.assertNotIn("sai", result.iloc[0]["vi_alt"])
        self.assertEqual(reports.iloc[0]["reason"], "override_cleared")
        self.assertEqual(reports.iloc[0]["candidates"], "sai")

    def test_character_source_switch_is_off(self) -> None:
        self.assertFalse(kaikki_en_char_readings_enabled())
        self.assertFalse((self.chars["source_vi"] == "kaikki_en_char").any())

    def test_a2_merge_is_real_and_validated(self) -> None:
        report = read_csv(ROOT / "data" / "final" / "merge_report.csv")
        rows = report.loc[report["merge"] == "words_kaikki_en"]
        self.assertFalse(rows.empty)
        self.assertEqual(set(rows["validate"]), {"1:1"})


if __name__ == "__main__":
    unittest.main()
