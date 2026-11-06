from __future__ import annotations

import unittest

from pipeline.stage4 import builders


class Stage4BuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.task1 = builders.build_task1_items()
        cls.task4 = builders.build_task4_items()

    def test_frozen_item_counts(self) -> None:
        self.assertEqual(len(self.task1), 8555)
        self.assertEqual(len(builders.chunked(self.task1, 100)), 86)
        self.assertEqual(len(self.task4), 302)
        self.assertEqual(len(builders.chunked(self.task4, 50)), 7)

    def test_pilot_sets(self) -> None:
        task1 = builders.build_pilot_task1()
        self.assertEqual(len(task1), 100)
        self.assertTrue(set(builders.PILOT_TASK1_REQUIRED).issubset({item["trad"] for item in task1}))
        task4_by_id = {item["word_id"]: item for item in self.task4}
        required_ids = {
            item["word_id"] for item in self.task4 if item["trad"] in builders.PILOT_TASK4_REQUIRED
        }
        self.assertTrue(required_ids.issubset(task4_by_id))

    def test_builders_are_byte_deterministic(self) -> None:
        first = builders.jsonl_text(builders.build_pilot_task1())
        second = builders.jsonl_text(builders.build_pilot_task1())
        self.assertEqual(first, second)
        self.assertEqual(builders.sha256_text(first), builders.sha256_text(second))
        first4 = builders.jsonl_text(self.task4)
        second4 = builders.jsonl_text(builders.build_task4_items())
        self.assertEqual(builders.sha256_text(first4), builders.sha256_text(second4))


if __name__ == "__main__":
    unittest.main()
