from __future__ import annotations

import copy
import unittest

from pipeline.stage4.validators import (
    RESPONSE_SCHEMAS,
    ValidationError,
    validate_task1,
    validate_task2,
    validate_task3,
    validate_task4,
)
from pipeline.stage4.runner import generation_config


class Stage4ValidatorTests(unittest.TestCase):
    def test_api_schemas_have_no_empty_enum_values(self) -> None:
        def walk(value: object) -> None:
            if isinstance(value, dict):
                if "enum" in value:
                    self.assertNotIn("", value["enum"])
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(RESPONSE_SCHEMAS)

    def test_generated_configs_carry_property_ordering(self) -> None:
        task1 = generation_config(1).response_schema["items"]
        self.assertEqual(task1["propertyOrdering"], [
            "word_id", "vi_check", "vi_check_reason", "meaning_ja__ja",
            "meaning_ja__ko", "meaning_ja__zh", "meaning_ja__vi",
            "meanings_differ", "confidence", "low_reason",
        ])
        task2 = generation_config(2).response_schema["items"]
        self.assertEqual(
            task2["propertyOrdering"],
            ["key", "meanings", "false_friend", "confidence", "low_reason"],
        )
        self.assertEqual(
            task2["properties"]["meanings"]["items"]["propertyOrdering"],
            ["lang", "meaning_ja", "is_trap"],
        )

    def setUp(self) -> None:
        self.task1_input = [{
            "word_id": "w1", "trad": "字", "ja": "じ", "ko": "",
            "pinyin": "zì", "vi": "tự",
        }]
        self.task1_output = [{
            "word_id": "w1", "meaning_ja__ja": "字", "meaning_ja__ko": "",
            "meaning_ja__zh": "文字", "meaning_ja__vi": "語", "meanings_differ": True,
            "vi_check": "same_word", "vi_check_reason": "", "confidence": "high", "low_reason": "",
        }]

    def test_task1_accepts_valid_item(self) -> None:
        validate_task1(self.task1_output, self.task1_input)

    def test_task1_rejects_wrong_word_id(self) -> None:
        bad = copy.deepcopy(self.task1_output)
        bad[0]["word_id"] = "wrong"
        with self.assertRaises(ValidationError):
            validate_task1(bad, self.task1_input)

    def test_task1_rejects_missing_language_field(self) -> None:
        bad = copy.deepcopy(self.task1_output)
        del bad[0]["meaning_ja__zh"]
        with self.assertRaises(ValidationError):
            validate_task1(bad, self.task1_input)

    def test_task1_rejects_meaning_for_absent_language(self) -> None:
        bad = copy.deepcopy(self.task1_output)
        bad[0]["meaning_ja__ko"] = "韓国語の意味"
        with self.assertRaises(ValidationError):
            validate_task1(bad, self.task1_input)

    def test_task1_rejects_single_character_different_word(self) -> None:
        bad = copy.deepcopy(self.task1_output)
        bad[0].update({
            "meaning_ja__vi": "", "vi_check": "different_word",
            "vi_check_reason": "別字", "confidence": "low", "low_reason": "別字",
        })
        with self.assertRaises(ValidationError):
            validate_task1(bad, self.task1_input)

    def test_task1_rejects_high_confidence_unsure(self) -> None:
        bad = copy.deepcopy(self.task1_output)
        bad[0].update({"vi_check": "unsure", "vi_check_reason": "根拠不足"})
        with self.assertRaises(ValidationError):
            validate_task1(bad, self.task1_input)

    def test_task2_rejects_absent_false_friend_language(self) -> None:
        inputs = [{"key": "x", "ja": "じ", "ko": "", "pinyin": "zì", "vi": ""}]
        output = [{
            "key": "x", "false_friend": ["ko"],
            "meanings": [
                {"lang": "ja", "meaning_ja": "字", "is_trap": False},
                {"lang": "zh", "meaning_ja": "文字", "is_trap": False},
            ],
            "confidence": "high", "low_reason": "",
        }]
        with self.assertRaises(ValidationError):
            validate_task2(output, inputs)

    def test_task2_rejects_baseline_language_as_false_friend(self) -> None:
        inputs = [{"key": "x", "ja": "じ", "ko": "", "pinyin": "zì", "vi": ""}]
        output = [{
            "key": "x", "false_friend": ["ja"],
            "meanings": [
                {"lang": "ja", "meaning_ja": "字", "is_trap": True},
                {"lang": "zh", "meaning_ja": "文字", "is_trap": False},
            ],
            "confidence": "high", "low_reason": "",
        }]
        with self.assertRaises(ValidationError):
            validate_task2(output, inputs)

    @staticmethod
    def valid_task3() -> tuple[dict, list[dict]]:
        inputs = [{
            "language": "zh", "level": 1, "seed": 1,
            "words": [
                {"word_id": "w1", "display": "学习", "meaning_ja": "学ぶ", "level": 1},
                {"word_id": "w2", "display": "中国", "meaning_ja": "中国", "level": 1},
                {"word_id": "w3", "display": "历史", "meaning_ja": "歴史", "level": 1},
            ],
        }]
        passage = {
            "translation_ja": "中国の歴史を学ぶ。",
            "tokens": [
                {"t": "学习", "word_id": "w1"}, {"t": "中国", "word_id": "w2"},
                {"t": "历史", "word_id": "w3"}, {"t": "。", "punct": True},
            ],
        }
        return {"passages": [copy.deepcopy(passage) for _ in range(6)]}, inputs

    def test_task3_rejects_wrong_token_text(self) -> None:
        output, inputs = self.valid_task3()
        output["passages"][0]["tokens"][0]["t"] = "學習"
        with self.assertRaises(ValidationError):
            validate_task3(output, inputs)

    def test_task3_rejects_unknown_word_id(self) -> None:
        output, inputs = self.valid_task3()
        output["passages"][0]["tokens"][0]["word_id"] = "bad"
        with self.assertRaises(ValidationError):
            validate_task3(output, inputs)

    def test_task4_rejects_unknown_readings(self) -> None:
        inputs = [{
            "word_id": "w1", "trad": "牡丹", "ko": "모란", "vi": "mẫu đơn",
            "differences": [{
                "char": "丹", "lang": "ko", "reading_here": "란", "primary": "단",
                "examples_primary": [{"trad": "丹心", "reading": "단"}], "examples_here": [],
            }],
        }]
        good = [{"word_id": "w1", "note_ja": "「丹」は通常「단」、「牡丹」では「란」と読む。"}]
        validate_task4(good, inputs)
        bad_hangul = [{"word_id": "w1", "note_ja": "「丹」は通常「락」、「牡丹」では「란」と読む。"}]
        with self.assertRaises(ValidationError):
            validate_task4(bad_hangul, inputs)
        bad_vi = [{"word_id": "w1", "note_ja": "「丹」は通常「dịch」、「牡丹」では「란」と読む。"}]
        with self.assertRaises(ValidationError):
            validate_task4(bad_vi, inputs)


if __name__ == "__main__":
    unittest.main()
