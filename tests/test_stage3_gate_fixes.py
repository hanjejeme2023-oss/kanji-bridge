from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

from build_chars import pinyin_values  # noqa: E402
from common import merge_with_report  # noqa: E402


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8", keep_default_na=False, dtype=str)


class Stage3GateFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.final = ROOT / "data" / "final"
        cls.staging = ROOT / "data" / "staging"
        cls.chars = read_csv(cls.final / "chars.csv")
        cls.words = read_csv(cls.final / "words.csv")
        cls.word_chars = read_csv(cls.final / "word_chars.csv")
        cls.by_key = cls.chars.set_index("key_char")

    def test_d39_korean_primaries_and_normalized_word_bases(self) -> None:
        expected = {
            "老": "로", "流": "류", "旅": "려", "連": "련", "聯": "련",
            "領": "령", "律": "률", "列": "렬", "陸": "륙", "輪": "륜",
            "兩": "량", "零": "령", "冷": "랭", "綠": "록", "勞": "로",
            "輯": "집", "歷": "력", "年": "년", "女": "녀", "怒": "노",
            "行": "행",
        }
        for char, reading in expected.items():
            with self.subTest(char=char):
                self.assertEqual(self.by_key.loc[char, "ko"], reading)
        self.assertIn(self.by_key.loc["樂", "ko"], {"락", "악"})
        self.assertEqual(self.by_key.loc["茶", "ko"], "차")

        expected_bases = {"流行": "류", "旅行": "려", "分裂": "렬"}
        for trad, expected_base in expected_bases.items():
            word_id = self.words.loc[self.words["trad"] == trad, "word_id"].iloc[0]
            rows = self.word_chars.loc[self.word_chars["word_id"] == word_id]
            position = 2 if trad == "分裂" else 1
            self.assertEqual(rows.loc[rows["position"] == str(position), "ko_base"].iloc[0], expected_base)

        no_evidence = read_csv(self.final / "char_primary_no_evidence.csv")
        suspects = set(no_evidence.loc[no_evidence["ko_law_form_suspect"] == "true", "key_char"])
        self.assertTrue({"爐", "廊", "虜", "魯", "碌"}.issubset(suspects))

    def test_d39_preserves_all_reading_sets_and_source_ordered_primaries(self) -> None:
        changes = read_csv(self.final / "char_primary_changes.csv")
        for row in changes.itertuples(index=False):
            readings = self.by_key.loc[row.key_char, f"{row.lang}_all"].split(";")
            self.assertIn(row.old, readings)
            self.assertIn(row.new, readings)
            self.assertEqual(readings[0], self.by_key.loc[row.key_char, row.lang])
            self.assertEqual(len(readings), len(set(readings)))

        kanjidic = read_csv(self.staging / "kanjidic2.csv").set_index("literal")
        unihan = read_csv(self.staging / "unihan.csv").set_index("char")
        for row in self.chars.itertuples(index=False):
            expected_ja = ""
            if row.jp in kanjidic.index and kanjidic.loc[row.jp, "ja_on_all"]:
                expected_ja = kanjidic.loc[row.jp, "ja_on_all"].split(";")[0]
            self.assertEqual(row.ja_on, expected_ja, row.key_char)
            mandarin = pinyin_values(unihan.loc[row.key_char, "kMandarin"]) if row.key_char in unihan.index else []
            self.assertEqual(row.pinyin, mandarin[0] if mandarin else "", row.key_char)

    def test_single_character_japanese_matching_uses_only_d42_forms(self) -> None:
        bad = {
            "弄": "瘧", "滾": "菌", "捉": "杓", "它": "佗", "她": "他",
            "聽": "听", "拆": "責", "蛋": "蜑", "掉": "棹",
        }
        for trad, bad_form in bad.items():
            rows = self.words.loc[self.words["trad"] == trad]
            self.assertFalse(rows.empty)
            self.assertNotIn(bad_form, set(rows["jp"]))
            self.assertTrue((rows["ja"] == "").all())

        expected = {
            "歲": "さい", "腳": "きゃく", "內": "ない", "值": "ち",
            "戶": "こ", "鄉": "きょう", "號": "ごう",
            "國": "こく", "電": "でん", "海": "かい", "手": "しゅ",
        }
        for trad, reading in expected.items():
            self.assertTrue((self.words.loc[self.words["trad"] == trad, "ja"] == reading).all(), trad)
        self.assertEqual(self.words.loc[self.words["trad"] == "模仿", "jp"].iloc[0], "模倣")
        self.assertEqual(self.words.loc[self.words["trad"] == "身份", "jp"].iloc[0], "身分")
        hsk_ja = self.words.loc[
            (self.words["source_level"] == "hsk30") & (self.words["ja"] != "")
        ]
        self.assertGreaterEqual(len(hsk_ja), 5650)
        self.assertLessEqual(len(hsk_ja), 5750)

    def test_vietnamese_conflicts_glosses_and_rule_example_source(self) -> None:
        dropped = {"食物", "實物", "不行", "只是", "父女", "路面", "定為"}
        for trad in dropped:
            self.assertTrue((self.words.loc[self.words["trad"] == trad, "vi"] == "").all(), trad)
        ambiguous = read_csv(self.final / "vi_ambiguous.csv")
        conflict_forms = set(ambiguous.loc[ambiguous["reason"] == "rule_b_conflict", "trad"])
        self.assertTrue(dropped.issubset(conflict_forms))
        # D53 rule A2 fills the former rule-B ambiguity from English Wiktionary.
        self.assertEqual(self.words.loc[self.words["trad"] == "麵", "vi"].iloc[0], "miến")
        self.assertEqual(
            self.words.loc[self.words["trad"] == "麵", "source_vi"].iloc[0],
            "kaikki_en_han",
        )
        self.assertEqual(self.words.loc[self.words["trad"] == "穩", "vi"].iloc[0], "ổn")

        rule_b = self.words.loc[self.words["source_vi"] == "composed_attested"]
        self.assertGreaterEqual(len(rule_b), 2100)
        self.assertGreaterEqual((rule_b["gloss_vi"] != "").mean(), 0.99)
        ff = read_csv(self.staging / "ff_candidates.csv")
        ff_with_vi = ff.loc[ff["vi"] != ""]
        self.assertGreaterEqual((ff_with_vi["gloss_vi"] != "").mean(), 0.99)

        rules = read_csv(self.final / "rules_examples.csv")
        giam = rules.loc[(rules["trad"] == "鑑") & (rules["vi"] == "giám")]
        self.assertEqual(giam["source_vi"].tolist(), ["kaikki_han"])

    def test_grown_simplified_forms_and_pinyin_alignment(self) -> None:
        expected = {"餵": "喂", "託": "托", "譁": "哗", "鵰": "雕", "陀": "陀", "簿": "簿"}
        for char, simplified in expected.items():
            # D53 reranks the capped VI-only set; a no-longer-used grown
            # character may disappear, but every retained row keeps D51's simp.
            if char in self.by_key.index:
                self.assertEqual(self.by_key.loc[char, "simp"], simplified)
        self.assertFalse((self.chars["simp"] == "").any())
        mismatches = read_csv(self.final / "char_simp_mismatch.csv")
        self.assertEqual(set(mismatches["trad"]), {"反覆", "答覆"})

        alignment = read_csv(self.final / "alignment_mismatches.csv")
        self.assertFalse((alignment["lang"] == "pinyin").any())
        single_ids = set(self.words.loc[self.words["trad"].str.len() == 1, "word_id"])
        single_parts = self.word_chars.loc[self.word_chars["word_id"].isin(single_ids)]
        pinyin_by_word = self.words.set_index("word_id")["pinyin"]
        for row in single_parts.itertuples(index=False):
            self.assertEqual(row.pinyin_syllable, pinyin_by_word[row.word_id])

    def test_vi_only_report_and_card_eligibility_are_consistent(self) -> None:
        report = read_csv(self.final / "vi_only_report.csv")
        selected = report["selected"] == "true"
        vi_only_count = int((self.words["source_level"] == "vi_band").sum())
        self.assertEqual(int(selected.sum()), vi_only_count)
        self.assertEqual(report.loc[selected, "word_id"].nunique(), vi_only_count)
        for column in ["rank", "level"]:
            self.assertTrue(report.loc[selected, column].str.fullmatch(r"\d+").all())
        self.assertEqual(int((self.words["card_eligible"] == "true").sum()), 8554)  # D65: 季女 lost its only target language
        self.assertEqual(
            int(((self.words["source_level"] == "hsk30") & (self.words["card_eligible"] == "true")).sum()),
            7354,
        )

    def test_merge_helper_and_report_use_real_validate_arguments(self) -> None:
        reports: list[dict[str, object]] = []
        merged = merge_with_report(
            pd.DataFrame({"key": [1, 2]}),
            pd.DataFrame({"key": [1], "value": ["x"]}),
            name="test",
            reports=reports,
            how="left",
            validate="1:1",
            on="key",
        )
        self.assertEqual(merged["_merge_test"].astype(str).tolist(), ["both", "left_only"])
        self.assertEqual({row["validate"] for row in reports}, {"1:1"})
        counts = {row["status"]: row["count"] for row in reports}
        self.assertEqual(counts, {"left_only": 1, "right_only": 0, "both": 1})
        with self.assertRaises(pd.errors.MergeError):
            merge_with_report(
                pd.DataFrame({"key": [1]}),
                pd.DataFrame({"key": [1, 1]}),
                name="bad",
                reports=[],
                how="left",
                validate="1:1",
                on="key",
            )

        report = read_csv(self.final / "merge_report.csv")
        expected = {
            "words_cedict_exact": "m:1",
            "words_kaikki_outer": "m:1",
            "words_jmdict": "1:1",
            "words_libhangul": "1:1",
            "words_vi": "1:1",
        }
        for merge, validate in expected.items():
            rows = report.loc[report["merge"] == merge]
            self.assertFalse(rows.empty)
            self.assertEqual(set(rows["validate"]), {validate})
        stage2 = report["merge"].isin(["unihan", "opencc", "libhangul", "kaikki", "kanjidic"])
        self.assertFalse((report.loc[stage2, "validate"] == "").any())


if __name__ == "__main__":
    unittest.main()
