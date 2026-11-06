from __future__ import annotations

import unittest

from pipeline.stage4 import builders
from pipeline.stage3_match import collapse_iy


class Stage4BuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.task1 = builders.build_task1_items()
        cls.task4 = builders.build_task4_items()

    def test_frozen_item_counts(self) -> None:
        self.assertEqual(len(self.task1), 8555)
        self.assertEqual(len(builders.chunked(self.task1, 100)), 86)
        self.assertEqual(len(self.task4), 234)
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


if __name__ == "__main__":
    unittest.main()
