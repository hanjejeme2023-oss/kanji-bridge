"""Load KANJIDIC2 Japanese on-readings and tie-break metadata."""

from __future__ import annotations

import gzip
from xml.etree import ElementTree as ET

import pandas as pd

from common import RAW, STAGING, katakana_to_hiragana, nfc, unique_preserve, write_csv


def main() -> None:
    rows: list[dict[str, object]] = []
    with gzip.open(RAW / "kanjidic2" / "kanjidic2.xml.gz", "rb") as handle:
        for _event, element in ET.iterparse(handle, events=("end",)):
            if element.tag != "character":
                continue
            literal = nfc(element.findtext("literal", ""))
            readings = unique_preserve(
                katakana_to_hiragana(node.text or "")
                for node in element.findall("./reading_meaning/rmgroup/reading")
                if node.attrib.get("r_type") == "ja_on"
            )
            meanings = unique_preserve(
                node.text or ""
                for node in element.findall("./reading_meaning/rmgroup/meaning")
                if "m_lang" not in node.attrib
            )
            grade_text = nfc(element.findtext("./misc/grade", ""))
            freq_text = nfc(element.findtext("./misc/freq", ""))
            rows.append(
                {
                    "literal": literal,
                    "ja_on_all": ";".join(readings),
                    "grade": int(grade_text) if grade_text.isdigit() else pd.NA,
                    "freq": int(freq_text) if freq_text.isdigit() else pd.NA,
                    "meanings_en": ";".join(meanings),
                }
            )
            element.clear()
    raw_frame = pd.DataFrame(rows, columns=["literal", "ja_on_all", "grade", "freq", "meanings_en"])
    # NFC folds CJK compatibility ideographs onto their unified forms. Aggregate
    # those source rows deterministically instead of discarding readings.
    aggregated = []
    for literal, group in raw_frame.groupby("literal", sort=False):
        readings = unique_preserve(
            reading for value in group["ja_on_all"] for reading in nfc(value).split(";")
        )
        meanings = unique_preserve(
            meaning for value in group["meanings_en"] for meaning in nfc(value).split(";")
        )
        grades = [int(value) for value in group["grade"].dropna()]
        freqs = [int(value) for value in group["freq"].dropna()]
        aggregated.append(
            {
                "literal": literal,
                "ja_on_all": ";".join(readings),
                "grade": min(grades) if grades else pd.NA,
                "freq": min(freqs) if freqs else pd.NA,
                "meanings_en": ";".join(meanings),
                "source_rows": len(group),
            }
        )
    frame = pd.DataFrame(
        aggregated, columns=["literal", "ja_on_all", "grade", "freq", "meanings_en", "source_rows"]
    )
    if frame["literal"].duplicated().any():
        raise ValueError("KANJIDIC2 NFC aggregation left duplicate literals")
    write_csv(frame, STAGING / "kanjidic2.csv")
    print(f"kanjidic2: {len(frame):,} characters")


if __name__ == "__main__":
    main()
