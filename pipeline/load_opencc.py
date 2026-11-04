"""Load OpenCC Japanese new/old character and phrase mappings (D28)."""

from __future__ import annotations

import pandas as pd

from common import RAW, STAGING, nfc, write_csv


def load_mapping(filename: str, key_name: str) -> pd.DataFrame:
    rows = []
    with (RAW / "opencc" / filename).open("r", encoding="utf-8") as handle:
        for source_order, raw_line in enumerate(handle, start=1):
            line = nfc(raw_line)
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t", 1)
            if len(parts) != 2:
                raise ValueError(f"Malformed OpenCC row in {filename}: {line!r}")
            japanese, values = parts
            for value_order, traditional in enumerate(values.split(), start=1):
                if traditional == japanese:
                    continue
                rows.append(
                    {
                        key_name: traditional,
                        "jp_candidate": japanese,
                        "source_order": source_order,
                        "value_order": value_order,
                    }
                )
    return pd.DataFrame(rows, columns=[key_name, "jp_candidate", "source_order", "value_order"])


def main() -> None:
    chars = load_mapping("JPShinjitaiCharacters.txt", "trad")
    phrases = load_mapping("JPShinjitaiPhrases.txt", "trad_phrase")
    write_csv(chars, STAGING / "opencc.csv")
    write_csv(phrases, STAGING / "opencc_phrases.csv")
    print(f"opencc: {len(chars):,} character pairs; {len(phrases):,} phrase pairs")


if __name__ == "__main__":
    main()
