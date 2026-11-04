"""Rebuild Kanji Bridge data in dependency order.

Stage 2 currently builds the complete character table. Later stages append word,
content, and app-export steps to SCRIPTS without changing the entry point.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "pipeline"
DATA = ROOT / "data"
REBUILD_DIRS = [DATA / "staging", DATA / "final"]
LOADERS = [
    "load_unihan.py",
    "load_kanjidic2.py",
    "load_hsk30.py",
    "load_opencc.py",
    "load_libhangul.py",
    "load_kaikki.py",
    "load_frequencywords.py",
]


def clean_rebuild_dirs() -> None:
    data_root = DATA.resolve()
    for directory in REBUILD_DIRS:
        target = directory.resolve()
        if target.parent != data_root or target.name not in {"staging", "final"}:
            raise RuntimeError(f"Refusing to clear unexpected path: {target}")
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
        (target / ".gitkeep").touch()


def run(script: str) -> None:
    command = [sys.executable, "-X", "utf8", str(PIPELINE / script)]
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="skip raw-file verification (used only by rebuild determinism tests)",
    )
    args = parser.parse_args()
    if not args.skip_download:
        run("download.py")
    clean_rebuild_dirs()
    for loader in LOADERS:
        run(loader)
    run("build_chars.py")
    print("Stage 2 rebuild complete")


if __name__ == "__main__":
    main()
