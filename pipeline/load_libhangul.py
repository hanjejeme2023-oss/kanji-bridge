"""Load libhangul single-Han-character readings for Stage 2 (D32)."""

from __future__ import annotations

import pandas as pd

from common import HANGUL_RE, RAW, STAGING, is_cjk_char, nfc, write_csv


def main() -> None:
    rows = []
    with (RAW / "libhangul" / "hanja.txt").open("r", encoding="utf-8") as handle:
        for source_order, raw_line in enumerate(handle, start=1):
            line = nfc(raw_line)
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            if len(parts) < 3:
                raise ValueError(f"Malformed libhangul row {source_order}: {line!r}")
            reading, hanja = nfc(parts[0]), nfc(parts[1])
            if is_cjk_char(hanja) and len(reading) == 1 and HANGUL_RE.fullmatch(reading):
                rows.append({"char": hanja, "ko": reading, "source_order": source_order})
    frame = pd.DataFrame(rows, columns=["char", "ko", "source_order"])
    frame = frame.drop_duplicates(["char", "ko"], keep="first").reset_index(drop=True)
    write_csv(frame, STAGING / "libhangul.csv")
    print(f"libhangul: {len(frame):,} distinct single-character readings")


if __name__ == "__main__":
    main()
