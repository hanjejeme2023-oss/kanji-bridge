"""Extract frozen prototype content into reproducible Stage 4 config inputs."""

from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "prototype" / "index.html"
FF_STATIC = ROOT / "config" / "ff_static.csv"
WORD_NOTES = ROOT / "config" / "word_notes.csv"
WORDS = ROOT / "data" / "final" / "words.csv"

LABEL_LANG = {"日": "ja", "韓": "ko", "中": "zh", "越": "vi"}
OBJECT_RE = re.compile(
    r"\{w:'([^']*)',safe:\[(.*?)\],trap:\[(.*?)\],t:'([^']*)'\}", re.DOTALL
)
TRIPLET_RE = re.compile(r"\['([^']*)','([^']*)','([^']*)'\]")


def extract_ff(text: str) -> pd.DataFrame:
    match = re.search(r"const FF=\[(.*?)\];", text, re.DOTALL)
    if not match:
        raise ValueError("prototype FF array was not found")
    records: list[dict[str, object]] = []
    row_number = 0
    objects = OBJECT_RE.findall(match.group(1))
    if len(objects) != 12:
        raise ValueError(f"prototype FF array must have 12 entries, found {len(objects)}")
    for word, safe_text, trap_text, _target in objects:
        for is_trap, values in ((False, safe_text), (True, trap_text)):
            for label, reading_display, meaning_ja in TRIPLET_RE.findall(values):
                row_number += 1
                if label not in LABEL_LANG:
                    raise ValueError(f"unknown prototype FF label: {label!r}")
                records.append({
                    "word": word,
                    "lang": LABEL_LANG[label],
                    "reading_display": reading_display,
                    "meaning_ja": meaning_ja,
                    "is_trap": is_trap,
                    "row": row_number,
                })
    if not records:
        raise ValueError("prototype FF array has no rows")
    return pd.DataFrame(records)


def extract_word_notes(text: str) -> pd.DataFrame:
    note = re.search(r"vietnam:\{[^\n]*note:'([^']*)'", text)
    if not note:
        raise ValueError("prototype 越南 note was not found")
    words = pd.read_csv(WORDS, encoding="utf-8", keep_default_na=False, dtype=str)
    target = words.loc[words["trad"] == "越南", "word_id"]
    if len(target) != 1:
        raise ValueError(f"expected one 越南 word row, found {len(target)}")
    return pd.DataFrame([{"word_id": target.iloc[0], "note_ja": note.group(1)}])


def csv_text(frame: pd.DataFrame, bool_columns: tuple[str, ...] = ()) -> str:
    output = frame.copy()
    for column in bool_columns:
        output[column] = output[column].map({True: "true", False: "false"})
    buffer = io.StringIO(newline="")
    output.to_csv(buffer, index=False, lineterminator="\n")
    return buffer.getvalue()


def write_or_check(path: Path, expected: str, check: bool) -> None:
    if check:
        actual = path.read_text(encoding="utf-8") if path.is_file() else ""
        if actual != expected:
            raise ValueError(f"{path.relative_to(ROOT)} differs from the frozen prototype extraction")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(expected, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify committed config without writing")
    args = parser.parse_args()
    text = PROTOTYPE.read_text(encoding="utf-8")
    ff = extract_ff(text)
    notes = extract_word_notes(text)
    write_or_check(FF_STATIC, csv_text(ff, ("is_trap",)), args.check)
    write_or_check(WORD_NOTES, csv_text(notes), args.check)
    action = "verified" if args.check else "wrote"
    print(f"{action} {FF_STATIC.relative_to(ROOT)} ({len(ff)} rows)")
    print(f"{action} {WORD_NOTES.relative_to(ROOT)} ({len(notes)} rows)")


if __name__ == "__main__":
    main()
