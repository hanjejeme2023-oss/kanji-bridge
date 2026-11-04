"""Load the HSK 3.0 character list and expand cleaned word variants (D30)."""

from __future__ import annotations

import json

import pandas as pd

from common import RAW, STAGING, nfc, normalize_text_columns, write_csv


def level(value: object) -> int:
    text = nfc(value)
    return 7 if text == "7-9" else int(text)


def load_chars() -> pd.DataFrame:
    source = pd.read_csv(
        RAW / "hsk30" / "hsk30-chars.csv", encoding="utf-8", keep_default_na=False, dtype=str
    )
    source = normalize_text_columns(source)
    rows = []
    for source_order, row in enumerate(source.itertuples(index=False), start=1):
        simp = nfc(row.Hanzi)
        trad_variants = [nfc(value) for value in nfc(row.Traditional).split("/") if nfc(value)]
        trad = trad_variants[0] if trad_variants else simp
        rows.append(
            {
                "source_order": source_order,
                "simp_hsk": simp,
                "trad": trad,
                "trad_variants": ";".join(trad_variants),
                "level": level(row.Level),
                "writing_level": nfc(row.WritingLevel),
                "hsk_freq": int(row.Freq) if nfc(row.Freq).isdigit() else pd.NA,
                "examples": nfc(row.Examples),
            }
        )
    frame = pd.DataFrame(rows)
    if len(frame) != 3000 or (frame["trad"] == "").any():
        raise ValueError(
            f"HSK character row failure: rows={len(frame)}, empty trad={int((frame['trad'] == '').sum())}"
        )
    # `trad` is deliberately not a key: hsk30 maps both 着 and 著 to 著.
    # build_chars derives the unique lookup key (`key_char`) generically from
    # every duplicated traditional-form group (D37).
    if frame["simp_hsk"].duplicated().any():
        duplicates = frame.loc[frame["simp_hsk"].duplicated(False), "simp_hsk"].tolist()
        raise ValueError(f"HSK source-character key failure: duplicate Hanzi={duplicates}")
    return frame


def aligned_fallback(row: pd.Series) -> tuple[list[dict[str, str]], bool]:
    fields = {
        "Simplified": nfc(row["Simplified"]).split("|"),
        "Traditional": nfc(row["Traditional"]).split("|"),
        "Pinyin": nfc(row["Pinyin"]).split("|"),
    }
    counts = {len(values) for values in fields.values()}
    mismatch = len(counts) != 1
    size = 1 if mismatch else len(fields["Simplified"])
    cedict = nfc(row["CEDICT"]).split("/")
    variants = []
    for index in range(size):
        variants.append(
            {
                "Simplified": fields["Simplified"][index],
                "Traditional": fields["Traditional"][index],
                "Pinyin": fields["Pinyin"][index],
                "POS": nfc(row["POS"]),
                "CEDICT": cedict[index] if index < len(cedict) else (cedict[0] if cedict else ""),
            }
        )
    return variants, mismatch


def load_words() -> tuple[pd.DataFrame, pd.DataFrame]:
    source = pd.read_csv(RAW / "hsk30" / "hsk30.csv", encoding="utf-8", keep_default_na=False, dtype=str)
    source = normalize_text_columns(source)
    rows: list[dict[str, object]] = []
    mismatches: list[dict[str, str]] = []
    for row in source.to_dict(orient="records"):
        variants_text = nfc(row["Variants"])
        if variants_text:
            variants = json.loads(variants_text)
        else:
            variants, mismatch = aligned_fallback(pd.Series(row))
            if mismatch:
                mismatches.append(
                    {
                        "hsk_id": nfc(row["ID"]),
                        "simplified": nfc(row["Simplified"]),
                        "traditional": nfc(row["Traditional"]),
                        "pinyin": nfc(row["Pinyin"]),
                        "reason": "pipe-separated field counts differ; first variant kept per D30",
                    }
                )
        kept_index = 0
        for variant_index, variant in enumerate(variants, start=1):
            if nfc(variant.get("Example", "")):
                continue
            kept_index += 1
            rows.append(
                {
                    "hsk_id": nfc(row["ID"]),
                    "variant_index": kept_index,
                    "simp": nfc(variant.get("Simplified", row["Simplified"])),
                    "trad": nfc(variant.get("Traditional", row["Traditional"])),
                    "pinyin": nfc(variant.get("Pinyin", row["Pinyin"])).lower().replace("-", ""),
                    "pos": nfc(variant.get("POS", row["POS"])),
                    "level": level(row["Level"]),
                    "cedict_key": nfc(variant.get("CEDICT", row["CEDICT"])),
                    "web_no": nfc(row["WebNo"]),
                    "source_order": len(rows) + 1,
                }
            )
        if kept_index == 0:
            raise ValueError(f"HSK row {row['ID']} had no non-example variant")
    return pd.DataFrame(rows), pd.DataFrame(
        mismatches, columns=["hsk_id", "simplified", "traditional", "pinyin", "reason"]
    )


def main() -> None:
    chars = load_chars()
    words, mismatches = load_words()
    write_csv(chars, STAGING / "hsk30.csv")
    write_csv(words, STAGING / "hsk30_words.csv")
    write_csv(mismatches, STAGING / "hsk30_variant_mismatches.csv")
    print(f"hsk30: {len(chars):,} chars; {len(words):,} expanded words; {len(mismatches):,} mismatches")


if __name__ == "__main__":
    main()
