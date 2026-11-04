"""Shared normalization, phonology, export, and ID helpers."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
STAGING = ROOT / "data" / "staging"
FINAL = ROOT / "data" / "final"
ID_MAP = ROOT / "pipeline" / "id_map.csv"

CJK_PATTERN = r"[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0003134f]"
CJK_RE = re.compile(CJK_PATTERN)
CJK_RUN_RE = re.compile(CJK_PATTERN + "+")
HANGUL_RE = re.compile(r"^[\uac00-\ud7a3]+$")
VI_FINAL_RE = re.compile(r"(ng|nh|ch|c|p|t|n|m)$")

TONE_MARKS = {"\u0300", "\u0301", "\u0303", "\u0309", "\u0323"}
JONGSEONG = [
    "", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ",
    "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
]


def nfc(value: object) -> str:
    """Strip and NFC-normalize a source text value."""
    if value is None or value is pd.NA:
        return ""
    try:
        if bool(pd.isna(value)):
            return ""
    except (TypeError, ValueError):
        pass
    return unicodedata.normalize("NFC", str(value).strip())


def normalize_text_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Apply the global strip + NFC rule to pandas text columns."""
    frame = frame.copy()
    for column in frame.select_dtypes(include=["object", "string"]).columns:
        frame[column] = frame[column].astype("string").str.strip().str.normalize("NFC")
    return frame


def _normalize_vietnamese_syllable(syllable: str) -> str:
    decomposed = unicodedata.normalize("NFD", nfc(syllable).lower())
    clusters: list[list[str]] = []
    for char in decomposed:
        if unicodedata.combining(char) and clusters:
            clusters[-1][1] += char
        else:
            clusters.append([char, ""])

    def base(index: int) -> str:
        return unicodedata.normalize("NFD", clusters[index][0])[0]

    # D25: move a tone from the second vowel to the first only when oa/oe/uy
    # ends an open syllable. A q before uy keeps the source placement.
    for index in range(1, len(clusters)):
        pair = base(index - 1) + base(index)
        tones = [mark for mark in clusters[index][1] if mark in TONE_MARKS]
        if (
            tones
            and index == len(clusters) - 1
            and pair in {"oa", "oe", "uy"}
            and not (pair == "uy" and index >= 2 and base(index - 2) == "q")
        ):
            if not any(mark in TONE_MARKS for mark in clusters[index - 1][1]):
                clusters[index - 1][1] += tones[0]
                clusters[index][1] = clusters[index][1].replace(tones[0], "", 1)
            break
    return unicodedata.normalize("NFC", "".join(char + marks for char, marks in clusters))


def normalize_vietnamese(value: object) -> str:
    """Normalize a Vietnamese word/phrase using D25 modern tone placement."""
    text = nfc(value).lower()
    return " ".join(_normalize_vietnamese_syllable(part) for part in text.split())


def katakana_to_hiragana(value: object) -> str:
    text = nfc(value)
    return "".join(chr(ord(char) - 0x60) if "ァ" <= char <= "ヶ" else char for char in text)


def hangul_final(value: object) -> str:
    text = nfc(value)
    if not text:
        return ""
    last = text[-1]
    if not ("가" <= last <= "힣"):
        return ""
    return JONGSEONG[(ord(last) - 0xAC00) % 28]


def vietnamese_final(value: object) -> str:
    text = normalize_vietnamese(value)
    if not text:
        return ""
    match = VI_FINAL_RE.search(text.split()[-1])
    return match.group(1) if match else ""


PINYIN_VOWELS = {
    "a": "āáǎà", "e": "ēéěè", "i": "īíǐì", "o": "ōóǒò", "u": "ūúǔù", "ü": "ǖǘǚǜ",
    "A": "ĀÁǍÀ", "E": "ĒÉĚÈ", "I": "ĪÍǏÌ", "O": "ŌÓǑÒ", "U": "ŪÚǓÙ", "Ü": "ǕǗǙǛ",
}


def pinyin_numbered_to_marked(value: object) -> str:
    """Convert one numbered pinyin token (e.g. xue2) to tone marks."""
    token = nfc(value).replace("u:", "ü").replace("v", "ü")
    match = re.search(r"([0-5])$", token)
    if not match:
        return token.lower()
    tone = int(match.group(1))
    body = token[:-1]
    if tone in {0, 5}:
        return body.lower()
    lower = body.lower()
    if "a" in lower:
        target = lower.index("a")
    elif "e" in lower:
        target = lower.index("e")
    elif "ou" in lower:
        target = lower.index("o")
    else:
        vowel_positions = [index for index, char in enumerate(lower) if char in "aeiouü"]
        if not vowel_positions:
            return body.lower()
        target = vowel_positions[-1]
    char = body[target]
    marked = PINYIN_VOWELS[char][tone - 1]
    return (body[:target] + marked + body[target + 1 :]).lower()


def unique_preserve(values: Iterable[object]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = nfc(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def split_multi(value: object, separator: str = ";") -> list[str]:
    return unique_preserve(nfc(value).split(separator)) if nfc(value) else []


def is_cjk_char(value: object) -> bool:
    text = nfc(value)
    return len(text) == 1 and CJK_RE.fullmatch(text) is not None


def all_cjk(value: object) -> bool:
    text = nfc(value)
    return bool(text) and all(CJK_RE.fullmatch(char) for char in text)


def write_csv(frame: pd.DataFrame, path: Path, bool_columns: Iterable[str] = ()) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    export = frame.copy()
    for column in bool_columns:
        if column in export:
            export[column] = export[column].map({True: "true", False: "false"})
    export.to_csv(path, index=False, encoding="utf-8", na_rep="", lineterminator="\n")


def _json_value(value: object) -> object:
    if value is None or value is pd.NA or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def write_json(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = [
        {column: _json_value(value) for column, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]
    path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_id_map() -> pd.DataFrame:
    if not ID_MAP.exists():
        return pd.DataFrame(columns=["kind", "key", "id"], dtype="string")
    frame = pd.read_csv(ID_MAP, encoding="utf-8", keep_default_na=False, dtype=str)
    if list(frame.columns) != ["kind", "key", "id"]:
        raise ValueError("pipeline/id_map.csv must have columns kind,key,id")
    if frame.duplicated(["kind", "key"]).any() or frame["id"].duplicated().any():
        raise ValueError("pipeline/id_map.csv contains duplicate keys or ids")
    return normalize_text_columns(frame)


def assign_ids(kind: str, keys: Iterable[str], prefix: str, width: int) -> dict[str, str]:
    frame = load_id_map()
    existing = frame.loc[frame["kind"] == kind, ["key", "id"]]
    mapping = dict(existing.itertuples(index=False, name=None))
    numbers = [int(identifier[len(prefix) :]) for identifier in frame["id"] if identifier.startswith(prefix)]
    next_number = max(numbers, default=0) + 1
    additions: list[dict[str, str]] = []
    for key in unique_preserve(keys):
        if key not in mapping:
            identifier = f"{prefix}{next_number:0{width}d}"
            next_number += 1
            mapping[key] = identifier
            additions.append({"kind": kind, "key": key, "id": identifier})
    if additions:
        frame = pd.concat([frame, pd.DataFrame(additions)], ignore_index=True)
    write_csv(frame, ID_MAP)
    return mapping


def require_nfc(frame: pd.DataFrame) -> None:
    for column in frame.select_dtypes(include=["object", "string"]).columns:
        for value in frame[column].dropna():
            text = str(value)
            if text != unicodedata.normalize("NFC", text):
                raise ValueError(f"Non-NFC value in {column}: {text!r}")
