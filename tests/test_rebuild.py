from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest_outputs() -> dict[str, str]:
    paths = sorted((ROOT / "data" / "final").glob("*")) + [ROOT / "pipeline" / "id_map.csv"]
    result = {}
    for path in paths:
        if path.is_file():
            result[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def vi_only_word_ids() -> set[str]:
    with (ROOT / "data" / "final" / "words.csv").open(encoding="utf-8", newline="") as source:
        return {
            row["word_id"] for row in csv.DictReader(source)
            if row["source_level"] == "vi_band"
        }


class RebuildDeterminismTests(unittest.TestCase):
    def test_two_rebuilds_are_identical(self) -> None:
        command = [sys.executable, "-X", "utf8", str(ROOT / "pipeline" / "run_all.py"), "--skip-download"]
        subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        first = digest_outputs()
        selected_with_overrides = vi_only_word_ids()

        overrides = ROOT / "pipeline" / "overrides.csv"
        backup = ROOT / "pipeline" / "overrides.csv.rebuild-test"
        self.assertFalse(backup.exists())
        overrides.replace(backup)
        try:
            subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
            selected_without_overrides = vi_only_word_ids()
        finally:
            backup.replace(overrides)
        self.assertEqual(selected_with_overrides, selected_without_overrides)

        subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        second = digest_outputs()
        self.assertEqual(first, second)
        self.assertIn("data/final/chars.csv", second)
        self.assertIn("data/final/words.csv", second)
        self.assertIn("data/final/word_chars.csv", second)
        self.assertIn("pipeline/id_map.csv", second)


if __name__ == "__main__":
    unittest.main()
