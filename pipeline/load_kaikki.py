"""Parse licensed Kaikki/Vietnamese Wiktionary Hán-Việt evidence (D24)."""

from __future__ import annotations

import gzip
import json
import re
from collections import Counter, defaultdict

import pandas as pd

from common import CJK_RUN_RE, RAW, STAGING, nfc, normalize_vietnamese, write_csv


ETYMOLOGY_RE = re.compile(r"^(?:Âm|Phiên âm) Hán-Việt của (?:chữ Hán )?(.+)$")
COMPONENT_RE = re.compile(r"\bvà\b|hoặc")
PAREN_RE = re.compile(r"\(.*?\)")


def main() -> None:
    explicit: dict[tuple[str, str], tuple[int, str]] = {}
    aligned: dict[str, Counter[str]] = defaultdict(Counter)
    aligned_first_seen: dict[tuple[str, str], int] = {}
    hv_syllables: set[str] = set()
    headwords: set[str] = set()
    evidence_order = 0

    with gzip.open(
        RAW / "kaikki-viwiktionary" / "vi-extract.jsonl.gz", "rt", encoding="utf-8"
    ) as handle:
        for raw_line in handle:
            record = json.loads(raw_line)
            if record.get("lang_code") != "vi" or not record.get("word"):
                continue
            word = normalize_vietnamese(record["word"])
            if not word:
                continue
            headwords.add(word)
            gloss = ""
            for sense in record.get("senses") or []:
                glosses = sense.get("glosses") or []
                if glosses:
                    gloss = nfc(glosses[0])
                    break
            for etymology in record.get("etymology_texts") or []:
                first_line = nfc(etymology).split("\n", 1)[0]
                match = ETYMOLOGY_RE.match(first_line)
                if not match:
                    continue
                body = PAREN_RE.sub("", match.group(1))
                runs = CJK_RUN_RE.findall(body)
                syllables = word.split()
                hv_syllables.update(syllables)
                evidence_order += 1
                if len(runs) == 1 and not COMPONENT_RE.search(body):
                    han = runs[0]
                    explicit.setdefault((han, word), (evidence_order, gloss))
                    if len(han) == len(syllables):
                        for char, syllable in zip(han, syllables):
                            aligned[char][syllable] += 1
                            aligned_first_seen.setdefault((char, syllable), evidence_order)
                elif (
                    len(runs) >= 2
                    and re.search(r"\bvà\b", body)
                    and all(len(run) == 1 for run in runs)
                    and len(runs) == len(syllables)
                ):
                    for char, syllable in zip(runs, syllables):
                        aligned[char][syllable] += 1
                        aligned_first_seen.setdefault((char, syllable), evidence_order)

    explicit_rows = [
        {
            "han": han,
            "vi": vi,
            "syllable_count": len(vi.split()),
            "source_order": source_order,
            "gloss_vi": gloss,
        }
        for (han, vi), (source_order, gloss) in explicit.items()
    ]
    char_rows = []
    for char in sorted(aligned, key=ord):
        for vi, count in sorted(
            aligned[char].items(), key=lambda item: (-item[1], aligned_first_seen[(char, item[0])], item[0])
        ):
            char_rows.append(
                {
                    "char": char,
                    "vi": vi,
                    "count": count,
                    "source_order": aligned_first_seen[(char, vi)],
                }
            )

    explicit_frame = pd.DataFrame(
        sorted(explicit_rows, key=lambda row: (row["source_order"], row["han"], row["vi"])),
        columns=["han", "vi", "syllable_count", "source_order", "gloss_vi"],
    )
    char_frame = pd.DataFrame(char_rows, columns=["char", "vi", "count", "source_order"])
    syllable_frame = pd.DataFrame({"vi": sorted(hv_syllables)})
    headword_frame = pd.DataFrame({"vi": sorted(headwords)})
    write_csv(explicit_frame, STAGING / "kaikki.csv")
    write_csv(char_frame, STAGING / "kaikki_char_readings.csv")
    write_csv(syllable_frame, STAGING / "kaikki_hv_syllables.csv")
    write_csv(headword_frame, STAGING / "kaikki_headwords.csv")
    print(
        f"kaikki: {len(explicit_frame):,} explicit pairs; {char_frame['char'].nunique():,} aligned chars; "
        f"{len(syllable_frame):,} Hán-Việt syllables; {len(headword_frame):,} Vietnamese headwords"
    )


if __name__ == "__main__":
    main()
