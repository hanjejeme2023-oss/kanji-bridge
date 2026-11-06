"""Build the Stage 2 HSK 3.0 character table and review reports."""

from __future__ import annotations

import json
import re

import pandas as pd

from common import (
    FINAL,
    STAGING,
    assign_ids,
    hangul_final,
    merge_with_report,
    nfc,
    pinyin_numbered_to_marked,
    require_nfc,
    split_multi,
    unique_preserve,
    vietnamese_final,
    write_csv,
    write_json,
)


CHAR_COLUMNS = [
    "char_id", "trad", "key_char", "simp", "jp", "ja_on", "ko", "pinyin", "vi",
    "ja_on_all", "ko_all", "pinyin_all", "vi_all", "ko_final", "vi_final",
    "in_hsk_chars", "level", "gloss_en", "source_ko", "source_vi", "source_ja",
    "source_pinyin",
]
PINYIN_REF_RE = re.compile(r"(?:^|\s)[^\s:]+:([^\s]+)")


def read_stage(filename: str) -> pd.DataFrame:
    return pd.read_csv(STAGING / filename, encoding="utf-8", keep_default_na=False, dtype=str)


def aggregate(frame: pd.DataFrame, key: str, value: str, output: str) -> pd.DataFrame:
    rows = []
    for group_key, group in frame.groupby(key, sort=False):
        rows.append({key: group_key, output: ";".join(unique_preserve(group[value]))})
    return pd.DataFrame(rows, columns=[key, output])


def merge_left(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    name: str,
    left_on: str,
    right_on: str,
    validate: str,
    reports: list[dict[str, object]],
) -> pd.DataFrame:
    indicator = f"_merge_{name}"
    merged = merge_with_report(
        left,
        right,
        name=name,
        reports=reports,
        how="left",
        left_on=left_on,
        right_on=right_on,
        validate=validate,
        suffixes=("", f"_{name}"),
    )
    return merged.drop(columns=[indicator, right_on] if right_on != left_on else [indicator])


def pinyin_values(value: object, referenced: bool = False) -> list[str]:
    text = nfc(value)
    if not text:
        return []
    chunks = PINYIN_REF_RE.findall(text) if referenced else re.split(r"[\s,]+", text)
    readings: list[str] = []
    for chunk in chunks:
        for token in chunk.split(","):
            token = token.strip()
            if token:
                readings.append(pinyin_numbered_to_marked(token).lower())
    return unique_preserve(readings)


def choose_jp(trad: str, candidates_text: str, kd: dict[str, dict[str, object]]) -> str:
    candidates = split_multi(candidates_text) if candidates_text else [trad]
    valid = [candidate for candidate in candidates if candidate in kd]
    if not valid:
        return ""
    return min(
        valid,
        key=lambda candidate: (
            kd[candidate]["grade"] if kd[candidate]["grade"] is not None else 99,
            kd[candidate]["freq"] if kd[candidate]["freq"] is not None else 99999,
            ord(candidate),
        ),
    )


def build() -> tuple[pd.DataFrame, dict[str, int]]:
    merge_reports: list[dict[str, object]] = []
    chars = read_stage("hsk30.csv")
    chars["level"] = pd.to_numeric(chars["level"], errors="raise").astype(int)
    shared_trad = chars["trad"].duplicated(keep=False)
    chars["key_char"] = chars["trad"]
    chars.loc[shared_trad, "key_char"] = chars.loc[shared_trad, "simp_hsk"]
    if chars["key_char"].duplicated().any() or (chars["key_char"] == "").any():
        duplicates = chars.loc[chars["key_char"].duplicated(False), "key_char"].tolist()
        raise ValueError(f"Derived key_char is not unique/non-empty: duplicates={duplicates}")

    unihan = read_stage("unihan.csv")
    chars = merge_left(
        chars, unihan, name="unihan", left_on="key_char", right_on="char",
        validate="one_to_one", reports=merge_reports,
    )

    opencc = read_stage("opencc.csv")
    opencc_agg = aggregate(opencc, "trad", "jp_candidate", "jp_candidates").rename(
        columns={"trad": "opencc_trad"}
    )
    chars = merge_left(
        chars, opencc_agg, name="opencc", left_on="key_char", right_on="opencc_trad",
        validate="one_to_one", reports=merge_reports,
    )

    libhangul = read_stage("libhangul.csv")
    libhangul_agg = aggregate(libhangul, "char", "ko", "ko_libhangul")
    chars = merge_left(
        chars, libhangul_agg, name="libhangul", left_on="key_char", right_on="char",
        validate="one_to_one", reports=merge_reports,
    )

    kaikki = read_stage("kaikki_char_readings.csv")
    kaikki_agg = aggregate(kaikki, "char", "vi", "vi_kaikki")
    chars = merge_left(
        chars, kaikki_agg, name="kaikki", left_on="key_char", right_on="char",
        validate="one_to_one", reports=merge_reports,
    )

    kd_frame = read_stage("kanjidic2.csv")
    kd: dict[str, dict[str, object]] = {}
    for row in kd_frame.itertuples(index=False):
        kd[row.literal] = {
            "ja_on_all": nfc(row.ja_on_all),
            "grade": int(row.grade) if nfc(row.grade).isdigit() else None,
            "freq": int(row.freq) if nfc(row.freq).isdigit() else None,
        }
    chars["jp"] = [
        choose_jp(nfc(row.key_char), nfc(row.jp_candidates), kd)
        for row in chars.itertuples(index=False)
    ]
    chars = merge_left(
        chars,
        kd_frame[["literal", "ja_on_all"]].rename(columns={"ja_on_all": "ja_on_all_kd"}),
        name="kanjidic",
        left_on="jp",
        right_on="literal",
        validate="many_to_one",
        reports=merge_reports,
    )

    hv_syllables = set(read_stage("kaikki_hv_syllables.csv")["vi"].map(nfc))
    output_rows: list[dict[str, object]] = []
    for row in chars.itertuples(index=False):
        trad = nfc(row.trad)
        key_char = nfc(row.key_char)
        simp_hsk = nfc(row.simp_hsk)

        ja_readings = split_multi(row.ja_on_all_kd)
        unihan_ko = split_multi(row.kHangul)
        lib_ko = split_multi(row.ko_libhangul)
        ko_all = unique_preserve([*unihan_ko, *lib_ko])
        if unihan_ko:
            ko, source_ko = unihan_ko[0], "unihan"
        elif len(lib_ko) == 1:
            ko, source_ko = lib_ko[0], "libhangul"
        else:
            ko, source_ko = "", ""

        mandarin = pinyin_values(row.kMandarin)
        pinyin_all = unique_preserve(
            [
                *mandarin,
                *pinyin_values(row.kHanyuPinyin, referenced=True),
                *pinyin_values(row.kXHC1983, referenced=True),
            ]
        )
        pinyin = mandarin[0] if mandarin else ""

        kaikki_vi = split_multi(row.vi_kaikki)
        unihan_vi = split_multi(row.kVietnamese)
        hvsyl_vi = [reading for reading in unihan_vi if reading in hv_syllables]
        verified_vi = unique_preserve([*kaikki_vi, *hvsyl_vi])
        if kaikki_vi:
            vi, source_vi, vi_all = kaikki_vi[0], "kaikki_aligned", verified_vi
        elif hvsyl_vi:
            vi, source_vi, vi_all = hvsyl_vi[0], "unihan_hvsyl", verified_vi
        elif unihan_vi:
            vi, source_vi, vi_all = unihan_vi[0], "unihan_unverified", unihan_vi
        else:
            vi, source_vi, vi_all = "", "", []

        output_rows.append(
            {
                "trad": trad,
                "key_char": key_char,
                "simp": simp_hsk,
                "jp": nfc(row.jp),
                "ja_on": ja_readings[0] if ja_readings else "",
                "ko": ko,
                "pinyin": pinyin,
                "vi": vi,
                "ja_on_all": ";".join(ja_readings),
                "ko_all": ";".join(ko_all),
                "pinyin_all": ";".join(pinyin_all),
                "vi_all": ";".join(vi_all),
                "ko_final": hangul_final(ko),
                "vi_final": vietnamese_final(vi),
                "in_hsk_chars": True,
                "level": int(row.level),
                "gloss_en": nfc(row.kDefinition),
                "source_ko": source_ko,
                "source_vi": source_vi,
                "source_ja": "kanjidic2" if ja_readings else "",
                "source_pinyin": "unihan" if pinyin else "",
                "source_order": int(row.source_order),
            }
        )

    output = pd.DataFrame(output_rows)
    id_mapping = assign_ids("char", output["key_char"], "c", 5)
    output.insert(0, "char_id", output["key_char"].map(id_mapping))
    output = output.sort_values("source_order", kind="stable").reset_index(drop=True)
    output = output[CHAR_COLUMNS]
    for column in output.select_dtypes(include=["object", "string"]).columns:
        output[column] = output[column].replace("", pd.NA)
    require_nfc(output)
    if (
        len(output) != 3000
        or output["key_char"].duplicated().any()
        or output["char_id"].duplicated().any()
        or output["trad"].isna().any()
    ):
        raise ValueError("Final chars must contain 3,000 rows with unique key_char/char_id and non-empty trad")

    merge_frame = pd.DataFrame(merge_reports, columns=["merge", "status", "count", "validate"])
    write_csv(merge_frame, FINAL / "merge_report.csv")
    summary = {
        "rows": len(output),
        "jp_missing": int(output["jp"].isna().sum()),
        "vi_verified": int(output["source_vi"].isin(["kaikki_aligned", "unihan_hvsyl"]).sum()),
        "vi_unverified": int((output["source_vi"] == "unihan_unverified").sum()),
        "vi_missing": int(output["vi"].isna().sum()),
    }
    return output, summary


def write_reports(chars: pd.DataFrame, summary: dict[str, int]) -> None:
    no_jp = chars.loc[
        chars["jp"].isna(), ["char_id", "trad", "key_char", "simp", "level"]
    ].copy()
    no_jp["reason"] = "no OpenCC/KANJIDIC2-valid Japanese form (D28)"
    write_csv(no_jp, FINAL / "no_jp_form.csv")

    collisions = chars.loc[
        chars["trad"].duplicated(keep=False), ["trad", "key_char", "level"]
    ].copy()
    collisions = collisions.rename(columns={"level": "source_level"}).sort_values(
        ["trad", "key_char"], kind="stable"
    )
    write_csv(collisions, FINAL / "char_key_collisions.csv")

    coverage_rows = []
    for column in ["jp", "ja_on", "ko", "pinyin", "vi"]:
        present = int(chars[column].notna().sum())
        coverage_rows.append(
            {
                "scope": "chars",
                "field": column,
                "value": "present",
                "count": present,
                "total": len(chars),
                "percent": round(present * 100 / len(chars), 2),
                "note": "",
            }
        )
        coverage_rows.append(
            {
                "scope": "chars",
                "field": column,
                "value": "missing",
                "count": len(chars) - present,
                "total": len(chars),
                "percent": round((len(chars) - present) * 100 / len(chars), 2),
                "note": "",
            }
        )
    for source, count in chars["source_vi"].fillna("missing").value_counts(dropna=False).items():
        coverage_rows.append(
            {
                "scope": "chars",
                "field": "source_vi",
                "value": source,
                "count": int(count),
                "total": len(chars),
                "percent": round(int(count) * 100 / len(chars), 2),
                "note": "unihan_unverified is excluded from composition and sound rules",
            }
        )
    write_csv(pd.DataFrame(coverage_rows), FINAL / "coverage_report.csv")

    eligible = chars.loc[
        chars["ko_all"].map(lambda value: len(split_multi(value)) == 1)
        & chars["vi_all"].map(lambda value: len(split_multi(value)) == 1)
        & chars["source_vi"].isin(["kaikki_aligned", "unihan_hvsyl"])
    ].copy()
    eligible["vi_final_label"] = eligible["vi_final"].fillna("").replace("", "(open)")
    pivot = eligible.pivot_table(
        index="ko_final",
        columns="vi_final_label",
        values="char_id",
        aggfunc="count",
        fill_value=0,
        dropna=False,
    )
    preferred = ["(open)", "c", "ch", "p", "t", "n", "m", "ng", "nh"]
    remaining = sorted(column for column in pivot.columns if column not in preferred)
    pivot = pivot.reindex(columns=[column for column in preferred if column in pivot.columns] + remaining)
    pivot = pivot.reset_index()
    write_csv(pivot, FINAL / "rules_report.csv")
    examples = eligible[
        ["char_id", "trad", "ko", "vi", "ko_final", "vi_final", "ja_on", "pinyin", "level", "source_vi"]
    ].sort_values(["ko_final", "vi_final", "level", "char_id"], kind="stable")
    write_csv(examples, FINAL / "rules_examples.csv")

    (FINAL / "build_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    chars, summary = build()
    write_csv(chars, FINAL / "chars.csv", bool_columns=["in_hsk_chars"])
    write_json(chars, FINAL / "chars.json")
    write_reports(chars, summary)
    print(
        "chars: {rows:,}; jp missing={jp_missing:,}; verified vi={vi_verified:,}; "
        "unverified vi={vi_unverified:,}; vi missing={vi_missing:,}".format(**summary)
    )


if __name__ == "__main__":
    main()
