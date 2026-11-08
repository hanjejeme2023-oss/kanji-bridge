from __future__ import annotations

import re
import json
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpcore
import httpx

from pipeline.stage4 import builders
from pipeline.stage4.runner import (
    MODEL_ID,
    REQUEST_TIMEOUT_MS,
    Stage4Error,
    calculate_cost,
    estimated_chargeable_output,
    enforce_argon_deadline,
    generation_config,
    guard_api_keys,
    response_text_or_error,
    run_status,
    run_task,
    generate_batch,
    main,
    prompt_text,
    stage4_lock,
    usage_from_response,
)


ROOT = Path(__file__).resolve().parents[1]


class Stage4SafetyTests(unittest.TestCase):
    def test_api_key_guard(self) -> None:
        guard_api_keys({})
        for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            with self.subTest(name=name), self.assertRaises(Stage4Error):
                guard_api_keys({name: "not-a-real-key"})

    def test_empty_response_reports_finish_reason_and_tokens(self) -> None:
        response = SimpleNamespace(
            text=None,
            candidates=[SimpleNamespace(finish_reason=SimpleNamespace(value="MAX_TOKENS"))],
        )
        usage = {"input_tokens": 11, "output_tokens": 0, "thinking_tokens": 32}
        with self.assertRaisesRegex(
            Stage4Error,
            r"finish_reason=MAX_TOKENS, input_tokens=11, output_tokens=0, thinking_tokens=32",
        ):
            response_text_or_error(response, usage)

    def test_total_token_count_difference_is_billed_at_output_rate(self) -> None:
        response = SimpleNamespace(usage_metadata=SimpleNamespace(
            prompt_token_count=10,
            candidates_token_count=20,
            thoughts_token_count=30,
            total_token_count=100,
        ))
        usage = usage_from_response(response)
        self.assertEqual(usage["total_token_count"], 100)
        self.assertEqual(usage["unreported_tokens"], 40)
        cost = calculate_cost(
            **usage,
            model_id="gemini-4-argon",
            at=datetime(2026, 11, 6, tzinfo=timezone.utc),
        )
        self.assertAlmostEqual(cost, 0.00092)

    def test_request_timeout_and_outer_retry_configuration(self) -> None:
        options = generation_config(1).http_options
        self.assertEqual(options.timeout, REQUEST_TIMEOUT_MS)
        self.assertEqual(options.retry_options.attempts, 1)

    def test_task3_prompt_is_selected_by_cell_language(self) -> None:
        zh_prompt = prompt_text(3, [{"language": "zh"}])
        vi_prompt = prompt_text(3, [{"language": "vi"}])
        self.assertIn("(v2", zh_prompt)
        self.assertIn("(v3, Vietnamese cells)", vi_prompt)
        self.assertNotEqual(zh_prompt, vi_prompt)
        for task in (1, 2, 4):
            with self.subTest(task=task):
                self.assertEqual(prompt_text(task), prompt_text(task, [{"language": "vi"}]))

    def test_argon_deadline_guard_uses_utc_date(self) -> None:
        before = datetime(2026, 11, 30, 23, 59, tzinfo=timezone.utc)
        boundary = datetime(2026, 12, 1, 0, 0, tzinfo=timezone.utc)
        enforce_argon_deadline(now=before)
        with self.assertRaisesRegex(Stage4Error, "UTC date 2026-12-01"):
            enforce_argon_deadline(now=boundary)
        enforce_argon_deadline(allow_after_deadline=True, now=boundary)

    def test_task_resume_skips_validated_batch_and_runs_failed_batch(self) -> None:
        item = {
            "key": "w1", "checks": ["ko"], "trad": "文字", "ja": "もじ", "ko": "문자",
            "pinyin": "wénzì", "vi": "văn tự",
        }
        output = [{
            "key": "w1", "ja_check": "", "ja_reason": "",
            "ko_check": "used", "ko_reason": "", "vi_use": "", "vi_reason": "",
        }]
        prompt = "test prompt"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inputs = root / "inputs"
            generated = root / "generated"
            output_path = generated / "task5" / "b001.jsonl"
            log_path = generated / "task5" / "b001.log.json"
            builders.write_jsonl(output_path, output)
            log = {
                "task": 5, "batch": "b001", "model": MODEL_ID,
                "prompt_sha256": builders.sha256_text(prompt),
                "input_sha256": builders.sha256_text(builders.jsonl_text([item])),
                "item_count": 1, "validation": {"ok": True, "error": ""},
            }
            log_path.write_text(json.dumps(log), encoding="utf-8")
            generate = Mock(return_value=output)
            with (
                patch("pipeline.stage4.runner.INPUTS", inputs),
                patch("pipeline.stage4.runner.GENERATED", generated),
                patch("pipeline.stage4.runner.prompt_text", return_value=prompt),
                patch("pipeline.stage4.runner.builders.task_batches", return_value=[[item]]),
                patch("pipeline.stage4.runner.require_accepted_layout"),
                patch("pipeline.stage4.runner.generate_batch", generate),
            ):
                self.assertEqual(run_task(Mock(), 5, None, False), 0)
                generate.assert_not_called()
                log["validation"]["ok"] = False
                log_path.write_text(json.dumps(log), encoding="utf-8")
                self.assertEqual(run_task(Mock(), 5, None, False), 0)
                generate.assert_called_once()

    def test_task3_resume_keeps_zh_v2_and_reruns_vi_v2(self) -> None:
        zh_items = [{"language": "zh", "level": 1, "words": []}]
        vi_items = [{"language": "vi", "level": 1, "words": []}]
        v2_sha = builders.sha256_text(prompt_text(3, zh_items))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generated = root / "generated"
            for number, items in enumerate((zh_items, vi_items), 1):
                name = f"b{number:03d}"
                output_path = generated / "task3" / f"{name}.jsonl"
                log_path = generated / "task3" / f"{name}.log.json"
                builders.write_jsonl(output_path, [{"passages": []}])
                log_path.write_text(json.dumps({
                    "task": 3,
                    "batch": name,
                    "model": MODEL_ID,
                    "prompt_sha256": v2_sha,
                    "input_sha256": builders.sha256_text(builders.jsonl_text(items)),
                    "item_count": 1,
                    "validation": {"ok": True, "error": ""},
                }), encoding="utf-8")
            generate = Mock(return_value={"passages": []})
            with (
                patch("pipeline.stage4.runner.INPUTS", root / "inputs"),
                patch("pipeline.stage4.runner.GENERATED", generated),
                patch("pipeline.stage4.runner.require_accepted_layout"),
                patch("pipeline.stage4.runner.builders.task_batches", return_value=[zh_items, vi_items]),
                patch("pipeline.stage4.runner.read_generated_output", return_value={"passages": []}),
                patch("pipeline.stage4.runner.validate", return_value=[]),
                patch("pipeline.stage4.runner.generate_batch", generate),
            ):
                with self.assertRaisesRegex(Stage4Error, "D65 refusal"):
                    run_task(Mock(), 3, None, False)
            generate.assert_not_called()

    def test_task5_dry_run_counts_only_stale_batches(self) -> None:
        first_items = [{"key": "a", "checks": ["ko"], "ko": "가", "vi": ""}]
        second_items = [{"key": "b", "checks": ["ko"], "ko": "나", "vi": ""}]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generated = root / "generated"
            output_path = generated / "task5" / "b001.jsonl"
            log_path = generated / "task5" / "b001.log.json"
            builders.write_jsonl(output_path, [{
                "key": "a", "ja_check": "", "ja_reason": "", "ko_check": "used",
                "ko_reason": "", "vi_use": "", "vi_reason": "",
            }])
            log_path.write_text(json.dumps({
                "task": 5,
                "batch": "b001",
                "model": MODEL_ID,
                "prompt_sha256": builders.sha256_text(prompt_text(5, first_items)),
                "input_sha256": builders.sha256_text(builders.jsonl_text(first_items)),
                "item_count": 1,
                "validation": {"ok": True, "error": ""},
            }), encoding="utf-8")
            count = Mock(return_value=17)
            stream = io.StringIO()
            with (
                patch("pipeline.stage4.runner.INPUTS", root / "inputs"),
                patch("pipeline.stage4.runner.GENERATED", generated),
                patch("pipeline.stage4.runner.require_accepted_layout"),
                patch("pipeline.stage4.runner.builders.task_batches", return_value=[first_items, second_items]),
                patch("pipeline.stage4.runner.count_tokens", count),
                redirect_stdout(stream),
            ):
                self.assertEqual(run_task(Mock(), 5, None, True), 0)
            self.assertEqual(count.call_count, 1)
            self.assertTrue(count.call_args.args[1].startswith(prompt_text(5, second_items)))
            self.assertIn("task=5 batches=1 total_input_tokens=17", stream.getvalue())

    def test_ceiling_estimate_uses_only_matching_prompt_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            generated = Path(temp)
            logs = (
                ("zh", 100, prompt_text(3, [{"language": "zh"}])),
                ("vi", 900, prompt_text(3, [{"language": "vi"}])),
            )
            for label, output_tokens, prompt in logs:
                (generated / f"{label}.log.json").write_text(json.dumps({
                    "task": 3,
                    "model": MODEL_ID,
                    "prompt_sha256": builders.sha256_text(prompt),
                    "item_count": 1,
                    "usage": {
                        "output_tokens": output_tokens,
                        "thinking_tokens": 0,
                        "unreported_tokens": 0,
                    },
                    "validation": {"ok": True},
                }), encoding="utf-8")
            with patch("pipeline.stage4.runner.GENERATED", generated):
                estimate = estimated_chargeable_output(
                    3, 2, prompt_sha256=builders.sha256_text(logs[1][2])
                )
            self.assertEqual(estimate, 1800)

    def test_api_errors_wait_30_then_60_seconds(self) -> None:
        client = SimpleNamespace(
            models=SimpleNamespace(
                generate_content=Mock(side_effect=RuntimeError("504 DEADLINE_EXCEEDED"))
            )
        )
        item = {"word_id": "w1"}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with (
                patch("pipeline.stage4.runner.vertex_settings", return_value=("project", "global")),
                patch("pipeline.stage4.runner.prompt_text", return_value="prompt"),
                patch("pipeline.stage4.runner.count_tokens", return_value=1),
                patch("pipeline.stage4.runner.enforce_ceiling"),
                patch("pipeline.stage4.runner.generation_config", return_value=object()),
                patch("pipeline.stage4.runner.append_cost"),
                patch("pipeline.stage4.runner.time.sleep") as sleep,
            ):
                result = generate_batch(
                    client, 1, "b001", [item], root / "out.jsonl", root / "out.log.json"
                )
        self.assertIsNone(result)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [30, 60])

    def test_task5_success_log_includes_reason_warnings(self) -> None:
        item = {
            "key": "w1", "checks": ["ko"], "trad": "記事", "ja": "きじ",
            "ko": "기사", "pinyin": "jìshì", "vi": "kí sự",
        }
        output = [{
            "key": "w1", "ja_check": "", "ja_reason": "",
            "ko_check": "rare", "ko_reason": "기사는通常使わない",
            "vi_use": "", "vi_reason": "",
        }]
        response = SimpleNamespace(
            text=json.dumps(output, ensure_ascii=False),
            usage_metadata=SimpleNamespace(
                prompt_token_count=10,
                candidates_token_count=20,
                thoughts_token_count=0,
                total_token_count=30,
            ),
        )
        client = SimpleNamespace(models=SimpleNamespace(
            generate_content=Mock(return_value=response)
        ))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log_path = root / "out.log.json"
            with (
                patch("pipeline.stage4.runner.vertex_settings", return_value=("project", "global")),
                patch("pipeline.stage4.runner.count_tokens", return_value=10),
                patch("pipeline.stage4.runner.enforce_ceiling"),
                patch("pipeline.stage4.runner.generation_config", return_value=object()),
                patch("pipeline.stage4.runner.append_cost"),
            ):
                result = generate_batch(
                    client, 5, "b055", [item], root / "out.jsonl", log_path
                )
            log = json.loads(log_path.read_text(encoding="utf-8"))
        self.assertEqual(result, output)
        self.assertEqual(log["reason_warnings"], [
            {"key": "w1", "field": "ko_reason", "text": "기사는"},
        ])
        self.assertTrue(log["validation"]["ok"])

    def test_count_tokens_remote_protocol_error_is_retried_inside_batch(self) -> None:
        response = SimpleNamespace(
            text="[]",
            usage_metadata=SimpleNamespace(
                prompt_token_count=1,
                candidates_token_count=1,
                thoughts_token_count=0,
                total_token_count=2,
            ),
        )
        client = SimpleNamespace(models=SimpleNamespace(
            count_tokens=Mock(side_effect=[
                httpcore.RemoteProtocolError(
                    b"Server disconnected without sending a response."
                ),
                httpx.RemoteProtocolError("Server disconnected without sending a response."),
                httpx.RemoteProtocolError("Server disconnected without sending a response."),
                SimpleNamespace(total_tokens=1),
            ]),
            generate_content=Mock(return_value=response),
        ))
        batches = [[{"word_id": "w1"}], [{"word_id": "w2"}]]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generated = root / "generated"
            with (
                patch("pipeline.stage4.runner.INPUTS", root / "inputs"),
                patch("pipeline.stage4.runner.GENERATED", generated),
                patch("pipeline.stage4.runner.vertex_settings", return_value=("project", "global")),
                patch("pipeline.stage4.runner.prompt_text", return_value="prompt"),
                patch("pipeline.stage4.runner.builders.task_batches", return_value=batches),
                patch("pipeline.stage4.runner.require_accepted_layout"),
                patch("pipeline.stage4.runner.enforce_ceiling"),
                patch("pipeline.stage4.runner.generation_config", return_value=object()),
                patch("pipeline.stage4.runner.validate", return_value=[]),
                patch("pipeline.stage4.runner.write_output"),
                patch("pipeline.stage4.runner.append_cost"),
                patch("pipeline.stage4.runner.time.sleep") as sleep,
            ):
                failed = run_task(client, 5, None, False)

            failed_log = json.loads(
                (generated / "task5" / "b001.log.json").read_text(encoding="utf-8")
            )
            next_log = json.loads(
                (generated / "task5" / "b002.log.json").read_text(encoding="utf-8")
            )

        self.assertEqual(failed, 1)
        self.assertEqual(client.models.count_tokens.call_count, 4)
        client.models.generate_content.assert_called_once()
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [30, 60])
        self.assertEqual(
            [attempt["operation"] for attempt in failed_log["attempts"]],
            ["count_tokens", "count_tokens", "count_tokens"],
        )
        self.assertTrue(all(
            "RemoteProtocolError" in attempt["error"]
            for attempt in failed_log["attempts"]
        ))
        self.assertFalse(failed_log["validation"]["ok"])
        self.assertTrue(next_log["validation"]["ok"])
        self.assertEqual(next_log["reason_warnings"], [])

    def test_launcher_uses_unbuffered_python(self) -> None:
        source = (ROOT / "pipeline" / "stage4" / "run_stage4.ps1").read_text(encoding="utf-8")
        self.assertIn("& $PythonPath -u $Generator @Arguments | Out-Host", source)

    def test_lock_refuses_live_process_and_replaces_dead_process(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            lock = Path(temp) / ".stage4.lock"
            lock.write_text(f"{os.getpid()}\n", encoding="ascii")
            with self.assertRaisesRegex(Stage4Error, "already running"):
                with stage4_lock(lock):
                    pass
            lock.write_text("999999999\n", encoding="ascii")
            with patch("pipeline.stage4.runner.process_is_running", return_value=False):
                with stage4_lock(lock):
                    self.assertEqual(lock.read_text(encoding="ascii").strip(), str(os.getpid()))
            self.assertFalse(lock.exists())

    def test_status_is_offline_and_reports_accepted_and_task5(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            stream = io.StringIO()
            with (
                patch("pipeline.stage4.runner.GENERATED", Path(temp)),
                patch("pipeline.stage4.runner.existing_cost", return_value=1.25),
                patch("pipeline.stage4.runner.load_prices", return_value={"hard_ceiling": 100}),
                patch("pipeline.stage4.runner.calculate_cost", return_value=15.78),
                redirect_stdout(stream),
            ):
                run_status()
            output = stream.getvalue()
            self.assertIn("task 1: 86/86 validated, 0 failed, 0 missing", output)
            self.assertIn("task 2: 79/79 validated, 0 failed, 0 missing", output)
            self.assertIn("task 5: 0/104 validated, 0 failed, 104 missing", output)
            self.assertIn("task 5 conservative estimate:", output)
            self.assertIn("spend to date: $1.25000000", output)

        with (
            patch("pipeline.stage4.runner.run_status") as status,
            patch("pipeline.stage4.runner.create_client") as create_client,
            patch("pipeline.stage4.runner.stage4_lock") as lock,
        ):
            self.assertEqual(main(["--status"]), 0)
            status.assert_called_once_with()
            create_client.assert_not_called()
            lock.assert_not_called()

    def test_tasks_1_to_4_refuse_before_client_creation(self) -> None:
        for task in range(1, 5):
            with (
                self.subTest(task=task),
                patch("pipeline.stage4.runner.create_client") as create_client,
            ):
                self.assertEqual(main(["--task", str(task)]), 1)
                create_client.assert_not_called()

    def test_run_all_does_not_import_stage4(self) -> None:
        source = (ROOT / "pipeline" / "run_all.py").read_text(encoding="utf-8").lower()
        self.assertNotIn("stage4", source)
        self.assertNotIn("google.genai", source)

    def test_no_credentials_in_project_files(self) -> None:
        api_key = re.compile(r"AIza[0-9A-Za-z_-]{35}")
        private_field = '"private' + '_key"'
        offenders: list[str] = []
        excluded = {".git", "raw", ".venv", "__pycache__"}
        for path in ROOT.rglob("*"):
            if not path.is_file() or excluded.intersection(path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if api_key.search(text) or private_field in text:
                offenders.append(path.relative_to(ROOT).as_posix())
        # HANDOFF contains the literal safety requirement itself, not a credential field.
        offenders = [path for path in offenders if path != "docs/HANDOFF.md"]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
