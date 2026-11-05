"""Load CC-CEDICT entries without selecting among readings (D41)."""

from __future__ import annotations

import gzip
import re

import pandas as pd

from common import RAW, STAGING, nfc, pinyin_numbered_to_marked, write_csv


ENTRY_RE = re.compile(r"^(\S+) (\S+) \[([^]]+)\] /(.+)/$")


def main() -> None:
    rows: list[dict[str, object]] = []
    path = RAW / "cc-cedict" / "cedict_1_0_ts_utf-8_mdbg.txt.gz"
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for source_order, raw_line in enumerate(handle, start=1):
            line = nfc(raw_line)
            if not line or line.startswith("#"):
                continue
            match = ENTRY_RE.match(line)
            if not match:
                raise ValueError(f"Malformed CC-CEDICT row {source_order}: {line!r}")
            trad, simp, numbered, gloss_text = match.groups()
            numbered_tokens = numbered.split()
            marked_tokens = [pinyin_numbered_to_marked(token) for token in numbered_tokens]
            glosses = [nfc(value) for value in gloss_text.split("/") if nfc(value)]
            rows.append({
                "trad": trad,
                "simp": simp,
                "pinyin": "".join(marked_tokens).lower(),
                "pinyin_spaced": " ".join(marked_tokens).lower(),
                "pinyin_numbered": numbered,
                "cedict_key": f"{trad}|{simp}[{numbered}]",
                "gloss_en": "; ".join(glosses),
                "first_gloss": glosses[0] if glosses else "",
                "capitalized_pinyin": any(token[:1].isupper() for token in numbered_tokens),
                "source_order": source_order,
            })
    frame = pd.DataFrame(rows)
    if frame["cedict_key"].duplicated().any():
        raise ValueError("CC-CEDICT loader produced duplicate exact keys")
    write_csv(frame, STAGING / "cedict.csv", bool_columns=["capitalized_pinyin"])
    print(f"cc-cedict: {len(frame):,} entries")


if __name__ == "__main__":
    main()
