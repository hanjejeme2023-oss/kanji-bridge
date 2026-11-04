from __future__ import annotations

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


class RebuildDeterminismTests(unittest.TestCase):
    def test_two_rebuilds_are_identical(self) -> None:
        command = [sys.executable, "-X", "utf8", str(ROOT / "pipeline" / "run_all.py"), "--skip-download"]
        subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        first = digest_outputs()
        subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        second = digest_outputs()
        self.assertEqual(first, second)
        self.assertIn("data/final/chars.csv", second)
        self.assertIn("pipeline/id_map.csv", second)


if __name__ == "__main__":
    unittest.main()
