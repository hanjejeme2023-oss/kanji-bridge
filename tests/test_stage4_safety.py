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
API_KEY_RE = re.compile(r"AIza[0-9A-Za-z_-]{35}")
PRIVATE_FIELD = '"private' + '_key"'
# Docs that report the credential scan quote the searched pattern in a code span
# (RELEASE_PLAN §3.1, the HANDOFF archive). Only those quoted occurrences are exempt.
QUOTED_PATTERN_FILES = {"docs/RELEASE_PLAN.md", "docs/HANDOFF_ARCHIVE.md"}


def credential_lines(text: str, allow_quoted_pattern: bool = False) -> list[int]:
    """1-based numbers of lines with an API key or a private-key field.

    With ``allow_quoted_pattern`` the pattern written as inline code (backticks
    around the quoted field name) is ignored; anything else on the line, or a
    real field elsewhere in the file, still counts.
    """
    hits = []
    for number, line in enumerate(text.splitlines(), 1):
        if allow_quoted_pattern:
            line = line.replace(f"`{PRIVATE_FIELD}`", "")
        if API_KEY_RE.search(line) or PRIVATE_FIELD in line:
            hits.append(number)
    return hits


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

    def test_task5_run_refuses_even_if_generated_files_are_stale(self) -> None:
        with (
            patch("pipeline.stage4.runner.builders.task_batches") as batches,
            patch("pipeline.stage4.runner.generate_batch") as generate,
        ):
            with self.assertRaisesRegex(Stage4Error, "D65 refusal"):
                run_task(Mock(), 5, None, False)
        batches.assert_not_called()
        generate.assert_not_called()

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

    def test_task5_dry_run_refuses_without_counting_tokens(self) -> None:
        with patch("pipeline.stage4.runner.count_tokens") as count:
            with self.assertRaisesRegex(Stage4Error, "D65 refusal"):
                run_task(Mock(), 5, None, True)
        count.assert_not_called()

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
                # R2: the date guards have their own fixed-clock tests; this test is
                # about the retry waits and must not depend on today's date.
                patch("pipeline.stage4.runner.enforce_argon_deadline"),
                patch("pipeline.stage4.runner.enforce_credit_deadline"),
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
                # R2: independent of today's date (see the retry test above).
                patch("pipeline.stage4.runner.enforce_argon_deadline"),
                patch("pipeline.stage4.runner.enforce_credit_deadline"),
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

    def test_accepted_task5_refusal_precedes_any_transport_call(self) -> None:
        client = Mock()
        with self.assertRaisesRegex(Stage4Error, "D65 refusal"):
            run_task(client, 5, None, False)
        client.models.count_tokens.assert_not_called()
        client.models.generate_content.assert_not_called()

    def test_launcher_uses_unbuffered_python(self) -> None:
        source = (ROOT / "pipeline" / "stage4" / "run_stage4.ps1").read_text(encoding="utf-8")
        self.assertIn("& $PythonPath -u $Generator @Arguments | Out-Host", source)
        self.assertIn("if ($TaskNumber -match '^[1-5]$')", source)
        self.assertIn("if ($TaskNumber -eq '6')", source)
        self.assertIn("D75 refusal: task 6 is accepted", source)
        self.assertNotIn("Use -Tasks 5", source)

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
        stream = io.StringIO()
        with (
            patch("pipeline.stage4.runner.existing_cost", return_value=1.25),
            patch("pipeline.stage4.runner.load_prices", return_value={"hard_ceiling": 100}),
            redirect_stdout(stream),
        ):
            run_status()
        output = stream.getvalue()
        self.assertIn("task 1: 86/86 validated, 0 failed, 0 missing", output)
        self.assertIn("task 2: 79/79 validated, 0 failed, 0 missing", output)
        self.assertIn("task 5: 104/104 validated, 0 failed, 0 missing", output)
        self.assertNotIn("conservative estimate", output)
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

    def test_tasks_1_to_5_refuse_before_client_creation(self) -> None:
        for task in range(1, 6):
            with (
                self.subTest(task=task),
                patch("pipeline.stage4.runner.create_client") as create_client,
            ):
                self.assertEqual(main(["--task", str(task)]), 1)
                create_client.assert_not_called()

    def test_run_all_does_not_import_stage4(self) -> None:
        source = (ROOT / "pipeline" / "run_all.py").read_text(encoding="utf-8").lower()
        self.assertNotIn("from pipeline.stage4", source)
        self.assertNotIn("import pipeline.stage4", source)
        self.assertNotIn("google.genai", source)
        self.assertIn('run("merge_stage4.py")', source)

    def test_no_credentials_in_project_files(self) -> None:
        offenders: list[str] = []
        excluded = {".git", "raw", ".venv", "__pycache__"}
        for path in ROOT.rglob("*"):
            if not path.is_file() or excluded.intersection(path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            name = path.relative_to(ROOT).as_posix()
            lines = credential_lines(text, allow_quoted_pattern=name in QUOTED_PATTERN_FILES)
            offenders += [f"{name}:{number}" for number in lines]
        self.assertEqual(offenders, [])

    def test_credential_scan_exempts_only_lines_quoting_the_pattern(self) -> None:
        # R2 (R1 note 5): the docs that report the scan are exempt line by line, not as files.
        field = '"private' + '_key"'
        quoted = f"0 matches for `{field}` in the whole history."
        real = f'{{"type": "service_account", {field}: "-----BEGIN"}}'
        self.assertEqual(credential_lines(quoted, allow_quoted_pattern=True), [])
        self.assertEqual(credential_lines(quoted, allow_quoted_pattern=False), [1])
        self.assertEqual(credential_lines(f"{quoted}\n{real}", allow_quoted_pattern=True), [2])
        self.assertEqual(credential_lines(f"{quoted} {real}", allow_quoted_pattern=True), [1])
        key = "AIza" + "B" * 35
        self.assertEqual(credential_lines(f"see `{key}`", allow_quoted_pattern=True), [1])
        self.assertEqual(QUOTED_PATTERN_FILES, {"docs/RELEASE_PLAN.md", "docs/HANDOFF_ARCHIVE.md"})


if __name__ == "__main__":
    unittest.main()
