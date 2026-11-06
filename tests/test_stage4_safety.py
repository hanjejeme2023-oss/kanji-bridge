from __future__ import annotations

import re
import unittest
from pathlib import Path
from types import SimpleNamespace

from pipeline.stage4.runner import Stage4Error, guard_api_keys, response_text_or_error


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
