"""Check a source refresh (EDRDG update, RELEASE_PLAN §2.5 / §6.3) after the rebuild.

Run after ``python pipeline/download.py --refresh --only kanjidic2,jmdict`` and
``python pipeline/run_all.py``. Compares the rebuilt tables with a baseline,
by default the committed version (``git show HEAD:<path>``):

* **Fails** (exit 1) when any ``word_id`` is added, removed or re-keyed: the
  word list is frozen (D46, D55, D57), so ``pipeline/id_map.csv`` must not
  change and every ``word_id`` keeps its ``trad``, ``simp`` and ``pinyin``.
* **Reports** every word whose Japanese form or reading changed (``jp``,
  ``ja``, ``ja_alt``, ``ja_common``, ``source_ja``) and every character whose
  Japanese form or on-readings changed (``jp``, ``ja_on``, ``ja_on_all``),
  in ``--out`` (default ``data/refresh_report.csv``), for Claude's check.

Usage (repository root):
    python -X utf8 pipeline/refresh_check.py [--baseline-ref HEAD] [--out data/refresh_report.csv]
"""

from __future__ import annotations

import argparse
import io
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORD_KEY_COLUMNS = ["trad", "simp", "pinyin"]
WORD_JA_COLUMNS = ["jp", "ja", "ja_alt", "ja_common", "source_ja"]
CHAR_JA_COLUMNS = ["jp", "ja_on", "ja_on_all"]
REPORT_COLUMNS = ["table", "id", "trad", "column", "before", "after"]


def read_text_csv(text: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)


def git_show(ref: str, path: str) -> pd.DataFrame:
    text = subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=ROOT, check=True, capture_output=True,
        text=True, encoding="utf-8",
    ).stdout
    return read_text_csv(text)


def compare(
    before_words: pd.DataFrame, after_words: pd.DataFrame,
    before_ids: pd.DataFrame, after_ids: pd.DataFrame,
    before_chars: pd.DataFrame, after_chars: pd.DataFrame,
) -> tuple[list[str], pd.DataFrame]:
    """Return (errors, report). ``errors`` is empty when no ID or word key changed."""
    errors: list[str] = []
    if not before_ids.sort_values(list(before_ids.columns)).reset_index(drop=True).equals(
        after_ids.sort_values(list(after_ids.columns)).reset_index(drop=True)
    ):
        errors.append("pipeline/id_map.csv changed (a new or removed ID)")
    before = before_words.set_index("word_id")
    after = after_words.set_index("word_id")
    added, removed = sorted(set(after.index) - set(before.index)), sorted(set(before.index) - set(after.index))
    if added:
        errors.append(f"{len(added)} word_id added: {added[:10]}")
    if removed:
        errors.append(f"{len(removed)} word_id removed: {removed[:10]}")
    rows: list[dict[str, str]] = []
    for word_id in sorted(set(before.index) & set(after.index)):
        for column in WORD_KEY_COLUMNS:
            if before.at[word_id, column] != after.at[word_id, column]:
                errors.append(
                    f"{word_id} {column} changed: {before.at[word_id, column]!r} -> {after.at[word_id, column]!r}"
                )
        for column in WORD_JA_COLUMNS:
            if column in before and before.at[word_id, column] != after.at[word_id, column]:
                rows.append({"table": "words", "id": word_id, "trad": after.at[word_id, "trad"], "column": column,
                             "before": before.at[word_id, column], "after": after.at[word_id, column]})
    chars_before = before_chars.set_index("char_id")
    chars_after = after_chars.set_index("char_id")
    if set(chars_before.index) != set(chars_after.index):
        errors.append("the set of char_id changed")
    for char_id in sorted(set(chars_before.index) & set(chars_after.index)):
        for column in CHAR_JA_COLUMNS:
            if chars_before.at[char_id, column] != chars_after.at[char_id, column]:
                rows.append({"table": "chars", "id": char_id, "trad": chars_after.at[char_id, "trad"],
                             "column": column, "before": chars_before.at[char_id, column],
                             "after": chars_after.at[char_id, column]})
    return errors, pd.DataFrame(rows, columns=REPORT_COLUMNS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--baseline-ref", default="HEAD", help="git ref with the tables before the refresh")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "refresh_report.csv")
    args = parser.parse_args()
    paths = {"words": "data/final/words.csv", "ids": "pipeline/id_map.csv", "chars": "data/final/chars.csv"}
    before = {key: git_show(args.baseline_ref, path) for key, path in paths.items()}
    after = {key: pd.read_csv(ROOT / path, dtype=str, keep_default_na=False) for key, path in paths.items()}
    errors, report = compare(before["words"], after["words"], before["ids"], after["ids"],
                             before["chars"], after["chars"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(args.out, index=False, encoding="utf-8", lineterminator="\n")
    print(f"Japanese changes: {len(report)} rows "
          f"({(report['table'] == 'words').sum()} word, {(report['table'] == 'chars').sum()} char) -> {args.out}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
