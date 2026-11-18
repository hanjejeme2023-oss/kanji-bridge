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
FF_MEANINGS_PATH = ROOT / "data" / "final" / "ff_meanings.csv"
TASK1_REVIEW_PATH = ROOT / "config" / "task1_review.csv"
TASK2_REVIEW_PATH = ROOT / "config" / "task2_review.csv"
ACCEPTED = ROOT / "content" / "accepted"

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
TASK5_FIELDS = [
    "key", "checks", "trad", "ja", "ko", "pinyin", "vi", "gloss_en",
    "gloss_ja_en", "gloss_ko", "gloss_vi", "meaning_ja__ja",
    "meaning_ja__ko", "meaning_ja__zh", "meaning_ja__vi",
]
TASK6_ZH_FIELDS = [
    "key", "target", "target_pinyin", "trad", "meaning_ja", "is_trap",
    "contrast_meaning_ja", "level", "pos",
]
TASK6_VI_FIELDS = [
    "key", "target", "trad", "meaning_ja", "is_trap",
    "contrast_meaning_ja", "vi_use", "level",
]
TASK6_NOTE_FIELDS = [
    "key", "char", "simp", "jp", "pinyin", "vi", "meaning_en",
    "zh_examples", "vi_examples", "vi_single_use", "reason",
]
TASK6_EXPECTED_COUNTS = {
    "zh_card": 5783, "zh_ff": 565, "vi_card": 4051, "vi_ff": 142,
    "note": 623,
}


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


def read_accepted_outputs(task: int) -> list[dict[str, Any]]:
    paths = sorted((ACCEPTED / f"task{task}").glob("b*.jsonl"))
    if not paths:
        raise ValueError(f"No accepted task-{task} outputs found")
    return read_jsonl_files(paths)


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


def _task2_meanings_after_review(
    outputs: Iterable[dict[str, Any]],
) -> tuple[dict[str, dict[str, str]], set[str]]:
    """Return accepted task-2 meanings with the D64/D65 overlay applied fail-closed."""
    meaning_maps: dict[str, dict[str, str]] = {}
    trap_maps: dict[str, dict[str, bool]] = {}
    for item in outputs:
        key = str(item.get("key", ""))
        if not key or key in meaning_maps:
            raise ValueError(f"Duplicate or empty task-2 key: {key!r}")
        meanings = item.get("meanings")
        if not isinstance(meanings, list):
            raise ValueError(f"Task-2 meanings are not a list for {key}")
        meaning_maps[key] = {}
        trap_maps[key] = {}
        for meaning in meanings:
            lang = str(meaning.get("lang", ""))
            if not lang or lang in meaning_maps[key]:
                raise ValueError(f"Duplicate or empty task-2 language for {key}: {lang!r}")
            meaning_maps[key][lang] = str(meaning.get("meaning_ja", ""))
            trap_maps[key][lang] = bool(meaning.get("is_trap"))

    review = load_csv(TASK2_REVIEW_PATH)
    required = {
        "key", "lang", "action", "meaning_ja_generated", "is_trap_generated",
        "meaning_ja_review", "false_friend_review", "reason",
    }
    missing = required - set(review.columns)
    if missing:
        raise ValueError(f"Task-2 review is missing columns: {sorted(missing)}")
    if review[["key", "lang"]].duplicated().any() or review["key"].eq("").any():
        raise ValueError("Task-2 review has an empty or duplicate (key, lang)")
    cleared_vi: set[str] = set()
    for row in review.to_dict(orient="records"):
        key, lang, action = row["key"], row["lang"], row["action"]
        if key not in meaning_maps or lang not in meaning_maps[key]:
            raise ValueError(f"Task-2 review target is missing from accepted output: {key}/{lang}")
        if meaning_maps[key][lang] != row["meaning_ja_generated"]:
            raise ValueError(f"Task-2 review meaning mismatch for {key}/{lang}")
        expected_trap = str(trap_maps[key][lang]).lower()
        if expected_trap != row["is_trap_generated"].lower():
            raise ValueError(f"Task-2 review trap mismatch for {key}/{lang}")
        if action == "same_as_ja":
            if lang != "ko" or not row["meaning_ja_review"]:
                raise ValueError(f"Invalid same_as_ja review row for {key}/{lang}")
            meaning_maps[key][lang] = row["meaning_ja_review"]
        elif action == "set_meaning":
            # R1 (D78 item 3): reviewed meaning text; the trap flag is unchanged.
            if not row["meaning_ja_review"]:
                raise ValueError(f"Invalid set_meaning review row for {key}/{lang}")
            meaning_maps[key][lang] = row["meaning_ja_review"]
        elif action == "clear_vi":
            if lang != "vi" or row["meaning_ja_review"]:
                raise ValueError(f"Invalid clear_vi review row for {key}/{lang}")
            meaning_maps[key][lang] = ""
            cleared_vi.add(key)
        else:
            raise ValueError(f"Unknown task-2 review action for {key}/{lang}: {action!r}")
    return meaning_maps, cleared_vi


def build_task5_items(
    words: pd.DataFrame | None = None,
    ff: pd.DataFrame | None = None,
    task1_outputs: Iterable[dict[str, Any]] | None = None,
    task2_outputs: Iterable[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build the D67 usage-check inputs from accepted Stage 4 content."""
    words = load_csv(WORDS_PATH) if words is None else words.copy()
    ff = load_csv(FF_PATH) if ff is None else ff.copy()
    accepted1 = read_accepted_outputs(1) if task1_outputs is None else list(task1_outputs)
    accepted2 = read_accepted_outputs(2) if task2_outputs is None else list(task2_outputs)
    task1_map = _task1_map(apply_task1_review(accepted1, words))
    task2_meanings, cleared_vi = _task2_meanings_after_review(accepted2)

    items: list[dict[str, Any]] = []
    eligible = words.loc[words["card_eligible"].str.lower() == "true"].sort_values("word_id")
    for _, row in eligible.iterrows():
        multi = len(str(row["trad"])) > 1
        checks: list[str] = []
        if multi and row["ja"] and row["ja_common"].lower() == "false":
            checks.append("ja")
        if multi and row["ko"]:
            checks.append("ko")
        if row["vi"]:
            checks.append("vi")
        if not checks:
            continue
        word_id = row["word_id"]
        if word_id not in task1_map:
            raise ValueError(f"Task 5 word is missing accepted task-1 output: {word_id}")
        meanings = {
            lang: str(task1_map[word_id].get(f"meaning_ja__{lang}", ""))
            for lang in ("ja", "ko", "zh", "vi")
        }
        meanings.update(task2_meanings.get(word_id, {}))
        item = {
            "key": word_id, "checks": checks,
            "trad": row["trad"], "ja": row["ja"], "ko": row["ko"],
            "pinyin": row["pinyin"], "vi": row["vi"],
            "gloss_en": row["gloss_en"], "gloss_ja_en": row["gloss_ja_en"],
            "gloss_ko": row["gloss_ko"],
            "gloss_vi": row["gloss_vi"] if "vi" in checks else "",
            **{f"meaning_ja__{lang}": meanings[lang] for lang in ("ja", "ko", "zh", "vi")},
        }
        items.append(_clean(item))

    for _, row in ff.loc[ff["ko"] != ""].sort_values("form").iterrows():
        key = row["form"]
        if key not in task2_meanings:
            raise ValueError(f"Task 5 ff row is missing accepted task-2 output: {key}")
        meanings = task2_meanings[key]
        vi = "" if key in cleared_vi else row.get("vi", "")
        item = {
            "key": key, "checks": ["ko"],
            "trad": row.get("trad", ""), "ja": row.get("ja", ""),
            "ko": row["ko"], "pinyin": row.get("pinyin", ""), "vi": vi,
            "gloss_en": row.get("gloss_en", ""),
            "gloss_ja_en": row.get("gloss_ja_en", ""), "gloss_ko": "", "gloss_vi": "",
            **{f"meaning_ja__{lang}": meanings.get(lang, "") for lang in ("ja", "ko", "zh", "vi")},
        }
        items.append(_clean(item))

    keys = [item["key"] for item in items]
    if len(keys) != len(set(keys)):
        raise ValueError("Task 5 keys are not unique")
    if any(list(item) != TASK5_FIELDS for item in items):
        raise ValueError("Task 5 input field order differs from the D67 contract")
    return items


def build_task5_batches() -> list[list[dict[str, Any]]]:
    return chunked(build_task5_items(), 100)


def _level_sort(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["_level_sort"] = pd.to_numeric(result["level"], errors="coerce").fillna(99)
    return result.sort_values(["_level_sort", "word_id"], kind="stable").drop(columns="_level_sort")


def _task6_contrast(ff_by_word: dict[str, list[dict[str, Any]]], word_id: str, lang: str) -> str:
    rows = ff_by_word.get(word_id, [])
    for contrast_lang in ("ja", "ko", "zh", "vi"):
        if contrast_lang == lang:
            continue
        for row in rows:
            if (row["lang"] == contrast_lang and not row["is_trap"]
                    and row["meaning_ja"]):
                return row["meaning_ja"]
    return ""


def _task6_sentence_items(
    words: pd.DataFrame, ff_meanings: pd.DataFrame, lang: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if lang not in {"zh", "vi"}:
        raise ValueError(f"Unknown task-6 sentence language: {lang}")
    ff_lang = ff_meanings.loc[ff_meanings["lang"] == lang].copy()
    if ff_lang["word_id"].eq("").any() or ff_lang["word_id"].duplicated().any():
        raise ValueError(f"Task 6 {lang} ff_meanings has an empty or duplicate word_id")
    ff_rows: dict[str, dict[str, Any]] = {}
    all_ff_by_word: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ff_meanings.to_dict(orient="records"):
        cleaned = _clean(row)
        cleaned["is_trap"] = str(cleaned["is_trap"]).lower() == "true"
        all_ff_by_word[cleaned["word_id"]].append(cleaned)
        if cleaned["lang"] == lang:
            ff_rows[cleaned["word_id"]] = cleaned

    multi = words["trad"].str.len() > 1
    eligible = words["card_eligible"].str.lower() == "true"
    if lang == "zh":
        card_mask = multi & eligible & words["origin"].isin(["hsk", "both"]) & words["pinyin"].ne("")
        meaning_field = "meaning_ja__zh"
    else:
        card_mask = multi & eligible & words["vi"].ne("")
        meaning_field = "meaning_ja__vi"
    cards = _level_sort(words.loc[card_mask])
    items: list[dict[str, Any]] = []
    covered: set[str] = set()
    for row in cards.to_dict(orient="records"):
        word_id = row["word_id"]
        ff = ff_rows.get(word_id)
        is_covered = ff is not None and row[meaning_field] == ff["meaning_ja"]
        if is_covered:
            covered.add(word_id)
        is_trap = bool(ff["is_trap"]) if is_covered else False
        common = {
            "key": f"{word_id}:{lang}:card",
            "target": row["simp"] if lang == "zh" else row["vi"],
            "trad": row["trad"],
            "meaning_ja": row[meaning_field],
            "is_trap": is_trap,
            "contrast_meaning_ja": (
                _task6_contrast(all_ff_by_word, word_id, lang) if is_trap else ""
            ),
        }
        if lang == "zh":
            item = {
                "key": common["key"], "target": common["target"],
                "target_pinyin": row["pinyin"], "trad": common["trad"],
                "meaning_ja": common["meaning_ja"], "is_trap": common["is_trap"],
                "contrast_meaning_ja": common["contrast_meaning_ja"],
                "level": row["level"], "pos": row["pos"],
            }
        else:
            item = {
                **common, "vi_use": row["vi_use"], "level": row["level"],
            }
        items.append(_clean(item))

    word_map = words.set_index("word_id", drop=False)
    ff_items: list[dict[str, Any]] = []
    for word_id in sorted(set(ff_rows) - covered):
        if word_id not in word_map.index:
            raise ValueError(f"Task 6 {lang} false-friend word is missing: {word_id}")
        row = word_map.loc[word_id]
        ff = ff_rows[word_id]
        reading_field = "pinyin" if lang == "zh" else "vi"
        if row[reading_field] != ff["reading"]:
            raise ValueError(
                f"Task 6 {lang} reading mismatch for {word_id}: "
                f"{row[reading_field]!r} != {ff['reading']!r}"
            )
        common = {
            "key": f"{word_id}:{lang}:ff",
            "target": row["simp"] if lang == "zh" else row["vi"],
            "trad": row["trad"], "meaning_ja": ff["meaning_ja"],
            "is_trap": bool(ff["is_trap"]),
            "contrast_meaning_ja": (
                _task6_contrast(all_ff_by_word, word_id, lang) if ff["is_trap"] else ""
            ),
        }
        if lang == "zh":
            item = {
                "key": common["key"], "target": common["target"],
                "target_pinyin": row["pinyin"], "trad": common["trad"],
                "meaning_ja": common["meaning_ja"], "is_trap": common["is_trap"],
                "contrast_meaning_ja": common["contrast_meaning_ja"],
                "level": row["level"], "pos": row["pos"],
            }
        else:
            item = {**common, "vi_use": row["vi_use"], "level": row["level"]}
        ff_items.append(_clean(item))
    return items, ff_items


def _task6_note_items(
    words: pd.DataFrame, chars: pd.DataFrame, word_chars: pd.DataFrame,
) -> list[dict[str, Any]]:
    char_words = word_chars.merge(
        words, on="word_id", how="left", validate="many_to_one", suffixes=("", "_word")
    )
    if char_words["trad"].eq("").any():
        raise ValueError("Task 6 note examples contain an unknown word_id")
    matches_by_char = {
        char_id: group.copy() for char_id, group in char_words.groupby("char_id", sort=False)
    }

    single_cards = words.loc[
        (words["card_eligible"].str.lower() == "true") & (words["trad"].str.len() == 1)
    ].sort_values(["level", "word_id"], kind="stable")
    single_by_char: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in single_cards.to_dict(orient="records"):
        single_by_char[row["trad"]].append(row)

    glyph_chars = set(chars.loc[
        ~((chars["jp"] == chars["key_char"]) & (chars["key_char"] == chars["simp"])),
        "key_char",
    ])
    glyph_chars.update(single_by_char)

    items: list[dict[str, Any]] = []
    ordered_chars = chars.copy()
    ordered_chars["_level_sort"] = pd.to_numeric(ordered_chars["level"], errors="coerce").fillna(99)
    ordered_chars = ordered_chars.sort_values(["_level_sort", "char_id"], kind="stable")
    for char in ordered_chars.to_dict(orient="records"):
        if char["key_char"] not in glyph_chars:
            continue
        matches = matches_by_char.get(char["char_id"], char_words.iloc[:0]).copy()
        matches = matches.loc[matches["trad"].str.len() > 1]
        zh = matches.loc[
            matches["origin"].isin(["hsk", "both"])
            & matches["pinyin"].ne("") & matches["pinyin_syllable"].ne("")
        ].copy()
        zh["_level_sort"] = pd.to_numeric(zh["level"], errors="coerce").fillna(99)
        zh = zh.sort_values(["_level_sort", "word_id"], kind="stable")
        zh_examples = [
            {"simp": row["simp"], "pinyin": row["pinyin"]}
            for row in zh.head(3).to_dict(orient="records")
        ]

        vi = matches.loc[
            (matches["card_eligible"].str.lower() == "true")
            & matches["vi"].ne("") & matches["vi_syllable"].ne("")
        ].copy()
        vi["_literary_sort"] = (vi["vi_use"] == "literary").astype(int)
        vi["_level_sort"] = pd.to_numeric(vi["level"], errors="coerce").fillna(99)
        vi["_freq_sort"] = pd.to_numeric(vi["freq_vi"], errors="coerce").fillna(float("inf"))
        vi = vi.sort_values(
            ["_literary_sort", "_level_sort", "_freq_sort", "word_id"], kind="stable"
        )
        vi_examples = [
            {"trad": row["trad"], "vi": row["vi"], "literary": row["vi_use"] == "literary"}
            for row in vi.head(3).to_dict(orient="records")
        ]
        singles = single_by_char.get(char["key_char"], [])
        vi_single_use = next((row["vi_use"] for row in singles if row["vi_use"]), "")
        own_literary = any(row["vi_use"] == "literary" for row in singles)
        reason = ""
        if char["vi"] and vi_examples and all(row["literary"] for row in vi_examples):
            reason = "vi_examples_literary"
        elif char["vi"] and own_literary:
            reason = "vi_single_literary"
        elif (char["vi"] and not vi_examples and char["level"]
              and int(char["level"]) <= 4):
            reason = "vi_no_examples"
        elif (char["pinyin"] and not zh_examples and char["level"]
              and int(char["level"]) <= 4):
            reason = "zh_no_examples"
        if not reason:
            continue
        item = {
            "key": f"{char['char_id']}:note", "char": char["key_char"],
            "simp": char["simp"], "jp": char["jp"], "pinyin": char["pinyin"],
            "vi": char["vi"], "meaning_en": char["gloss_en"][:80],
            "zh_examples": zh_examples, "vi_examples": vi_examples,
            "vi_single_use": vi_single_use, "reason": reason,
        }
        items.append(_clean(item))
    return items


def build_task6_items(
    words: pd.DataFrame | None = None,
    ff_meanings: pd.DataFrame | None = None,
    chars: pd.DataFrame | None = None,
    word_chars: pd.DataFrame | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Build D72 sentence and character-note items without any network access."""
    words = load_csv(WORDS_PATH) if words is None else words.copy()
    ff_meanings = load_csv(FF_MEANINGS_PATH) if ff_meanings is None else ff_meanings.copy()
    chars = load_csv(CHARS_PATH) if chars is None else chars.copy()
    word_chars = load_csv(WORD_CHARS_PATH) if word_chars is None else word_chars.copy()
    zh_card, zh_ff = _task6_sentence_items(words, ff_meanings, "zh")
    vi_card, vi_ff = _task6_sentence_items(words, ff_meanings, "vi")
    notes = _task6_note_items(words, chars, word_chars)
    result = {
        "zh_card": zh_card, "zh_ff": zh_ff,
        "vi_card": vi_card, "vi_ff": vi_ff, "note": notes,
    }
    counts = {kind: len(items) for kind, items in result.items()}
    if counts != TASK6_EXPECTED_COUNTS:
        raise ValueError(
            f"Task 6 item counts differ from D72: expected {TASK6_EXPECTED_COUNTS}, got {counts}"
        )
    expected_fields = {
        "zh_card": TASK6_ZH_FIELDS, "zh_ff": TASK6_ZH_FIELDS,
        "vi_card": TASK6_VI_FIELDS, "vi_ff": TASK6_VI_FIELDS,
        "note": TASK6_NOTE_FIELDS,
    }
    all_keys: list[str] = []
    for kind, items in result.items():
        if any(list(item) != expected_fields[kind] for item in items):
            raise ValueError(f"Task 6 {kind} input field order differs from D72")
        all_keys.extend(item["key"] for item in items)
    if len(all_keys) != len(set(all_keys)):
        raise ValueError("Task 6 input keys are not unique")
    if any(not item["target"] or not item["meaning_ja"] for item in zh_card):
        raise ValueError("Task 6 zh card item has an empty target or meaning")
    if any(not item["meaning_ja"] for item in vi_card):
        raise ValueError("Task 6 vi card item has an empty meaning")
    return result


def build_task6_batches() -> list[tuple[str, str, list[dict[str, Any]]]]:
    items = build_task6_items()
    result: list[tuple[str, str, list[dict[str, Any]]]] = []
    number = 1
    for kind, values in (("zh", items["zh_card"] + items["zh_ff"]),
                         ("vi", items["vi_card"] + items["vi_ff"]),
                         ("note", items["note"])):
        for batch in chunked(values, 50):
            result.append((f"b{number:03d}", kind, batch))
            number += 1
    return result


def _pilot_add_by_forms(
    destination: list[dict[str, Any]], pool: list[dict[str, Any]], forms: list[str],
) -> None:
    keys = {item["key"] for item in destination}
    for form in forms:
        match = next((item for item in pool if item["trad"] == form and item["key"] not in keys), None)
        if match is None:
            raise ValueError(f"Task 6 pilot item is missing for {form}")
        destination.append(match)
        keys.add(match["key"])


def build_pilot_task6() -> dict[str, list[dict[str, Any]]]:
    items = build_task6_items()
    zh_cards, zh_ffs = items["zh_card"], items["zh_ff"]
    zh: list[dict[str, Any]] = []
    _pilot_add_by_forms(zh, zh_cards, [
        "大學", "學習", "銀行", "新聞", "經濟", "發展", "注意", "歷史", "心理",
        "博士", "勉強", "主義", "東西", "老師", "愛人", "工夫", "自己",
    ])
    _pilot_add_by_forms(zh, zh_ffs, ["手紙", "大丈夫"])
    for item in zh_cards:
        if len(zh) >= 40:
            break
        if item["level"] == "1" and item["key"] not in {value["key"] for value in zh}:
            zh.append(item)
    for item in zh_cards:
        if len(zh) >= 50:
            break
        if item["level"] == "7" and item["key"] not in {value["key"] for value in zh}:
            zh.append(item)

    vi_cards, vi_ffs = items["vi_card"], items["vi_ff"]
    vi: list[dict[str, Any]] = []
    _pilot_add_by_forms(vi, vi_cards, [
        "大學", "學習", "銀行", "經濟", "發展", "注意", "歷史", "心理", "博士",
        "勉強", "主義", "越南", "自己", "工夫", "飛機", "老師",
    ])
    _pilot_add_by_forms(vi, vi_ffs, ["大丈夫"])
    single_ff = [item for item in vi_ffs if len(item["trad"]) == 1]
    vi.extend(single_ff[:6])
    vi_keys = {item["key"] for item in vi}
    for item in vi_cards:
        if len(vi) >= 40:
            break
        if item["vi_use"] == "literary" and item["key"] not in vi_keys:
            vi.append(item)
            vi_keys.add(item["key"])
    pilot_word_map = load_csv(WORDS_PATH).set_index("word_id")
    for item in vi_cards:
        if len(vi) >= 50:
            break
        word_id = item["key"].split(":", 1)[0]
        row = pilot_word_map.loc[word_id]
        if row["origin"] == "vi_freq" and item["key"] not in vi_keys:
            vi.append(item)
            vi_keys.add(item["key"])

    notes = items["note"]
    note: list[dict[str, Any]] = []
    bang = next((item for item in notes if item["char"] == "幫"), None)
    if bang is not None:
        note.append(bang)
    note.extend(item for item in notes if item not in note and len(note) < 50)
    result = {"zh": zh, "vi": vi, "note": note}
    if {kind: len(values) for kind, values in result.items()} != {"zh": 50, "vi": 50, "note": 50}:
        raise ValueError(f"Task 6 pilot needs 50 items per kind: { {k: len(v) for k, v in result.items()} }")
    return result


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


def ordered_jsonl_text(items: Iterable[dict[str, Any]]) -> str:
    return "".join(json.dumps(_clean(item), ensure_ascii=False, separators=(",", ":")) + "\n" for item in items)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_jsonl(path: Path, items: Iterable[dict[str, Any]]) -> str:
    text = jsonl_text(items)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return sha256_text(text)


def write_ordered_jsonl(path: Path, items: Iterable[dict[str, Any]]) -> str:
    text = ordered_jsonl_text(items)
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
    if task == 5:
        return build_task5_batches()
    raise ValueError(f"Unknown task: {task}")
