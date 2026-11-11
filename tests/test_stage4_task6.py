from __future__ import annotations

import copy
import io
import json
import tempfile
import unicodedata
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pipeline.stage4 import builders
from pipeline.stage4.runner import (
    CREDIT_DEADLINE_UTC,
    Stage4Error,
    dry_run_task6,
    enforce_ceiling,
    enforce_credit_deadline,
    generate_task6_batch,
    main,
    rerun_task6,
)
from pipeline.stage4.validators import (
    RESPONSE_SCHEMAS,
    ValidationError,
    validate_task6,
    validate_task6_items,
)


def zh_input(key: str = "w00001:zh:card", target: str = "学习", pinyin: str = "xuéxí") -> dict:
    return {"key": key, "target": target, "target_pinyin": pinyin}


def zh_output(
    key: str = "w00001:zh:card", sentence: str = "我学习汉语。",
    pinyin: str = "Wǒ xuéxí hànyǔ.", translation: str = "私は中国語を勉強します。",
) -> dict:
    return {
        "key": key, "status": "ok", "sentence": sentence, "pinyin": pinyin,
        "translation_ja": translation, "confidence": "high", "review_note": "",
    }


def vi_input(key: str = "w00001:vi:card", target: str = "việt nam") -> dict:
    return {"key": key, "target": target}


def vi_output(key: str = "w00001:vi:card", sentence: str = "Việt Nam rất đẹp.") -> dict:
    return {
        "key": key, "status": "ok", "sentence": sentence,
        "translation_ja": "ベトナムはとても美しいです。", "confidence": "high",
        "review_note": "",
    }


class Task6BuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.items = builders.build_task6_items()

    def test_exact_counts_and_batch_boundaries(self) -> None:
        self.assertEqual(
            {kind: len(items) for kind, items in self.items.items()},
            builders.TASK6_EXPECTED_COUNTS,
        )
        batches = builders.build_task6_batches()
        self.assertEqual(len(batches), 224)
        self.assertEqual((batches[0][0], batches[126][0]), ("b001", "b127"))
        self.assertEqual({kind for _, kind, _ in batches[:127]}, {"zh"})
        self.assertEqual((batches[127][0], batches[210][0]), ("b128", "b211"))
        self.assertEqual({kind for _, kind, _ in batches[127:211]}, {"vi"})
        self.assertEqual((batches[211][0], batches[-1][0]), ("b212", "b224"))
        self.assertEqual({kind for _, kind, _ in batches[211:]}, {"note"})

    def test_coverage_rule_creates_20_and_8_meaning_conflicts(self) -> None:
        words = builders.load_csv(builders.WORDS_PATH).set_index("word_id")
        ff = builders.load_csv(builders.FF_MEANINGS_PATH)
        for lang, expected in (("zh", 20), ("vi", 8)):
            card_ids = {item["key"].split(":", 1)[0] for item in self.items[f"{lang}_card"]}
            rows = ff.loc[(ff["lang"] == lang) & ff["word_id"].isin(card_ids)]
            field = f"meaning_ja__{lang}"
            differing = sum(words.loc[row.word_id, field] != row.meaning_ja for row in rows.itertuples())
            self.assertEqual(differing, expected)

    def test_field_order_and_determinism(self) -> None:
        expected = {
            "zh_card": builders.TASK6_ZH_FIELDS, "zh_ff": builders.TASK6_ZH_FIELDS,
            "vi_card": builders.TASK6_VI_FIELDS, "vi_ff": builders.TASK6_VI_FIELDS,
            "note": builders.TASK6_NOTE_FIELDS,
        }
        for kind, items in self.items.items():
            self.assertTrue(all(list(item) == expected[kind] for item in items))
        first = builders.jsonl_text(item for values in self.items.values() for item in values)
        second_items = builders.build_task6_items()
        second = builders.jsonl_text(item for values in second_items.values() for item in values)
        self.assertEqual(first, second)

    def test_pilot_sets(self) -> None:
        pilot = builders.build_pilot_task6()
        self.assertEqual({kind: len(items) for kind, items in pilot.items()}, {"zh": 50, "vi": 50, "note": 50})
        self.assertTrue({"手紙", "大丈夫"}.issubset({item["trad"] for item in pilot["zh"]}))
        self.assertEqual(sum(len(item["trad"]) == 1 and item["key"].endswith(":ff") for item in pilot["vi"]), 6)
        self.assertEqual(pilot["note"][0]["char"], "幫")


class Task6ValidatorTests(unittest.TestCase):
    def test_schemas_have_exact_property_order(self) -> None:
        for kind in ("zh", "vi", "note"):
            self.assertEqual(
                RESPONSE_SCHEMAS[6][kind]["items"]["propertyOrdering"],
                __import__("pipeline.stage4.validators", fromlist=["TASK6_KEYS"]).TASK6_KEYS[kind],
            )

    def test_special_pinyin_cases_pass(self) -> None:
        cases = [
            ("一点儿", "yīdiǎnr", "我买一点儿菜。", "Wǒ mǎi yīdiǎnr cài."),
            ("哪儿", "nǎr", "你去哪儿？", "Nǐ qù nǎr?"),
            ("东西", "dōngxi", "这个东西很好。", "Zhège dōngxi hěn hǎo."),
            ("对不起", "duìbuqǐ", "对不起，我来晚了。", "Duìbuqǐ, wǒ lái wǎn le."),
            ("西安", "xī'ān", "我住在西安。", "Wǒ zhù zài Xī'ān."),
        ]
        for index, (target, target_pinyin, sentence, pinyin) in enumerate(cases):
            key = f"w{index}:zh:card"
            with self.subTest(target=target):
                validate_task6([zh_output(key, sentence, pinyin)], [zh_input(key, target, target_pinyin)], "zh")

    def test_batch_order_schema_and_common_string_rules(self) -> None:
        inputs = [zh_input("a:zh:card"), zh_input("b:zh:card")]
        outputs = [zh_output("a:zh:card"), zh_output("b:zh:card")]
        with self.assertRaises(ValidationError):
            validate_task6(list(reversed(outputs)), inputs, "zh")
        bad = copy.deepcopy(outputs)
        bad[0] = {"status": "ok", **bad[0]}
        with self.assertRaises(ValidationError):
            validate_task6(bad, inputs, "zh")
        bad = copy.deepcopy(outputs)
        bad[0]["translation_ja"] = " 日本語です。"
        with self.assertRaises(ValidationError):
            validate_task6(bad, inputs, "zh")
        bad = copy.deepcopy(outputs)
        bad[0]["review_note"] = "한글"
        with self.assertRaises(ValidationError):
            validate_task6(bad, inputs, "zh")

    def test_no_sentence_and_low_rules(self) -> None:
        item = zh_output()
        item.update({"status": "no_sentence", "sentence": "", "pinyin": "", "translation_ja": "", "review_note": "現代語では使わない"})
        validate_task6([item], [zh_input()], "zh")
        item["review_note"] = ""
        with self.assertRaises(ValidationError):
            validate_task6([item], [zh_input()], "zh")
        item.update({"status": "ok", "sentence": "我学习汉语。", "pinyin": "Wǒ xuéxí hànyǔ.", "translation_ja": "勉強します。", "confidence": "low"})
        with self.assertRaises(ValidationError):
            validate_task6([item], [zh_input()], "zh")

    def test_zh_rejections_and_item_isolation(self) -> None:
        bad_values = [
            ("我學习汉语。", "Wǒ xuéxí hànyǔ.", "traditional"),
            ("我学习汉语。", "Wǒ xuéxi hànyǔ.", "target tone"),
            ("我学习一下。", "Wǒ xuéxí yíxià.", "sandhi"),
            ("我学习汉语。", "Wǒ xue2xi2 hànyǔ.", "tone numbers"),
            ("我学习汉语。", "Wǒ xuéxí.", "alignment"),
        ]
        inputs = [zh_input()]
        for sentence, pinyin, label in bad_values:
            with self.subTest(label=label), self.assertRaises(ValidationError):
                validate_task6([zh_output(sentence=sentence, pinyin=pinyin)], inputs, "zh")
        good = zh_output("a:zh:card")
        bad = zh_output("b:zh:card", pinyin="bad")
        valid, errors, _ = validate_task6_items(
            [good, bad], [zh_input("a:zh:card"), zh_input("b:zh:card")], "zh"
        )
        self.assertEqual([item["key"] for item in valid], ["a:zh:card"])
        self.assertEqual(set(errors), {"b:zh:card"})

    def test_vi_casefold_and_rejections(self) -> None:
        validate_task6([vi_output()], [vi_input()], "vi")
        bad = vi_output(sentence="Đây là Việt Nam đẹp")
        with self.assertRaises(ValidationError):
            validate_task6([bad], [vi_input()], "vi")
        double_tone = unicodedata.normalize("NFC", "Việt Nắ\u0301m đẹp.")
        bad = vi_output(sentence=double_tone)
        with self.assertRaises(ValidationError):
            validate_task6([bad], [vi_input(target=unicodedata.normalize("NFC", "việt nắ\u0301m"))], "vi")

    def test_translation_and_note_rules(self) -> None:
        bad = zh_output(translation="Tiếng Việt")
        with self.assertRaises(ValidationError):
            validate_task6([bad], [zh_input()], "zh")
        note_input = [{"key": "c00001:note"}]
        good = [{"key": "c00001:note", "note_ja": "ベトナム語では普通使わない", "confidence": "high", "review_note": ""}]
        validate_task6(good, note_input, "note")
        empty = copy.deepcopy(good)
        empty[0]["note_ja"] = ""
        warnings = validate_task6(empty, note_input, "note")
        self.assertEqual(warnings[0]["warning"], "empty_note_ja")
        bad_note = copy.deepcopy(good)
        bad_note[0]["note_ja"] = "Vietnamese only"
        with self.assertRaises(ValidationError):
            validate_task6(bad_note, note_input, "note")


class Task6RunnerTests(unittest.TestCase):
    def test_credit_guard_boundary_and_override(self) -> None:
        enforce_credit_deadline(now=datetime(2026, 11, 16, 7, 59, 59, tzinfo=timezone.utc))
        with self.assertRaisesRegex(Stage4Error, "2026-11-16T08:00:00Z"):
            enforce_credit_deadline(now=CREDIT_DEADLINE_UTC)
        enforce_credit_deadline(True, now=CREDIT_DEADLINE_UTC)

    def test_dry_run_path_never_constructs_client_or_counts_tokens(self) -> None:
        with (
            patch("pipeline.stage4.runner.stage4_lock"),
            patch("pipeline.stage4.runner.run_task6", return_value=0) as run,
            patch("pipeline.stage4.runner.create_client") as client,
            patch("pipeline.stage4.runner.count_tokens") as count,
        ):
            self.assertEqual(main(["--task", "6", "--dry-run"]), 0)
        run.assert_called_once_with(None, None, True)
        client.assert_not_called()
        count.assert_not_called()

    def test_ceiling_uses_200_output_tokens_per_item(self) -> None:
        with (
            patch("pipeline.stage4.runner.existing_cost", return_value=199.999),
            patch("pipeline.stage4.runner.load_prices", return_value={
                "hard_ceiling": 200,
                "models": {"gemini-4-argon": [{"through": "2026-11-30", "input_per_million": 2, "output_per_million": 10, "thinking_per_million": 10}]},
            }),
        ):
            with self.assertRaises(Stage4Error):
                enforce_ceiling(1, 6, 1)

    def test_item_repair_keeps_valid_items_and_resume_only_failed_keys(self) -> None:
        inputs = [zh_input("a:zh:card"), zh_input("b:zh:card", "银行", "yínháng")]
        good_a = zh_output("a:zh:card")
        bad_b = zh_output("b:zh:card", "我去银行。", "bad")
        good_b = zh_output("b:zh:card", "我去银行。", "Wǒ qù yínháng.", "私は銀行へ行きます。")
        calls: list[list[str]] = []

        def partial_request(client, batch, label, items, kind, *flags):
            calls.append([item["key"] for item in items])
            output = [good_a, bad_b] if len(calls) == 1 else [bad_b]
            return output, {"attempt": label, "keys": calls[-1], "usage": {}, "usd": 0, "validation_ok": True, "error": ""}

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output_path, log_path = root / "b001.jsonl", root / "b001.log.json"
            with (
                patch("pipeline.stage4.runner.vertex_settings", return_value=("p", "global")),
                patch("pipeline.stage4.runner._task6_api_request", side_effect=partial_request),
            ):
                self.assertIsNone(generate_task6_batch(Mock(), "b001", "zh", inputs, output_path, log_path))
            log = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(log["validation"]["state"], "partial")
            self.assertEqual(log["failed_keys"], ["b:zh:card"])
            self.assertEqual(calls, [["a:zh:card", "b:zh:card"], ["b:zh:card"], ["b:zh:card"]])

            calls.clear()
            def resume_request(client, batch, label, items, kind, *flags):
                calls.append([item["key"] for item in items])
                return [good_b], {"attempt": label, "keys": calls[-1], "usage": {}, "usd": 0, "validation_ok": True, "error": ""}
            with (
                patch("pipeline.stage4.runner.vertex_settings", return_value=("p", "global")),
                patch("pipeline.stage4.runner._task6_api_request", side_effect=resume_request),
            ):
                result = generate_task6_batch(Mock(), "b001", "zh", inputs, output_path, log_path)
            self.assertEqual(calls, [["b:zh:card"]])
            self.assertEqual([item["key"] for item in result], ["a:zh:card", "b:zh:card"])

    def test_unknown_rerun_key_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "config").mkdir()
            (root / "config" / "task6_rerun.csv").write_text(
                "round,key,reason\n1,unknown,wrong\n", encoding="utf-8"
            )
            with (
                patch("pipeline.stage4.runner.ROOT", root),
                patch("pipeline.stage4.runner.builders.build_task6_items", return_value={
                    "zh_card": [zh_input()], "zh_ff": [], "vi_card": [], "vi_ff": [], "note": [],
                }),
            ):
                with self.assertRaisesRegex(Stage4Error, "unknown key"):
                    rerun_task6(Mock(), 1)


if __name__ == "__main__":
    unittest.main()
