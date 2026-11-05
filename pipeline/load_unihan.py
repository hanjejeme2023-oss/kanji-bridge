"""Load relevant Unihan properties into one normalized character row."""

from __future__ import annotations

import re
import zipfile
from collections import defaultdict

import pandas as pd

from common import RAW, STAGING, nfc, normalize_vietnamese, unique_preserve, write_csv


FIELDS = [
    "kDefinition",
    "kMandarin",
    "kHangul",
    "kVietnamese",
    "kSimplifiedVariant",
    "kTraditionalVariant",
    "kHanyuPinyin",
    "kXHC1983",
    "kCompatibilityVariant",
    "kZVariant",
    "kSemanticVariant",
    "kSpecializedSemanticVariant",
]
# Unihan kHangul source tags include values such as :0E and :0N. They are
# provenance markers, not part of the Hangul reading (global data rule 2).
HANGUL_SUFFIX_RE = re.compile(r":[0-9A-Za-z]+$")


def clean_hangul(value: str) -> str:
    readings = [HANGUL_SUFFIX_RE.sub("", token) for token in re.split(r"[\s,]+", nfc(value))]
    return ";".join(unique_preserve(readings))


def clean_vietnamese(value: str) -> str:
    readings = [normalize_vietnamese(token) for token in re.split(r"[\s,]+", nfc(value))]
    return ";".join(unique_preserve(readings))


def main() -> None:
    values: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    with zipfile.ZipFile(RAW / "unihan" / "Unihan.zip") as archive:
        for member in archive.namelist():
            if not member.endswith(".txt"):
                continue
            with archive.open(member) as handle:
                for raw_line in handle:
                    line = raw_line.decode("utf-8").strip()
                    if not line or line.startswith("#"):
                        continue
                    codepoint, field, value = line.split("\t", 2)
                    if field in FIELDS:
                        char = chr(int(codepoint[2:], 16))
                        values[char][field].append(nfc(value))

    rows: list[dict[str, str]] = []
    for char in sorted(values, key=ord):
        properties = values[char]
        row = {"char": char}
        for field in FIELDS:
            raw_values = unique_preserve(properties.get(field, []))
            joined = " ".join(raw_values)
            if field == "kHangul":
                row[field] = clean_hangul(joined)
            elif field == "kVietnamese":
                row[field] = clean_vietnamese(joined)
            else:
                row[field] = joined
        rows.append(row)
    frame = pd.DataFrame(rows, columns=["char", *FIELDS])
    if frame["char"].duplicated().any():
        raise ValueError("Unihan loader produced duplicate characters")
    write_csv(frame, STAGING / "unihan.csv")
    print(f"unihan: {len(frame):,} characters")


if __name__ == "__main__":
    main()
