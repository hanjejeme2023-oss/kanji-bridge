from __future__ import annotations

import re
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pipeline.stage4 import builders
from pipeline.stage4.runner import (
    MODEL_ID,
    REQUEST_TIMEOUT_MS,
    Stage4Error,
    calculate_cost,
    enforce_argon_deadline,
    generation_config,
    guard_api_keys,
    response_text_or_error,
    run_task,
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

    def test_argon_deadline_guard_uses_utc_date(self) -> None:
        before = datetime(2026, 11, 30, 23, 59, tzinfo=timezone.utc)
        boundary = datetime(2026, 12, 1, 0, 0, tzinfo=timezone.utc)
        enforce_argon_deadline(now=before)
        with self.assertRaisesRegex(Stage4Error, "UTC date 2026-12-01"):
            enforce_argon_deadline(now=boundary)
        enforce_argon_deadline(allow_after_deadline=True, now=boundary)

    def test_task_resume_skips_validated_batch_and_runs_failed_batch(self) -> None:
        item = {
            "word_id": "w1", "trad": "文字", "ja": "もじ", "ko": "문자",
            "pinyin": "wénzì", "vi": "văn tự",
        }
        output = [{
            "word_id": "w1", "meaning_ja__ja": "文字", "meaning_ja__ko": "文字",
            "meaning_ja__zh": "文字", "meaning_ja__vi": "文字",
            "meanings_differ": False, "vi_check": "same_word",
            "vi_check_reason": "", "confidence": "high", "low_reason": "",
        }]
        prompt = "test prompt"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inputs = root / "inputs"
            generated = root / "generated"
            output_path = generated / "task1" / "b001.jsonl"
            log_path = generated / "task1" / "b001.log.json"
            builders.write_jsonl(output_path, output)
            log = {
                "task": 1, "batch": "b001", "model": MODEL_ID,
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
                patch("pipeline.stage4.runner.generate_batch", generate),
            ):
                self.assertEqual(run_task(Mock(), 1, None, False), 0)
                generate.assert_not_called()
                log["validation"]["ok"] = False
                log_path.write_text(json.dumps(log), encoding="utf-8")
                self.assertEqual(run_task(Mock(), 1, None, False), 0)
                generate.assert_called_once()

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
