"""Deterministic Stage 4 input builders."""

from __future__ import annotations

import hashlib
import json
import random
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from pipeline.stage3_match import collapse_iy, korean_base_candidates


ROOT = Path(__file__).resolve().parents[2]
WORDS_PATH = ROOT / "data" / "final" / "words.csv"
CHARS_PATH = ROOT / "data" / "final" / "chars.csv"
WORD_CHARS_PATH = ROOT / "data" / "final" / "word_chars.csv"
FF_PATH = ROOT / "data" / "staging" / "ff_candidates.csv"
TASK1_REVIEW_PATH = ROOT / "config" / "task1_review.csv"

TASK1_FIELDS = [
    "word_id", "trad", "simp", "jp", "ja", "ja_alt", "ja_common", "ko",
    "ko_alt", "pinyin", "vi", "vi_alt", "source_vi", "pos", "level",
    "gloss_en", "gloss_ja_en", "gloss_ko", "gloss_vi",
]
WORD_CONTEXT_FIELDS = [
    "word_id", "trad", "simp", "jp", "ja", "ko", "pinyin", "vi",
    "gloss_en", "gloss_ja_en", "gloss_ko", "gloss_vi", "source_vi",
]
FIXED_TEST_FORMS = [
    "學", "國", "茶", "行", "生", "樂", "經濟", "大學", "勉強", "手紙",
    "銀行", "發展", "歷史", "博士", "新聞", "注意", "主義", "學習", "心理", "越南",
]
PILOT_TASK1_REQUIRED = ["越南", "自己", "容易", "小姐", "老公"]
PILOT_TASK2_REQUIRED = ["自己", "手紙", "大丈夫", "勉強", "新聞"]
PILOT_TASK4_REQUIRED = ["牡丹", "貿易", "音樂"]
TASK3_SAMPLE_SEED = 4103


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8", keep_default_na=False, dtype=str)


def load_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return load_csv(WORDS_PATH), load_csv(CHARS_PATH), load_csv(WORD_CHARS_PATH), load_csv(FF_PATH)


def _clean(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value.strip())
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    return value


def _records(frame: pd.DataFrame, fields: list[str]) -> list[dict[str, Any]]:
    missing = set(fields) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing input columns: {sorted(missing)}")
    return [_clean(row) for row in frame[fields].to_dict(orient="records")]


def chunked(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def build_task1_items(words: pd.DataFrame | None = None) -> list[dict[str, Any]]:
    words = load_csv(WORDS_PATH) if words is None else words.copy()
    eligible = words.loc[words["card_eligible"].str.lower() == "true"].sort_values("word_id")
    return _records(eligible, TASK1_FIELDS)


def build_task1_batches(words: pd.DataFrame | None = None) -> list[list[dict[str, Any]]]:
    return chunked(build_task1_items(words), 100)


def _take_form(rows: pd.DataFrame, form: str) -> pd.DataFrame:
    match = rows.loc[rows["trad"] == form].sort_values("word_id")
    return match.iloc[:1]


def build_pilot_task1(words: pd.DataFrame | None = None) -> list[dict[str, Any]]:
    words = load_csv(WORDS_PATH) if words is None else words.copy()
    eligible = words.loc[words["card_eligible"].str.lower() == "true"].sort_values("word_id")
    chosen: list[str] = []

    def add_rows(rows: pd.DataFrame, limit: int | None = None) -> None:
        for word_id in rows["word_id"]:
            if word_id not in chosen:
                chosen.append(word_id)
                if limit is not None and len(chosen) >= limit:
                    return

    for form in FIXED_TEST_FORMS + PILOT_TASK1_REQUIRED:
        add_rows(_take_form(eligible, form))

    composed = eligible.loc[
        (eligible["source_vi"] == "composed_attested") & (eligible["trad"].str.len() > 1)
    ]
    composed_ids = list(composed["word_id"])
    random.Random(4101).shuffle(composed_ids)
    add_rows(composed.set_index("word_id").loc[composed_ids[:40]].reset_index())

    rng = random.Random(4102)
    by_level: dict[str, list[str]] = {}
    for level in map(str, range(1, 8)):
        ids = [i for i in eligible.loc[eligible["level"] == level, "word_id"] if i not in chosen]
        rng.shuffle(ids)
        by_level[level] = ids
    while len(chosen) < 100:
        progressed = False
        for level in map(str, range(1, 8)):
            if by_level[level] and len(chosen) < 100:
                chosen.append(by_level[level].pop())
                progressed = True
        if not progressed:
            break
    if len(chosen) != 100:
        raise ValueError(f"Pilot task 1 needs 100 words, found {len(chosen)}")
    selected = eligible.set_index("word_id").loc[chosen].reset_index()
    return _records(selected, TASK1_FIELDS)


def read_jsonl_files(paths: Iterable[Path]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for path in sorted(paths):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"{path}:{number}: expected a JSON object")
                result.append(_clean(value))
    return result


def _task1_map(outputs: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in outputs:
        key = str(item.get("word_id", ""))
        if not key or key in result:
            raise ValueError(f"Duplicate or empty task-1 key: {key!r}")
        result[key] = item
    return result


def _task1_review() -> pd.DataFrame:
    review = load_csv(TASK1_REVIEW_PATH)
    required = {
        "word_id", "trad", "vi", "vi_check_task1", "vi_check_review",
        "gloss_vi_task2", "reason",
    }
    missing = required - set(review.columns)
    if missing:
        raise ValueError(f"Task-1 review is missing columns: {sorted(missing)}")
    if review["word_id"].eq("").any() or review["word_id"].duplicated().any():
        raise ValueError("Task-1 review has an empty or duplicate word_id")
    invalid_gloss = set(review["gloss_vi_task2"]) - {"keep", "blank"}
    if invalid_gloss:
        raise ValueError(f"Task-1 review has invalid gloss_vi_task2 values: {sorted(invalid_gloss)}")
    return review


def apply_task1_review(
    outputs: Iterable[dict[str, Any]], words: pd.DataFrame | None = None,
) -> list[dict[str, Any]]:
    """Apply D63 without modifying the generated task-1 files."""
    output_list = [_clean(dict(item)) for item in outputs]
    output_map = _task1_map(output_list)
    words = load_csv(WORDS_PATH) if words is None else words.copy()
    if words["word_id"].eq("").any() or words["word_id"].duplicated().any():
        raise ValueError("Frozen words table has an empty or duplicate word_id")
    word_map = words.set_index("word_id", drop=False)

    for row in _task1_review().to_dict(orient="records"):
        word_id = row["word_id"]
        if word_id not in word_map.index:
            raise ValueError(f"Task-1 review word_id is missing from frozen words: {word_id}")
        if word_id not in output_map:
            raise ValueError(f"Task-1 review word_id is missing from task-1 output: {word_id}")
        word = word_map.loc[word_id]
        if word["trad"] != row["trad"] or word["vi"] != row["vi"]:
            raise ValueError(
                f"Task-1 review frozen-word mismatch for {word_id}: "
                f"expected trad={word['trad']!r}, vi={word['vi']!r}"
            )
        result = output_map[word_id]
        if result.get("vi_check") != row["vi_check_task1"]:
            raise ValueError(
                f"Task-1 review generated-output mismatch for {word_id}: "
                f"expected vi_check={row['vi_check_task1']!r}, "
                f"got {result.get('vi_check')!r}"
            )
        result["vi_check"] = row["vi_check_review"]
    return output_list


def _word_task2_item(row: pd.Series, result: dict[str, Any]) -> dict[str, Any]:
    item = {field: row[field] for field in WORD_CONTEXT_FIELDS}
    item["key"] = row["word_id"]
    item["task1_meanings"] = {
        lang: result.get(f"meaning_ja__{lang}", "") for lang in ("ja", "ko", "zh", "vi")
    }
    if result.get("vi_check") == "different_word":
        item["vi"] = ""
        item["gloss_vi"] = ""
    return _clean(item)


def _ff_task2_item(row: pd.Series) -> dict[str, Any]:
    item = {field: row.get(field, "") for field in (
        "form", "trad", "simp", "ja", "gloss_ja_en", "ko", "pinyin",
        "gloss_en", "vi", "gloss_vi",
    )}
    item["key"] = row["form"]
    item["source"] = "ff_candidates"
    return _clean(item)


def build_task2_items(
    task1_outputs: Iterable[dict[str, Any]],
    words: pd.DataFrame | None = None,
    ff: pd.DataFrame | None = None,
) -> list[dict[str, Any]]:
    words = load_csv(WORDS_PATH) if words is None else words.copy()
    ff = load_csv(FF_PATH) if ff is None else ff.copy()
    result_map = _task1_map(task1_outputs)
    review_map = _task1_review().set_index("word_id")
    selected_ids = {
        word_id for word_id, result in result_map.items() if result.get("meanings_differ") is True
    }
    selected_ids.update(words.loc[words["trad"] == "自己", "word_id"])
    selected_ids.update(review_map.index)
    word_by_id = words.set_index("word_id", drop=False)
    items: list[dict[str, Any]] = []
    for word_id in sorted(selected_ids):
        if word_id not in word_by_id.index or word_id not in result_map:
            continue
        item = _word_task2_item(word_by_id.loc[word_id], result_map[word_id])
        if word_id in review_map.index and review_map.loc[word_id, "gloss_vi_task2"] == "blank":
            item["gloss_vi"] = ""
        items.append(item)
    items.extend(_ff_task2_item(row) for _, row in ff.sort_values("form").iterrows())
    keys = [item["key"] for item in items]
    if len(keys) != len(set(keys)):
        raise ValueError("Task 2 keys are not unique")
    return items


def build_task2_batches(task1_outputs: Iterable[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    return chunked(build_task2_items(task1_outputs), 50)


def build_pilot_task2(
    pilot_task1_outputs: Iterable[dict[str, Any]],
    words: pd.DataFrame | None = None,
    ff: pd.DataFrame | None = None,
) -> list[dict[str, Any]]:
    words = load_csv(WORDS_PATH) if words is None else words.copy()
    ff = load_csv(FF_PATH) if ff is None else ff.copy()
    result_map = _task1_map(pilot_task1_outputs)
    word_by_id = words.set_index("word_id", drop=False)
    required: list[dict[str, Any]] = []
    for form in PILOT_TASK2_REQUIRED:
        current = words.loc[(words["trad"] == form) & words["word_id"].isin(result_map)].sort_values("word_id")
        if not current.empty:
            row = current.iloc[0]
            required.append(_word_task2_item(row, result_map[row["word_id"]]))
            continue
        candidate = ff.loc[ff["form"] == form]
        if not candidate.empty:
            required.append(_ff_task2_item(candidate.iloc[0]))
    required_keys = {item["key"] for item in required}
    pool = [_ff_task2_item(row) for _, row in ff.sort_values("form").iterrows() if row["form"] not in required_keys]
    random.Random(4201).shuffle(pool)
    result = required + pool[:50 - len(required)]
    if len(result) != 50:
        raise ValueError(f"Pilot task 2 needs 50 items, found {len(result)}")
    return result


def _task3_candidates(
    lang: str,
    level: int,
    task1_outputs: Iterable[dict[str, Any]],
    words: pd.DataFrame,
) -> list[dict[str, Any]]:
    result_map = _task1_map(task1_outputs)
    reading = "pinyin" if lang == "zh" else "vi"
    meaning_key = f"meaning_ja__{lang}"
    rows: list[dict[str, Any]] = []
    for _, row in words.sort_values("word_id").iterrows():
        result = result_map.get(row["word_id"])
        if result is None or not row[reading] or not row["level"]:
            continue
        if int(row["level"]) > level or not result.get(meaning_key):
            continue
        if lang == "vi":
            confidence_ok = (
                result.get("confidence") == "high" or result.get("low_reason") == "ko_rare"
            )
            if result.get("vi_check") != "same_word" or not confidence_ok:
                continue
        display = row["simp"] or row["trad"] if lang == "zh" else row["vi"]
        rows.append({
            "word_id": row["word_id"], "display": display,
            "meaning_ja": result[meaning_key], "level": int(row["level"]),
        })
    current = [row for row in rows if row["level"] == level]
    lower = [row for row in rows if row["level"] < level]
    rng = random.Random(TASK3_SAMPLE_SEED + level * 10 + (0 if lang == "zh" else 1))
    rng.shuffle(current)
    rng.shuffle(lower)
    return current[:300] + lower[:200]


def build_task3_batches(
    task1_outputs: Iterable[dict[str, Any]], words: pd.DataFrame | None = None,
) -> list[list[dict[str, Any]]]:
    words = load_csv(WORDS_PATH) if words is None else words.copy()
    outputs = list(task1_outputs)
    batches: list[list[dict[str, Any]]] = []
    for lang in ("zh", "vi"):
        for level in range(1, 8):
            batches.append([{
                "language": lang, "level": level, "seed": TASK3_SAMPLE_SEED,
                "words": _task3_candidates(lang, level, outputs, words),
            }])
    return batches


def build_pilot_task3(
    lang: str, level: int, pilot_task1_outputs: Iterable[dict[str, Any]],
    words: pd.DataFrame | None = None,
) -> list[dict[str, Any]]:
    words = load_csv(WORDS_PATH) if words is None else words.copy()
    candidates = _task3_candidates(lang, level, list(pilot_task1_outputs), words)
    if len(candidates) < 3:
        raise ValueError(f"Pilot task 3 {lang}/{level} has only {len(candidates)} linkable words")
    return [{"language": lang, "level": level, "seed": TASK3_SAMPLE_SEED, "words": candidates}]


def build_task4_items(
    words: pd.DataFrame | None = None,
    chars: pd.DataFrame | None = None,
    word_chars: pd.DataFrame | None = None,
    task1_outputs: Iterable[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if words is None or chars is None or word_chars is None:
        loaded_words, loaded_chars, loaded_word_chars, _ = load_tables()
        words = loaded_words if words is None else words
        chars = loaded_chars if chars is None else chars
        word_chars = loaded_word_chars if word_chars is None else word_chars
    word_cols = words[["word_id", "trad", "ko", "vi", "card_eligible", "level"]]
    char_cols = chars[["char_id", "key_char", "ko", "vi", "source_vi"]].rename(
        columns={"key_char": "char", "ko": "ko_primary", "vi": "vi_primary"}
    )
    merged = word_chars.merge(char_cols, on="char_id", how="left", validate="many_to_one")
    merged = merged.merge(word_cols, on="word_id", how="left", validate="many_to_one")
    merged["eligible_sort"] = (merged["card_eligible"].str.lower() != "true").astype(int)
    merged["level_sort"] = pd.to_numeric(merged["level"], errors="coerce").fillna(99)
    example_index: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    ordered = merged.sort_values(["eligible_sort", "level_sort", "word_id"])
    seen_examples: set[tuple[str, str, str, str]] = set()
    for _, example in ordered.iterrows():
        for lang, column in (("ko", "ko_base"), ("vi", "vi_syllable")):
            reading = example[column]
            marker = (example["char_id"], lang, reading, example["word_id"])
            if reading and marker not in seen_examples:
                seen_examples.add(marker)
                example_index[(example["char_id"], lang, reading)].append({
                    "word_id": example["word_id"], "trad": example["trad"], "reading": reading,
                })
    diffs = merged.loc[
        ((merged["ko_base"] != "") & (merged["ko_primary"] != "") & (merged["ko_base"] != merged["ko_primary"]))
        | ((merged["vi_syllable"] != "") & (merged["vi_primary"] != "") & (merged["vi_syllable"] != merged["vi_primary"]))
    ]
    task1_map = _task1_map(task1_outputs) if task1_outputs is not None else None
    items: list[dict[str, Any]] = []
    for word_id, group in diffs.groupby("word_id", sort=True):
        word = group.iloc[0]
        trad = str(word["trad"])
        ko = str(word["ko"])
        ko_is_aligned = len(trad) == len(ko)
        positions: list[dict[str, Any]] = []
        for _, row in group.sort_values("position").iterrows():
            for lang, here_col, primary_col in (
                ("ko", "ko_base", "ko_primary"), ("vi", "vi_syllable", "vi_primary")
            ):
                here, primary = row[here_col], row[primary_col]
                if not here or not primary or here == primary:
                    continue
                if lang == "ko" and ko_is_aligned:
                    index = int(row["position"]) - 1
                    written_syllable = ko[index]
                    if (
                        written_syllable != here
                        and primary in korean_base_candidates(written_syllable, index)
                    ):
                        continue
                    if here != written_syllable:
                        raise ValueError(
                            f"Task 4 Korean reading mismatch for {word_id} {trad} at "
                            f"position {index + 1}: ko={written_syllable}, ko_base={here}"
                        )
                elif lang == "vi":
                    if row["source_vi"] == "unihan_unverified":
                        continue
                    if len(collapse_iy([here, primary])) == 1:
                        continue
                    if task1_map is not None and task1_map.get(word_id, {}).get("vi_check") != "same_word":
                        continue
                primary_examples = [
                    {"trad": ex["trad"], "reading": ex["reading"]}
                    for ex in example_index.get((row["char_id"], lang, primary), [])
                    if ex["word_id"] != word_id
                ][:3]
                here_examples = [
                    {"trad": ex["trad"], "reading": ex["reading"]}
                    for ex in example_index.get((row["char_id"], lang, here), [])
                    if ex["word_id"] != word_id
                ][:3]
                positions.append({
                    "position": int(row["position"]), "char": row["char"], "lang": lang,
                    "reading_here": here, "primary": primary,
                    "examples_primary": primary_examples,
                    "examples_here": here_examples,
                })
        if not positions:
            continue
        items.append(_clean({
            "word_id": word_id, "trad": trad, "ko": ko, "vi": word["vi"],
            "differences": positions,
        }))
    return items


def build_task4_batches(
    task1_outputs: Iterable[dict[str, Any]] | None = None,
) -> list[list[dict[str, Any]]]:
    return chunked(build_task4_items(task1_outputs=task1_outputs), 50)


def build_pilot_task4() -> list[dict[str, Any]]:
    items = build_task4_items()
    required = [item for form in PILOT_TASK4_REQUIRED for item in items if item["trad"] == form]
    required_ids = {item["word_id"] for item in required}
    pool = [item for item in items if item["word_id"] not in required_ids]
    random.Random(4401).shuffle(pool)
    result = required + pool[:50 - len(required)]
    if len(result) != 50:
        raise ValueError(f"Pilot task 4 needs 50 items, found {len(result)}")
    return result


def jsonl_text(items: Iterable[dict[str, Any]]) -> str:
    return "".join(json.dumps(_clean(item), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for item in items)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_jsonl(path: Path, items: Iterable[dict[str, Any]]) -> str:
    text = jsonl_text(items)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return sha256_text(text)


def task_batches(task: int, task1_outputs: Iterable[dict[str, Any]] | None = None) -> list[list[dict[str, Any]]]:
    if task == 1:
        return build_task1_batches()
    if task == 2:
        if task1_outputs is None:
            raise ValueError("Task 2 requires accepted/generated task-1 output")
        return build_task2_batches(apply_task1_review(task1_outputs))
    if task == 3:
        if task1_outputs is None:
            raise ValueError("Task 3 requires accepted/generated task-1 output")
        return build_task3_batches(apply_task1_review(task1_outputs))
    if task == 4:
        reviewed = apply_task1_review(task1_outputs) if task1_outputs is not None else None
        return build_task4_batches(reviewed)
    raise ValueError(f"Unknown task: {task}")
