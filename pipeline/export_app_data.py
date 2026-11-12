"""Export the reduced, offline ``window.KB_DATA`` payload for Stage 5."""

from __future__ import annotations

import csv
import json
import re
import shutil
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.stage4.validators import _piece_segmentations


FINAL = ROOT / "data" / "final"
CONFIG = ROOT / "config"
BUILD_DATE = "2026-11-12"
APP = ROOT / "app"


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


def _pinyin_key(value: str) -> str:
    return re.sub(r"[ '\u2019]", "", value).casefold()


def _tone_digit(syllable: str) -> str:
    tones = {
        "\u0304": "1", "\u0301": "2", "\u030c": "3", "\u0300": "4",
    }
    found = [tones[char] for char in unicodedata.normalize("NFD", syllable) if char in tones]
    if len(found) > 1:
        raise ValueError(f"pinyin syllable has more than one tone mark: {syllable!r}")
    return found[0] if found else "5"


def _fallback_pinyin_syllables(value: str) -> list[str]:
    pieces = [piece for piece in re.split(r"[ '\u2019]+", value) if piece]
    if not pieces:
        return []
    choices = [_piece_segmentations(piece) for piece in pieces]
    if any(not values for values in choices):
        return []
    combined: list[tuple[str, ...]] = [()]
    for values in choices:
        combined = [
            prefix + tuple(marked for marked, _base, _erhua in segmentation)
            for prefix in combined for segmentation in values
        ]
    unique = sorted(set(combined))
    return list(unique[0]) if len(unique) == 1 else []


def derive_pinyin_tones(
    word: dict[str, str], word_chars: list[dict[str, str]],
) -> str:
    pinyin = word.get("pinyin", "")
    if not pinyin:
        return ""
    ordered = sorted(word_chars, key=lambda row: int(row["position"]))
    syllables = [row.get("pinyin_syllable", "") for row in ordered]
    if syllables and all(syllables) and _pinyin_key("".join(syllables)) == _pinyin_key(pinyin):
        return "".join(_tone_digit(syllable) for syllable in syllables)
    syllables = _fallback_pinyin_syllables(pinyin)
    if not syllables or _pinyin_key("".join(syllables)) != _pinyin_key(pinyin):
        return ""
    return "".join(_tone_digit(syllable) for syllable in syllables)


def export_words(
    raw: list[dict[str, str]], word_chars_raw: list[dict[str, str]],
) -> list[dict[str, Any]]:
    chars_by_word: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in word_chars_raw:
        chars_by_word[row["word_id"]].append(row)
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
        tones = derive_pinyin_tones(row, chars_by_word.get(row["word_id"], []))
        if tones:
            item["pt"] = tones
        if row.get("vi_use") == "literary":
            item["lit"] = True
        output.append(item)
    return output


def export_chars(raw: list[dict[str, str]], include_ids: set[str]) -> list[dict[str, Any]]:
    output = []
    for row in raw:
        if row["char_id"] not in include_ids:
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


def build_glyphs(
    words_raw: list[dict[str, str]], chars_raw: list[dict[str, str]],
    word_chars_raw: list[dict[str, str]],
) -> list[list[Any]]:
    chars = {row["char_id"]: row for row in chars_raw}
    chars_for_word: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in word_chars_raw:
        chars_for_word[row["word_id"]].append(row)
    single_rows: list[list[Any]] = []
    represented: set[str] = set()
    for word in words_raw:
        if word["card_eligible"] != "true" or len(word["trad"]) != 1:
            continue
        links = chars_for_word.get(word["word_id"], [])
        if len(links) != 1 or links[0]["position"] != "1" or links[0]["char_id"] not in chars:
            raise ValueError(f"single-character card word does not link once: {word['word_id']}")
        char_id = links[0]["char_id"]
        represented.add(char_id)
        single_rows.append([
            char_id, word["word_id"], int(word["level"]) if word["level"] else "",
            word["pinyin"], word["vi"],
        ])
    other_rows: list[list[Any]] = []
    for char in chars_raw:
        if char["jp"] == char["key_char"] == char["simp"] or char["char_id"] in represented:
            continue
        other_rows.append([
            char["char_id"], "", int(char["level"]) if char["level"] else "",
            char["pinyin"], "" if char["source_vi"] == "unihan_unverified" else char["vi"],
        ])
    output = single_rows + other_rows
    output.sort(key=lambda row: (
        row[2] if row[2] != "" else 99, row[0], row[1],
    ))
    if len(single_rows) != 1571 or len(other_rows) != 644 or len(output) != 2215:
        raise ValueError(
            f"glyph row counts differ: single={len(single_rows)}, other={len(other_rows)}, total={len(output)}"
        )
    if len({row[0] for row in output}) != 2164:
        raise ValueError("glyph rows do not cover 2,164 unique characters")
    return output


def build_usage(
    glyphs: list[list[Any]], words_raw: list[dict[str, str]],
    word_chars_raw: list[dict[str, str]],
) -> list[list[Any]]:
    words = {row["word_id"]: row for row in words_raw}
    by_char: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_word: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in word_chars_raw:
        by_char[row["char_id"]].append(row)
        by_word[row["word_id"]].append(row)
    output: list[list[Any]] = []
    for char_id in sorted({row[0] for row in glyphs}):
        zh_candidates: list[tuple[tuple[Any, ...], list[Any]]] = []
        vi_candidates: list[tuple[tuple[Any, ...], list[Any]]] = []
        for link in by_char.get(char_id, []):
            word = words.get(link["word_id"])
            if not word or len(word["trad"]) <= 1:
                continue
            level = int(word["level"]) if word["level"] else 99
            if word["origin"] in {"hsk", "both"} and word["pinyin"] and link["pinyin_syllable"]:
                ordered = sorted(by_word[word["word_id"]], key=lambda row: int(row["position"]))
                syllables = [row["pinyin_syllable"] for row in ordered]
                if not syllables or not all(syllables):
                    raise ValueError(f"usage pinyin syllables are incomplete: {word['word_id']}")
                joined = " ".join(syllables)
                if _pinyin_key(joined) != _pinyin_key(word["pinyin"]):
                    raise ValueError(f"usage pinyin syllables differ from word: {word['word_id']}")
                zh_candidates.append((
                    (level, word["word_id"]),
                    [word["word_id"], int(link["position"]), joined],
                ))
            if word["card_eligible"] == "true" and word["vi"] and link["vi_syllable"]:
                vi_syllables = word["vi"].split()
                position = int(link["position"])
                if position > len(vi_syllables) or vi_syllables[position - 1].casefold() != link["vi_syllable"].casefold():
                    raise ValueError(f"usage Vietnamese syllables differ from word: {word['word_id']}")
                vi_candidates.append((
                    (
                        1 if word["vi_use"] == "literary" else 0,
                        level,
                        int(word["freq_vi"]) if word["freq_vi"] else 10**12,
                        word["word_id"],
                    ),
                    [word["word_id"], position],
                ))
        zh = [value for _rank, value in sorted(zh_candidates, key=lambda item: item[0])[:3]]
        vi = [value for _rank, value in sorted(vi_candidates, key=lambda item: item[0])[:3]]
        output.append([char_id, zh, vi])
    if len(output) != 2164:
        raise ValueError(f"usage has {len(output)} rows, expected 2,164")
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
    examples_raw = read_csv(FINAL / "examples.csv")
    notes_raw = read_csv(FINAL / "char_notes.csv")
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

    glyphs = build_glyphs(words_raw, chars_raw, word_chars_raw)
    glyph_char_ids = {row[0] for row in glyphs}
    chars = export_chars(chars_raw, glyph_char_ids)
    words = export_words(words_raw, word_chars_raw)
    word_chars = export_word_chars(word_chars_raw, words_raw)
    ff_meanings = export_ff_meanings(ff_raw)
    rules = build_rules(words_raw, chars_raw, word_chars_raw)
    usage = build_usage(glyphs, words_raw, word_chars_raw)
    examples = [
        [
            row["word_id"], row["lang"], row["use"], row["sentence"], row["pinyin"],
            row["translation_ja"], int(row["target_start"]), int(row["target_len"]),
        ]
        for row in examples_raw
    ]
    char_notes = [[row["char_id"], row["note_ja"]] for row in notes_raw]
    payload_word_ids = {row["word_id"] for row in words}
    payload_char_ids = {row["char_id"] for row in chars}
    example_unknown = sorted({row[0] for row in examples} - payload_word_ids)
    glyph_word_unknown = sorted({row[1] for row in glyphs if row[1]} - payload_word_ids)
    glyph_char_unknown = sorted({row[0] for row in glyphs} - payload_char_ids)
    usage_char_unknown = sorted({row[0] for row in usage} - payload_char_ids)
    usage_word_unknown = sorted(
        {entry[0] for row in usage for entries in row[1:] for entry in entries} - payload_word_ids
    )
    note_unknown = sorted({row[0] for row in char_notes} - payload_char_ids)
    if any((example_unknown, glyph_word_unknown, glyph_char_unknown, usage_char_unknown,
            usage_word_unknown, note_unknown)):
        raise ValueError(
            "compact app-data references are unresolved: "
            f"examples={example_unknown[:3]}, glyph_words={glyph_word_unknown[:3]}, "
            f"glyph_chars={glyph_char_unknown[:3]}, usage_chars={usage_char_unknown[:3]}, "
            f"usage_words={usage_word_unknown[:3]}, notes={note_unknown[:3]}"
        )
    if len(examples) != 10367 or len(char_notes) != 581 or len(glyphs) != 2215 or len(usage) != 2164:
        raise ValueError("compact app-data counts differ from D75")
    pt_count = sum("pt" in row for row in words)
    literary_count = sum(row.get("lit") is True for row in words)
    return {
        "meta": {
            "built": BUILD_DATE,
            "counts": {
                "chars": len(chars_raw),
                "payload_chars": len(chars),
                "glyphs": len(glyphs),
                "words": len(words),
                "word_chars": len(word_chars),
                "ff_meanings": len(ff_meanings),
                "passages": len(passages),
                "examples": len(examples),
                "char_notes": len(char_notes),
                "usage": len(usage),
                "pinyin_tones": pt_count,
                "pinyin_tones_omitted": len(words) - pt_count,
                "literary_words": literary_count,
            },
        },
        "chars": chars,
        "words": words,
        "word_chars": word_chars,
        "ff_meanings": ff_meanings,
        "passages": passages,
        "rules": rules,
        "examples": examples,
        "char_notes": char_notes,
        "glyphs": glyphs,
        "usage": usage,
    }


def export_data_js(path: Path = FINAL / "data.js") -> dict[str, Any]:
    payload = build_payload()
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.KB_DATA = {encoded};\n", encoding="utf-8", newline="\n")
    if path.resolve() == (FINAL / "data.js").resolve():
        APP.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, APP / "data.js")
    return payload


def main() -> None:
    payload = export_data_js()
    counts = payload["meta"]["counts"]
    print(
        "Exported data.js: "
        f"{(FINAL / 'data.js').stat().st_size:,} bytes; "
        f"{counts['words']:,} words; {counts['glyphs']:,} glyph rows; "
        f"{counts['usage']:,} usage rows; {counts['examples']:,} examples; "
        f"{counts['char_notes']:,} character notes; "
        f"{counts['pinyin_tones']:,} words with pinyin tone hints"
    )


if __name__ == "__main__":
    main()
