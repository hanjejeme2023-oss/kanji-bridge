"""Merge accepted Stage 4 content into the final Kanji Bridge tables."""

from __future__ import annotations

import copy
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

try:
    from pipeline.common import assign_ids, require_nfc, split_multi, write_csv, write_json
    from pipeline.extract_prototype_config import extract_ff, extract_word_notes
except ModuleNotFoundError:  # direct execution as pipeline/merge_stage4.py
    from common import assign_ids, require_nfc, split_multi, write_csv, write_json
    from extract_prototype_config import extract_ff, extract_word_notes


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "data" / "final"
STAGING = ROOT / "data" / "staging"
ACCEPTED = ROOT / "content" / "accepted"
CONFIG = ROOT / "config"
EXPECTED_BATCHES = {1: 86, 2: 79, 3: 14, 4: 5, 5: 104}
LANGS = ("ja", "ko", "zh", "vi")
READING_COLUMN = {"ja": "ja", "ko": "ko", "zh": "pinyin", "vi": "vi"}
LANG_ORDER = {lang: index for index, lang in enumerate(LANGS)}
WORD_COLUMNS = [
    "word_id", "trad", "simp", "jp", "ja", "ja_common", "ko", "pinyin", "vi",
    "ja_alt", "ko_alt", "vi_alt", "pos", "hsk_ids", "gloss_en", "gloss_ja_en",
    "gloss_ko", "gloss_vi", "meaning_ja__ja", "meaning_ja__ko", "meaning_ja__zh",
    "meaning_ja__vi", "note_ja", "level", "freq_vi", "origin", "card_eligible",
    "false_friend", "syl_aligned", "verified", "ja_use", "ko_use", "vi_use",
    "source_ja", "source_ko", "source_pinyin", "source_vi", "source_level",
]
FF_COLUMNS = ["word_id", "lang", "reading", "reading_display", "meaning_ja", "is_trap"]
PASSAGE_COLUMNS = ["passage_id", "lang", "level", "translation_ja", "tokens"]


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8", keep_default_na=False, dtype=str)


def clean(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value.strip())
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items()}
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: expected a JSON object")
        result.append(clean(value))
    return result


def accepted_batches(task: int, *, inputs: bool = False) -> dict[str, list[dict[str, Any]]]:
    expected = EXPECTED_BATCHES[task]
    directory = ACCEPTED / f"task{task}" / ("inputs" if inputs else "")
    result: dict[str, list[dict[str, Any]]] = {}
    expected_names = {f"b{number:03d}" for number in range(1, expected + 1)}
    for name in sorted(expected_names):
        path = directory / f"{name}.jsonl"
        if not path.is_file():
            raise ValueError(f"accepted task {task} is missing {path.relative_to(ROOT)}")
        result[name] = read_jsonl(path)
        if not inputs:
            log_path = ACCEPTED / f"task{task}" / f"{name}.log.json"
            if not log_path.is_file():
                raise ValueError(f"accepted task {task} is missing {log_path.relative_to(ROOT)}")
            log = json.loads(log_path.read_text(encoding="utf-8"))
            if (
                log.get("task") != task
                or log.get("batch") != name
                or log.get("validation", {}).get("ok") is not True
                or int(log.get("item_count", -1)) != len(result[name])
            ):
                raise ValueError(f"accepted task {task} has an invalid log for {name}")
    actual_names = {path.stem for path in directory.glob("b*.jsonl")}
    if actual_names != expected_names:
        raise ValueError(f"accepted task {task} has unexpected batch files")
    return result


def flatten(batches: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [item for name in sorted(batches) for item in batches[name]]


def keyed(items: Iterable[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for original in items:
        item = copy.deepcopy(original)
        value = str(item.get(key, ""))
        if not value or value in result:
            raise ValueError(f"{label} has an empty or duplicate {key}: {value!r}")
        result[value] = item
    return result


def apply_task1_review(
    outputs: dict[str, dict[str, Any]], words: pd.DataFrame, review: pd.DataFrame,
) -> dict[str, dict[str, Any]]:
    result = copy.deepcopy(outputs)
    if review["word_id"].eq("").any() or review["word_id"].duplicated().any():
        raise ValueError("task1_review.csv has an empty or duplicate word_id")
    word_map = words.set_index("word_id", drop=False)
    for row in review.to_dict(orient="records"):
        word_id = row["word_id"]
        if word_id not in word_map.index or word_id not in result:
            raise ValueError(f"task-1 review target is missing: {word_id}")
        word = word_map.loc[word_id]
        if word["trad"] != row["trad"] or word["vi"] != row["vi"]:
            raise ValueError(f"task-1 review frozen-word mismatch for {word_id}")
        if result[word_id].get("vi_check") != row["vi_check_task1"]:
            raise ValueError(f"task-1 review generated-output mismatch for {word_id}")
        result[word_id]["vi_check"] = row["vi_check_review"]
    return result


def apply_task1_meaning_review(
    outputs: dict[str, dict[str, Any]], words: pd.DataFrame, review: pd.DataFrame,
) -> dict[str, dict[str, Any]]:
    """Review overlay for task-1 meanings (R1, D78 item 3); fail-closed like the other overlays.

    Every row must name an accepted task-1 word with the frozen ``trad``, match the
    generated text exactly and carry a reviewed text and a reason, so each row is
    applied exactly once and a changed source stops the build.
    """
    result = copy.deepcopy(outputs)
    expected = ["word_id", "trad", "lang", "meaning_ja_generated", "meaning_ja_review", "reason"]
    if list(review.columns) != expected:
        raise ValueError("task1_meaning_review.csv has the wrong columns")
    if review[["word_id", "lang"]].duplicated().any() or review["word_id"].eq("").any():
        raise ValueError("task1_meaning_review.csv has an empty or duplicate (word_id, lang)")
    word_map = words.set_index("word_id", drop=False)
    for row in review.to_dict(orient="records"):
        word_id, lang = row["word_id"], row["lang"]
        if lang not in LANGS or not row["meaning_ja_review"] or not row["reason"]:
            raise ValueError(f"invalid task-1 meaning review row for {word_id}/{lang}")
        if word_id not in word_map.index or word_id not in result:
            raise ValueError(f"task-1 meaning review target is missing: {word_id}")
        if word_map.loc[word_id, "trad"] != row["trad"]:
            raise ValueError(f"task-1 meaning review frozen-word mismatch for {word_id}")
        field = f"meaning_ja__{lang}"
        if result[word_id].get(field) != row["meaning_ja_generated"]:
            raise ValueError(f"task-1 meaning review generated-output mismatch for {word_id}/{lang}")
        result[word_id][field] = row["meaning_ja_review"]
    return result


def task2_meaning(item: dict[str, Any], lang: str) -> dict[str, Any]:
    matches = [row for row in item.get("meanings", []) if row.get("lang") == lang]
    if len(matches) != 1:
        raise ValueError(f"task-2 key {item.get('key')} needs exactly one {lang} meaning")
    return matches[0]


def split_langs(value: str) -> list[str]:
    result = [part for part in value.split(";") if part]
    if len(result) != len(set(result)) or set(result) - set(LANGS):
        raise ValueError(f"invalid language list: {value!r}")
    return result


def apply_task2_reviews(
    outputs: dict[str, dict[str, Any]], review: pd.DataFrame, retrap: pd.DataFrame,
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    raw = copy.deepcopy(outputs)
    result = copy.deepcopy(outputs)
    if review[["key", "lang"]].duplicated().any() or review["key"].eq("").any():
        raise ValueError("task2_review.csv has an empty or duplicate (key, lang)")
    cleared_vi: set[str] = set()
    for row in review.to_dict(orient="records"):
        key, lang, action = row["key"], row["lang"], row["action"]
        if key not in result:
            raise ValueError(f"task-2 review target is missing: {key}")
        generated = task2_meaning(raw[key], lang)
        if (
            generated.get("meaning_ja") != row["meaning_ja_generated"]
            or str(bool(generated.get("is_trap"))).lower() != row["is_trap_generated"].lower()
        ):
            raise ValueError(f"task-2 review generated-output mismatch for {key}/{lang}")
        reviewed_ff = split_langs(row["false_friend_review"])
        if action == "same_as_ja":
            if lang != "ko" or not row["meaning_ja_review"]:
                raise ValueError(f"invalid task-2 same_as_ja row for {key}/{lang}")
            current = task2_meaning(result[key], lang)
            current["meaning_ja"] = row["meaning_ja_review"]
            current["is_trap"] = lang in reviewed_ff
        elif action == "set_meaning":
            # R1 (D78 item 3): a reviewed meaning text for any language; the trap
            # flag follows false_friend_review and must not change.
            if not row["meaning_ja_review"] or not row["reason"]:
                raise ValueError(f"invalid task-2 set_meaning row for {key}/{lang}")
            current = task2_meaning(result[key], lang)
            if bool(current.get("is_trap")) != (lang in reviewed_ff):
                raise ValueError(f"task-2 set_meaning would change the trap flag for {key}/{lang}")
            current["meaning_ja"] = row["meaning_ja_review"]
        elif action == "clear_vi":
            if lang != "vi" or row["meaning_ja_review"]:
                raise ValueError(f"invalid task-2 clear_vi row for {key}/{lang}")
            result[key]["meanings"] = [m for m in result[key]["meanings"] if m.get("lang") != "vi"]
            cleared_vi.add(key)
        else:
            raise ValueError(f"unknown task-2 review action: {action!r}")
        result[key]["false_friend"] = reviewed_ff

    if retrap[["key", "lang"]].duplicated().any() or retrap["key"].eq("").any():
        raise ValueError("task2_retrap.csv has an empty or duplicate (key, lang)")
    for key, group in retrap.groupby("key", sort=False):
        if key not in result or group["false_friend_review"].nunique() != 1:
            raise ValueError(f"invalid task-2 retrap group: {key}")
        reviewed_ff = split_langs(group.iloc[0]["false_friend_review"])
        for row in group.to_dict(orient="records"):
            lang = row["lang"]
            generated = task2_meaning(raw[key], lang)
            if (
                generated.get("meaning_ja") != row["meaning_ja_generated"]
                or str(bool(generated.get("is_trap"))).lower() != row["is_trap_generated"].lower()
            ):
                raise ValueError(f"task-2 retrap generated-output mismatch for {key}/{lang}")
            current = task2_meaning(result[key], lang)
            current["is_trap"] = row["is_trap_review"].lower() == "true"
        result[key]["false_friend"] = reviewed_ff

    for key, item in result.items():
        ff = item.get("false_friend")
        if not isinstance(ff, list) or len(ff) != len(set(ff)) or set(ff) - set(LANGS):
            raise ValueError(f"task-2 false_friend is invalid for {key}")
        languages = [str(row.get("lang", "")) for row in item.get("meanings", [])]
        if len(languages) != len(set(languages)) or any(lang not in LANGS for lang in languages):
            raise ValueError(f"task-2 meanings are invalid for {key}")
    return result, cleared_vi


def apply_task4_review(
    outputs: dict[str, dict[str, Any]], words: pd.DataFrame, review: pd.DataFrame,
) -> dict[str, dict[str, Any]]:
    result = copy.deepcopy(outputs)
    if review["word_id"].eq("").any() or review["word_id"].duplicated().any():
        raise ValueError("task4_review.csv has an empty or duplicate word_id")
    word_map = words.set_index("word_id", drop=False)
    for row in review.to_dict(orient="records"):
        word_id = row["word_id"]
        if word_id not in result or word_id not in word_map.index:
            raise ValueError(f"task-4 review target is missing: {word_id}")
        if word_map.loc[word_id, "trad"] != row["trad"]:
            raise ValueError(f"task-4 review frozen-word mismatch for {word_id}")
        if result[word_id].get("note_ja") != row["note_ja_generated"]:
            raise ValueError(f"task-4 review generated-output mismatch for {word_id}")
        result[word_id]["note_ja"] = row["note_ja_review"]
    return result


def apply_task5_review(
    outputs: dict[str, dict[str, Any]], inputs: dict[str, dict[str, Any]], review: pd.DataFrame,
) -> dict[str, dict[str, Any]]:
    result = copy.deepcopy(outputs)
    if set(result) != set(inputs):
        raise ValueError("accepted task-5 input/output keys differ")
    if review[["key", "lang"]].duplicated().any() or review["key"].eq("").any():
        raise ValueError("task5_review.csv has an empty or duplicate (key, lang)")
    for row in review.to_dict(orient="records"):
        key, lang = row["key"], row["lang"]
        field = f"{lang}_check" if lang in {"ja", "ko"} else "vi_use"
        if key not in result or lang not in READING_COLUMN:
            raise ValueError(f"task-5 review target is missing: {key}/{lang}")
        source = inputs[key]
        if source.get("trad") != row["trad"] or source.get(READING_COLUMN[lang]) != row["reading"]:
            raise ValueError(f"task-5 review frozen-input mismatch for {key}/{lang}")
        if result[key].get(field) != row["check_generated"]:
            raise ValueError(f"task-5 review generated-output mismatch for {key}/{lang}")
        result[key][field] = row["check_review"]

    for key, item in result.items():
        source = inputs[key]
        checks = source.get("checks")
        if not isinstance(checks, list) or len(checks) != len(set(checks)):
            raise ValueError(f"task-5 checks are invalid for {key}")
        for lang, field, allowed in (
            ("ja", "ja_check", {"used", "rare", "wrong_meaning", "unsure"}),
            ("ko", "ko_check", {"used", "rare", "wrong_meaning", "unsure"}),
            ("vi", "vi_use", {"common", "literary", "unsure"}),
        ):
            value = str(item.get(field, ""))
            if (lang in checks) != bool(value) or (value and value not in allowed):
                raise ValueError(f"task-5 {field} is invalid for {key}")
    return result


def usage_for(item: dict[str, Any] | None) -> dict[str, str]:
    if item is None:
        return {"ja": "", "ko": "", "vi": ""}
    ja = "rare" if item.get("ja_check") == "unsure" else str(item.get("ja_check", ""))
    ko = "rare" if item.get("ko_check") == "unsure" else str(item.get("ko_check", ""))
    return {"ja": ja, "ko": ko, "vi": str(item.get("vi_use", ""))}


def apply_task3_review(
    batch: str, output: dict[str, Any], review: pd.DataFrame, *, include_positions: bool = False,
) -> list[Any]:
    passages = copy.deepcopy(output.get("passages"))
    if not isinstance(passages, list):
        raise ValueError(f"task-3 {batch} has no passages list")
    rows = review.loc[review["batch"] == batch]
    drops: set[int] = set()
    deletes: dict[int, list[int]] = {}
    for row in rows.to_dict(orient="records"):
        passage_number = int(row["passage"])
        if passage_number < 1 or passage_number > len(passages):
            raise ValueError(f"task-3 review passage is out of range: {batch}/{passage_number}")
        passage = passages[passage_number - 1]
        action = row["action"]
        if action == "drop":
            if passage.get("translation_ja") != row["generated"]:
                raise ValueError(f"task-3 drop mismatch: {batch}/{passage_number}")
            drops.add(passage_number)
        elif action == "delete_token":
            index = int(row["token_index"])
            if passage["tokens"][index] != json.loads(row["generated"]):
                raise ValueError(f"task-3 delete_token mismatch: {batch}/{passage_number}/{index}")
            deletes.setdefault(passage_number, []).append(index)
        elif action == "set_t":
            index = int(row["token_index"])
            token = passage["tokens"][index]
            if token.get("t") != row["generated"] or "word_id" not in token:
                raise ValueError(f"task-3 set_t mismatch: {batch}/{passage_number}/{index}")
            token["t"] = row["review"]
        else:
            raise ValueError(f"unknown task-3 review action: {action!r}")
    for passage_number, indices in deletes.items():
        for index in sorted(indices, reverse=True):
            del passages[passage_number - 1]["tokens"][index]
    kept = [(number, passage) for number, passage in enumerate(passages, 1) if number not in drops]
    return kept if include_positions else [passage for _, passage in kept]


def validate_task3_review_batches(review: pd.DataFrame, batches: Iterable[str]) -> None:
    accepted = set(batches)
    unknown = sorted(set(review["batch"]) - accepted)
    if unknown:
        raise ValueError(f"task-3 review refers to unknown accepted batches: {unknown}")


def validate_passage(passage: dict[str, Any], lang: str, words: pd.DataFrame) -> None:
    if not passage.get("translation_ja") or not isinstance(passage.get("tokens"), list):
        raise ValueError("passage is missing translation or tokens")
    word_map = words.set_index("word_id", drop=False)
    linked = 0
    for token in passage["tokens"]:
        if not isinstance(token, dict) or not isinstance(token.get("t"), str) or not token["t"]:
            raise ValueError("passage has an invalid token")
        annotations = [name for name in ("word_id", "gloss_ja", "punct") if name in token]
        if len(annotations) != 1:
            raise ValueError(f"passage token needs one annotation: {token}")
        if "word_id" in token:
            word_id = token["word_id"]
            if word_id not in word_map.index:
                raise ValueError(f"passage token has unknown word_id: {word_id}")
            row = word_map.loc[word_id]
            expected = row["simp"] or row["trad"] if lang == "zh" else row["vi"]
            if not expected or token["t"].casefold() != expected.casefold():
                raise ValueError(f"passage token does not resolve: {word_id} {token['t']!r} != {expected!r}")
            linked += 1
        elif "gloss_ja" in token and not token["gloss_ja"]:
            raise ValueError("passage function token has an empty gloss")
        elif "punct" in token and token["punct"] is not True:
            raise ValueError("passage punctuation marker is not true")
    if linked < 3:
        raise ValueError("passage has fewer than three linked tokens")


def config_from_prototype() -> tuple[pd.DataFrame, pd.DataFrame]:
    prototype = (ROOT / "prototype" / "index.html").read_text(encoding="utf-8")
    expected_ff = extract_ff(prototype)
    expected_notes = extract_word_notes(prototype)
    actual_ff = load_csv(CONFIG / "ff_static.csv")
    actual_ff["is_trap"] = actual_ff["is_trap"].str.lower().map({"true": True, "false": False})
    actual_ff["row"] = pd.to_numeric(actual_ff["row"], errors="raise").astype(int)
    actual_notes = load_csv(CONFIG / "word_notes.csv")
    if actual_ff.to_dict(orient="records") != expected_ff.to_dict(orient="records"):
        raise ValueError("config/ff_static.csv differs from the frozen prototype extraction")
    if actual_notes.to_dict(orient="records") != expected_notes.to_dict(orient="records"):
        raise ValueError("config/word_notes.csv differs from the frozen prototype extraction")
    return actual_ff, actual_notes


def source_reading(source: pd.Series, lang: str) -> str:
    return str(source.get(READING_COLUMN[lang], ""))


def validate_static_reading(source: pd.Series, row: dict[str, Any]) -> None:
    display = row["reading_display"]
    if re.fullmatch(r"（.*）", display):
        return
    lang = row["lang"]
    primary = source_reading(source, lang)
    alternatives = split_multi(source.get(f"{lang}_alt", "")) if lang in {"ja", "ko", "vi"} else []
    readings = [primary, *alternatives]
    allowed = {value for value in readings if value}
    if lang == "zh":
        simp = str(source.get("simp", ""))
        allowed.update(f"{simp} {value}" for value in readings if simp and value)
    if display not in allowed:
        raise ValueError(
            f"static FF reading differs from dictionary data: {row['word']}/{lang} {display!r}"
        )


def make_ff_only_word(
    source: pd.Series, word_id: str, false_friend: str,
    meanings: dict[str, str], usage: dict[str, str],
) -> dict[str, Any]:
    return {
        "word_id": word_id, "trad": source["trad"], "simp": source["simp"],
        "jp": source["form"], "ja": source["ja"], "ja_common": True,
        "ko": source["ko"], "pinyin": source["pinyin"], "vi": source["vi"],
        "ja_alt": "", "ko_alt": "", "vi_alt": "", "pos": "", "hsk_ids": "",
        "gloss_en": source["gloss_en"], "gloss_ja_en": source["gloss_ja_en"],
        "gloss_ko": "", "gloss_vi": source["gloss_vi"],
        **{f"meaning_ja__{lang}": meanings.get(lang, "") for lang in LANGS},
        "note_ja": "", "level": "", "freq_vi": "", "origin": "ff_only",
        "card_eligible": False, "false_friend": false_friend, "syl_aligned": False,
        "verified": False, "ja_use": usage["ja"], "ko_use": usage["ko"],
        "vi_use": usage["vi"], "source_ja": "jmdict" if source["ja"] else "",
        "source_ko": source.get("source_ko", "") if source["ko"] else "",
        "source_pinyin": "cc-cedict" if source["pinyin"] else "",
        "source_vi": source.get("source_vi", "") if source["vi"] else "",
        "source_level": "",
    }


def validate_recursive_nfc(value: Any) -> None:
    if isinstance(value, str) and value != unicodedata.normalize("NFC", value):
        raise ValueError(f"non-NFC Stage 4 value: {value!r}")
    if isinstance(value, list):
        for item in value:
            validate_recursive_nfc(item)
    elif isinstance(value, dict):
        for item in value.values():
            validate_recursive_nfc(item)


def main() -> None:
    words = load_csv(FINAL / "words.csv")
    ff_candidates = load_csv(STAGING / "ff_candidates.csv")
    if words["word_id"].duplicated().any() or ff_candidates["form"].duplicated().any():
        raise ValueError("Stage 3 word or false-friend keys are not unique")
    for column in WORD_COLUMNS:
        if column not in words:
            words[column] = ""
    # Permit a local re-merge without accumulating the derived ff_only rows.
    words = words.loc[words["origin"] != "ff_only", WORD_COLUMNS].copy()
    for column in [
        "meaning_ja__ja", "meaning_ja__ko", "meaning_ja__zh", "meaning_ja__vi",
        "note_ja", "false_friend", "ja_use", "ko_use", "vi_use",
    ]:
        words[column] = ""
    words["verified"] = "false"
    word_map = words.set_index("word_id", drop=False)

    output_batches = {task: accepted_batches(task) for task in EXPECTED_BATCHES}
    input_batches = {task: accepted_batches(task, inputs=True) for task in EXPECTED_BATCHES}
    task1_raw = keyed(flatten(output_batches[1]), "word_id", "task 1")
    task2_raw = keyed(flatten(output_batches[2]), "key", "task 2")
    task4_raw = keyed(flatten(output_batches[4]), "word_id", "task 4")
    task5_raw = keyed(flatten(output_batches[5]), "key", "task 5")
    task5_inputs = keyed(flatten(input_batches[5]), "key", "task-5 inputs")

    task1_review = load_csv(CONFIG / "task1_review.csv")
    task1 = apply_task1_review(task1_raw, words, task1_review)
    task1 = apply_task1_meaning_review(task1, words, load_csv(CONFIG / "task1_meaning_review.csv"))
    task2, cleared_vi = apply_task2_reviews(
        task2_raw, load_csv(CONFIG / "task2_review.csv"), load_csv(CONFIG / "task2_retrap.csv")
    )
    task4 = apply_task4_review(task4_raw, words, load_csv(CONFIG / "task4_review.csv"))
    task5 = apply_task5_review(task5_raw, task5_inputs, load_csv(CONFIG / "task5_review.csv"))
    ff_static, word_notes = config_from_prototype()

    if set(task1) - set(word_map.index) or set(task4) - set(word_map.index):
        raise ValueError("accepted word content refers to an unknown Stage 3 word")
    if len(task1) != 8555 or len(task2) != 3937 or len(task5) != 10400:
        raise ValueError("accepted Stage 4 item counts differ from the reviewed content")

    for word_id, item in task1.items():
        index = words.index[words["word_id"] == word_id][0]
        for lang in LANGS:
            words.at[index, f"meaning_ja__{lang}"] = str(item.get(f"meaning_ja__{lang}", ""))
        words.at[index, "verified"] = "true"

    # D63: the reviewed Vietnamese meaning is supplied by accepted task 2.
    for word_id in task1_review["word_id"]:
        meaning = task2_meaning(task2[word_id], "vi").get("meaning_ja", "")
        if not meaning:
            raise ValueError(f"task 2 did not supply the D63 Vietnamese meaning for {word_id}")
        words.loc[words["word_id"] == word_id, "meaning_ja__vi"] = meaning

    notes = {word_id: item["note_ja"] for word_id, item in task4.items()}
    for row in word_notes.to_dict(orient="records"):
        notes[row["word_id"]] = (
            row["note_ja"] + (" " + notes[row["word_id"]] if notes.get(row["word_id"]) else "")
        )
    for word_id, note in notes.items():
        words.loc[words["word_id"] == word_id, "note_ja"] = note

    usage_map = {key: usage_for(item) for key, item in task5.items()}
    for word_id, usage in usage_map.items():
        if word_id not in word_map.index:
            continue
        for lang, column in (("ja", "ja_use"), ("ko", "ko_use"), ("vi", "vi_use")):
            words.loc[words["word_id"] == word_id, column] = usage[lang]

    # Empty readings and task-5 usage decisions remove meanings fail-closed.
    for index, row in words.iterrows():
        for lang in LANGS:
            if not row[READING_COLUMN[lang]]:
                words.at[index, f"meaning_ja__{lang}"] = ""
        if not row["vi"]:
            # R1: a usage judgment about a Vietnamese reading that no longer exists
            # (吧 và, removed at the loader) is dropped with that reading.
            words.at[index, "vi_use"] = ""
        for lang in ("ja", "ko"):
            if row[f"{lang}_use"] in {"rare", "wrong_meaning"}:
                words.at[index, f"meaning_ja__{lang}"] = ""

    ff_sources: dict[str, pd.Series] = {
        row["word_id"]: row for _, row in words.iterrows()
    }
    ff_candidates_by_form = ff_candidates.set_index("form", drop=False)
    for form, row in ff_candidates_by_form.iterrows():
        source = row.copy()
        source["ja_alt"] = source["ko_alt"] = source["vi_alt"] = ""
        pinyin_values = split_multi(source["pinyin"])
        source["pinyin"] = pinyin_values[0] if pinyin_values else ""
        if form in cleared_vi:
            source["vi"] = source["gloss_vi"] = source["source_vi"] = ""
        ff_sources[form] = source

    # Resolve and validate all 12 frozen prototype entries before applying them.
    static_keys: dict[str, str] = {}
    for word in ff_static["word"].drop_duplicates():
        candidates = set(words.loc[(words["jp"] == word) | (words["trad"] == word), "word_id"])
        if word in ff_candidates_by_form.index:
            candidates.add(word)
        candidates &= set(task2)
        if len(candidates) != 1:
            raise ValueError(f"prototype FF word must resolve once: {word!r} -> {sorted(candidates)}")
        static_keys[word] = next(iter(candidates))
    for row in ff_static.to_dict(orient="records"):
        validate_static_reading(ff_sources[static_keys[row["word"]]], row)

    fixed_notes = dict(
        load_csv(CONFIG / "ff_fixed_notes.csv")[["lang", "text"]].itertuples(index=False, name=None)
    )
    if set(fixed_notes) != {"ja", "ko"}:
        raise ValueError("ff_fixed_notes.csv must contain exactly ja and ko")

    static_by_key: dict[str, list[dict[str, Any]]] = {}
    for row in ff_static.sort_values("row").to_dict(orient="records"):
        static_by_key.setdefault(static_keys[row["word"]], []).append(row)

    ff_rows: list[dict[str, Any]] = []
    active: dict[str, tuple[str, list[dict[str, Any]], dict[str, str]]] = {}
    empty_reading_drops = Counter()
    for key, item in task2.items():
        if key not in ff_sources:
            raise ValueError(f"task-2 key has no dictionary source: {key}")
        source = ff_sources[key]
        usage = usage_map.get(key, {"ja": "", "ko": "", "vi": ""})
        ff_langs = list(item["false_friend"])
        generated_by_lang = {row["lang"]: row for row in item["meanings"]}
        for lang in list(ff_langs):
            if lang not in generated_by_lang:
                raise ValueError(f"task-2 trap has no meaning row: {key}/{lang}")
            reading = source_reading(source, lang)
            if not reading:
                ff_langs.remove(lang)
                empty_reading_drops[lang] += 1
            elif lang in {"ja", "ko"} and usage[lang] in {"rare", "wrong_meaning"}:
                ff_langs.remove(lang)

        rows: list[dict[str, Any]] = []
        for lang in sorted(generated_by_lang, key=LANG_ORDER.get):
            reading = source_reading(source, lang)
            if not reading:
                continue
            use = usage.get(lang, "")
            if lang in {"ja", "ko"} and use == "wrong_meaning":
                continue
            if lang in {"ja", "ko"} and use == "rare":
                rows.append({
                    "lang": lang, "reading": reading, "reading_display": fixed_notes[lang],
                    "meaning_ja": "", "is_trap": False,
                })
            else:
                rows.append({
                    "lang": lang, "reading": reading, "reading_display": "",
                    "meaning_ja": generated_by_lang[lang]["meaning_ja"],
                    "is_trap": lang in ff_langs,
                })

        if key in static_by_key:
            static_langs = {row["lang"] for row in static_by_key[key]}
            rows = [row for row in rows if row["lang"] not in static_langs]
            for static in static_by_key[key]:
                rows.append({
                    "lang": static["lang"],
                    "reading": source_reading(source, static["lang"]),
                    "reading_display": static["reading_display"],
                    "meaning_ja": static["meaning_ja"],
                    "is_trap": bool(static["is_trap"]),
                })
        rows.sort(key=lambda row: LANG_ORDER[row["lang"]])
        traps = [row["lang"] for row in rows if row["is_trap"]]
        if traps:
            active[key] = (";".join(traps), rows, usage)

    words["false_friend"] = ""
    added_words: list[dict[str, Any]] = []
    ff_only_keys = set(active) - set(word_map.index)
    ff_only_forms = [form for form in ff_candidates["form"] if form in ff_only_keys]
    if len(ff_only_forms) != len(ff_only_keys):
        raise ValueError("active ff_only entries do not resolve once in ff_candidates row order")
    ff_only_id_keys = [f"x|{ff_sources[form]['trad']}" for form in ff_only_forms]
    ff_only_ids = assign_ids("word", ff_only_id_keys, "w", 5)
    for key, (false_friend, rows, usage) in active.items():
        if key in word_map.index:
            word_id = key
            words.loc[words["word_id"] == word_id, "false_friend"] = false_friend
        else:
            source = ff_sources[key]
            word_id = ff_only_ids[f"x|{source['trad']}"]
            meanings = {row["lang"]: row["meaning_ja"] for row in rows}
            added_words.append(make_ff_only_word(source, word_id, false_friend, meanings, usage))
        for row in rows:
            ff_rows.append({"word_id": word_id, **row})

    if len({row["word_id"] for row in added_words}) != len(added_words):
        raise ValueError("ff_only word identifiers are not unique")
    if added_words:
        words = pd.concat([words, pd.DataFrame(added_words)], ignore_index=True)
    words = words[WORD_COLUMNS]

    ff_meanings = pd.DataFrame(ff_rows, columns=FF_COLUMNS)
    if ff_meanings.duplicated(["word_id", "lang"]).any():
        raise ValueError("ff_meanings has duplicate (word_id, lang) keys")
    active_ids = set(words.loc[words["false_friend"] != "", "word_id"])
    if set(ff_meanings["word_id"]) != active_ids:
        raise ValueError("ff_meanings and words.false_friend entries differ")
    for word_id, group in ff_meanings.groupby("word_id"):
        expected = ";".join(group.loc[group["is_trap"], "lang"])
        actual = words.loc[words["word_id"] == word_id, "false_friend"].iloc[0]
        if expected != actual:
            raise ValueError(
                f"ff_meanings traps differ from words.false_friend for {word_id}: "
                f"{expected!r} != {actual!r}; "
                f"rows={words.loc[words['word_id'] == word_id, ['word_id', 'trad', 'false_friend']].to_dict(orient='records')}"
            )

    passage_review = load_csv(CONFIG / "task3_review.csv")
    validate_task3_review_batches(passage_review, output_batches[3])
    passage_rows: list[dict[str, Any]] = []
    cell_counts = Counter()
    for batch in sorted(output_batches[3]):
        if len(output_batches[3][batch]) != 1 or len(input_batches[3][batch]) != 1:
            raise ValueError(f"task-3 {batch} must contain one cell object")
        source = input_batches[3][batch][0]
        lang, level = source["language"], int(source["level"])
        kept = apply_task3_review(
            batch, output_batches[3][batch][0], passage_review, include_positions=True
        )
        for source_number, passage in kept:
            validate_passage(passage, lang, words)
            passage_rows.append({
                "id_key": f"{lang}|{level}|{source_number}", "lang": lang, "level": level,
                "translation_ja": passage["translation_ja"], "tokens": passage["tokens"],
            })
            cell_counts[(lang, level)] += 1
    if set(cell_counts) != {(lang, level) for lang in ("zh", "vi") for level in range(1, 8)}:
        raise ValueError("passage language/level cells are incomplete")
    if any(count < 5 for count in cell_counts.values()):
        raise ValueError("a passage language/level cell has fewer than five passages")
    passage_ids = assign_ids("passage", (row["id_key"] for row in passage_rows), "p", 4)
    passages = pd.DataFrame([
        {"passage_id": passage_ids[row.pop("id_key")], **row} for row in passage_rows
    ], columns=PASSAGE_COLUMNS)
    if passages["passage_id"].duplicated().any():
        raise ValueError("passages has duplicate passage_id values")

    for frame in (words, ff_meanings):
        for column in frame.select_dtypes(include=["object", "string"]).columns:
            frame[column] = frame[column].map(lambda value: clean(value) if isinstance(value, str) else value)
        require_nfc(frame)
    for row in passages.to_dict(orient="records"):
        validate_recursive_nfc(row)

    bool_columns = ["ja_common", "card_eligible", "syl_aligned", "verified"]
    for column in bool_columns:
        words[column] = words[column].map(
            lambda value: value if isinstance(value, bool) else str(value).lower() == "true"
        )
    ff_meanings["is_trap"] = ff_meanings["is_trap"].astype(bool)
    words["level"] = pd.to_numeric(words["level"], errors="coerce").astype("Int64")
    words["freq_vi"] = pd.to_numeric(words["freq_vi"], errors="coerce").astype("Int64")
    passages["level"] = passages["level"].astype(int)
    if words["word_id"].duplicated().any() or set(words.columns) != set(WORD_COLUMNS):
        raise ValueError("final words schema or key is invalid")
    if any("reason" in column for frame in (words, ff_meanings, passages) for column in frame.columns):
        raise ValueError("review reason text must not enter final tables")

    write_csv(words, FINAL / "words.csv", bool_columns=bool_columns)
    write_json(words.replace("", pd.NA), FINAL / "words.json")
    write_csv(ff_meanings, FINAL / "ff_meanings.csv", bool_columns=["is_trap"])
    write_json(ff_meanings.replace("", pd.NA), FINAL / "ff_meanings.json")
    passages_csv = passages.copy()
    passages_csv["tokens"] = passages_csv["tokens"].map(
        lambda value: json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    )
    write_csv(passages_csv, FINAL / "passages.csv")
    write_json(passages.replace("", pd.NA), FINAL / "passages.json")

    summary = {
        "words": len(words), "ff_only_words": len(added_words),
        "false_friend_entries": len(active_ids), "ff_meanings": len(ff_meanings),
        "passages": len(passages), "empty_reading_traps_dropped": dict(empty_reading_drops),
        "task1_verified": int(words["verified"].sum()),
    }
    (FINAL / "stage4_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
