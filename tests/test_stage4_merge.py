from __future__ import annotations

import json
import unittest
from pathlib import Path

import pandas as pd

from pipeline.merge_stage4 import (
    FF_COLUMNS,
    PASSAGE_COLUMNS,
    WORD_COLUMNS,
    apply_task1_review,
    apply_task2_reviews,
    apply_task3_review,
    apply_task4_review,
    apply_task5_review,
    accepted_batches,
    config_from_prototype,
    validate_task3_review_batches,
)


ROOT = Path(__file__).resolve().parents[1]


class Stage4OverlayFailClosedTests(unittest.TestCase):
    def test_task1_overlay_rejects_generated_mismatch(self) -> None:
        outputs = {"w00001": {"word_id": "w00001", "vi_check": "different_word"}}
        words = pd.DataFrame([{"word_id": "w00001", "trad": "愛", "vi": "ái"}])
        review = pd.DataFrame([{
            "word_id": "w00001", "trad": "愛", "vi": "ái",
            "vi_check_task1": "unsure", "vi_check_review": "same_word",
        }])
        with self.assertRaisesRegex(ValueError, "generated-output mismatch"):
            apply_task1_review(outputs, words, review)

    def test_task2_overlay_rejects_generated_mismatch(self) -> None:
        outputs = {"form": {
            "key": "form", "false_friend": ["vi"],
            "meanings": [{"lang": "vi", "meaning_ja": "generated", "is_trap": True}],
        }}
        review = pd.DataFrame([{
            "key": "form", "lang": "vi", "action": "clear_vi",
            "meaning_ja_generated": "different", "is_trap_generated": "true",
            "meaning_ja_review": "", "false_friend_review": "", "reason": "test",
        }])
        retrap = pd.DataFrame(columns=[
            "key", "lang", "meaning_ja_generated", "is_trap_generated",
            "is_trap_review", "false_friend_review",
        ])
        with self.assertRaisesRegex(ValueError, "generated-output mismatch"):
            apply_task2_reviews(outputs, review, retrap)

    def test_task2_retrap_overlay_rejects_generated_mismatch(self) -> None:
        outputs = {"w00001": {
            "key": "w00001", "false_friend": ["zh"],
            "meanings": [{"lang": "zh", "meaning_ja": "generated", "is_trap": True}],
        }}
        review = pd.DataFrame(columns=[
            "key", "lang", "action", "meaning_ja_generated", "is_trap_generated",
            "meaning_ja_review", "false_friend_review", "reason",
        ])
        retrap = pd.DataFrame([{
            "key": "w00001", "lang": "zh", "meaning_ja_generated": "different",
            "is_trap_generated": "true", "is_trap_review": "false",
            "false_friend_review": "", "reason": "test",
        }])
        with self.assertRaisesRegex(ValueError, "generated-output mismatch"):
            apply_task2_reviews(outputs, review, retrap)

    def test_task3_overlay_rejects_generated_mismatch(self) -> None:
        output = {"passages": [{"translation_ja": "generated", "tokens": []}]}
        review = pd.DataFrame([{
            "batch": "b001", "passage": "1", "action": "drop", "token_index": "",
            "generated": "different", "review": "", "reason": "test",
        }])
        with self.assertRaisesRegex(ValueError, "drop mismatch"):
            apply_task3_review("b001", output, review)

    def test_task3_overlay_rejects_unknown_batch(self) -> None:
        review = pd.DataFrame([{"batch": "b999"}])
        with self.assertRaisesRegex(ValueError, "unknown accepted batches"):
            validate_task3_review_batches(review, {"b001", "b002"})

    def test_task4_overlay_rejects_generated_mismatch(self) -> None:
        outputs = {"w00001": {"word_id": "w00001", "note_ja": "generated"}}
        words = pd.DataFrame([{"word_id": "w00001", "trad": "愛"}])
        review = pd.DataFrame([{
            "word_id": "w00001", "trad": "愛", "note_ja_generated": "different",
            "note_ja_review": "reviewed", "reason": "test",
        }])
        with self.assertRaisesRegex(ValueError, "generated-output mismatch"):
            apply_task4_review(outputs, words, review)

    def test_task5_overlay_rejects_generated_mismatch(self) -> None:
        outputs = {"w00001": {
            "key": "w00001", "ja_check": "rare", "ko_check": "", "vi_use": "",
        }}
        inputs = {"w00001": {
            "key": "w00001", "checks": ["ja"], "trad": "愛", "ja": "あい",
        }}
        review = pd.DataFrame([{
            "key": "w00001", "lang": "ja", "trad": "愛", "reading": "あい",
            "check_generated": "used", "check_review": "rare",
        }])
        with self.assertRaisesRegex(ValueError, "generated-output mismatch"):
            apply_task5_review(outputs, inputs, review)


class Stage4FinalTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.words = pd.read_csv(
            ROOT / "data/final/words.csv", encoding="utf-8", keep_default_na=False, dtype=str
        )
        cls.ff = pd.read_csv(
            ROOT / "data/final/ff_meanings.csv", encoding="utf-8", keep_default_na=False, dtype=str
        )
        cls.passages = pd.read_csv(
            ROOT / "data/final/passages.csv", encoding="utf-8", keep_default_na=False, dtype=str
        )

    def test_prototype_configs_are_exact_extractions(self) -> None:
        ff, notes = config_from_prototype()
        self.assertEqual(len(ff), 34)
        self.assertEqual(len(ff["word"].unique()), 12)
        self.assertEqual(len(notes), 1)

    def test_schema_keys_and_row_counts(self) -> None:
        self.assertEqual(list(self.words.columns), WORD_COLUMNS)
        self.assertEqual(list(self.ff.columns), FF_COLUMNS)
        self.assertEqual(list(self.passages.columns), PASSAGE_COLUMNS)
        self.assertEqual(len(self.words), 12508)
        self.assertEqual((self.words["origin"] == "ff_only").sum(), 279)
        self.assertEqual(len(self.ff), 4044)
        self.assertEqual(len(self.passages), 80)
        self.assertFalse(self.words["word_id"].duplicated().any())
        self.assertFalse(self.ff.duplicated(["word_id", "lang"]).any())
        self.assertFalse(self.passages["passage_id"].duplicated().any())

    def test_final_ids_match_formats_and_id_map_keys(self) -> None:
        self.assertTrue(self.words["word_id"].str.fullmatch(r"w\d{5}").all())
        self.assertTrue(self.passages["passage_id"].str.fullmatch(r"p\d{4}").all())

        id_map = pd.read_csv(
            ROOT / "pipeline/id_map.csv", encoding="utf-8", keep_default_na=False, dtype=str
        )
        mapped_words = {
            (row.key, row.id)
            for row in id_map.loc[id_map["kind"] == "word"].itertuples(index=False)
        }
        for row in self.words.itertuples(index=False):
            key = f"{row.trad}|{row.pinyin}" if row.source_level == "hsk30" else f"x|{row.trad}"
            self.assertIn((key, row.word_id), mapped_words)

        outputs = accepted_batches(3)
        inputs = accepted_batches(3, inputs=True)
        review = pd.read_csv(
            ROOT / "config/task3_review.csv", encoding="utf-8", keep_default_na=False, dtype=str
        )
        mapped_passages = dict(
            id_map.loc[id_map["kind"] == "passage", ["key", "id"]].itertuples(
                index=False, name=None
            )
        )
        expected = []
        for batch in sorted(outputs):
            source = inputs[batch][0]
            kept = apply_task3_review(
                batch, outputs[batch][0], review, include_positions=True
            )
            expected.extend(
                mapped_passages[f"{source['language']}|{source['level']}|{number}"]
                for number, _ in kept
            )
        self.assertEqual(self.passages["passage_id"].tolist(), expected)

    def test_ff_only_pinyin_is_single_sourced_value(self) -> None:
        ff_only = self.words.loc[self.words["origin"] == "ff_only"].set_index("trad")
        self.assertEqual(ff_only.at["年下", "pinyin"], "niánxià")
        self.assertEqual(ff_only.at["裁縫", "pinyin"], "cáiféng")
        with_pinyin = ff_only.loc[ff_only["pinyin"] != ""]
        self.assertTrue((with_pinyin["source_pinyin"] == "cc-cedict").all())
        self.assertFalse(with_pinyin["pinyin"].str.contains(";", regex=False).any())

    def test_json_types_match_schema(self) -> None:
        words = json.loads((ROOT / "data/final/words.json").read_text(encoding="utf-8"))
        ff = json.loads((ROOT / "data/final/ff_meanings.json").read_text(encoding="utf-8"))
        passages = json.loads((ROOT / "data/final/passages.json").read_text(encoding="utf-8"))
        self.assertIsInstance(words[0]["ja_common"], bool)
        self.assertIsInstance(words[0]["card_eligible"], bool)
        self.assertIsInstance(words[0]["level"], int)
        self.assertIsInstance(ff[0]["is_trap"], bool)
        self.assertIsInstance(passages[0]["level"], int)
        self.assertIsInstance(passages[0]["tokens"], list)

    def test_final_readings_are_copied_from_words(self) -> None:
        joined = self.ff.merge(
            self.words[["word_id", "ja", "ko", "pinyin", "vi"]],
            on="word_id", how="left", validate="many_to_one",
        )
        self.assertFalse(joined["ja"].isna().any())
        column = {"ja": "ja", "ko": "ko", "zh": "pinyin", "vi": "vi"}
        for lang, group in joined.groupby("lang"):
            self.assertTrue((group["reading"] == group[column[lang]]).all(), lang)

    def test_claude_expected_usage_and_false_friend_numbers(self) -> None:
        cards = self.words.loc[self.words["card_eligible"] == "true"]
        ko_rare = cards["ko_use"] == "rare"
        ja_rare = cards["ja_use"] == "rare"
        self.assertEqual(ko_rare.sum(), 1500)
        self.assertEqual(ja_rare.sum(), 437)
        self.assertEqual((ko_rare & ja_rare).sum(), 241)
        self.assertEqual((cards["ko_use"] == "wrong_meaning").sum(), 18)
        self.assertEqual((cards["ja_use"] == "wrong_meaning").sum(), 1)
        # R1: 吧 w00006 lost its Nôm vi (và), and its literary usage judgment with it (1,277 before)
        self.assertEqual((cards["vi_use"] == "literary").sum(), 1276)
        self.assertEqual((cards["vi_use"] == "unsure").sum(), 1)
        self.assertEqual((self.words["false_friend"] != "").sum(), 1242)
        self.assertEqual((self.ff["reading_display"] == "（韓国語ではほぼ使わない）").sum(), 227)
        self.assertEqual((self.ff["reading_display"] == "（日本語ではほぼ使わない）").sum(), 76)
        for trad in ("孫子", "內衣", "應當"):
            rows = self.words.loc[self.words["trad"] == trad]
            self.assertFalse(rows.empty, trad)
            self.assertTrue((rows["false_friend"] == "").all(), trad)

    def test_passage_tokens_resolve(self) -> None:
        word_ids = set(self.words["word_id"])
        counts = self.passages.groupby(["lang", "level"]).size()
        self.assertEqual(len(counts), 14)
        self.assertGreaterEqual(counts.min(), 5)
        for raw in self.passages["tokens"]:
            tokens = json.loads(raw)
            for token in tokens:
                if "word_id" in token:
                    self.assertIn(token["word_id"], word_ids)

    def test_task5_reason_text_does_not_reach_final_tables(self) -> None:
        for frame in (self.words, self.ff, self.passages):
            self.assertFalse(any("reason" in column for column in frame.columns))
        review = pd.read_csv(
            ROOT / "config/task5_review.csv", encoding="utf-8", keep_default_na=False, dtype=str
        )
        reasons = set(review["reason_generated"]) | set(review["reason"])
        reasons.discard("")
        final_values = {
            value
            for frame in (self.words, self.ff, self.passages)
            for column in frame.columns
            for value in frame[column]
            if isinstance(value, str)
        }
        self.assertTrue(reasons.isdisjoint(final_values))


if __name__ == "__main__":
    unittest.main()
