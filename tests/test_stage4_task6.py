from __future__ import annotations

import copy
import csv
import json
import tempfile
import unicodedata
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from pipeline.stage4 import builders
from pipeline.stage4.runner import (
    CREDIT_DEADLINE_UTC,
    Stage4Error,
    enforce_ceiling,
    enforce_credit_deadline,
    generate_task6_batch,
    main,
    rerun_task6,
)
from pipeline.stage4.validators import (
    PINYIN_SYLLABLES,
    RESPONSE_SCHEMAS,
    ValidationError,
    _toneless,
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

    def test_inventory_covers_all_dictionary_character_readings(self) -> None:
        chars = builders.load_csv(builders.CHARS_PATH)
        syllables = {
            _toneless(reading)
            for readings in chars["pinyin_all"]
            for reading in readings.split(";")
            if reading
        }
        self.assertFalse(syllables - PINYIN_SYLLABLES)

    def test_r_syllables_and_initial_tone_marked_capitals(self) -> None:
        cases = [
            ("自然", "zìrán", "这是自然现象。", "Zhè shì zìrán xiànxiàng."),
            ("然后", "ránhòu", "我先吃饭，然后出门。", "Wǒ xiān chīfàn, ránhòu chūmén."),
            ("让", "ràng", "请让他进来。", "Qǐng ràng tā jìnlái."),
            ("土壤", "tǔrǎng", "土壤很肥沃。", "Tǔrǎng hěn féiwò."),
            ("围绕", "wéirào", "大家围绕这个问题讨论。", "Dàjiā wéirào zhège wèntí tǎolùn."),
            ("扰乱", "rǎoluàn", "别扰乱课堂。", "Bié rǎoluàn kètáng."),
            ("按照", "ànzhào", "按照惯例，我们先开会。", "Ànzhào guànlì, wǒmen xiān kāihuì."),
            ("欧洲", "ōuzhōu", "欧洲的冬天很冷。", "Ōuzhōu de dōngtiān hěn lěng."),
            ("二", "èr", "二楼有教室。", "Èr lóu yǒu jiàoshì."),
        ]
        for target, target_pinyin, sentence, pinyin in cases:
            with self.subTest(target=target):
                validate_task6(
                    [zh_output(sentence=sentence, pinyin=pinyin)],
                    [zh_input(target=target, pinyin=target_pinyin)], "zh",
                )

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

    def test_foreign_letters_warn_without_failing(self) -> None:
        note = {"key": "c00001:note", "note_ja": "「điện não」はベトナム語。", "confidence": "high", "review_note": ""}
        self.assertEqual(validate_task6([note], [{"key": note["key"]}], "note"), [])
        zh = zh_output(translation="人々はCDを使う。")
        self.assertEqual(validate_task6([zh], [zh_input()], "zh"), [])
        cases = [
            ("zh", zh_input(), {**zh, "translation_ja": "人々はCDを使う。م"}, "translation_ja"),
            ("vi", vi_input(), {**vi_output(), "translation_ja": "とてもきれいです。م"}, "translation_ja"),
            ("note", {"key": note["key"]}, {**note, "note_ja": "日常語です。Жé"}, "note_ja"),
        ]
        for kind, item, output, field in cases:
            with self.subTest(kind=kind):
                self.assertIn(
                    {"key": output["key"], "warning": "translation_script", "field": field},
                    validate_task6([output], [item], kind),
                )


class Task6RunnerTests(unittest.TestCase):
    def test_credit_guard_boundary_and_override(self) -> None:
        enforce_credit_deadline(now=datetime(2026, 11, 16, 7, 59, 59, tzinfo=timezone.utc))
        with self.assertRaisesRegex(Stage4Error, "2026-11-16T08:00:00Z"):
            enforce_credit_deadline(now=CREDIT_DEADLINE_UTC)
        enforce_credit_deadline(True, now=CREDIT_DEADLINE_UTC)

    def test_accepted_task6_dry_run_is_refused_before_client_or_counting(self) -> None:
        with (
            patch("pipeline.stage4.runner.stage4_lock"),
            patch("pipeline.stage4.runner.run_task6", return_value=0) as run,
            patch("pipeline.stage4.runner.create_client") as client,
            patch("pipeline.stage4.runner.count_tokens") as count,
        ):
            self.assertEqual(main(["--task", "6", "--dry-run"]), 1)
        run.assert_not_called()
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
        last_bad_b = {"sentence": bad_b["sentence"], "key": bad_b["key"]}
        calls: list[list[str]] = []

        def partial_request(client, batch, label, items, kind, *flags):
            calls.append([item["key"] for item in items])
            output = {"1": [good_a, bad_b], "1r1": [last_bad_b]}.get(label)
            return output, {
                "attempt": label, "keys": calls[-1], "usage": {"input_tokens": 10}, "usd": 0.01,
                "validation_ok": label == "1", "error": "invalid schema or no response",
            }

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
            self.assertEqual(log["failed_outputs"], {"b:zh:card": last_bad_b})
            self.assertEqual(list(log["failed_outputs"]["b:zh:card"]), list(last_bad_b))
            self.assertEqual(calls, [["a:zh:card", "b:zh:card"], ["b:zh:card"], ["b:zh:card"]])
            stored_partial = output_path.read_bytes()

            def resume_request(client, batch, label, items, kind, *flags):
                calls.append([item["key"] for item in items])
                return [good_b], {
                    "attempt": label, "keys": calls[-1], "usage": {"input_tokens": 10},
                    "usd": 0.01, "validation_ok": True, "error": "",
                }

            for legacy in (False, True):
                with self.subTest(legacy=legacy):
                    prior_log = dict(log)
                    if legacy:
                        del prior_log["failed_outputs"]
                        del prior_log["requests"]
                    log_path.write_text(json.dumps(prior_log), encoding="utf-8")
                    output_path.write_bytes(stored_partial)
                    calls.clear()
                    with (
                        patch("pipeline.stage4.runner.vertex_settings", return_value=("p", "global")),
                        patch("pipeline.stage4.runner._task6_api_request", side_effect=resume_request),
                    ):
                        result = generate_task6_batch(None, "b001", "zh", inputs, output_path, log_path)
                    self.assertEqual(calls, [["b:zh:card"]])
                    self.assertEqual(result, [good_a, good_b])
                    resumed = json.loads(log_path.read_text(encoding="utf-8"))
                    self.assertEqual(resumed["failed_outputs"], {})
                    expected_attempts = ["2r1"] if legacy else ["1", "1r1", "1r2", "2r1"]
                    self.assertEqual([request["attempt"] for request in resumed["requests"]], expected_attempts)
                    self.assertEqual(resumed["usage"]["input_tokens"], 10 * len(expected_attempts))
                    self.assertAlmostEqual(resumed["usd"], 0.01 * len(expected_attempts))

    def test_round_one_builds_all_review_inputs_without_a_client(self) -> None:
        with (builders.ROOT / "config" / "task6_rerun.csv").open(encoding="utf-8", newline="") as source:
            expected = {row["key"]: row["reason"] for row in csv.DictReader(source) if row["round"] == "1"}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with (
                patch("pipeline.stage4.runner.INPUTS", root / "inputs"),
                patch("pipeline.stage4.runner.GENERATED", root / "generated"),
                patch("pipeline.stage4.runner.generate_task6_batch", return_value=[]) as generate,
            ):
                self.assertEqual(rerun_task6(None, 1), 0)
            built = [call.args[3] for call in generate.call_args_list]
            self.assertEqual(
                [(call.args[0], call.args[2]) for call in generate.call_args_list],
                [(None, "zh"), (None, "vi")],
            )
            self.assertEqual([len(items) for items in built], [19, 6])
            self.assertEqual({item["key"]: item["review_feedback"] for items in built for item in items}, expected)

    def test_rerun_retry_skips_validated_batch_and_resumes_partial(self) -> None:
        zh = zh_output()
        vi_a = vi_output()
        vi_b = vi_output("w00002:vi:card")
        bad_b = {**vi_b, "sentence": "Việt Nam rất đẹp"}
        results = iter([[zh], [vi_a, bad_b], [bad_b], [bad_b], [vi_b]])

        def request(client, batch, label, items, kind, *flags):
            return next(results), {"attempt": label, "validation_ok": True, "usage": {}, "usd": 0}

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "config").mkdir()
            (root / "config" / "task6_rerun.csv").write_text(
                "round,key,reason\n1,w00001:zh:card,review\n1,w00001:vi:card,review\n1,w00002:vi:card,review\n",
                encoding="utf-8",
            )
            with (
                patch("pipeline.stage4.runner.ROOT", root),
                patch("pipeline.stage4.runner.INPUTS", root / "inputs"),
                patch("pipeline.stage4.runner.GENERATED", root / "generated"),
                patch("pipeline.stage4.runner.builders.build_task6_items", return_value={
                    "zh_card": [zh_input()], "vi_card": [vi_input(), vi_input(vi_b["key"])],
                }),
                patch("pipeline.stage4.runner.vertex_settings", return_value=("p", "global")),
                patch("pipeline.stage4.runner._task6_api_request", side_effect=request) as api,
            ):
                self.assertEqual(rerun_task6(None, 1), 1)
                api.reset_mock()
                self.assertEqual(rerun_task6(None, 1), 0)
            api.assert_called_once()
            _, batch, label, items, kind, *_ = api.call_args.args
            self.assertEqual((batch, label, kind), ("b002", "2r1", "vi"))
            self.assertEqual([item["key"] for item in items], [vi_b["key"]])

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
