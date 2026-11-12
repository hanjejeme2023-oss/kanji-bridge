from __future__ import annotations

import csv
import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from pipeline import export_app_data, merge_task6
from pipeline.stage4.runner import ACCEPTED_BATCH_COUNTS, main as stage4_main


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "data" / "final"


def load_data_js() -> dict:
    text = (FINAL / "data.js").read_text(encoding="utf-8")
    return json.loads(text.removeprefix("window.KB_DATA = ")[:-2])


class Task6MergeUnitTests(unittest.TestCase):
    def test_rerun_highest_round_supersedes_main(self) -> None:
        main = {"w1:zh:card": {"sentence": "main"}}
        result = merge_task6.effective_answers(main, {
            2: {"w1:zh:card": {"sentence": "round 2"}},
            1: {"w1:zh:card": {"sentence": "round 1"}},
        })
        self.assertEqual(result["w1:zh:card"]["sentence"], "round 2")
        with self.assertRaisesRegex(ValueError, "unknown keys"):
            merge_task6.effective_answers(main, {1: {"unknown": {}}})

    def test_review_actions_and_mismatches_fail_closed(self) -> None:
        cases = (
            (
                "drop", "w1:vi:card",
                {"sentence": "generated", "translation_ja": "old"}, "sentence", "",
            ),
            (
                "set_translation_ja", "w1:zh:card",
                {"sentence": "s", "translation_ja": "generated"}, "translation_ja", "fixed",
            ),
            (
                "set_note_ja", "c1:note",
                {"note_ja": "generated"}, "note_ja", "fixed",
            ),
        )
        for action, key, answer, field, review in cases:
            with self.subTest(action=action):
                effective = {key: dict(answer)}
                row = {
                    "key": key, "action": action, "generated": answer[field],
                    "review": review, "reason": "reviewed",
                }
                dropped = merge_task6.apply_review_rows(effective, [row], enforce_counts=False)
                if action == "drop":
                    self.assertEqual(dropped, {key})
                else:
                    self.assertEqual(effective[key][field], "fixed")
                bad = {**row, "generated": "does not match"}
                with self.assertRaisesRegex(ValueError, "generated value differs"):
                    merge_task6.apply_review_rows({key: dict(answer)}, [bad], enforce_counts=False)

        with self.assertRaisesRegex(ValueError, "unknown keys"):
            merge_task6.apply_review_rows(
                {"w1:zh:card": {"sentence": "s"}},
                [{"key": "unknown", "action": "drop", "generated": "s", "review": "", "reason": "r"}],
                enforce_counts=False,
            )
        with self.assertRaisesRegex(ValueError, "unknown action"):
            merge_task6.apply_review_rows(
                {"w1:zh:card": {"sentence": "s"}},
                [{"key": "w1:zh:card", "action": "edit", "generated": "s", "review": "x", "reason": "r"}],
                enforce_counts=False,
            )

    def test_target_offsets_and_pinyin_spacing(self) -> None:
        self.assertEqual(merge_task6._target_offset("我爱学习。", "学习", "zh"), 2)
        self.assertEqual(merge_task6._target_offset("Tôi học Việt Nam học.", "việt nam", "vi"), 8)
        with self.assertRaisesRegex(ValueError, "whole syllables"):
            merge_task6._target_offset("người Việt Namese", "Việt Nam", "vi")
        self.assertEqual(
            merge_task6.normalize_pinyin_spacing("Nǐ hǎo , shìjiè ! "),
            ("Nǐ hǎo, shìjiè!", True),
        )


class AppDataPartATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_data_js()

    def test_expected_table_and_compact_counts(self) -> None:
        with (FINAL / "examples.csv").open(encoding="utf-8", newline="") as handle:
            examples = list(csv.DictReader(handle))
        with (FINAL / "char_notes.csv").open(encoding="utf-8", newline="") as handle:
            notes = list(csv.DictReader(handle))
        self.assertEqual(len(examples), 10367)
        self.assertEqual(len(notes), 581)
        self.assertEqual(
            Counter((row["lang"], row["use"]) for row in examples),
            Counter({("zh", "card"): 5783, ("zh", "ff"): 560,
                     ("vi", "card"): 3909, ("vi", "ff"): 115}),
        )
        self.assertEqual(len(self.data["examples"]), 10367)
        self.assertEqual(len(self.data["char_notes"]), 581)
        self.assertEqual(len(self.data["glyphs"]), 2215)
        self.assertEqual(len(self.data["usage"]), 2164)

    def test_compact_orders_and_references(self) -> None:
        words = {row["word_id"] for row in self.data["words"]}
        chars = {row["char_id"] for row in self.data["chars"]}
        examples = self.data["examples"]
        self.assertEqual(
            examples,
            sorted(examples, key=lambda row: (row[0], {"zh": 0, "vi": 1}[row[1]], {"card": 0, "ff": 1}[row[2]])),
        )
        self.assertTrue({row[0] for row in examples}.issubset(words))
        self.assertTrue({row[0] for row in self.data["char_notes"]}.issubset(chars))
        self.assertTrue({row[0] for row in self.data["glyphs"]}.issubset(chars))
        self.assertTrue({row[1] for row in self.data["glyphs"] if row[1]}.issubset(words))
        self.assertEqual([row[0] for row in self.data["usage"]], sorted(chars))
        self.assertTrue(all(len(row[1]) <= 3 and len(row[2]) <= 3 for row in self.data["usage"]))

    def test_pinyin_tones_neutral_erhua_and_reported_count(self) -> None:
        self.assertEqual(export_app_data.derive_pinyin_tones(
            {"pinyin": "nǐde"},
            [{"position": "1", "pinyin_syllable": "nǐ"},
             {"position": "2", "pinyin_syllable": "de"}],
        ), "35")
        self.assertEqual(export_app_data.derive_pinyin_tones(
            {"pinyin": "huār"}, [{"position": "1", "pinyin_syllable": "huār"}],
        ), "1")
        actual = sum("pt" in row for row in self.data["words"])
        self.assertEqual(actual, self.data["meta"]["counts"]["pinyin_tones"])
        self.assertEqual(actual + self.data["meta"]["counts"]["pinyin_tones_omitted"], 12508)
        self.assertTrue(all(set(row["pt"]) <= set("12345") for row in self.data["words"] if "pt" in row))

    def test_standalone_copy_is_byte_identical_and_below_limit(self) -> None:
        final = (FINAL / "data.js").read_bytes()
        app = (ROOT / "app" / "data.js").read_bytes()
        self.assertEqual(hashlib.sha256(final).digest(), hashlib.sha256(app).digest())
        self.assertLessEqual(len(final), 8 * 1024 * 1024)
        html = (ROOT / "app" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<script src="data.js"></script>', html)
        self.assertNotIn("../data/final", html)


class Task6RefusalTests(unittest.TestCase):
    def test_task6_modes_refuse_before_client_creation(self) -> None:
        self.assertEqual(ACCEPTED_BATCH_COUNTS[6], 224)
        for args in (["--task", "6"], ["--task", "6", "--dry-run"],
                     ["--pilot6"], ["--task", "6", "--rerun-round", "1"]):
            with self.subTest(args=args), patch("pipeline.stage4.runner.create_client") as client:
                self.assertEqual(stage4_main(args), 1)
                client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
