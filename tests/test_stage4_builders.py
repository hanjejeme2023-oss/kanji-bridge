from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipeline.stage4 import builders
from pipeline.stage3_match import collapse_iy


class Stage4BuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.task1 = builders.build_task1_items()
        cls.task4 = builders.build_task4_items()
        cls.generated_task1 = builders.read_jsonl_files(
            (builders.ROOT / "content" / "generated" / "task1").glob("b*.jsonl")
        )
        cls.reviewed_task1 = builders.apply_task1_review(cls.generated_task1)

    def test_frozen_item_counts(self) -> None:
        self.assertEqual(len(self.task1), 8554)  # D65 step 6 (季女); accepted task-1 output keeps 8,555
        self.assertEqual(len(builders.chunked(self.task1, 100)), 86)
        self.assertEqual(len(self.task4), 228)  # D65 step 6 cleared vi of 一行 中斷 更改 案件 液體 進出 (already outside the 212 accepted notes)
        self.assertEqual(len(builders.chunked(self.task4, 50)), 5)

    def test_task4_korean_filter_uses_the_written_syllable(self) -> None:
        by_trad = {item["trad"]: item for item in self.task4}
        dropped = {
            "異常", "異口同聲", "異性", "異議", "異物", "異端",
            "諾言", "鬧鐘", "寧靜",
        }
        kept = {"議論", "風餐露宿", "胡思亂想", "喜怒哀樂"}
        self.assertTrue(dropped.isdisjoint(by_trad))
        self.assertTrue(kept.issubset(by_trad))
        for item in self.task4:
            if len(item["trad"]) != len(item["ko"]):
                continue
            for difference in item["differences"]:
                if difference["lang"] == "ko":
                    self.assertEqual(
                        difference["reading_here"],
                        item["ko"][difference["position"] - 1],
                    )

    def test_pilot_sets(self) -> None:
        task1 = builders.build_pilot_task1()
        self.assertEqual(len(task1), 100)
        self.assertTrue(set(builders.PILOT_TASK1_REQUIRED).issubset({item["trad"] for item in task1}))
        task4_by_id = {item["word_id"]: item for item in self.task4}
        required_ids = {
            item["word_id"] for item in self.task4 if item["trad"] in builders.PILOT_TASK4_REQUIRED
        }
        self.assertTrue(required_ids.issubset(task4_by_id))
        self.assertTrue(required_ids.issubset({item["word_id"] for item in builders.build_pilot_task4()}))

    def test_builders_are_byte_deterministic(self) -> None:
        first = builders.jsonl_text(builders.build_pilot_task1())
        second = builders.jsonl_text(builders.build_pilot_task1())
        self.assertEqual(first, second)
        self.assertEqual(builders.sha256_text(first), builders.sha256_text(second))
        first4 = builders.jsonl_text(self.task4)
        second4 = builders.jsonl_text(builders.build_task4_items())
        self.assertEqual(builders.sha256_text(first4), builders.sha256_text(second4))

    def test_task4_filters_iy_and_unverified_vietnamese_differences(self) -> None:
        chars = builders.load_csv(builders.CHARS_PATH).set_index("key_char")
        for item in self.task4:
            for difference in item["differences"]:
                if difference["lang"] != "vi":
                    continue
                self.assertNotEqual(chars.loc[difference["char"], "source_vi"], "unihan_unverified")
                self.assertGreater(
                    len(collapse_iy([difference["reading_here"], difference["primary"]])),
                    1,
                )

    def test_task1_review_changes_exactly_16_vi_checks(self) -> None:
        before = {item["word_id"]: item["vi_check"] for item in self.generated_task1}
        after = {item["word_id"]: item["vi_check"] for item in self.reviewed_task1}
        changed = {word_id for word_id in before if before[word_id] != after[word_id]}
        review_ids = set(builders._task1_review()["word_id"])
        self.assertEqual(changed, review_ids)
        self.assertEqual(len(changed), 16)
        self.assertEqual({after[word_id] for word_id in changed}, {"same_word"})

    def test_task1_review_refuses_a_frozen_word_mismatch(self) -> None:
        source = builders.TASK1_REVIEW_PATH.read_text(encoding="utf-8")
        bad = source.replace("w01892,聲明,thanh minh,", "w01892,聲明,wrong reading,", 1)
        with tempfile.TemporaryDirectory() as temp:
            review_path = Path(temp) / "task1_review.csv"
            review_path.write_text(bad, encoding="utf-8")
            with (
                patch.object(builders, "TASK1_REVIEW_PATH", review_path),
                self.assertRaisesRegex(ValueError, "frozen-word mismatch"),
            ):
                builders.apply_task1_review(self.generated_task1)

    def test_task2_includes_reviewed_words_with_reviewed_gloss_policy(self) -> None:
        items = builders.build_task2_items(self.reviewed_task1)
        by_key = {item["key"]: item for item in items}
        review = builders._task1_review().set_index("word_id")
        words = builders.load_csv(builders.WORDS_PATH).set_index("word_id")
        self.assertEqual(len(items), 3937)
        self.assertEqual(len(builders.chunked(items, 50)), 79)
        for word_id, row in review.iterrows():
            self.assertIn(word_id, by_key)
            self.assertEqual(by_key[word_id]["vi"], row["vi"])
            expected_gloss = words.loc[word_id, "gloss_vi"] if row["gloss_vi_task2"] == "keep" else ""
            self.assertEqual(by_key[word_id]["gloss_vi"], expected_gloss)
            self.assertEqual(by_key[word_id]["task1_meanings"]["vi"], "")

    def test_task3_keeps_ko_rare_same_word_and_drops_different_word(self) -> None:
        outputs = {item["word_id"]: item for item in self.reviewed_task1}
        candidates = builders._task3_candidates(
            "vi", 7, self.reviewed_task1, builders.load_csv(builders.WORDS_PATH)
        )
        candidate_ids = {item["word_id"] for item in candidates}
        ko_rare = {
            word_id for word_id, item in outputs.items()
            if item.get("vi_check") == "same_word"
            and item.get("low_reason") == "ko_rare"
            and item.get("meaning_ja__vi")
        }
        different = {
            word_id for word_id, item in outputs.items()
            if item.get("vi_check") == "different_word"
        }
        self.assertTrue(ko_rare)
        self.assertTrue(ko_rare & candidate_ids)
        self.assertTrue(different)
        self.assertTrue(different.isdisjoint(candidate_ids))

    def test_task4_review_does_not_drop_reviewed_vietnamese_differences(self) -> None:
        baseline = {item["word_id"]: item for item in self.task4}
        reviewed = {
            item["word_id"]: item
            for item in builders.build_task4_items(task1_outputs=self.reviewed_task1)
        }
        review_ids = set(builders._task1_review()["word_id"])
        expected = {
            word_id for word_id in review_ids & baseline.keys()
            if any(diff["lang"] == "vi" for diff in baseline[word_id]["differences"])
        }
        self.assertTrue(expected)
        self.assertTrue(expected.issubset(reviewed))
        for word_id in expected:
            self.assertTrue(any(diff["lang"] == "vi" for diff in reviewed[word_id]["differences"]))


if __name__ == "__main__":
    unittest.main()
