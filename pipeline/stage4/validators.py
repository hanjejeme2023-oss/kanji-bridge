"""Strict local validation and API response schemas for Stage 4."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Any


LANGS = ("ja", "ko", "zh", "vi")
TASK1_KEYS = {
    "word_id", "meaning_ja__ja", "meaning_ja__ko", "meaning_ja__zh", "meaning_ja__vi",
    "meanings_differ", "vi_check", "vi_check_reason", "confidence", "low_reason",
}
TASK2_KEYS = {"key", "false_friend", "meanings", "confidence", "low_reason"}
TASK4_KEYS = {"word_id", "note_ja"}
TASK5_KEYS = {
    "key", "ja_check", "ja_reason", "ko_check", "ko_reason", "vi_use", "vi_reason",
}
PUNCT_RE = re.compile(r"^[\s\u3000-\u303f\uff01-\uff65.,!?;:…—–―・]+$")
HANGUL_RE = re.compile(r"[가-힣]+")
LATIN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ỹĐđ]+")
QUOTED_RE = re.compile(r"「([^」]+)」")


class ValidationError(ValueError):
    pass


def _fail(message: str) -> None:
    raise ValidationError(message)


def _is_nfc(value: Any) -> bool:
    if isinstance(value, str):
        return unicodedata.is_normalized("NFC", value)
    if isinstance(value, list):
        return all(_is_nfc(item) for item in value)
    if isinstance(value, dict):
        return all(_is_nfc(key) and _is_nfc(item) for key, item in value.items())
    return True


def _expect_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        _fail(f"{label}: keys differ; expected {sorted(expected)}, got {sorted(value)}")


def _expect_string(value: Any, label: str) -> str:
    if not isinstance(value, str):
        _fail(f"{label}: expected string, got {type(value).__name__}")
    return value


def _check_output_collection(output: Any, inputs: list[dict[str, Any]], key: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    if not isinstance(output, list) or not all(isinstance(item, dict) for item in output):
        _fail("Response must be an array of objects")
    input_keys = [str(item[key]) for item in inputs]
    output_keys = [str(item.get(key, "")) for item in output]
    if Counter(input_keys) != Counter(output_keys):
        _fail(f"Output keys do not exactly match input keys: input={input_keys}, output={output_keys}")
    if len(output_keys) != len(set(output_keys)):
        _fail(f"Duplicate output {key}")
    return output, {str(item[key]): item for item in inputs}


def present_languages(item: dict[str, Any]) -> list[str]:
    fields = {"ja": "ja", "ko": "ko", "zh": "pinyin", "vi": "vi"}
    return [lang for lang in LANGS if bool(item.get(fields[lang], ""))]


def validate_task1(output: Any, inputs: list[dict[str, Any]]) -> None:
    values, input_map = _check_output_collection(output, inputs, "word_id")
    for value in values:
        word_id = str(value.get("word_id", ""))
        _expect_exact_keys(value, TASK1_KEYS, word_id)
        source = input_map[word_id]
        for key in TASK1_KEYS - {"meanings_differ"}:
            _expect_string(value[key], f"{word_id}.{key}")
        if not isinstance(value["meanings_differ"], bool):
            _fail(f"{word_id}.meanings_differ must be boolean")
        if value["confidence"] not in {"high", "low"}:
            _fail(f"{word_id}.confidence invalid: {value['confidence']!r}")
        if value["vi_check"] not in {"", "same_word", "different_word", "unsure"}:
            _fail(f"{word_id}.vi_check invalid: {value['vi_check']!r}")
        if bool(source.get("vi")) != bool(value["vi_check"]):
            _fail(f"{word_id}.vi_check must be empty iff input vi is empty")
        for lang, reading_field in (("ja", "ja"), ("ko", "ko"), ("zh", "pinyin"), ("vi", "vi")):
            expected = bool(source.get(reading_field))
            if lang == "vi" and value["vi_check"] == "different_word":
                expected = False
            if bool(value[f"meaning_ja__{lang}"]) != expected:
                _fail(f"{word_id}.meaning_ja__{lang} presence does not match {reading_field}")
        if value["vi_check"] in {"different_word", "unsure"} and not value["vi_check_reason"]:
            _fail(f"{word_id}.vi_check_reason is required for {value['vi_check']}")
        if value["vi_check"] == "different_word" and len(str(source.get("trad", ""))) == 1:
            _fail(f"{word_id}: a single-character word cannot be different_word")
        if value["vi_check"] in {"different_word", "unsure"} and value["confidence"] != "low":
            _fail(f"{word_id}: {value['vi_check']} requires confidence=low")
        if value["confidence"] == "low" and not value["low_reason"]:
            _fail(f"{word_id}.low_reason required when confidence=low")
        if not _is_nfc(value):
            _fail(f"{word_id}: output is not NFC")


def validate_task2(output: Any, inputs: list[dict[str, Any]]) -> None:
    values, input_map = _check_output_collection(output, inputs, "key")
    for value in values:
        key = str(value.get("key", ""))
        _expect_exact_keys(value, TASK2_KEYS, key)
        _expect_string(value["key"], f"{key}.key")
        _expect_string(value["confidence"], f"{key}.confidence")
        _expect_string(value["low_reason"], f"{key}.low_reason")
        if value["confidence"] not in {"high", "low"}:
            _fail(f"{key}.confidence invalid")
        if value["confidence"] == "low" and not value["low_reason"]:
            _fail(f"{key}.low_reason required when confidence=low")
        if not isinstance(value["false_friend"], list) or not all(isinstance(x, str) for x in value["false_friend"]):
            _fail(f"{key}.false_friend must be a string array")
        present = present_languages(input_map[key])
        traps = value["false_friend"]
        if len(traps) != len(set(traps)) or not set(traps).issubset(present):
            _fail(f"{key}.false_friend contains duplicate or absent language")
        baseline = next((lang for lang in ("ja", "ko", "zh") if lang in present), None)
        if baseline in traps:
            _fail(f"{key}.false_friend cannot contain baseline language {baseline}")
        meanings = value["meanings"]
        if not isinstance(meanings, list) or not all(isinstance(x, dict) for x in meanings):
            _fail(f"{key}.meanings must be an object array")
        langs: list[str] = []
        for meaning in meanings:
            _expect_exact_keys(meaning, {"lang", "meaning_ja", "is_trap"}, f"{key}.meanings")
            if meaning["lang"] not in LANGS or not isinstance(meaning["meaning_ja"], str) or not meaning["meaning_ja"]:
                _fail(f"{key}.meanings has invalid language or empty meaning")
            if not isinstance(meaning["is_trap"], bool):
                _fail(f"{key}.{meaning['lang']}.is_trap must be boolean")
            if meaning["is_trap"] != (meaning["lang"] in traps):
                _fail(f"{key}.{meaning['lang']}.is_trap disagrees with false_friend")
            langs.append(meaning["lang"])
        if Counter(langs) != Counter(present):
            _fail(f"{key}.meanings languages {langs} do not match present languages {present}")
        if not _is_nfc(value):
            _fail(f"{key}: output is not NFC")


def validate_task3(output: Any, inputs: list[dict[str, Any]]) -> None:
    if len(inputs) != 1:
        _fail("Task 3 expects one cell per request")
    if not isinstance(output, dict) or set(output) != {"passages"} or not isinstance(output["passages"], list):
        _fail("Task 3 response must be {'passages': [...]} ")
    if len(output["passages"]) != 6:
        _fail(f"Task 3 must return exactly 6 passages, got {len(output['passages'])}")
    source = inputs[0]
    allowed = {item["word_id"]: item for item in source["words"]}
    current_ids = {item["word_id"] for item in source["words"] if int(item["level"]) == int(source["level"])}
    for index, passage in enumerate(output["passages"], 1):
        if not isinstance(passage, dict) or set(passage) != {"translation_ja", "tokens"}:
            _fail(f"passage {index}: invalid keys")
        if not isinstance(passage["translation_ja"], str) or not passage["translation_ja"]:
            _fail(f"passage {index}: translation_ja is empty")
        if not isinstance(passage["tokens"], list) or not passage["tokens"]:
            _fail(f"passage {index}: tokens are empty")
        linked: list[str] = []
        for token_index, token in enumerate(passage["tokens"], 1):
            if not isinstance(token, dict) or "t" not in token or not isinstance(token["t"], str) or not token["t"]:
                _fail(f"passage {index} token {token_index}: invalid text")
            annotations = [name for name in ("word_id", "gloss_ja", "punct") if name in token]
            if len(annotations) != 1:
                _fail(f"passage {index} token {token_index}: exactly one annotation required")
            if "word_id" in token:
                word_id = token["word_id"]
                if word_id not in allowed:
                    _fail(f"passage {index}: unknown word_id {word_id}")
                expected = allowed[word_id]["display"]
                equal = token["t"] == expected if source["language"] == "zh" else token["t"].casefold() == expected.casefold()
                if not equal:
                    _fail(f"passage {index}: {word_id} text {token['t']!r} != {expected!r}")
                linked.append(word_id)
            elif "gloss_ja" in token:
                if not isinstance(token["gloss_ja"], str) or not token["gloss_ja"]:
                    _fail(f"passage {index}: function token needs gloss_ja")
            else:
                if token["punct"] is not True or not PUNCT_RE.fullmatch(token["t"]):
                    _fail(f"passage {index}: punctuation token contains non-punctuation")
        if len(linked) < 3:
            _fail(f"passage {index}: fewer than 3 linked tokens")
        if current_ids and not current_ids.intersection(linked):
            _fail(f"passage {index}: no linked word at level {source['level']}")
    if not _is_nfc(output):
        _fail("Task 3 output is not NFC")


def _all_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for value_item in value for item in _all_strings(value_item)]
    if isinstance(value, dict):
        return [item for value_item in value.values() for item in _all_strings(value_item)]
    return []


def validate_task4(output: Any, inputs: list[dict[str, Any]]) -> None:
    values, input_map = _check_output_collection(output, inputs, "word_id")
    for value in values:
        word_id = str(value.get("word_id", ""))
        _expect_exact_keys(value, TASK4_KEYS, word_id)
        note = _expect_string(value["note_ja"], f"{word_id}.note_ja")
        if not note or "\n" in note or "\r" in note or len(note) > 80:
            _fail(f"{word_id}.note_ja must be one non-empty line of at most 80 characters")
        source_strings = _all_strings(input_map[word_id])
        allowed_quotes = set(source_strings)
        for quoted in QUOTED_RE.findall(note):
            if quoted not in allowed_quotes:
                _fail(f"{word_id}.note_ja quotes unknown text {quoted!r}")
        allowed_hangul = {part for text in source_strings for part in HANGUL_RE.findall(text)}
        for part in HANGUL_RE.findall(note):
            if part not in allowed_hangul:
                _fail(f"{word_id}.note_ja contains unknown Hangul reading {part!r}")
        allowed_latin = {part.casefold() for text in source_strings for part in LATIN_RE.findall(text)}
        for part in LATIN_RE.findall(note):
            if part.casefold() not in allowed_latin:
                _fail(f"{word_id}.note_ja contains unknown Vietnamese reading {part!r}")
        if not _is_nfc(value):
            _fail(f"{word_id}: output is not NFC")


def validate_task5(output: Any, inputs: list[dict[str, Any]]) -> list[dict[str, str]]:
    values, input_map = _check_output_collection(output, inputs, "key")
    reason_warnings: list[dict[str, str]] = []
    field_specs = {
        "ja": ("ja_check", "ja_reason", {"used", "rare", "wrong_meaning", "unsure"}, "used"),
        "ko": ("ko_check", "ko_reason", {"used", "rare", "wrong_meaning", "unsure"}, "used"),
        "vi": ("vi_use", "vi_reason", {"common", "literary", "unsure"}, "common"),
    }
    for value in values:
        key = str(value.get("key", ""))
        _expect_exact_keys(value, TASK5_KEYS, key)
        source = input_map[key]
        checks = source.get("checks")
        if (not isinstance(checks, list) or not checks
                or len(checks) != len(set(checks)) or not set(checks).issubset(field_specs)):
            _fail(f"{key}.checks is invalid")
        for field in TASK5_KEYS:
            _expect_string(value[field], f"{key}.{field}")
        for lang, (check_field, reason_field, allowed, no_reason_value) in field_specs.items():
            check = value[check_field]
            reason = value[reason_field]
            expected = lang in checks
            if bool(check) != expected or bool(reason) and not expected:
                _fail(f"{key}.{lang} fields must be non-empty exactly when that language is checked")
            if not expected:
                continue
            if check not in allowed:
                _fail(f"{key}.{check_field} invalid: {check!r}")
            if (check == no_reason_value) != (reason == ""):
                _fail(f"{key}.{reason_field} must be empty iff {check_field}={no_reason_value}")
            if reason and (len(reason) > 80 or "\n" in reason or "\r" in reason):
                _fail(f"{key}.{reason_field} must be one line of at most 80 characters")
        ko = str(source.get("ko", ""))
        vi = str(source.get("vi", ""))
        vi_folded = vi.casefold()
        for reason_field in ("ja_reason", "ko_reason", "vi_reason"):
            reason = value[reason_field]
            for part in HANGUL_RE.findall(reason):
                if part not in ko:
                    reason_warnings.append({
                        "key": key, "field": reason_field, "text": part,
                    })
            for part in LATIN_RE.findall(reason):
                if part.casefold() not in vi_folded:
                    reason_warnings.append({
                        "key": key, "field": reason_field, "text": part,
                    })
        if not _is_nfc(value):
            _fail(f"{key}: output is not NFC")
    return reason_warnings


def validate(task: int, output: Any, inputs: list[dict[str, Any]]) -> list[dict[str, str]]:
    warnings = {1: validate_task1, 2: validate_task2, 3: validate_task3, 4: validate_task4,
                5: validate_task5}[task](output, inputs)
    return warnings or []


STRING = {"type": "string"}
BOOL = {"type": "boolean"}


def _object(
    properties: dict[str, Any], property_ordering: list[str] | None = None,
) -> dict[str, Any]:
    schema = {
        "type": "object", "properties": properties,
        "required": list(properties), "additionalProperties": False,
    }
    if property_ordering is not None:
        schema["propertyOrdering"] = property_ordering
    return schema


TASK1_ITEM_SCHEMA = _object({
    "word_id": STRING,
    # Decide vi_check before writing the Vietnamese meaning. The explicit
    # ordering is a Vertex schema extension and is also asserted in tests.
    "vi_check": STRING,
    "vi_check_reason": STRING,
    "meaning_ja__ja": STRING,
    "meaning_ja__ko": STRING,
    "meaning_ja__zh": STRING,
    "meaning_ja__vi": STRING,
    "meanings_differ": BOOL,
    "confidence": {"type": "string", "enum": ["high", "low"]},
    "low_reason": STRING,
}, [
    "word_id", "vi_check", "vi_check_reason", "meaning_ja__ja",
    "meaning_ja__ko", "meaning_ja__zh", "meaning_ja__vi",
    "meanings_differ", "confidence", "low_reason",
])
MEANING_SCHEMA = _object({
    "lang": {"type": "string", "enum": list(LANGS)}, "meaning_ja": STRING, "is_trap": BOOL,
}, ["lang", "meaning_ja", "is_trap"])
TASK2_ITEM_SCHEMA = _object({
    "key": STRING,
    "meanings": {"type": "array", "items": MEANING_SCHEMA},
    "false_friend": {"type": "array", "items": {"type": "string", "enum": list(LANGS)}},
    "confidence": {"type": "string", "enum": ["high", "low"]},
    "low_reason": STRING,
}, ["key", "meanings", "false_friend", "confidence", "low_reason"])
TOKEN_SCHEMA = {
    "type": "object",
    "properties": {"t": STRING, "word_id": STRING, "gloss_ja": STRING, "punct": BOOL},
    "required": ["t"],
    "additionalProperties": False,
}
PASSAGE_SCHEMA = _object({
    "translation_ja": STRING, "tokens": {"type": "array", "items": TOKEN_SCHEMA},
})
TASK3_SCHEMA = _object({"passages": {"type": "array", "items": PASSAGE_SCHEMA}})
TASK4_ITEM_SCHEMA = _object({"word_id": STRING, "note_ja": STRING})
TASK5_ITEM_SCHEMA = _object({
    "key": STRING,
    "ja_check": STRING,
    "ja_reason": STRING,
    "ko_check": STRING,
    "ko_reason": STRING,
    "vi_use": STRING,
    "vi_reason": STRING,
}, ["key", "ja_check", "ja_reason", "ko_check", "ko_reason", "vi_use", "vi_reason"])
RESPONSE_SCHEMAS = {
    1: {"type": "array", "items": TASK1_ITEM_SCHEMA},
    2: {"type": "array", "items": TASK2_ITEM_SCHEMA},
    3: TASK3_SCHEMA,
    4: {"type": "array", "items": TASK4_ITEM_SCHEMA},
    5: {"type": "array", "items": TASK5_ITEM_SCHEMA},
}
