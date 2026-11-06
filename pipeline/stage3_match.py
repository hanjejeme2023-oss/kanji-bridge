"""Deterministic dictionary matching helpers for the Stage 3 word build."""

from __future__ import annotations

import itertools
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

import pandas as pd

try:
    from .common import TONE_MARKS, nfc, split_multi, unique_preserve
except ImportError:  # Direct script-style imports used by the Stage 3 pipeline.
    from common import TONE_MARKS, nfc, split_multi, unique_preserve


STRICT_PRI_RE = re.compile(r"^(?:ichi1|news1|spec1|gai1|nf(?:0[1-9]|1\d|2[0-4]))$")
NF_RE = re.compile(r"^nf(\d\d)$")
BAD_KE = {"iK", "oK", "rK", "sK"}
BAD_RE = {"ik", "ok", "rk", "sk"}
CHOSEONG = ["ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
JUNGSEONG = ["ㅏ", "ㅐ", "ㅑ", "ㅒ", "ㅓ", "ㅔ", "ㅕ", "ㅖ", "ㅗ", "ㅘ", "ㅙ", "ㅚ", "ㅛ", "ㅜ", "ㅝ", "ㅞ", "ㅟ", "ㅠ", "ㅡ", "ㅢ", "ㅣ"]
IOTIZED = {"ㅑ", "ㅒ", "ㅕ", "ㅖ", "ㅛ", "ㅠ", "ㅣ"}


def toneless(value: object) -> str:
    text = unicodedata.normalize("NFD", nfc(value).lower().replace("ü", "v"))
    return "".join(char for char in text if not unicodedata.combining(char) and char.isalpha())


def variant_char(value: object) -> list[str]:
    result = []
    for token in re.split(r"[\s,]+", nfc(value)):
        match = re.match(r"U\+([0-9A-Fa-f]+)", token)
        if match:
            result.append(chr(int(match.group(1), 16)))
    return unique_preserve(result)


def tags(value: object) -> list[str]:
    return split_multi(value)


def strict_priority(value: object) -> bool:
    return any(STRICT_PRI_RE.match(tag) for tag in tags(value))


def nf_value(value: object) -> int:
    numbers = [int(match.group(1)) for tag in tags(value) if (match := NF_RE.match(tag))]
    return min(numbers, default=99)


def jmdict_rank(row: object) -> tuple[int, int, int, int, int, int]:
    return (
        0 if strict_priority(row.re_pri) else 1,
        nf_value(row.re_pri),
        0 if strict_priority(row.ke_pri) else 1,
        int(row.ent_seq),
        int(row.reb_pos),
        int(row.keb_pos),
    )


def valid_jmdict_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    good = frame.loc[
        ~frame["re_inf"].map(lambda value: bool(set(tags(value)) & BAD_RE))
        & ~frame["ke_inf"].map(lambda value: bool(set(tags(value)) & BAD_KE))
        & ~frame["gloss_ja_en"].str.startswith('kanji "', na=False)
    ]
    if good.empty:
        good = frame.loc[
            ~frame["re_inf"].map(lambda value: bool(set(tags(value)) & BAD_RE))
            & ~frame["gloss_ja_en"].str.startswith('kanji "', na=False)
        ]
    return good if not good.empty else frame.iloc[0:0]


def make_jmdict_index(frame: pd.DataFrame) -> dict[str, list[dict[str, object]]]:
    result: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in frame.to_dict(orient="records"):
        result[nfc(row["keb"])].append(row)
    return result


def find_jmdict(
    forms: Iterable[str], index: dict[str, list[dict[str, object]]]
) -> tuple[str, pd.DataFrame]:
    for form in unique_preserve(forms):
        if form not in index:
            continue
        candidates = valid_jmdict_rows(pd.DataFrame(index[form]))
        if candidates.empty:
            continue
        candidates = candidates.copy()
        candidates["_rank"] = [jmdict_rank(row) for row in candidates.itertuples(index=False)]
        candidates = candidates.sort_values("_rank", kind="stable")
        return form, candidates.drop(columns="_rank")
    return "", pd.DataFrame()


def decompose_hangul(syllable: str) -> tuple[int, int, int] | None:
    if len(syllable) != 1 or not ("가" <= syllable <= "힣"):
        return None
    offset = ord(syllable) - 0xAC00
    return offset // 588, (offset % 588) // 28, offset % 28


def replace_initial(syllable: str, initial: str) -> str:
    parts = decompose_hangul(syllable)
    if parts is None:
        return syllable
    _old, vowel, final = parts
    return chr(0xAC00 + CHOSEONG.index(initial) * 588 + vowel * 28 + final)


def initial_of(syllable: str) -> str:
    parts = decompose_hangul(syllable)
    return CHOSEONG[parts[0]] if parts else ""


def vowel_of(syllable: str) -> str:
    parts = decompose_hangul(syllable)
    return JUNGSEONG[parts[1]] if parts else ""


def korean_base_candidates(syllable: str, position: int) -> list[str]:
    result = [syllable]
    initial = initial_of(syllable)
    vowel = vowel_of(syllable)
    if position == 0:
        if initial == "ㅇ" and vowel in IOTIZED:
            result.extend([replace_initial(syllable, "ㄹ"), replace_initial(syllable, "ㄴ")])
        elif initial == "ㄴ":
            result.append(replace_initial(syllable, "ㄹ"))
    elif syllable in {"열", "율"}:
        result.append("렬" if syllable == "열" else "률")
    if position > 0:
        if initial == "ㄴ":
            result.append(replace_initial(syllable, "ㄹ"))
        elif initial == "ㄹ":
            result.append(replace_initial(syllable, "ㄴ"))
    return unique_preserve(result)


def korean_alignment_base(syllable: str, allowed: Iterable[str], position: int) -> str:
    """Return a D43-compatible source reading for dictionary alignment."""
    allowed_set = set(allowed)
    for candidate in korean_base_candidates(syllable, position):
        if candidate in allowed_set:
            return candidate
    return ""


def korean_normalized_base(
    syllable: str,
    allowed: Iterable[str],
    position: int,
    previous_syllable: str = "",
) -> str:
    """Normalize a Korean word syllable exactly as D39 specifies."""
    allowed_set = set(allowed)
    if not syllable:
        return ""
    if position == 0:
        initial = initial_of(syllable)
        vowel = vowel_of(syllable)
        if initial == "ㅇ" and vowel in IOTIZED:
            for replacement in ["ㄹ", "ㄴ"]:
                candidate = replace_initial(syllable, replacement)
                if candidate in allowed_set:
                    return candidate
        elif initial == "ㄴ" and vowel not in IOTIZED:
            candidate = replace_initial(syllable, "ㄹ")
            if candidate in allowed_set:
                return candidate
    elif syllable in {"열", "율"} and previous_syllable:
        previous = decompose_hangul(previous_syllable)
        previous_final = previous[2] if previous else -1
        if previous_final in {0, 4}:  # open syllable or ㄴ-final
            candidate = "렬" if syllable == "열" else "률"
            if candidate in allowed_set:
                return candidate
    return syllable if syllable in allowed_set else ""


# Compatibility name for D43 matching call sites. D39 counting must use
# korean_normalized_base instead.
korean_base = korean_alignment_base


def law_penalty(word: str) -> int:
    if not word:
        return 99
    first = word[0]
    penalty = int(initial_of(first) == "ㄹ" or (initial_of(first) == "ㄴ" and vowel_of(first) in IOTIZED))
    penalty += sum(1 for syllable in word[1:] if syllable in {"렬", "률"})
    return penalty


def generate_variant_forms(
    word: str, graph: dict[str, list[str]], limit: int = 512
) -> list[str]:
    choices = [unique_preserve([char, *graph.get(char, [])]) for char in word]
    size = 1
    for values in choices:
        size *= len(values)
        if size > limit:
            return []
    return ["".join(values) for values in itertools.product(*choices)]


def collapse_iy(readings: Iterable[str]) -> list[str]:
    values = unique_preserve(readings)
    groups: dict[str, list[str]] = defaultdict(list)

    def key(value: str) -> str:
        syllables = []
        for syllable in value.split():
            decomposed = unicodedata.normalize("NFD", syllable)
            tone = "".join(char for char in decomposed if char in TONE_MARKS)
            base = unicodedata.normalize(
                "NFC", "".join(char for char in decomposed if char not in TONE_MARKS)
            )
            if re.fullmatch(r"[bcdđghklmnpqrstvx]+[iy]", base) and base != "gi":
                base = base[:-1] + "Y"
            syllables.append(base + "/" + tone)
        return " ".join(syllables)

    def y_score(value: str) -> int:
        score = 0
        for syllable in value.split():
            base = unicodedata.normalize(
                "NFC",
                "".join(char for char in unicodedata.normalize("NFD", syllable) if char not in TONE_MARKS),
            )
            if base.endswith("y"):
                score += 1
        return score

    for value in values:
        groups[key(value)].append(value)
    result = []
    for group in groups.values():
        result.append(max(group, key=y_score))
    return unique_preserve(result)


def canonicalize_a2_spelling(value: object) -> str:
    """Apply D56's narrow i/y convention to a source-7C (rule A2) value."""
    output = []
    for syllable in nfc(value).split():
        decomposed = unicodedata.normalize("NFD", syllable)
        base = "".join(char for char in decomposed if char not in TONE_MARKS)
        if re.fullmatch(r"[hklmt]i", base):
            index = max(i for i, char in enumerate(decomposed) if char == "i")
            decomposed = decomposed[:index] + "y" + decomposed[index + 1 :]
        output.append(unicodedata.normalize("NFC", decomposed))
    return " ".join(output)


@dataclass
class ReadingLookup:
    ko: dict[str, list[str]]
    vi: dict[str, list[str]]
    vi_source: dict[tuple[str, str], str]
    ja_on: dict[str, list[str]]
    pinyin: dict[str, list[str]]

