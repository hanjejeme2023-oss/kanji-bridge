"""Validate and merge accepted task-6 content without network access."""

from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import require_nfc, write_csv, write_json
from pipeline.stage4 import builders
from pipeline.stage4.validators import validate


FINAL = ROOT / "data" / "final"
ACCEPTED = ROOT / "content" / "accepted" / "task6"
CONFIG = ROOT / "config"
PROMPTS = ROOT / "content" / "prompts"
MODEL = "gemini-4-argon"
EXPECTED_BATCHES = 224
EXPECTED_EXAMPLES = Counter({
    ("zh", "card"): 5783,
    ("zh", "ff"): 560,
    ("vi", "card"): 3909,
    ("vi", "ff"): 115,
})
EXAMPLE_COLUMNS = [
    "word_id", "lang", "use", "sentence", "pinyin", "translation_ja",
    "target", "target_start", "target_len",
]
NOTE_COLUMNS = ["char_id", "note_ja"]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return builders.read_jsonl_files([path])


def _prompt_sha(kind: str) -> str:
    version = "v1" if kind == "note" else "v2"
    text = (PROMPTS / f"task6_{kind}_{version}.md").read_text(encoding="utf-8")
    return builders.sha256_text(unicodedata.normalize("NFC", text.strip()))


def _expected_names(directory: Path, suffix: str, count: int) -> None:
    expected = {f"b{number:03d}{suffix}" for number in range(1, count + 1)}
    actual = {path.name for path in directory.glob(f"b*{suffix}")}
    if actual != expected:
        missing = sorted(expected - actual)[:5]
        extra = sorted(actual - expected)[:5]
        raise ValueError(
            f"task-6 accepted files differ in {directory.relative_to(ROOT)}: "
            f"missing={missing}, extra={extra}"
        )


def _validate_batch(
    name: str,
    kind: str,
    inputs: list[dict[str, Any]],
    directory: Path,
    input_directory: Path,
) -> list[dict[str, Any]]:
    input_path = input_directory / f"{name}.jsonl"
    expected_input = builders.ordered_jsonl_text(inputs)
    if input_path.read_text(encoding="utf-8") != expected_input:
        raise ValueError(f"accepted task-6 input differs from the fresh build: {name}")
    output_path = directory / f"{name}.jsonl"
    log_path = directory / f"{name}.log.json"
    output = _read_jsonl(output_path)
    log = json.loads(log_path.read_text(encoding="utf-8"))
    expected_log = {
        "task": 6,
        "batch": name,
        "kind": kind,
        "model": MODEL,
        "prompt_sha256": _prompt_sha(kind),
        "input_sha256": builders.sha256_text(expected_input),
        "item_count": len(inputs),
    }
    if any(log.get(field) != value for field, value in expected_log.items()):
        raise ValueError(f"accepted task-6 log metadata differs: {name}")
    if log.get("validation", {}).get("state") != "validated" or log.get("validation", {}).get("ok") is not True:
        raise ValueError(f"accepted task-6 log is not validated: {name}")
    validate(6, output, inputs, kind)
    return output


def _keyed(items: Iterable[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        key = str(item.get("key", ""))
        if not key or key in result:
            raise ValueError(f"{label} has an empty or duplicate key: {key!r}")
        result[key] = dict(item)
    return result


def _restore_reviewed_inputs(fresh: list[tuple[str, str, list[dict[str, Any]]]]) -> None:
    """Undo reviewed input changes made after generation (R1, D78 item 3); fail-closed.

    A later review overlay can change a field that a task-6 input copies (e.g. the
    contrast meaning). ``config/task6_input_review.csv`` lists each such field with
    the value the accepted answer was generated from and the value a fresh build
    gives now; the fresh item must hold exactly ``current_value``, is compared with
    ``generated_value``, and every row must be used exactly once. Any other
    difference still stops the build.
    """
    with (CONFIG / "task6_input_review.csv").open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["key", "field", "generated_value", "current_value", "reason"]:
            raise ValueError("task6_input_review.csv has the wrong columns")
        rows = list(reader)
    by_key = {item["key"]: item for _name, _kind, items in fresh for item in items}
    seen: set[tuple[str, str]] = set()
    for row in rows:
        marker = (row["key"], row["field"])
        if marker in seen or not row["reason"].strip():
            raise ValueError(f"task6_input_review.csv row is duplicated or has no reason: {marker}")
        seen.add(marker)
        item = by_key.get(row["key"])
        if item is None or row["field"] not in item or row["field"] == "key":
            raise ValueError(f"task6_input_review.csv target is missing: {marker}")
        if item[row["field"]] != row["current_value"]:
            raise ValueError(f"task6_input_review.csv current value differs from the fresh build: {marker}")
        item[row["field"]] = row["generated_value"]


def _load_main_answers() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    fresh = builders.build_task6_batches()
    _restore_reviewed_inputs(fresh)
    if len(fresh) != EXPECTED_BATCHES:
        raise ValueError(f"fresh task-6 build has {len(fresh)} batches, expected {EXPECTED_BATCHES}")
    _expected_names(ACCEPTED, ".jsonl", EXPECTED_BATCHES)
    _expected_names(ACCEPTED, ".log.json", EXPECTED_BATCHES)
    _expected_names(ACCEPTED / "inputs", ".jsonl", EXPECTED_BATCHES)
    input_items: list[dict[str, Any]] = []
    output_items: list[dict[str, Any]] = []
    for name, kind, items in fresh:
        input_items.extend(items)
        output_items.extend(_validate_batch(name, kind, items, ACCEPTED, ACCEPTED / "inputs"))
    inputs = _keyed(input_items, "task-6 main inputs")
    outputs = _keyed(output_items, "task-6 main outputs")
    if set(inputs) != set(outputs):
        raise ValueError("task-6 main input and output keys differ")
    return inputs, outputs


def _read_rerun_rows(main_inputs: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    with (CONFIG / "task6_rerun.csv").open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["round", "key", "reason"]:
            raise ValueError("task6_rerun.csv columns must be round,key,reason")
        rows = list(reader)
    if any(row["round"] != "1" for row in rows):
        raise ValueError("task6_rerun.csv has an unsupported rerun round")
    keys = [row["key"] for row in rows]
    if not keys or len(keys) != len(set(keys)):
        raise ValueError("task6_rerun.csv has no keys or duplicate keys")
    unknown = sorted(set(keys) - set(main_inputs))
    if unknown:
        raise ValueError(f"task6_rerun.csv has unknown keys: {unknown[:5]}")
    return rows


def _kind_for_key(key: str) -> str:
    if key.endswith(":note"):
        return "note"
    parts = key.split(":")
    if len(parts) == 3 and parts[1] in {"zh", "vi"}:
        return parts[1]
    raise ValueError(f"invalid task-6 key: {key}")


def _load_rerun_answers(
    main_inputs: dict[str, dict[str, Any]], rows: list[dict[str, str]],
) -> dict[str, dict[str, Any]]:
    selected: dict[str, list[dict[str, Any]]] = {"zh": [], "vi": [], "note": []}
    for row in rows:
        key = row["key"]
        selected[_kind_for_key(key)].append({
            **main_inputs[key], "review_feedback": row["reason"],
        })
    batches: list[tuple[str, str, list[dict[str, Any]]]] = []
    number = 1
    for kind in ("zh", "vi", "note"):
        for items in builders.chunked(selected[kind], 50):
            batches.append((f"b{number:03d}", kind, items))
            number += 1
    directory = ACCEPTED / "rerun1"
    input_directory = ACCEPTED / "inputs" / "rerun1"
    count = len(batches)
    _expected_names(directory, ".jsonl", count)
    _expected_names(directory, ".log.json", count)
    _expected_names(input_directory, ".jsonl", count)
    output_items: list[dict[str, Any]] = []
    for name, kind, items in batches:
        output_items.extend(_validate_batch(name, kind, items, directory, input_directory))
    outputs = _keyed(output_items, "task-6 rerun outputs")
    if set(outputs) != {row["key"] for row in rows}:
        raise ValueError("task-6 rerun output keys differ from task6_rerun.csv")
    return outputs


def apply_review_rows(
    effective: dict[str, dict[str, Any]], rows: list[dict[str, str]], *, enforce_counts: bool,
) -> set[str]:
    keys = [row["key"] for row in rows]
    if not keys or len(keys) != len(set(keys)):
        raise ValueError("task6_review.csv must have unique keys")
    if enforce_counts and len(rows) != 29:
        raise ValueError("task6_review.csv must have 29 unique keys")
    unknown = sorted(set(keys) - set(effective))
    if unknown:
        raise ValueError(f"task6_review.csv has unknown keys: {unknown[:5]}")
    dropped: set[str] = set()
    actions = Counter()
    for row in rows:
        key, action = row["key"], row["action"]
        answer = effective[key]
        if action == "drop":
            field = "note_ja" if key.endswith(":note") else "sentence"
            dropped.add(key)
        elif action == "set_translation_ja":
            field = "translation_ja"
        elif action == "set_note_ja":
            field = "note_ja"
        else:
            raise ValueError(f"task6_review.csv has unknown action: {action}")
        if str(answer.get(field, "")) != row["generated"]:
            raise ValueError(f"task6_review.csv generated value differs for {key}")
        if action != "drop":
            if not row["review"]:
                raise ValueError(f"task6_review.csv replacement is empty for {key}")
            answer[field] = unicodedata.normalize("NFC", row["review"])
        actions[action] += 1
    if enforce_counts and actions != Counter({"drop": 11, "set_translation_ja": 13, "set_note_ja": 5}):
        raise ValueError(f"task6_review.csv action counts differ: {dict(actions)}")
    return dropped


def _apply_review(effective: dict[str, dict[str, Any]]) -> set[str]:
    with (CONFIG / "task6_review.csv").open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["key", "action", "generated", "review", "reason"]:
            raise ValueError("task6_review.csv columns differ from D75")
        rows = list(reader)
    return apply_review_rows(effective, rows, enforce_counts=True)


def effective_answers(
    main: dict[str, dict[str, Any]], reruns: dict[int, dict[str, dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    result = {key: dict(value) for key, value in main.items()}
    for round_number in sorted(reruns):
        unknown = sorted(set(reruns[round_number]) - set(result))
        if unknown:
            raise ValueError(f"task-6 rerun {round_number} has unknown keys: {unknown[:5]}")
        result.update({key: dict(value) for key, value in reruns[round_number].items()})
    return result


def normalize_pinyin_spacing(value: str) -> tuple[str, bool]:
    normalized = re.sub(r"\s+([,.!?;:])", r"\1", value).strip()
    removed_only = re.sub(r"\s+([,.!?;:])", r"\1", value).strip()
    if normalized != removed_only:
        raise ValueError("pinyin normalization changed more than punctuation whitespace")
    return normalized, normalized != value


def _target_offset(sentence: str, target: str, lang: str) -> int:
    if lang == "zh":
        position = sentence.find(target)
        if position < 0:
            raise ValueError(f"Chinese target is absent: {target!r} in {sentence!r}")
        return position
    folded_sentence, folded_target = sentence.casefold(), target.casefold()
    if len(folded_sentence) != len(sentence) or len(folded_target) != len(target):
        raise ValueError("Vietnamese casefold changed character indexes")
    start = 0
    while True:
        position = folded_sentence.find(folded_target, start)
        if position < 0:
            raise ValueError(f"Vietnamese target is absent as whole syllables: {target!r}")
        end = position + len(target)
        before_ok = position == 0 or not sentence[position - 1].isalpha()
        after_ok = end == len(sentence) or not sentence[end].isalpha()
        if before_ok and after_ok:
            return position
        start = position + 1


def build_tables() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    main_inputs, main_answers = _load_main_answers()
    rerun_rows = _read_rerun_rows(main_inputs)
    effective = effective_answers(
        main_answers, {1: _load_rerun_answers(main_inputs, rerun_rows)},
    )
    dropped = _apply_review(effective)
    words = pd.read_csv(FINAL / "words.csv", encoding="utf-8", keep_default_na=False, dtype=str)
    word_map = words.set_index("word_id", drop=False)

    examples: list[dict[str, Any]] = []
    normalized_count = 0
    for key in sorted(effective):
        if key.endswith(":note") or key in dropped:
            continue
        answer = effective[key]
        if answer["status"] == "no_sentence":
            continue
        word_id, lang, use = key.split(":")
        if word_id not in word_map.index:
            raise ValueError(f"task-6 example has unknown word_id: {word_id}")
        word = word_map.loc[word_id]
        target = main_inputs[key]["target"]
        expected_target = word["simp"] if lang == "zh" else word["vi"]
        if target != expected_target:
            raise ValueError(f"task-6 target differs from words.csv for {key}")
        pinyin = ""
        if lang == "zh":
            pinyin, changed = normalize_pinyin_spacing(answer["pinyin"])
            normalized_count += changed
        offset = _target_offset(answer["sentence"], target, lang)
        examples.append({
            "word_id": word_id, "lang": lang, "use": use,
            "sentence": answer["sentence"], "pinyin": pinyin,
            "translation_ja": answer["translation_ja"], "target": target,
            "target_start": offset, "target_len": len(target),
        })
    examples.sort(key=lambda row: (
        row["word_id"], {"zh": 0, "vi": 1}[row["lang"]],
        {"card": 0, "ff": 1}[row["use"]],
    ))
    distribution = Counter((row["lang"], row["use"]) for row in examples)
    if distribution != EXPECTED_EXAMPLES or len(examples) != 10367:
        raise ValueError(f"task-6 example counts differ from D75: {dict(distribution)}")
    if normalized_count != 998:
        raise ValueError(f"task-6 pinyin normalization count is {normalized_count}, expected 998")

    notes = []
    for key in sorted(effective):
        if not key.endswith(":note") or key in dropped:
            continue
        note = effective[key]["note_ja"]
        if note:
            notes.append({"char_id": key.removesuffix(":note"), "note_ja": note})
    if len(notes) != 581 or len({row["char_id"] for row in notes}) != len(notes):
        raise ValueError(f"task-6 character-note count is {len(notes)}, expected 581 unique rows")
    examples_frame = pd.DataFrame(examples, columns=EXAMPLE_COLUMNS)
    notes_frame = pd.DataFrame(notes, columns=NOTE_COLUMNS)
    require_nfc(examples_frame)
    require_nfc(notes_frame)
    summary = {
        "examples": len(examples_frame),
        "examples_by_kind": {f"{lang}_{use}": count for (lang, use), count in sorted(distribution.items())},
        "char_notes": len(notes_frame),
        "pinyin_spacing_normalized": normalized_count,
        "rerun_answers": len(rerun_rows),
        "review_actions": 29,
    }
    return examples_frame, notes_frame, summary


def main() -> None:
    examples, notes, summary = build_tables()
    write_csv(examples, FINAL / "examples.csv")
    write_json(examples, FINAL / "examples.json")
    write_csv(notes, FINAL / "char_notes.csv")
    write_json(notes, FINAL / "char_notes.json")
    (FINAL / "task6_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
