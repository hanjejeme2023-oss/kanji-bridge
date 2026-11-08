"""Export the reduced, offline ``window.KB_DATA`` payload for Stage 5."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "data" / "final"
CONFIG = ROOT / "config"
BUILD_DATE = "2026-11-07"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_bool(value: str, *, field: str) -> bool:
    if value not in {"true", "false"}:
        raise ValueError(f"{field}: expected true/false, got {value!r}")
    return value == "true"


def add_value(
    output: dict[str, Any],
    source: dict[str, str],
    field: str,
    *,
    integer: bool = False,
) -> None:
    value = source.get(field, "")
    if value == "":
        return

    output[field] = int(value) if integer else value


def export_words(raw: list[dict[str, str]]) -> list[dict[str, Any]]:
    output = []
    for row in raw:
        item: dict[str, Any] = {"word_id": row["word_id"], "trad": row["trad"]}
        for field in (
            "simp",
            "jp",
            "ja",
            "ko",
            "pinyin",
            "vi",
            "vi_alt",
            "note_ja",
            "false_friend",
            "ja_use",
            "ko_use",
        ):
            add_value(item, row, field)
        add_value(item, row, "level", integer=True)
        add_value(item, row, "freq_vi", integer=True)
        item["card_eligible"] = parse_bool(row["card_eligible"], field="card_eligible")
        item["syl_aligned"] = parse_bool(row["syl_aligned"], field="syl_aligned")
        output.append(item)
    return output


def export_chars(raw: list[dict[str, str]]) -> list[dict[str, Any]]:
    output = []
    for row in raw:
        if row["jp"] == row["key_char"] == row["simp"]:
            continue
        item: dict[str, Any] = {
            "char_id": row["char_id"],
            "key_char": row["key_char"],
            "simp": row["simp"],
            "jp": row["jp"],
        }
        for field in ("pinyin_all", "ja_on_all", "ko_base_all", "vi_all"):
            add_value(item, row, field)
        add_value(item, row, "level", integer=True)
        output.append(item)
    return output


def export_word_chars(
    raw: list[dict[str, str]], words_raw: list[dict[str, str]]
) -> list[dict[str, Any]]:
    aligned = {
        row["word_id"]
        for row in words_raw
        if parse_bool(row["syl_aligned"], field="syl_aligned")
    }
    output = []
    for row in raw:
        if row["word_id"] not in aligned:
            continue
        item: dict[str, Any] = {
            "word_id": row["word_id"],
            "position": int(row["position"]),
        }
        add_value(item, row, "ko_syllable")
        add_value(item, row, "vi_syllable")
        output.append(item)
    return output


def export_ff_meanings(raw: list[dict[str, str]]) -> list[dict[str, Any]]:
    output = []
    for row in raw:
        item: dict[str, Any] = {
            "word_id": row["word_id"],
            "lang": row["lang"],
            "is_trap": parse_bool(row["is_trap"], field="is_trap"),
        }
        for field in ("reading", "reading_display", "meaning_ja"):
            add_value(item, row, field)
        output.append(item)
    return output


def build_rules(
    words_raw: list[dict[str, str]],
    chars_raw: list[dict[str, str]],
    word_chars_raw: list[dict[str, str]],
) -> list[dict[str, Any]]:
    words = {row["word_id"]: row for row in words_raw}
    chars = {row["char_id"]: row for row in chars_raw}
    config = json.loads((CONFIG / "rules.json").read_text(encoding="utf-8"))
    output = []

    for rule in config["rules"]:
        candidates: dict[str, tuple[tuple[int, int, str], list[str]]] = {}
        for pair in word_chars_raw:
            word = words[pair["word_id"]]
            if word["syl_aligned"] != "true":
                continue
            char = chars.get(pair["char_id"])
            if not char:
                continue
            if pair["ko_base"] != char["ko"] or pair["vi_syllable"] != char["vi"]:
                continue
            if char["ko_final"] != rule["kr"] or char["vi_final"] not in rule["vi"]:
                continue
            if not all((char["key_char"], char["ko"], char["vi"])):
                continue
            rank = (
                int(word["level"]) if word["level"] else 99,
                int(word["freq_vi"]) if word["freq_vi"] else 10**9,
                char["char_id"],
            )
            example = [
                char["key_char"],
                char["ko"],
                char["ja_on"],
                char["vi"],
                char["pinyin"],
            ]
            current = candidates.get(char["char_id"])
            if current is None or rank < current[0]:
                candidates[char["char_id"]] = (rank, example)

        examples = [value[1] for value in sorted(candidates.values(), key=lambda value: value[0])[:8]]
        if len(examples) < 4:
            raise ValueError(f"rule {rule['id']} has only {len(examples)} eligible examples")
        if len({example[0] for example in examples}) != len(examples):
            raise ValueError(f"rule {rule['id']} has duplicate progress keys")
        output.append({**rule, "ex": examples})

    return output


def build_payload() -> dict[str, Any]:
    words_raw = read_csv(FINAL / "words.csv")
    chars_raw = read_csv(FINAL / "chars.csv")
    word_chars_raw = read_csv(FINAL / "word_chars.csv")
    ff_raw = read_csv(FINAL / "ff_meanings.csv")
    passages = json.loads((FINAL / "passages.json").read_text(encoding="utf-8"))

    word_ids = {row["word_id"] for row in words_raw}
    unresolved = sorted(
        {
            token["word_id"]
            for passage in passages
            for token in passage["tokens"]
            if "word_id" in token and token["word_id"] not in word_ids
        }
    )
    if unresolved:
        raise ValueError(f"passage tokens have unknown word IDs: {unresolved[:5]}")

    chars = export_chars(chars_raw)
    words = export_words(words_raw)
    word_chars = export_word_chars(word_chars_raw, words_raw)
    ff_meanings = export_ff_meanings(ff_raw)
    rules = build_rules(words_raw, chars_raw, word_chars_raw)
    return {
        "meta": {
            "built": BUILD_DATE,
            "counts": {
                "chars": len(chars_raw),
                "glyphs": len(chars),
                "words": len(words),
                "word_chars": len(word_chars),
                "ff_meanings": len(ff_meanings),
                "passages": len(passages),
            },
        },
        "chars": chars,
        "words": words,
        "word_chars": word_chars,
        "ff_meanings": ff_meanings,
        "passages": passages,
        "rules": rules,
    }


def export_data_js(path: Path = FINAL / "data.js") -> dict[str, Any]:
    payload = build_payload()
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.KB_DATA = {encoded};\n", encoding="utf-8", newline="\n")
    return payload


def main() -> None:
    payload = export_data_js()
    counts = payload["meta"]["counts"]
    print(
        "Exported data.js: "
        f"{(FINAL / 'data.js').stat().st_size:,} bytes; "
        f"{counts['words']:,} words; {counts['glyphs']:,} glyphs; "
        f"{counts['ff_meanings']:,} false-friend meaning rows"
    )


if __name__ == "__main__":
    main()
