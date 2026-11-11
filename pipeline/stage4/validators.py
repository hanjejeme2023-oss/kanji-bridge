"""Strict local validation and API response schemas for Stage 4."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd


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
TASK6_KEYS = {
    "zh": ["key", "status", "sentence", "pinyin", "translation_ja", "confidence", "review_note"],
    "vi": ["key", "status", "sentence", "translation_ja", "confidence", "review_note"],
    "note": ["key", "note_ja", "confidence", "review_note"],
}
PUNCT_RE = re.compile(r"^[\s\u3000-\u303f\uff01-\uff65.,!?;:…—–―・]+$")
HANGUL_RE = re.compile(r"[가-힣]+")
LATIN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ỹĐđ]+")
QUOTED_RE = re.compile(r"「([^」]+)」")
HANGUL_ANY_RE = re.compile(r"[\u1100-\u11ff\u3130-\u318f\ua960-\ua97f\uac00-\ud7af\ud7b0-\ud7ff]")
HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0002ffff\u3007]")
KANA_OR_HAN_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0002ffff]")
KANA_RE = re.compile(r"[\u3040-\u30ff]")
ZH_SENTENCE_RE = re.compile(r"^[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0002ffff\u3007，。！？、：；“”‘’《》（）—…]+$")
ZH_PINYIN_RE = re.compile(r'^[A-Za-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜüÜ\'’ ,.!?:;"“”()—…]+$')
VI_SENTENCE_RE = re.compile(r'^[A-Za-zÀ-ỹĐđ\u0102\u0103\u0110\u0111\u0128-\u01b0\u1ea0-\u1ef9 0-9.,!?;:"\'“”‘’()\-–…]+$')
LATIN_DIACRITIC_RE = re.compile(r"[\u00c0-\u024f\u1e00-\u1eff]")
TONE_COMBINERS = {"\u0300", "\u0301", "\u0304", "\u030c"}
VI_TONE_COMBINERS = {"\u0300", "\u0301", "\u0303", "\u0309", "\u0323"}
VI_VOWEL_COMBINERS = VI_TONE_COMBINERS | {"\u0302", "\u0306", "\u031b"}
VI_PUNCTUATION = set(" .,! ?;:\"'“”‘’()-–…".replace(" ", ""))

# Standard orthographic Hanyu Pinyin syllables. Tone marks are removed before lookup;
# ü remains distinct from u.
PINYIN_SYLLABLES = set("""
a ai an ang ao e ei en eng er o ou
ba bai ban bang bao bei ben beng bi bian biao bie bin bing bo bu
pa pai pan pang pao pei pen peng pi pian piao pie pin ping po pou pu
ma mai man mang mao me mei men meng mi mian miao mie min ming miu mo mou mu
fa fan fang fei fen feng fo fou fu
da dai dan dang dao de dei den deng di dia dian diao die ding diu dong dou du duan dui dun duo
ta tai tan tang tao te teng ti tian tiao tie ting tong tou tu tuan tui tun tuo
na nai nan nang nao ne nei nen neng ni nian niang niao nie nin ning niu nong nou nu nuan nun nuo nü nüe
la lai lan lang lao le lei leng li lia lian liang liao lie lin ling liu long lou lu luan lun luo lü lüe
ga gai gan gang gao ge gei gen geng gong gou gu gua guai guan guang gui gun guo
ka kai kan kang kao ke ken keng kong kou ku kua kuai kuan kuang kui kun kuo
ha hai han hang hao he hei hen heng hong hou hu hua huai huan huang hui hun huo
ji jia jian jiang jiao jie jin jing jiong jiu ju juan jue jun
qi qia qian qiang qiao qie qin qing qiong qiu qu quan que qun
xi xia xian xiang xiao xie xin xing xiong xiu xu xuan xue xun
zha zhai zhan zhang zhao zhe zhei zhen zheng zhi zhong zhou zhu zhua zhuai zhuan zhuang zhui zhun zhuo
cha chai chan chang chao che chen cheng chi chong chou chu chua chuai chuan chuang chui chun chuo
sha shai shan shang shao she shei shen sheng shi shou shu shua shuai shuan shuang shui shun shuo
re ren reng ri rong rou ru rua ruan rui run ruo
za zai zan zang zao ze zei zen zeng zi zong zou zu zuan zui zun zuo
ca cai can cang cao ce cen ceng ci cong cou cu cuan cui cun cuo
sa sai san sang sao se sen seng si song sou su suan sui sun suo
ya yan yang yao ye yi yin ying yo yong you yu yuan yue yun
wa wai wan wang wei wen weng wo wu
m n ng hm hng
""".split())


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


def _toneless(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    kept = "".join(char for char in decomposed if char not in TONE_COMBINERS)
    return unicodedata.normalize("NFC", kept)


def _tone_count(value: str) -> int:
    return sum(char in TONE_COMBINERS for char in unicodedata.normalize("NFD", value))


def _piece_segmentations(piece: str) -> list[list[tuple[str, str, bool]]]:
    """Return (marked, toneless-base, erhua) segmentations for one pinyin word."""
    folded = piece.casefold()
    plain = _toneless(folded)
    results: list[list[tuple[str, str, bool]]] = []

    def visit(position: int, current: list[tuple[str, str, bool]]) -> None:
        if position == len(plain):
            results.append(list(current))
            return
        for end in range(position + 1, min(len(plain), position + 7) + 1):
            raw_plain = plain[position:end]
            erhua = raw_plain.endswith("r") and raw_plain != "er" and raw_plain[:-1] in PINYIN_SYLLABLES
            base = raw_plain[:-1] if erhua else raw_plain
            if base not in PINYIN_SYLLABLES:
                continue
            marked = folded[position:end]
            if _tone_count(marked) > 1:
                continue
            current.append((marked, base, erhua))
            visit(end, current)
            current.pop()

    # NFC pinyin letters are one code point each, so indexes match the toneless form.
    if len(folded) == len(plain):
        visit(0, [])
    return results


def _pinyin_alignments(sentence: str, pinyin: str) -> list[list[tuple[int, int, str, str]]]:
    han = HAN_RE.findall(sentence)
    normalized = pinyin.replace("’", "'")
    pieces = [
        piece for piece in re.split(r"[\s',.!?:;\"“”()—…]+", normalized)
        if piece
    ]
    choices = [_piece_segmentations(piece) for piece in pieces]
    if any(not options for options in choices):
        return []
    alignments: list[list[tuple[int, int, str, str]]] = []

    def visit_piece(index: int, char_index: int, current: list[tuple[int, int, str, str]]) -> None:
        if index == len(choices):
            if char_index == len(han):
                alignments.append(list(current))
            return
        for segmentation in choices[index]:
            next_char = char_index
            added: list[tuple[int, int, str, str]] = []
            valid = True
            for marked, base, erhua in segmentation:
                consumed = 2 if erhua else 1
                if next_char + consumed > len(han) or (erhua and han[next_char + 1] != "儿"):
                    valid = False
                    break
                added.append((next_char, next_char + consumed, marked, base))
                next_char += consumed
            if valid:
                current.extend(added)
                visit_piece(index + 1, next_char, current)
                del current[-len(added):]

    visit_piece(0, 0, [])
    return alignments


@lru_cache(maxsize=1)
def _task6_reference() -> tuple[set[str], dict[str, set[str]], set[str]]:
    root = Path(__file__).resolve().parents[2]
    chars = pd.read_csv(
        root / "data" / "final" / "chars.csv", encoding="utf-8",
        keep_default_na=False, dtype=str,
    )
    words = pd.read_csv(
        root / "data" / "final" / "words.csv", encoding="utf-8",
        keep_default_na=False, dtype=str,
    )
    simplified_chars = set("".join(chars["simp"])) | set("".join(words["simp"]))
    traditional_only = {
        row["key_char"] for row in chars.to_dict(orient="records")
        if row["key_char"] != row["simp"] and row["key_char"] not in simplified_chars
    }
    pinyin_by_simp: dict[str, set[str]] = {}
    for row in chars.to_dict(orient="records"):
        readings = {
            _toneless(value) for value in row["pinyin_all"].split(";") if value
        }
        if readings:
            pinyin_by_simp.setdefault(row["simp"], set()).update(readings)
    word_forms = {value for value in words["simp"] if value}
    return traditional_only, pinyin_by_simp, word_forms


def _task6_batch(output: Any, inputs: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    if kind not in TASK6_KEYS:
        _fail(f"Task 6 kind is invalid: {kind!r}")
    if not isinstance(output, list) or not all(isinstance(item, dict) for item in output):
        _fail("Response must be an array of objects")
    input_keys = [str(item.get("key", "")) for item in inputs]
    output_keys = [str(item.get("key", "")) for item in output]
    if output_keys != input_keys:
        _fail(f"Output keys do not exactly match input keys in order: input={input_keys}, output={output_keys}")
    if len(output_keys) != len(set(output_keys)):
        _fail("Duplicate output key")
    expected = TASK6_KEYS[kind]
    for item in output:
        key = str(item.get("key", ""))
        if list(item) != expected:
            _fail(f"{key}: keys/order differ; expected {expected}, got {list(item)}")
        for field in expected:
            _expect_string(item[field], f"{key}.{field}")
        if item["confidence"] not in {"high", "low"}:
            _fail(f"{key}.confidence invalid")
        if kind != "note" and item["status"] not in {"ok", "no_sentence"}:
            _fail(f"{key}.status invalid")
    return output


def _task6_common_item(value: dict[str, Any]) -> None:
    key = value["key"]
    for field, text in value.items():
        if not isinstance(text, str):
            continue
        if not unicodedata.is_normalized("NFC", text):
            _fail(f"{key}.{field} is not NFC")
        if text != text.strip():
            _fail(f"{key}.{field} has leading or trailing space")
        if "\n" in text or "\r" in text or "\t" in text:
            _fail(f"{key}.{field} contains a line break or tab")
        if HANGUL_ANY_RE.search(text):
            _fail(f"{key}.{field} contains Hangul")
    if len(value["review_note"]) > 80:
        _fail(f"{key}.review_note exceeds 80 characters")
    if value["confidence"] == "low" and not value["review_note"]:
        _fail(f"{key}.review_note is required when confidence=low")


def _validate_translation(key: str, value: str) -> None:
    if len(value) > 60:
        _fail(f"{key}.translation_ja exceeds 60 characters")
    if not KANA_OR_HAN_RE.search(value):
        _fail(f"{key}.translation_ja needs Japanese kana or Han")
    if LATIN_DIACRITIC_RE.search(value):
        _fail(f"{key}.translation_ja contains a non-ASCII Latin letter")


def _target_readings(
    sentence: str, target: str, alignment: list[tuple[int, int, str, str]],
) -> list[str]:
    han = "".join(HAN_RE.findall(sentence))
    result: list[str] = []
    start = 0
    while True:
        start = han.find(target, start)
        if start < 0:
            break
        end = start + len(target)
        parts = [marked for left, right, marked, _ in alignment if left >= start and right <= end]
        if parts and min(left for left, right, _, _ in alignment if left >= start and right <= end) == start:
            covered = sum(right - left for left, right, _, _ in alignment if left >= start and right <= end)
            if covered == len(target):
                result.append("".join(parts))
        start += 1
    return result


def _validate_task6_zh(
    value: dict[str, Any], source: dict[str, Any], warnings: list[dict[str, str]],
) -> None:
    key, sentence, pinyin = value["key"], value["sentence"], value["pinyin"]
    if not ZH_SENTENCE_RE.fullmatch(sentence):
        _fail(f"{key}.sentence contains a non-Chinese character or unsupported punctuation")
    han = HAN_RE.findall(sentence)
    if not (1 <= len(han) <= 30):
        _fail(f"{key}.sentence must contain 1-30 Han characters")
    if not re.search(r"[。！？][”’]?$", sentence):
        _fail(f"{key}.sentence must end in Chinese sentence punctuation")
    target = str(source["target"])
    if target not in sentence:
        _fail(f"{key}.sentence does not contain target")
    traditional_only, pinyin_by_simp, word_forms = _task6_reference()
    bad_trad = sorted(set(han) & traditional_only)
    if bad_trad:
        _fail(f"{key}.sentence contains traditional-only character: {''.join(bad_trad)}")
    normalized_pinyin = pinyin.replace("’", "'")
    if not ZH_PINYIN_RE.fullmatch(normalized_pinyin) or re.search(r"\d|v|u:", normalized_pinyin, re.I):
        _fail(f"{key}.pinyin contains an invalid character or notation")
    alignments = _pinyin_alignments(sentence, normalized_pinyin)
    if not alignments:
        _fail(f"{key}: pinyin does not align with the characters")
    readings = {
        reading.casefold().replace("'", "").replace(" ", "")
        for alignment in alignments for reading in _target_readings(sentence, target, alignment)
    }
    expected = str(source["target_pinyin"]).casefold().replace("'", "").replace(" ", "")
    if readings != {expected}:
        _fail(f"{key}: target pinyin differs or is ambiguous; expected {expected!r}, got {sorted(readings)!r}")
    for alignment in alignments:
        for left, right, marked, base in alignment:
            char = han[left]
            if char == "一" and marked.casefold() not in {"yī", "yi"}:
                _fail(f"{key}: 一 must use dictionary tone yī/yi")
            if char == "不" and marked.casefold() not in {"bù", "bu"}:
                _fail(f"{key}: 不 must use dictionary tone bù/bu")
    alignment = alignments[0]
    for left, right, marked, base in alignment:
        char = han[left]
        known = pinyin_by_simp.get(char, set())
        if known and base not in known:
            warnings.append({"key": key, "warning": "pinyin_reading", "character": char, "syllable": marked})
    occurrences = sentence.count(target)
    if occurrences > 1:
        warnings.append({"key": key, "warning": "target_multiple", "count": str(occurrences)})
    for position in [match.start() for match in re.finditer(re.escape(target), sentence)]:
        before = sentence[position - 1:position] if position else ""
        after = sentence[position + len(target):position + len(target) + 1]
        if (before and before + target in word_forms) or (after and target + after in word_forms):
            warnings.append({"key": key, "warning": "target_inside_longer_word"})
            break


def _validate_task6_vi(value: dict[str, Any], source: dict[str, Any], warnings: list[dict[str, str]]) -> None:
    key, sentence, target = value["key"], value["sentence"], str(source["target"])
    def allowed_char(char: str) -> bool:
        if char.isascii():
            return char.isalpha() or char.isdigit() or char.isspace() or char in VI_PUNCTUATION
        if char in "Đđ":
            return True
        decomposed = unicodedata.normalize("NFD", char)
        return (bool(decomposed) and decomposed[0] in "AEIOUYaeiouy"
                and bool(decomposed[1:]) and set(decomposed[1:]).issubset(VI_VOWEL_COMBINERS))
    if not all(allowed_char(char) for char in sentence):
        _fail(f"{key}.sentence contains a non-Vietnamese character or unsupported punctuation")
    if not re.match(r'^["“‘]?\s*[A-ZÀ-ỸĐ]', sentence):
        _fail(f"{key}.sentence must start with an upper-case letter")
    if not re.search(r"[.!?][”’\"]?$", sentence):
        _fail(f"{key}.sentence must end with sentence punctuation")
    tokens = [token for token in re.split(r"[\s\-–]+", re.sub(r'[,!.?;:"\'“”‘’()…]', "", sentence)) if token]
    if not (3 <= len(tokens) <= 25):
        _fail(f"{key}.sentence must contain 3-25 syllables")
    for token in tokens:
        if sum(char in VI_TONE_COMBINERS for char in unicodedata.normalize("NFD", token)) > 1:
            _fail(f"{key}.sentence syllable has more than one tone mark: {token!r}")
    pattern = re.compile(rf"(?<![A-Za-zÀ-ỹĐđ]){re.escape(target)}(?![A-Za-zÀ-ỹĐđ])", re.I)
    matches = list(pattern.finditer(sentence.casefold()))
    if not matches:
        _fail(f"{key}.sentence does not contain target as a whole word")
    if len(matches) > 1:
        warnings.append({"key": key, "warning": "target_multiple", "count": str(len(matches))})


def validate_task6_items(
    output: Any, inputs: list[dict[str, Any]], kind: str,
) -> tuple[list[dict[str, Any]], dict[str, str], list[dict[str, str]]]:
    """Validate item rules while preserving valid task-6 items for repair."""
    values = _task6_batch(output, inputs, kind)
    input_map = {str(item["key"]): item for item in inputs}
    valid: list[dict[str, Any]] = []
    errors: dict[str, str] = {}
    warnings: list[dict[str, str]] = []
    for value in values:
        key = value["key"]
        try:
            _task6_common_item(value)
            if kind == "note":
                note = value["note_ja"]
                if len(note) > 60 or (note and not KANA_RE.search(note)):
                    _fail(f"{key}.note_ja must be empty or at most 60 characters with kana")
                if not note:
                    warnings.append({"key": key, "warning": "empty_note_ja"})
            else:
                empty_fields = ["sentence", "translation_ja"] + (["pinyin"] if kind == "zh" else [])
                if value["status"] == "no_sentence":
                    if any(value[field] for field in empty_fields) or not value["review_note"]:
                        _fail(f"{key}: no_sentence requires empty content and a review_note")
                else:
                    if any(not value[field] for field in empty_fields):
                        _fail(f"{key}: ok requires sentence, translation and zh pinyin")
                    _validate_translation(key, value["translation_ja"])
                    if kind == "zh":
                        _validate_task6_zh(value, input_map[key], warnings)
                    else:
                        _validate_task6_vi(value, input_map[key], warnings)
            valid.append(value)
        except ValidationError as exc:
            errors[key] = str(exc).replace("\n", " ").replace("\r", " ")
    return valid, errors, warnings


def validate_task6(output: Any, inputs: list[dict[str, Any]], kind: str) -> list[dict[str, str]]:
    _, errors, warnings = validate_task6_items(output, inputs, kind)
    if errors:
        key = next(iter(errors))
        _fail(errors[key])
    return warnings


def validate(
    task: int, output: Any, inputs: list[dict[str, Any]], kind: str | None = None,
) -> list[dict[str, str]]:
    if task == 6:
        if kind is None:
            _fail("Task 6 validation requires a kind")
        return validate_task6(output, inputs, kind)
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
TASK6_ZH_ITEM_SCHEMA = _object({
    "key": STRING,
    "status": {"type": "string", "enum": ["ok", "no_sentence"]},
    "sentence": STRING,
    "pinyin": STRING,
    "translation_ja": STRING,
    "confidence": {"type": "string", "enum": ["high", "low"]},
    "review_note": STRING,
}, TASK6_KEYS["zh"])
TASK6_VI_ITEM_SCHEMA = _object({
    "key": STRING,
    "status": {"type": "string", "enum": ["ok", "no_sentence"]},
    "sentence": STRING,
    "translation_ja": STRING,
    "confidence": {"type": "string", "enum": ["high", "low"]},
    "review_note": STRING,
}, TASK6_KEYS["vi"])
TASK6_NOTE_ITEM_SCHEMA = _object({
    "key": STRING,
    "note_ja": STRING,
    "confidence": {"type": "string", "enum": ["high", "low"]},
    "review_note": STRING,
}, TASK6_KEYS["note"])
RESPONSE_SCHEMAS = {
    1: {"type": "array", "items": TASK1_ITEM_SCHEMA},
    2: {"type": "array", "items": TASK2_ITEM_SCHEMA},
    3: TASK3_SCHEMA,
    4: {"type": "array", "items": TASK4_ITEM_SCHEMA},
    5: {"type": "array", "items": TASK5_ITEM_SCHEMA},
    6: {
        "zh": {"type": "array", "items": TASK6_ZH_ITEM_SCHEMA},
        "vi": {"type": "array", "items": TASK6_VI_ITEM_SCHEMA},
        "note": {"type": "array", "items": TASK6_NOTE_ITEM_SCHEMA},
    },
}
