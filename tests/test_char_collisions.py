from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


class CharacterCollisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.chars = pd.read_csv(
            ROOT / "data" / "final" / "chars.csv",
            encoding="utf-8",
            keep_default_na=False,
            dtype=str,
        )
        cls.hsk = pd.read_csv(
            ROOT / "data" / "staging" / "hsk30.csv",
            encoding="utf-8",
            keep_default_na=False,
            dtype=str,
        )

    def test_c1_many_source_rows_to_one_traditional_form(self) -> None:
        shared = self.chars.loc[
            self.chars["trad"].duplicated(keep=False), ["trad", "key_char"]
        ].sort_values(["trad", "key_char"], kind="stable")
        self.assertEqual(shared.to_dict(orient="records"), [
            {"trad": "著", "key_char": "着"},
            {"trad": "著", "key_char": "著"},
        ])
        self.assertFalse(self.chars["char_id"].duplicated().any())
        self.assertFalse(self.chars["key_char"].duplicated().any())
        report = pd.read_csv(
            ROOT / "data" / "final" / "char_key_collisions.csv",
            encoding="utf-8",
            keep_default_na=False,
            dtype=str,
        )
        self.assertEqual(list(report.columns), ["trad", "key_char", "source_level"])
        self.assertEqual(report[["trad", "key_char"]].to_dict(orient="records"), shared.to_dict(orient="records"))

    def test_c2_one_source_row_to_multiple_traditional_variants(self) -> None:
        variants = self.hsk["trad_variants"].map(lambda value: [x for x in value.split(";") if x])
        multi = variants.map(len) > 1
        non_first = [variant for values in variants[multi] for variant in values[1:]]
        base = self.chars.loc[self.chars["in_hsk_chars"] == "true"]
        existing_trad = set(base["trad"])
        self.assertEqual(int(multi.sum()), 83)
        self.assertEqual(int((variants[multi].map(len) == 2).sum()), 78)
        self.assertEqual(int((variants[multi].map(len) >= 3).sum()), 5)
        self.assertEqual(len(set(non_first)), 89)
        self.assertEqual(set(non_first) & existing_trad, {"覆"})
        self.assertEqual(len(set(non_first) - existing_trad), 88)
        self.assertFalse((self.chars["trad"] == "").any())

        words = pd.read_csv(
            ROOT / "data" / "final" / "words.csv", encoding="utf-8",
            keep_default_na=False, dtype=str,
        )
        words = words.loc[words["origin"] != "ff_only"]
        used = {char for value in words["trad"] for char in value}
        available = set(self.chars["trad"]) | set(self.chars["key_char"])
        self.assertFalse(used - available)

    def test_traditional_key_preserves_korean_coverage(self) -> None:
        base = self.chars["in_hsk_chars"] == "true"
        changed = self.chars["simp"] != self.chars["trad"]
        self.assertGreaterEqual(int((base & changed & (self.chars["ko"] != "")).sum()), 1000)


if __name__ == "__main__":
    unittest.main()
