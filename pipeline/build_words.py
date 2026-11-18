"""Build Stage 3 words, extend chars, align readings, and write review reports."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import pandas as pd

from build_chars import CHAR_COLUMNS, choose_jp, pinyin_values
from common import (
    FINAL, ROOT, STAGING, all_cjk, assign_ids, hangul_final, nfc, normalize_vietnamese,
    merge_with_report, require_nfc, split_multi, unique_preserve, vietnamese_final,
    write_csv, write_json,
)
from stage3_match import (
    ReadingLookup, canonicalize_a2_spelling, collapse_iy, find_jmdict, generate_variant_forms, initial_of,
    korean_base, korean_normalized_base, law_penalty, make_jmdict_index,
    strict_priority, tags, toneless, variant_char, vowel_of,
)


WORD_COLUMNS = [
    "word_id", "trad", "simp", "jp", "ja", "ja_common", "ko", "pinyin", "vi",
    "ja_alt", "ko_alt", "vi_alt", "pos", "hsk_ids", "gloss_en", "gloss_ja_en",
    "gloss_ko", "gloss_vi", "meaning_ja__ja", "meaning_ja__ko", "meaning_ja__zh",
    "meaning_ja__vi", "note_ja", "level", "freq_vi", "origin", "card_eligible",
    "false_friend", "syl_aligned", "verified", "ja_use", "ko_use", "vi_use",
    "source_ja", "source_ko",
    "source_pinyin", "source_vi", "source_level",
]
VARIANT_FIELDS = [
    "kCompatibilityVariant", "kZVariant", "kSemanticVariant", "kSpecializedSemanticVariant"
]
OVERRIDE_COLUMNS = ["table", "key", "column", "value", "reason"]
REPORT_COLUMNS = {
    "cedict_unmatched": ["trad", "simp", "pinyin", "cedict_key", "reason"],
    "ja_multi_candidates": ["word_key", "word_id", "trad", "pinyin", "level", "candidates"],
    "ko_multi_candidates": ["word_key", "word_id", "trad", "pinyin", "level", "candidates", "chosen"],
    "ko_unresolved": ["word_key", "word_id", "trad", "pinyin", "forms", "candidates", "reason"],
    "vi_ambiguous": ["word_key", "word_id", "trad", "pinyin", "level", "candidates", "reason"],
    "char_ambiguous": ["word_id", "trad", "position", "char", "candidates", "reason"],
    "char_simp_mismatch": ["word_id", "trad", "simp", "position", "char_id", "char_simp", "word_simp"],
    "alignment_mismatches": ["word_id", "lang", "reason", "detail"],
}


def read_stage(name: str) -> pd.DataFrame:
    return pd.read_csv(STAGING / name, encoding="utf-8", keep_default_na=False, dtype=str)


def ordered_union(values: Iterable[object]) -> str:
    return ";".join(unique_preserve(values))


def normalize_hsk_pinyin(value: object) -> str:
    return nfc(value).lower().replace(" ", "")


def build_hsk_words(merge_rows: list[dict[str, object]]) -> pd.DataFrame:
    raw = read_stage("hsk30_words.csv")
    raw["pinyin"] = raw["pinyin"].map(normalize_hsk_pinyin)
    rows = []
    for (trad, pinyin), group in raw.groupby(["trad", "pinyin"], sort=False):
        for column in ["simp", "cedict_key"]:
            if group[column].nunique() != 1:
                raise ValueError(f"HSK duplicate group conflicts in {column}: {(trad, pinyin)}")
        rows.append({
            "trad": trad, "simp": group.iloc[0]["simp"], "pinyin": pinyin,
            "level": int(group["level"].astype(int).min()),
            "pos": ordered_union(group["pos"]), "hsk_ids": ordered_union(group["hsk_id"]),
            "cedict_key": group.iloc[0]["cedict_key"],
            "source_order": int(group["source_order"].astype(int).min()),
            "word_key": f"{trad}|{pinyin}", "origin": "hsk", "source_level": "hsk30",
        })
    frame = pd.DataFrame(rows).sort_values("source_order", kind="stable").reset_index(drop=True)
    merge_rows.extend([
        {"merge": "hsk_dedupe", "status": "input", "count": len(raw), "validate": "unique after group"},
        {"merge": "hsk_dedupe", "status": "output", "count": len(frame), "validate": "unique after group"},
    ])
    if len(frame) != 11028 or frame.duplicated(["trad", "pinyin"]).any():
        raise ValueError(f"D41 expected 11,028 unique HSK rows, got {len(frame):,}")
    return frame


def attach_cedict(words: pd.DataFrame, merge_rows: list[dict[str, object]]) -> pd.DataFrame:
    cedict = read_stage("cedict.csv")
    exact = cedict[[
        "cedict_key", "gloss_en", "pinyin_spaced"
    ]].rename(columns={
        "gloss_en": "cedict_gloss_en",
        "pinyin_spaced": "cedict_pinyin_spaced_exact",
    })
    merged = merge_with_report(
        words,
        exact,
        name="words_cedict_exact",
        reports=merge_rows,
        how="left",
        validate="m:1",
        on="cedict_key",
    )
    indicator = "_merge_words_cedict_exact"
    by_trad: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in cedict.to_dict(orient="records"):
        by_trad[nfc(item["trad"])].append(item)
    outputs = []
    unmatched = []
    fallback_matches = []
    for _index, row in merged.iterrows():
        chosen = None
        mode = ""
        if row[indicator] == "both":
            mode = "exact"
        else:
            candidates = pd.DataFrame(by_trad.get(row.trad, []))
            if not candidates.empty:
                full = candidates.loc[candidates["pinyin"].map(toneless) == toneless(row.pinyin)]
                exact_letters_tones = candidates.loc[
                    candidates["pinyin"].map(lambda value: nfc(value).replace("'", ""))
                    == nfc(row.pinyin).replace("'", "")
                ]
                if len(exact_letters_tones) == 1:
                    chosen, mode = exact_letters_tones.iloc[0], "trad_pinyin"
                elif len(full) == 1:
                    chosen, mode = full.iloc[0], "trad_toneless_unique"
            if chosen is not None:
                fallback_matches.append({"word_key": row.word_key})
        data = row.to_dict()
        data.pop(indicator, None)
        exact_gloss = nfc(data.pop("cedict_gloss_en", ""))
        exact_spaced = nfc(data.pop("cedict_pinyin_spaced_exact", ""))
        if mode == "exact":
            data.update({
                "gloss_en": exact_gloss,
                "cedict_pinyin_spaced": exact_spaced,
                "source_pinyin": "hsk30",
                "cedict_match": mode,
            })
        elif chosen is None:
            data.update({"gloss_en": "", "cedict_pinyin_spaced": "", "source_pinyin": "hsk30"})
            unmatched.append({
                "trad": row.trad, "simp": row.simp, "pinyin": row.pinyin,
                "cedict_key": row.cedict_key, "reason": "no same-letter CC-CEDICT entry",
            })
        else:
            data.update({
                "gloss_en": nfc(chosen["gloss_en"]),
                "cedict_pinyin_spaced": nfc(chosen["pinyin_spaced"]),
                "source_pinyin": "hsk30", "cedict_match": mode,
            })
        outputs.append(data)
    fallback_backbone = merged.loc[merged[indicator] == "left_only", ["word_key"]]
    fallback_frame = pd.DataFrame(fallback_matches, columns=["word_key"])
    fallback_audit = merge_with_report(
        fallback_backbone,
        fallback_frame,
        name="words_cedict_fallback",
        reports=merge_rows,
        how="left",
        validate="1:1",
        on="word_key",
    )
    del fallback_audit
    write_csv(pd.DataFrame(unmatched, columns=REPORT_COLUMNS["cedict_unmatched"]), FINAL / "cedict_unmatched.csv")
    return pd.DataFrame(outputs)


def make_variant_graph(unihan: pd.DataFrame, opencc: pd.DataFrame) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = defaultdict(list)
    for row in unihan.itertuples(index=False):
        for field in VARIANT_FIELDS:
            for other in variant_char(getattr(row, field)):
                graph[row.char].append(other)
                graph[other].append(row.char)
    for row in opencc.itertuples(index=False):
        graph[row.trad].append(row.jp_candidate)
        graph[row.jp_candidate].append(row.trad)
    for first, second in [("青", "靑"), ("清", "淸")]:
        graph[first].append(second)
        graph[second].append(first)
    return {key: unique_preserve(values) for key, values in graph.items()}


def make_lookup() -> tuple[ReadingLookup, dict[str, dict[str, object]], dict[str, list[str]], set[str]]:
    unihan = read_stage("unihan.csv")
    kd_frame = read_stage("kanjidic2.csv")
    lib = read_stage("libhangul.csv")
    kaikki_chars = read_stage("kaikki_char_readings.csv")
    kaikkien_chars = read_stage("kaikki_en_char_readings.csv")
    vi_config_path = ROOT / "config" / "vi_sources.json"
    vi_config = json.loads(vi_config_path.read_text(encoding="utf-8")) if vi_config_path.exists() else {}
    enable_kaikki_en_chars = vi_config.get("kaikki_en_char_readings") is True
    hv = set(read_stage("kaikki_hv_syllables.csv")["vi"].map(nfc))
    kd = {row.literal: row._asdict() for row in kd_frame.itertuples(index=False)}
    lib_map = {key: unique_preserve(group["ko"]) for key, group in lib.groupby("char", sort=False)}
    kaikki_map = {key: unique_preserve(group["vi"]) for key, group in kaikki_chars.groupby("char", sort=False)}
    kaikkien_map = {
        key: unique_preserve(group["vi"]) for key, group in kaikkien_chars.groupby("char", sort=False)
    }
    ko: dict[str, list[str]] = {}
    vi: dict[str, list[str]] = {}
    vi_source: dict[tuple[str, str], str] = {}
    pinyin: dict[str, list[str]] = {}
    for row in unihan.itertuples(index=False):
        ko[row.char] = unique_preserve([*split_multi(row.kHangul), *lib_map.get(row.char, [])])
        kaikki_values = kaikki_map.get(row.char, [])
        unihan_values = split_multi(row.kVietnamese)
        hvsyl = [value for value in unihan_values if value in hv]
        en_values = kaikkien_map.get(row.char, []) if enable_kaikki_en_chars else []
        confirmed_en = [value for value in en_values if value in unihan_values]
        if not unihan_values and not kaikki_values and not hvsyl:
            confirmed_en = en_values
        vi[row.char] = unique_preserve([*kaikki_values, *confirmed_en, *hvsyl])
        for value in vi[row.char]:
            if value in kaikki_values:
                vi_source[(row.char, value)] = "kaikki_aligned"
            elif value in confirmed_en:
                vi_source[(row.char, value)] = "kaikki_en_char"
            else:
                vi_source[(row.char, value)] = "unihan_hvsyl"
        pinyin[row.char] = unique_preserve([
            *pinyin_values(row.kMandarin), *pinyin_values(row.kHanyuPinyin, referenced=True),
            *pinyin_values(row.kXHC1983, referenced=True),
        ])
    for char, readings in lib_map.items():
        ko.setdefault(char, readings)
    for char, readings in kaikki_map.items():
        vi.setdefault(char, readings)
        for value in readings:
            vi_source[(char, value)] = "kaikki_aligned"
    ja_on = {key: split_multi(value["ja_on_all"]) for key, value in kd.items()}
    lookup = ReadingLookup(ko=ko, vi=vi, vi_source=vi_source, ja_on=ja_on, pinyin=pinyin)
    graph = make_variant_graph(unihan, read_stage("opencc.csv"))
    return lookup, kd, graph, hv


def phrase_inverse() -> dict[str, list[str]]:
    frame = read_stage("opencc_phrases.csv")
    result: dict[str, list[str]] = defaultdict(list)
    for row in frame.itertuples(index=False):
        result[row.trad_phrase].append(row.jp_candidate)
    return result


def charwise_jp(word: str, base_chars: pd.DataFrame) -> str:
    by_key = base_chars.drop_duplicates("key_char").set_index("key_char")
    values = []
    for char in word:
        if char not in by_key.index or not nfc(by_key.loc[char, "jp"]):
            return ""
        values.append(nfc(by_key.loc[char, "jp"]))
    return "".join(values)


def word_forms(row: object, graph: dict[str, list[str]], phrases: dict[str, list[str]]) -> list[str]:
    values = [nfc(getattr(row, "jp_form", "")), nfc(row.trad), nfc(getattr(row, "key_form", ""))]
    values.extend(phrases.get(nfc(row.trad), []))
    if len(nfc(row.trad)) >= 2:
        values.append(nfc(row.simp))
        values.extend(generate_variant_forms(nfc(row.trad), graph))
    return unique_preserve(values)


def prepare_forms(words: pd.DataFrame, chars: pd.DataFrame) -> pd.DataFrame:
    result = words.copy()
    trad_groups = {key: group for key, group in chars.groupby("trad", sort=False)}
    key_index = chars.drop_duplicates("key_char").set_index("key_char")
    jp_forms = []
    key_forms = []
    linked_ja_on_all = []
    for row in result.itertuples(index=False):
        jp_values = []
        key_values = []
        for position, char in enumerate(row.trad):
            group = trad_groups.get(char, pd.DataFrame())
            selected = None
            if len(group) == 1:
                selected = group.iloc[0]
            elif len(group) > 1 and position < len(row.simp):
                exact = group.loc[group["simp"] == row.simp[position]]
                if len(exact) == 1:
                    selected = exact.iloc[0]
            elif char in key_index.index:
                selected = key_index.loc[char]
            if selected is None:
                key_values.append(char)
                jp_values.append("")
            else:
                key_values.append(nfc(selected["key_char"]))
                jp_values.append(nfc(selected["jp"]))
        key_forms.append("".join(key_values))
        jp_forms.append("".join(jp_values) if all(jp_values) else "")
        if len(row.trad) == 1 and selected is not None:
            linked_ja_on_all.append(nfc(selected["ja_on_all"]))
        else:
            linked_ja_on_all.append("")
    result["key_form"] = key_forms
    result["jp_form"] = jp_forms
    result["linked_ja_on_all"] = linked_ja_on_all
    return result


def match_japanese_row(
    row: object,
    index: dict[str, list[dict[str, object]]],
    graph: dict[str, list[str]],
    phrases: dict[str, list[str]],
    lookup: ReadingLookup,
) -> dict[str, object]:
    form, candidates = find_jmdict(word_forms(row, graph, phrases), index)
    if candidates.empty:
        return {
            "jp": "", "ja": "", "ja_alt": "", "ja_common": False,
            "gloss_ja_en": "", "source_ja": "", "ja_priority_count": 0,
            "ja_candidates": "",
        }
    pairs = candidates.drop_duplicates("reb", keep="first")
    readings = pairs["reb"].tolist()
    top = pairs.iloc[0]
    ja = readings[0]
    source = "jmdict"
    if len(row.trad) == 1:
        on = split_multi(getattr(row, "linked_ja_on_all", ""))
        matched = [reading for reading in readings if reading in on and not re.search(r"[ァ-ヶ]", reading)]
        if matched:
            ja = matched[0]
        elif on:
            ja = on[0]
            source = "kanjidic2_on"
        else:
            non_katakana = [reading for reading in readings if not re.search(r"[ァ-ヶ]", reading)]
            ja = non_katakana[0] if non_katakana else ""
        alt = [reading for reading in readings if reading != ja]
    else:
        alt = readings[1:]
    priority_readings = unique_preserve(
        pair.reb for pair in pairs.itertuples(index=False)
        if strict_priority(pair.re_pri)
    )
    return {
        "jp": form, "ja": ja, "ja_alt": ";".join(alt),
        "ja_common": bool(strict_priority(top["re_pri"]) or strict_priority(top["ke_pri"])),
        "gloss_ja_en": nfc(top["gloss_ja_en"]), "source_ja": source,
        "ja_priority_count": len(priority_readings),
        "ja_candidates": ";".join(readings),
    }


def libhangul_index() -> dict[str, list[object]]:
    frame = read_stage("libhangul_words.csv")
    result: dict[str, list[object]] = defaultdict(list)
    for row in frame.itertuples(index=False):
        result[row.hanja].append(row)
    return result


def korean_candidates(
    row: object,
    index: dict[str, list[object]],
    graph: dict[str, list[str]],
    lookup: ReadingLookup,
) -> tuple[list[dict[str, object]], list[str]]:
    forms = unique_preserve([
        nfc(row.trad), nfc(row.jp_form), nfc(row.key_form), nfc(row.simp),
        *generate_variant_forms(nfc(row.trad), graph),
    ])
    candidates = []
    for form_order, form in enumerate(forms):
        if form not in index:
            continue
        for record in index[form]:
            reading = nfc(record.reading)
            if len(reading) != len(row.trad):
                continue
            bases = []
            valid = True
            exception = ""
            for position, (char, syllable) in enumerate(zip(row.trad, reading)):
                base = korean_base(syllable, lookup.ko.get(char, []), position)
                if not base and reading in {"숫자", "찻간"}:
                    base = syllable[:-1] if False else ("수" if syllable == "숫" else "차")
                    exception = reading
                if reading == "곤란" and position == 1 and syllable == "란" and base == "난":
                    exception = reading
                if not base:
                    valid = False
                    break
                bases.append(base)
            if not valid:
                continue
            candidates.append({
                "reading": reading, "bases": bases, "form": form,
                "source": "libhangul" if form in {row.trad, row.jp_form, row.key_form, row.simp} else "libhangul_variant",
                "form_order": form_order, "source_order": int(record.source_order),
                "comment": nfc(record.comment), "exception": exception,
            })
    unique = {}
    for candidate in sorted(candidates, key=lambda item: (law_penalty(item["reading"]), item["form_order"], item["source_order"])):
        unique.setdefault(candidate["reading"], candidate)
    values = list(unique.values())
    if len(row.trad) > 1 and len(values) > 1:
        filtered = []
        for candidate in values:
            discard = False
            for other in values:
                if law_penalty(other["reading"]) >= law_penalty(candidate["reading"]):
                    continue
                related = all(
                    left == right
                    or korean_base(left, [right], position) == right
                    or korean_base(right, [left], position) == left
                    for position, (left, right) in enumerate(zip(candidate["reading"], other["reading"]))
                )
                if related:
                    discard = True
                    break
            if not discard:
                filtered.append(candidate)
        values = filtered
    return values, forms


def choose_korean(
    row: object,
    candidates: list[dict[str, object]],
    char_counts: dict[tuple[str, str], int],
    pinyin_counts: dict[tuple[str, str, str], int],
) -> tuple[str, list[str]]:
    if not candidates:
        return "", []
    if len(candidates) == 1:
        return candidates[0]["reading"], []
    for preferred in ["숫자", "찻간", "곤란"]:
        if any(candidate["reading"] == preferred for candidate in candidates):
            return preferred, [candidate["reading"] for candidate in candidates if candidate["reading"] != preferred]
    if len(row.trad) == 1:
        base_targets = []
        for candidate in candidates:
            reading = candidate["reading"]
            if any(
                other["reading"] != reading
                and korean_base(other["reading"], [reading], 0) == reading
                for other in candidates
            ):
                base_targets.append(reading)
        if len(unique_preserve(base_targets)) == 1:
            chosen = unique_preserve(base_targets)[0]
            return chosen, [candidate["reading"] for candidate in candidates if candidate["reading"] != chosen]
        bases = unique_preserve(base for candidate in candidates for base in candidate["bases"])
        if len(bases) == 1:
            return bases[0], [candidate["reading"] for candidate in candidates if candidate["reading"] != bases[0]]
        scored = []
        pinyin_syllable = nfc(row.pinyin)
        for candidate in candidates:
            base = candidate["bases"][0]
            score = pinyin_counts.get((row.trad, pinyin_syllable, base), 0)
            scored.append((score, char_counts.get((row.trad, base), 0), candidate))
        scored.sort(key=lambda value: (-value[0], -value[1], value[2]["source_order"]))
        if scored[0][0] == scored[1][0] and scored[0][1] == scored[1][1] and scored[0][0] == 0:
            return "", [value[2]["reading"] for value in scored]
        chosen = scored[0][2]["reading"]
        return chosen, [value[2]["reading"] for value in scored[1:]]
    scored = []
    for candidate in candidates:
        score = sum(char_counts.get((char, base), 0) for char, base in zip(row.trad, candidate["bases"]))
        scored.append((score, candidate))
    scored.sort(key=lambda value: (-value[0], law_penalty(value[1]["reading"]), value[1]["source_order"]))
    chosen = scored[0][1]["reading"]
    return chosen, [value[1]["reading"] for value in scored[1:]]


def explicit_index() -> dict[str, pd.DataFrame]:
    frame = read_stage("kaikki.csv")
    return {key: group.copy() for key, group in frame.groupby("han", sort=False)}


def kaikki_en_index() -> dict[str, pd.DataFrame]:
    frame = read_stage("kaikki_en.csv")
    frame["obsolete_only"] = frame["obsolete_only"].str.lower().isin({"true", "1"})
    return {key: group.copy() for key, group in frame.groupby("han", sort=False)}


def kaikki_en_candidates(
    row: object,
    explicit_en: dict[str, pd.DataFrame],
    graph: dict[str, list[str]],
) -> list[dict[str, object]]:
    trad = nfc(row.trad)
    forms = [trad] if len(trad) == 1 else unique_preserve(
        [trad, getattr(row, "simp", ""), *generate_variant_forms(trad, graph)]
    )
    values: list[dict[str, object]] = []
    for form in forms:
        group = explicit_en.get(form)
        if group is None:
            continue
        for record in group.itertuples(index=False):
            vi = canonicalize_a2_spelling(normalize_vietnamese(record.vi))
            if len(vi.split()) == len(trad):
                values.append({
                    "vi": vi,
                    "source": "kaikki_en_han",
                    "gloss_vi": nfc(record.gloss_vi),
                    "obsolete_only": bool(record.obsolete_only),
                    "rule_b_conflict": False,
                })
        if values:
            break
    collapsed = collapse_iy(value["vi"] for value in values)
    return [next(value for value in values if value["vi"] == vi) for vi in collapsed]


def headword_index() -> dict[str, dict[str, object]]:
    frame = read_stage("kaikki_headwords.csv")
    return {
        row.vi: {"gloss_vi": nfc(row.gloss_vi), "han_forms": split_multi(row.han_forms)}
        for row in frame.itertuples(index=False)
    }


def vi_candidates(
    row: object,
    explicit: dict[str, pd.DataFrame],
    graph: dict[str, list[str]],
    lookup: ReadingLookup,
    headwords: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    trad = nfc(row.trad)
    if len(trad) == 1:
        forms = [trad]
    else:
        forms = unique_preserve([trad, row.simp, *generate_variant_forms(trad, graph)])
    values: list[dict[str, str]] = []
    for form in forms:
        if form not in explicit:
            continue
        for record in explicit[form].itertuples(index=False):
            vi = normalize_vietnamese(record.vi)
            if len(vi.split()) == len(row.trad):
                values.append({
                    "vi": vi, "source": "kaikki_han", "gloss_vi": nfc(record.gloss_vi),
                    "rule_b_conflict": False,
                })
        if values:
            break
    if not values:
        choices = [lookup.vi.get(char, []) for char in row.trad]
        product_size = math.prod(len(choice) for choice in choices) if all(choices) else 0
        if 0 < product_size <= 512:
            products = [" ".join(parts) for parts in __import__("itertools").product(*choices)]
            for vi in products:
                if vi in headwords:
                    info = headwords[vi]
                    han_forms = set(info["han_forms"])
                    conflict = bool(
                        len(trad) >= 2
                        and han_forms
                        and not han_forms.intersection(forms)
                    )
                    values.append({
                        "vi": vi,
                        "source": "composed_attested",
                        "gloss_vi": nfc(info["gloss_vi"]),
                        "rule_b_conflict": conflict,
                    })
    preferred = collapse_iy(value["vi"] for value in values)
    result = []
    for vi in preferred:
        result.append(next(value for value in values if value["vi"] == vi))
    return result


def frequency_score(value: object, counts: dict[str, int]) -> int | None:
    syllables = normalize_vietnamese(value).split()
    if not syllables or any(syllable not in counts for syllable in syllables):
        return None
    return min(counts[syllable] for syllable in syllables)


def prefer_existing_vi(current: object, a2_value: object) -> str:
    """D53 rule A2 fills only an empty Vietnamese value."""
    return nfc(current) or nfc(a2_value)


def initial_jp_form(word: str, kd: dict[str, dict[str, object]], opencc: pd.DataFrame) -> str:
    candidates: dict[str, list[str]] = defaultdict(list)
    for row in opencc.itertuples(index=False):
        candidates[row.trad].append(row.jp_candidate)
    values = []
    for char in word:
        selected = choose_jp(char, ";".join(candidates.get(char, [])), kd)
        if not selected:
            return ""
        values.append(selected)
    return "".join(values)


def select_vi_only(
    hsk: pd.DataFrame,
    lookup: ReadingLookup,
    kd: dict[str, dict[str, object]],
    graph: dict[str, list[str]],
    jmdict_index: dict[str, list[dict[str, object]]],
    korean_index: dict[str, list[object]],
    phrases: dict[str, list[str]],
    explicit: dict[str, pd.DataFrame],
    explicit_en: dict[str, pd.DataFrame],
    headwords: dict[str, dict[str, object]],
    frequency: dict[str, int],
    merge_rows: list[dict[str, object]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    opencc = read_stage("opencc.csv")
    cedict = read_stage("cedict.csv")
    cedict_trad: dict[str, list[dict[str, object]]] = defaultdict(list)
    cedict_simp: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in cedict.to_dict(orient="records"):
        cedict_trad[nfc(item["trad"])].append(item)
        cedict_simp[nfc(item["simp"])].append(item)
    hsk_forms = set(hsk["trad"]) | set(hsk["simp"])
    hsk_variant_forms = set()
    for form in hsk_forms:
        hsk_variant_forms.update(generate_variant_forms(form, graph))
    rows = []
    report = []
    kaikki_rule_a = pd.DataFrame([
        {"han": han, "vi_values_rule_a": ";".join(collapse_iy(group["vi"]))}
        for han, group in explicit.items()
    ])
    outer = merge_with_report(
        hsk[["trad"]],
        kaikki_rule_a,
        name="words_kaikki_outer",
        reports=merge_rows,
        how="outer",
        validate="m:1",
        left_on="trad",
        right_on="han",
    )
    del outer
    candidate_groups: dict[str, tuple[pd.DataFrame, str]] = {
        han: (group, "kaikki_han") for han, group in explicit.items()
    }
    for han, group in explicit_en.items():
        if han not in candidate_groups and len(han) >= 2:
            candidate_groups[han] = (group, "kaikki_en_han")

    for han, (group, source_vi) in candidate_groups.items():
        vis = collapse_iy(
            (
                canonicalize_a2_spelling(normalize_vietnamese(row.vi))
                if source_vi == "kaikki_en_han"
                else normalize_vietnamese(row.vi)
            )
            for row in group.itertuples(index=False)
            if len(normalize_vietnamese(row.vi).split()) == len(han)
            and not bool(getattr(row, "obsolete_only", False))
        )
        base = {
            "han": han, "vi_values": ";".join(vis), "source_vi": source_vi,
            "selected": False, "reason": "",
        }
        if len(han) < 2:
            report.append({**base, "reason": "single_character"})
            continue
        if han in hsk_forms or han in hsk_variant_forms:
            report.append({**base, "reason": "hsk_or_variant"})
            continue
        if len(vis) != 1:
            reason = "obsolete_only" if source_vi == "kaikki_en_han" and not vis else "ambiguous_vi"
            report.append({**base, "reason": reason})
            continue
        vi = vis[0]
        score = frequency_score(vi, frequency)
        if score is None:
            report.append({**base, "reason": "no_frequency"})
            continue
        cc = pd.DataFrame(cedict_trad.get(han, []))
        if cc.empty:
            cc = pd.DataFrame(cedict_simp.get(han, []))
        if not cc.empty and cc["trad"].nunique() == 1:
            chosen_cc = cc.iloc[0]
            trad = nfc(chosen_cc["trad"])
            simp = nfc(chosen_cc["simp"])
            pinyin = nfc(chosen_cc["pinyin"])
            cedict_spaced = nfc(chosen_cc["pinyin_spaced"])
            gloss_en = nfc(chosen_cc["gloss_en"])
        else:
            trad, simp = han, ""
            pinyin = cedict_spaced = gloss_en = ""
        pseudo = type("Word", (), {
            "trad": trad, "simp": simp, "pinyin": pinyin,
            "jp_form": initial_jp_form(trad, kd, opencc), "key_form": trad,
        })()
        ja_match = match_japanese_row(pseudo, jmdict_index, graph, phrases, lookup)
        ko_candidates, _forms = korean_candidates(pseudo, korean_index, graph, lookup)
        if not ja_match["ja"] and not ko_candidates:
            report.append({**base, "reason": "no_ja_or_ko"})
            continue
        ko = ko_candidates[0]["reading"] if len(ko_candidates) == 1 else ""
        rows.append({
            "han": han,
            "trad": trad, "simp": simp, "pinyin": pinyin, "level": 0,
            "pos": "", "hsk_ids": "", "cedict_key": "", "source_order": 0,
            "word_key": f"x|{trad}", "origin": "vi_freq", "source_level": "vi_band",
            "gloss_en": gloss_en, "cedict_pinyin_spaced": cedict_spaced,
            "source_pinyin": "cc-cedict" if pinyin else "", "vi": vi,
            "source_vi": source_vi, "gloss_vi": nfc(group.iloc[0]["gloss_vi"]),
            "freq_score": score, "pre_ja_common": bool(ja_match["ja_common"]),
            "pre_jp": nfc(ja_match["jp"]) or nfc(pseudo.jp_form),
            "candidate_ko": ko,
        })
        report.append({**base, "reason": "candidate", "freq_score": score})

    # D46 seed: dictionary-composed 越南, kept outside the 1,200 cap.
    if not any(row["trad"] == "越南" for row in rows):
        seed = type("Word", (), {
            "trad": "越南", "simp": "越南", "pinyin": "",
            "jp_form": initial_jp_form("越南", kd, opencc), "key_form": "越南",
        })()
        candidates = [
            value for value in vi_candidates(seed, explicit, graph, lookup, headwords)
            if not value.get("rule_b_conflict", False)
        ]
        if len(candidates) != 1:
            raise ValueError(f"D46 越南 seed did not resolve uniquely by Vietnamese rule B: {candidates}")
        seed_vi = candidates[0]["vi"]
        cc = pd.DataFrame(cedict_trad.get("越南", []))
        chosen = cc.iloc[0] if not cc.empty else None
        rows.append({
            "han": "越南",
            "trad": "越南", "simp": nfc(chosen["simp"]) if chosen is not None else "越南",
            "pinyin": nfc(chosen["pinyin"]) if chosen is not None else "",
            "level": 3, "pos": "", "hsk_ids": "", "cedict_key": "", "source_order": 0,
            "word_key": "x|越南", "origin": "vi_freq", "source_level": "vi_band",
            "gloss_en": nfc(chosen["gloss_en"]) if chosen is not None else "",
            "cedict_pinyin_spaced": nfc(chosen["pinyin_spaced"]) if chosen is not None else "",
            "source_pinyin": "cc-cedict" if chosen is not None else "",
            "vi": seed_vi, "source_vi": "composed_attested",
            "gloss_vi": "", "freq_score": frequency_score(seed_vi, frequency) or 0,
            "pre_ja_common": True, "candidate_ko": "",
            "pre_jp": nfc(seed.jp_form),
            "is_seed": True,
        })
        report.append({
            "han": "越南", "vi_values": seed_vi, "source_vi": "composed_attested",
            "reason": "seed", "selected": True,
        })

    candidates = pd.DataFrame(rows)
    candidates["source_rank"] = candidates["source_vi"].map(
        {"kaikki_han": 0, "kaikki_en_han": 1, "composed_attested": 2}
    ).fillna(9)
    ranked_normal = candidates.loc[candidates["trad"] != "越南"].sort_values(
        ["pre_ja_common", "freq_score", "source_rank", "trad", "han"],
        ascending=[False, False, True, True, True],
        kind="stable",
    )
    duplicate_keys = set(
        ranked_normal.loc[ranked_normal["word_key"].duplicated(keep="first"), "han"]
    )
    unique_ranked = ranked_normal.drop_duplicates("word_key", keep="first")
    normal = unique_ranked.head(1200).copy()
    for item in report:
        if item["han"] in duplicate_keys and item.get("reason") == "candidate":
            item["reason"] = "duplicate_word_key"
    seed_rows = candidates.loc[candidates["trad"] == "越南"].copy()
    selected = pd.concat([normal, seed_rows], ignore_index=True)
    selected["rank"] = range(1, len(selected) + 1)
    selected["level"] = selected["rank"].map(
        lambda rank: 3 if rank <= 150 else 4 if rank <= 400 else 5 if rank <= 700 else 6 if rank <= 1000 else 7
    )
    selected.loc[selected["trad"] == "越南", "level"] = 3
    selected["source_order"] = selected["rank"]
    report_frame = pd.DataFrame(report)
    selected_details = selected[[
        "han", "trad", "word_key", "freq_score", "rank", "level"
    ]].copy()
    report_frame = report_frame.drop(columns=["selected", "freq_score"], errors="ignore").merge(
        selected_details,
        how="left",
        on="han",
        validate="1:1",
    )
    report_frame["selected"] = report_frame["word_key"].map(nfc) != ""
    report_frame = report_frame[[
        "han", "trad", "word_key", "vi_values", "source_vi", "selected", "reason",
        "freq_score", "rank", "level",
    ]]
    return selected, report_frame


def split_pinyin_by_template(word: str, spaced: str, expected: int) -> list[str]:
    template = [value for value in nfc(spaced).split() if value]
    if len(template) != expected or toneless("".join(template)) != toneless(word):
        return []
    clusters = []
    for char in unicodedata.normalize("NFD", nfc(word)):
        if unicodedata.combining(char) and clusters:
            clusters[-1] += char
        elif char not in {"'", " ", "-"}:
            clusters.append(char)
    result = []
    offset = 0
    for token in template:
        length = len(toneless(token))
        result.append(unicodedata.normalize("NFC", "".join(clusters[offset:offset + length])))
        offset += length
    return result if offset == len(clusters) else []


def split_pinyin_by_inventory(word: str, expected: int, inventory: set[str]) -> list[str]:
    letters = toneless(word)
    if not letters or expected <= 0:
        return []
    memo: dict[tuple[int, int], list[str] | None] = {}

    def solve(offset: int, remaining: int) -> list[str] | None:
        key = (offset, remaining)
        if key in memo:
            return memo[key]
        if remaining == 0:
            return [] if offset == len(letters) else None
        candidates = sorted(
            (
                syllable for syllable in inventory
                if letters.startswith(syllable, offset)
                and len(letters) - offset - len(syllable) >= remaining - 1
            ),
            key=lambda value: (-len(value), value),
        )
        for syllable in candidates:
            rest = solve(offset + len(syllable), remaining - 1)
            if rest is not None:
                memo[key] = [syllable, *rest]
                return memo[key]
        memo[key] = None
        return None

    segments = solve(0, expected)
    if segments is None:
        return []
    return split_pinyin_by_template(word, " ".join(segments), expected)


def add_pinyin_segments(words: pd.DataFrame) -> pd.DataFrame:
    result = words.copy()
    cedict = read_stage("cedict.csv")
    inventory = {
        toneless(token)
        for spaced in cedict["pinyin_spaced"]
        for token in nfc(spaced).split()
        if toneless(token)
    }
    inventory.add("r")
    segments = []
    for row in result.itertuples(index=False):
        if not nfc(row.pinyin):
            parts = []
        elif len(row.trad) == 1:
            parts = [nfc(row.pinyin)]
        else:
            parts = split_pinyin_by_template(row.pinyin, row.cedict_pinyin_spaced, len(row.trad))
            if not parts:
                parts = split_pinyin_by_inventory(row.pinyin, len(row.trad), inventory)
        segments.append(";".join(parts))
    result["pinyin_segments"] = segments
    return result


def grow_chars(
    words: pd.DataFrame,
    base: pd.DataFrame,
    lookup: ReadingLookup,
    kd: dict[str, dict[str, object]],
) -> pd.DataFrame:
    unihan = read_stage("unihan.csv").set_index("char", drop=False)
    opencc = read_stage("opencc.csv")
    opencc_map = {key: ";".join(unique_preserve(group["jp_candidate"])) for key, group in opencc.groupby("trad", sort=False)}
    kabeh = read_stage("kaikki_char_readings.csv")
    kaikki_map = {key: unique_preserve(group["vi"]) for key, group in kabeh.groupby("char", sort=False)}
    lib = read_stage("libhangul.csv")
    lib_map = {key: unique_preserve(group["ko"]) for key, group in lib.groupby("char", sort=False)}
    existing = set(base["trad"]) | set(base["key_char"])
    observed_simp: dict[str, list[str]] = defaultdict(list)
    first_use: list[str] = []
    min_level: dict[str, int] = {}
    for row in words.itertuples(index=False):
        for position, char in enumerate(row.trad):
            if position < len(row.simp):
                observed_simp[char].append(row.simp[position])
            min_level[char] = min(min_level.get(char, 99), int(row.level))
            if char not in existing and char not in first_use:
                first_use.append(char)
    additions = []
    for char in first_use:
        uni = unihan.loc[char] if char in unihan.index else None
        if isinstance(uni, pd.DataFrame):
            uni = uni.iloc[0]
        simple_values = variant_char(uni["kSimplifiedVariant"]) if uni is not None else []
        observed = unique_preserve(observed_simp.get(char, []))
        if len(observed) == 1:
            simp = observed[0]
        elif len(simple_values) == 1:
            simp = simple_values[0]
        elif not simple_values:
            simp = char
        else:
            simp = ""
        ko_values = lookup.ko.get(char, lib_map.get(char, []))
        mandarin = pinyin_values(uni["kMandarin"]) if uni is not None else []
        pinyin_all = unique_preserve([
            *mandarin,
            *(pinyin_values(uni["kHanyuPinyin"], referenced=True) if uni is not None else []),
            *(pinyin_values(uni["kXHC1983"], referenced=True) if uni is not None else []),
        ])
        verified_vi = lookup.vi.get(char, [])
        unihan_vi = split_multi(uni["kVietnamese"]) if uni is not None else []
        if verified_vi:
            vi_values = verified_vi
            vi = vi_values[0]
            source_vi = lookup.vi_source.get((char, vi), "")
        else:
            vi_values = unihan_vi
            vi = unihan_vi[0] if unihan_vi else ""
            source_vi = "unihan_unverified" if vi else ""
        jp = choose_jp(char, opencc_map.get(char, ""), kd)
        ja_values = split_multi(kd.get(jp, {}).get("ja_on_all", ""))
        additions.append({
            "trad": char, "key_char": char, "simp": simp, "jp": jp,
            "ja_on": ja_values[0] if ja_values else "", "ko": ko_values[0] if ko_values else "",
            "pinyin": mandarin[0] if mandarin else "", "vi": vi,
            "ja_on_all": ";".join(ja_values), "ko_all": ";".join(ko_values),
            "pinyin_all": ";".join(pinyin_all), "vi_all": ";".join(vi_values),
            "ko_final": hangul_final(ko_values[0] if ko_values else ""),
            "vi_final": vietnamese_final(vi), "in_hsk_chars": False,
            "level": min_level.get(char, ""),
            "gloss_en": nfc(uni["kDefinition"]) if uni is not None else "",
            "source_ko": "unihan" if uni is not None and split_multi(uni["kHangul"]) else ("libhangul" if ko_values else ""),
            "source_vi": source_vi, "source_ja": "kanjidic2" if ja_values else "",
            "source_pinyin": "unihan" if mandarin else "",
        })
    additions_frame = pd.DataFrame(additions)
    if not additions_frame.empty:
        ids = assign_ids("char", additions_frame["key_char"], "c", 5)
        additions_frame.insert(0, "char_id", additions_frame["key_char"].map(ids))
        result = pd.concat([base, additions_frame], ignore_index=True)
    else:
        result = base.copy()
    if result["key_char"].duplicated().any() or result["char_id"].duplicated().any():
        raise ValueError("Character growth produced duplicate key_char or char_id")
    return result


def link_word_chars(words: pd.DataFrame, chars: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    by_trad = {key: group for key, group in chars.groupby("trad", sort=False)}
    by_key = chars.set_index("key_char", drop=False)
    links = []
    ambiguous = []
    mismatches = []
    for row in words.itertuples(index=False):
        pinyin_parts = [value for value in nfc(row.pinyin_segments).split(";") if value]
        for position, char in enumerate(row.trad):
            group = by_trad.get(char, pd.DataFrame())
            selected = None
            if len(group) == 1:
                selected = group.iloc[0]
            elif len(group) == 0 and char in by_key.index:
                selected = by_key.loc[char]
                if isinstance(selected, pd.DataFrame):
                    selected = None
            elif len(group) > 1:
                if position < len(row.simp):
                    matches = group.loc[group["simp"] == row.simp[position]]
                    if len(matches) == 1:
                        selected = matches.iloc[0]
                if selected is None and position < len(pinyin_parts):
                    matches = group.loc[group["pinyin_all"].map(lambda value: pinyin_parts[position] in split_multi(value))]
                    if len(matches) == 1:
                        selected = matches.iloc[0]
            if selected is None:
                ambiguous.append({
                    "word_id": row.word_id, "trad": row.trad, "position": position + 1,
                    "char": char, "candidates": ";".join(group["char_id"]) if not group.empty else "",
                    "reason": "unlinked" if group.empty else "multiple rows unresolved",
                })
                char_id = ""
            else:
                char_id = nfc(selected["char_id"])
                if position < len(row.simp) and nfc(selected["simp"]) != row.simp[position]:
                    mismatches.append({
                        "word_id": row.word_id, "trad": row.trad, "simp": row.simp,
                        "position": position + 1, "char_id": char_id,
                        "char_simp": nfc(selected["simp"]), "word_simp": row.simp[position],
                    })
            links.append({
                "word_id": row.word_id, "position": position + 1, "char_id": char_id,
                "pinyin_syllable": pinyin_parts[position] if len(pinyin_parts) == len(row.trad) else "",
                "ko_syllable": "", "ko_base": "", "vi_syllable": "",
            })
    return (
        pd.DataFrame(links),
        pd.DataFrame(ambiguous, columns=REPORT_COLUMNS["char_ambiguous"]),
        pd.DataFrame(mismatches, columns=REPORT_COLUMNS["char_simp_mismatch"]),
    )


def match_all_words(
    words: pd.DataFrame,
    chars: pd.DataFrame,
    lookup: ReadingLookup,
    graph: dict[str, list[str]],
    jmdict_index: dict[str, list[dict[str, object]]],
    korean_index: dict[str, list[object]],
    explicit: dict[str, pd.DataFrame],
    explicit_en: dict[str, pd.DataFrame],
    headwords: dict[str, dict[str, object]],
    phrases: dict[str, list[str]],
    merge_rows: list[dict[str, object]],
) -> tuple[pd.DataFrame, dict[str, list[dict[str, object]]], dict[str, list[dict[str, object]]]]:
    backbone = prepare_forms(words, chars)
    result = backbone.copy()
    print("stage3: matching Japanese", flush=True)
    japanese = []
    ja_report = []
    for row in result.itertuples(index=False):
        match = match_japanese_row(row, jmdict_index, graph, phrases, lookup)
        japanese.append(match)
        if match["ja_priority_count"] >= 2:
            ja_report.append({
                "word_key": row.word_key, "word_id": row.word_id, "trad": row.trad,
                "pinyin": row.pinyin, "level": row.level, "candidates": match["ja_candidates"],
            })
    for column in ["jp", "ja", "ja_alt", "ja_common", "gloss_ja_en", "source_ja"]:
        result[column] = [match[column] for match in japanese]

    print("stage3: matching Korean candidates", flush=True)
    ko_cache: dict[str, list[dict[str, object]]] = {}
    ko_forms: dict[str, list[str]] = {}
    char_counts: Counter[tuple[str, str]] = Counter()
    pinyin_counts: Counter[tuple[str, str, str]] = Counter()
    for row in result.itertuples(index=False):
        candidates, forms = korean_candidates(row, korean_index, graph, lookup)
        ko_cache[row.word_key] = candidates
        ko_forms[row.word_key] = forms
        if len(candidates) == 1 and len(row.trad) > 1:
            candidate = candidates[0]
            pinyin_parts = [value for value in nfc(row.pinyin_segments).split(";") if value]
            for position, (char, base) in enumerate(zip(row.trad, candidate["bases"])):
                char_counts[(char, base)] += 1
                if len(pinyin_parts) == len(row.trad):
                    pinyin_counts[(char, pinyin_parts[position], base)] += 1
    print("stage3: choosing Korean readings", flush=True)
    ko_values = []
    ko_reports = []
    ko_unresolved = []
    for row in result.itertuples(index=False):
        candidates = ko_cache[row.word_key]
        chosen, alt = choose_korean(row, candidates, char_counts, pinyin_counts)
        chosen_record = next((value for value in candidates if value["reading"] == chosen), None)
        reportable = len(candidates) > 1
        if reportable and len(row.trad) == 1 and chosen:
            reportable = not all(
                candidate["reading"] == chosen
                or korean_base(candidate["reading"], [chosen], 0) == chosen
                or korean_base(chosen, [candidate["reading"]], 0) == candidate["reading"]
                for candidate in candidates
            )
        if reportable:
            ko_reports.append({
                "word_key": row.word_key, "word_id": row.word_id, "trad": row.trad,
                "pinyin": row.pinyin, "level": row.level,
                "candidates": ";".join(value["reading"] for value in candidates), "chosen": chosen,
            })
        if not chosen and (candidates or any(form in korean_index for form in ko_forms[row.word_key])):
            ko_unresolved.append({
                "word_key": row.word_key, "word_id": row.word_id, "trad": row.trad,
                "pinyin": row.pinyin, "forms": ";".join(ko_forms[row.word_key]),
                "candidates": ";".join(value["reading"] for value in candidates),
                "reason": "multiple without evidence" if candidates else "forms exist but alignment rejected",
            })
        ko_values.append({
            "ko": chosen, "ko_alt": ";".join(alt),
            "source_ko": chosen_record["source"] if chosen_record else "",
            "gloss_ko": chosen_record["comment"] if chosen_record else "",
            "ko_evidence": len(candidates) == 1,
        })
    for column in ["ko", "ko_alt", "source_ko", "gloss_ko", "ko_evidence"]:
        result[column] = [value[column] for value in ko_values]
    print("stage3: matching Vietnamese", flush=True)
    vi_cache: dict[str, list[dict[str, object]]] = {}
    a2_cache: dict[str, list[dict[str, object]]] = {}
    triple_counts: Counter[tuple[str, str, str]] = Counter()
    for row in result.itertuples(index=False):
        candidates = vi_candidates(row, explicit, graph, lookup, headwords)
        # VI-only rows have already passed D46 and retain their selected explicit reading.
        if row.origin == "vi_freq" and nfc(getattr(row, "vi", "")):
            candidates = [{
                "vi": nfc(row.vi), "source": nfc(getattr(row, "source_vi", "kaikki_han")),
                "gloss_vi": nfc(getattr(row, "gloss_vi", "")),
                "rule_b_conflict": False,
            }]
        a2_cache[row.word_key] = kaikki_en_candidates(row, explicit_en, graph)
        vi_cache[row.word_key] = [*candidates, *a2_cache[row.word_key]]
        valid_candidates = [value for value in candidates if not value.get("rule_b_conflict", False)]
        if len(valid_candidates) == 1 and len(row.trad) > 1:
            parts = valid_candidates[0]["vi"].split()
            py = [value for value in nfc(row.pinyin_segments).split(";") if value]
            if len(parts) == len(row.trad) and len(py) == len(row.trad):
                for char, pinyin_part, vi in zip(row.trad, py, parts):
                    triple_counts[(char, pinyin_part, vi)] += 1
    vi_values = []
    unresolved: dict[str, dict[str, object]] = {}
    for row in result.itertuples(index=False):
        all_candidates = [
            value for value in vi_cache[row.word_key] if value.get("source") != "kaikki_en_han"
        ]
        conflicts = [value for value in all_candidates if value.get("rule_b_conflict", False)]
        candidates = [value for value in all_candidates if not value.get("rule_b_conflict", False)]
        chosen = ""
        several = []
        if len(candidates) == 1:
            chosen = candidates[0]["vi"]
        elif len(candidates) > 1:
            py = [value for value in nfc(row.pinyin_segments).split(";") if value]
            scores = []
            for candidate in candidates:
                parts = candidate["vi"].split()
                score = sum(
                    triple_counts[(char, pinyin_part, vi)]
                    for char, pinyin_part, vi in zip(row.trad, py, parts)
                ) if len(py) == len(parts) == len(row.trad) else 0
                scores.append((score, candidate))
            scores.sort(key=lambda value: -value[0])
            if len(scores) == 1 or scores[0][0] > scores[1][0]:
                chosen = scores[0][1]["vi"]
            else:
                several = candidates
        selected = next((value for value in candidates if value["vi"] == chosen), None)
        vi_values.append({
            "vi": chosen,
            "vi_alt": ";".join(value["vi"] for value in candidates if value["vi"] != chosen),
            "source_vi": selected["source"] if selected else "",
            "gloss_vi": selected["gloss_vi"] if selected else "",
            "vi_evidence": len(candidates) == 1,
        })
        unresolved[row.word_key] = {
            "row": row, "several": several, "conflicts": conflicts,
        }
    for column in ["vi", "vi_alt", "source_vi", "gloss_vi", "vi_evidence"]:
        result[column] = [value[column] for value in vi_values]

    a2_rows = []
    for row in result.itertuples(index=False):
        active = [value for value in a2_cache[row.word_key] if not value.get("obsolete_only", False)]
        if len(active) == 1:
            candidate = active[0]
            a2_rows.append({
                "word_key": row.word_key,
                "vi_a2": candidate["vi"],
                "source_vi_a2": candidate["source"],
                "gloss_vi_a2": candidate["gloss_vi"],
            })
    a2_frame = pd.DataFrame(
        a2_rows, columns=["word_key", "vi_a2", "source_vi_a2", "gloss_vi_a2"]
    )
    result = merge_with_report(
        result,
        a2_frame,
        name="words_kaikki_en",
        reports=merge_rows,
        how="left",
        validate="1:1",
        on="word_key",
    )
    for column in ["vi_a2", "source_vi_a2", "gloss_vi_a2"]:
        result[column] = result[column].fillna("").map(nfc)
    use_a2 = (result["vi"] == "") & (result["vi_a2"] != "")
    result.loc[use_a2, "vi"] = [
        prefer_existing_vi(current, candidate)
        for current, candidate in zip(result.loc[use_a2, "vi"], result.loc[use_a2, "vi_a2"])
    ]
    result.loc[use_a2, "source_vi"] = result.loc[use_a2, "source_vi_a2"]
    result.loc[use_a2, "gloss_vi"] = result.loc[use_a2, "gloss_vi_a2"]
    result.loc[use_a2, "vi_evidence"] = True

    vi_reports = []
    for row in result.itertuples(index=False):
        if nfc(row.vi):
            continue
        info = unresolved[row.word_key]
        active = [value for value in a2_cache[row.word_key] if not value.get("obsolete_only", False)]
        obsolete = [value for value in a2_cache[row.word_key] if value.get("obsolete_only", False)]
        if len(active) > 1:
            report_candidates, reason = active, "several_candidates"
        elif obsolete and not active:
            report_candidates, reason = obsolete, "obsolete_only"
        elif info["several"]:
            report_candidates, reason = info["several"], "several_candidates"
        elif info["conflicts"]:
            report_candidates, reason = info["conflicts"], "rule_b_conflict"
        else:
            continue
        vi_reports.append({
            "word_key": row.word_key, "word_id": row.word_id, "trad": row.trad,
            "pinyin": row.pinyin, "level": row.level,
            "candidates": ";".join(value["vi"] for value in report_candidates),
            "reason": reason,
        })
    result = result.drop(
        columns=["vi_a2", "source_vi_a2", "gloss_vi_a2", "_merge_words_kaikki_en"]
    )

    computed = result.copy()
    result = backbone.copy()
    match_specs = [
        ("words_jmdict", "ja", ["jp", "ja", "ja_alt", "ja_common", "gloss_ja_en", "source_ja"]),
        ("words_libhangul", "ko", ["ko", "ko_alt", "source_ko", "gloss_ko"]),
        ("words_vi", "vi", ["vi", "vi_alt", "source_vi", "gloss_vi"]),
    ]
    for name, value_column, columns in match_specs:
        result = result.drop(columns=columns, errors="ignore")
        match_frame = computed.loc[
            computed[value_column].map(nfc) != "", ["word_key", *columns]
        ].copy()
        result = merge_with_report(
            result,
            match_frame,
            name=name,
            reports=merge_rows,
            how="left",
            validate="1:1",
            on="word_key",
        )
        result = result.drop(columns=[f"_merge_{name}"])
        for column in columns:
            if column == "ja_common":
                result[column] = result[column].fillna(False).astype(bool)
            else:
                result[column] = result[column].fillna("").map(nfc)

    computed_by_key = computed.set_index("word_key")
    for column in ["ko_alt", "vi_alt", "ko_evidence", "vi_evidence"]:
        result[column] = result["word_key"].map(computed_by_key[column])
    # Display-only Japanese form is built from characters only for a Korean-backed word.
    result.loc[(result["jp"] == "") & (result["ko"] != ""), "jp"] = result["jp_form"]
    result.loc[(result["source_ja"] == "") & (result["jp"] != "") & (result["ja"] == ""), "source_ja"] = "built_from_chars"

    write_csv(pd.DataFrame(ja_report, columns=REPORT_COLUMNS["ja_multi_candidates"]), FINAL / "ja_multi_candidates.csv")
    write_csv(pd.DataFrame(ko_reports, columns=REPORT_COLUMNS["ko_multi_candidates"]), FINAL / "ko_multi_candidates.csv")
    write_csv(pd.DataFrame(ko_unresolved, columns=REPORT_COLUMNS["ko_unresolved"]), FINAL / "ko_unresolved.csv")
    write_csv(pd.DataFrame(vi_reports, columns=REPORT_COLUMNS["vi_ambiguous"]), FINAL / "vi_ambiguous.csv")
    return result, ko_cache, vi_cache


def load_overrides() -> pd.DataFrame:
    path = ROOT / "pipeline" / "overrides.csv"
    if not path.exists():
        return pd.DataFrame(columns=OVERRIDE_COLUMNS)
    frame = pd.read_csv(path, encoding="utf-8", keep_default_na=False, dtype=str)
    if list(frame.columns) != OVERRIDE_COLUMNS:
        raise ValueError("pipeline/overrides.csv has the wrong columns")
    return frame


def apply_word_overrides(
    words: pd.DataFrame,
    overrides: pd.DataFrame,
    ko_cache: dict[str, list[dict[str, object]]],
    vi_cache: dict[str, list[dict[str, object]]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    result = words.copy()
    vi_reports = []
    for override in overrides.loc[overrides["table"] == "words"].itertuples(index=False):
        matches = result.index[result["word_key"] == override.key].tolist()
        if len(matches) != 1:
            raise ValueError(f"Word override key does not resolve once: {override.key}")
        index = matches[0]
        if override.column == "ko":
            allowed = [item["reading"] for item in ko_cache.get(override.key, [])]
            selected_record = next(
                (item for item in ko_cache.get(override.key, []) if item["reading"] == override.value), None
            )
        elif override.column == "vi":
            allowed = [item["vi"] for item in vi_cache.get(override.key, [])]
            selected_record = next(
                (item for item in vi_cache.get(override.key, []) if item["vi"] == override.value), None
            )
        elif override.column == "ja":
            allowed = split_multi(result.at[index, "ja_alt"]) + [nfc(result.at[index, "ja"])]
            selected_record = None
        else:
            raise ValueError(f"Unsupported word override column: {override.column}")
        is_vi_clear = override.column == "vi" and override.value == ""
        if is_vi_clear and not nfc(override.reason):
            raise ValueError(f"A clearing Vietnamese override requires a reason: {override.key}")
        if not is_vi_clear and override.value not in allowed:
            raise ValueError(f"Override value is not a dictionary candidate: {override}")
        old = nfc(result.at[index, override.column])
        alt_column = f"{override.column}_alt"
        if alt_column in result and override.column != "vi":
            result.at[index, alt_column] = ";".join(unique_preserve([old, *split_multi(result.at[index, alt_column])]))
        elif alt_column in result and override.column == "vi" and override.value:
            result.at[index, alt_column] = ";".join(
                value for value in split_multi(result.at[index, alt_column]) if value != override.value
            )
        elif alt_column in result and is_vi_clear:
            result.at[index, alt_column] = ""
        result.at[index, override.column] = override.value
        if override.column == "ko":
            result.at[index, "ko_evidence"] = True
            if selected_record is not None:
                result.at[index, "source_ko"] = selected_record["source"]
                result.at[index, "gloss_ko"] = selected_record["comment"]
        elif override.column == "vi":
            result.at[index, "vi_evidence"] = not is_vi_clear
            if old and old != override.value:
                vi_reports.append({
                    "word_key": override.key,
                    "word_id": result.at[index, "word_id"],
                    "trad": result.at[index, "trad"],
                    "pinyin": result.at[index, "pinyin"],
                    "level": result.at[index, "level"],
                    "candidates": old,
                    "reason": "override_cleared" if is_vi_clear else "override_replaced",
                })
            if is_vi_clear:
                result.at[index, "source_vi"] = ""
                result.at[index, "gloss_vi"] = ""
            elif selected_record is not None:
                result.at[index, "source_vi"] = selected_record["source"]
                result.at[index, "gloss_vi"] = selected_record["gloss_vi"]
    return result, pd.DataFrame(vi_reports, columns=REPORT_COLUMNS["vi_ambiguous"])


def align_word_readings(
    words: pd.DataFrame,
    links: pd.DataFrame,
    chars: pd.DataFrame,
    ko_cache: dict[str, list[dict[str, object]]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    result = links.copy()
    char_by_id = chars.set_index("char_id")
    mismatches = []
    aligned_flags: dict[str, bool] = {}
    word_by_id = words.set_index("word_id")
    for word_id, indices in result.groupby("word_id", sort=False).groups.items():
        word = word_by_id.loc[word_id]
        positions = list(indices)
        ko = nfc(word["ko"])
        vi = nfc(word["vi"])
        ko_parts = list(ko) if ko else []
        vi_parts = vi.split() if vi else []
        ko_ok = bool(ko) and len(ko_parts) == len(positions)
        vi_ok = bool(vi) and len(vi_parts) == len(positions)
        if ko and not ko_ok:
            mismatches.append({"word_id": word_id, "lang": "ko", "reason": "count", "detail": f"{len(ko_parts)} syllables/{len(positions)} chars"})
        if vi and not vi_ok:
            mismatches.append({"word_id": word_id, "lang": "vi", "reason": "count", "detail": f"{len(vi_parts)} syllables/{len(positions)} chars"})
        if nfc(word["pinyin"]) and not all(nfc(result.at[index, "pinyin_syllable"]) for index in positions):
            mismatches.append({"word_id": word_id, "lang": "pinyin", "reason": "count", "detail": "CC-CEDICT template did not resolve"})
        chosen_record = next(
            (item for item in ko_cache.get(word["word_key"], []) if item["reading"] == ko), None
        )
        for offset, index in enumerate(positions):
            char_id = nfc(result.at[index, "char_id"])
            if ko_ok:
                syllable = ko_parts[offset]
                result.at[index, "ko_syllable"] = syllable
                if chosen_record is not None and chosen_record.get("exception"):
                    base = chosen_record["bases"][offset]
                elif char_id:
                    base = korean_normalized_base(
                        syllable,
                        split_multi(char_by_id.loc[char_id, "ko_all"]),
                        offset,
                        ko_parts[offset - 1] if offset > 0 else "",
                    )
                else:
                    base = ""
                result.at[index, "ko_base"] = base
                if base != syllable and chosen_record is not None and chosen_record.get("exception"):
                    mismatches.append({
                        "word_id": word_id, "lang": "ko", "reason": "ko_exception",
                        "detail": f"position {offset + 1}: {syllable}->{base}",
                    })
                if char_id and base and base not in split_multi(char_by_id.loc[char_id, "ko_all"]):
                    mismatches.append({
                        "word_id": word_id, "lang": "ko", "reason": "not_in_all",
                        "detail": f"position {offset + 1}: {base}",
                    })
            if vi_ok:
                syllable = vi_parts[offset]
                result.at[index, "vi_syllable"] = syllable
                if char_id and syllable not in split_multi(char_by_id.loc[char_id, "vi_all"]):
                    mismatches.append({
                        "word_id": word_id, "lang": "vi", "reason": "not_in_all",
                        "detail": f"position {offset + 1}: {syllable}",
                    })
        aligned_flags[word_id] = ko_ok and vi_ok
    words_out = words.copy()
    words_out["syl_aligned"] = words_out["word_id"].map(aligned_flags).fillna(False)
    mismatch_frame = pd.DataFrame(mismatches, columns=REPORT_COLUMNS["alignment_mismatches"])
    return words_out, result, mismatch_frame


def primary_from_evidence(
    old: str, readings: list[str], counts: Counter[str]
) -> tuple[str, int, int]:
    if not readings or not counts:
        return old, counts.get(old, 0), counts.get(old, 0)
    highest = max(counts.get(reading, 0) for reading in readings)
    if highest <= 0:
        return old, counts.get(old, 0), counts.get(old, 0)
    winners = [reading for reading in readings if counts.get(reading, 0) == highest]
    new = old if old in winners else winners[0]
    return new, counts.get(old, 0), counts.get(new, 0)


CHAR_SOURCE_EVIDENCE = {"kaikki_aligned", "kaikki_en_char", "unihan_hvsyl"}


def apply_d39(
    chars: pd.DataFrame,
    words: pd.DataFrame,
    word_chars: pd.DataFrame,
    lookup: ReadingLookup,
    overrides: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    result = chars.copy()
    original_sets = {
        (row.char_id, lang): set(split_multi(getattr(row, f"{lang}_all")))
        for row in result.itertuples(index=False)
        for lang in ["ko", "vi"]
    }
    evidence = words.set_index("word_id")[["ko_evidence", "vi_evidence"]].to_dict(orient="index")
    char_all = result.set_index("char_id")[["ko_all", "vi_all"]].to_dict(orient="index")
    ko_counts: dict[str, Counter[str]] = defaultdict(Counter)
    vi_counts: dict[str, Counter[str]] = defaultdict(Counter)
    ko_later: dict[str, Counter[str]] = defaultdict(Counter)
    for row in word_chars.itertuples(index=False):
        if not nfc(row.char_id):
            continue
        if (
            bool(evidence.get(row.word_id, {}).get("ko_evidence", False))
            and nfc(row.ko_base)
            and row.ko_base in split_multi(char_all[row.char_id]["ko_all"])
        ):
            ko_counts[row.char_id][row.ko_base] += 1
            if int(row.position) > 1:
                ko_later[row.char_id][row.ko_base] += 1
        if (
            bool(evidence.get(row.word_id, {}).get("vi_evidence", False))
            and nfc(row.vi_syllable)
            and row.vi_syllable in split_multi(char_all[row.char_id]["vi_all"])
        ):
            vi_counts[row.char_id][row.vi_syllable] += 1
    changes = []
    no_evidence = []
    for index, row in result.iterrows():
        char_id = row["char_id"]
        for lang, counter_map in [("ko", ko_counts), ("vi", vi_counts)]:
            readings = split_multi(row[f"{lang}_all"])
            old = nfc(row[lang])
            counter = counter_map.get(char_id, Counter())
            new, old_count, new_count = primary_from_evidence(old, readings, counter)
            if not counter:
                law_suspect = bool(
                    lang == "ko"
                    and old
                    and (normalized := korean_normalized_base(old, readings, 0))
                    and normalized != old
                )
                no_evidence.append({
                    "char_id": char_id, "trad": row["trad"], "key_char": row["key_char"],
                    "lang": lang, "ko_law_form_suspect": law_suspect,
                    # R1 (RELEASE_PLAN §1.3): no word evidence, but the primary itself is
                    # attested at character level (Kaikki aligned/English, or a Unihan
                    # reading confirmed as a Hán-Việt syllable), e.g. 荷 痕 瀾 蓮.
                    "char_source_evidence": bool(
                        lang == "vi" and old and nfc(row["source_vi"]) in CHAR_SOURCE_EVIDENCE
                    ),
                })
            if new != old:
                changes.append({
                    "char_id": char_id, "trad": row["trad"], "key_char": row["key_char"],
                    "lang": lang, "old": old, "new": new,
                    "old_count": old_count, "new_count": new_count,
                })
            result.at[index, lang] = new
            result.at[index, f"{lang}_all"] = ";".join(unique_preserve([new, *readings]))
            if lang == "ko" and new:
                # Every selected value is source-backed; preserve the precise source when possible.
                result.at[index, "source_ko"] = "unihan" if new in lookup.ko.get(row["key_char"], []) else "libhangul"
            if lang == "vi" and new:
                result.at[index, "source_vi"] = lookup.vi_source.get((row["key_char"], new), nfc(row["source_vi"]))

    for override in overrides.loc[overrides["table"] == "chars"].itertuples(index=False):
        matches = result.index[result["key_char"] == override.key].tolist()
        if len(matches) != 1 or override.column not in {"ko", "vi"}:
            raise ValueError(f"Invalid character override: {override}")
        index = matches[0]
        if override.value not in split_multi(result.at[index, f"{override.column}_all"]):
            raise ValueError(f"Character override is not in *_all: {override}")
        old = nfc(result.at[index, override.column])
        result.at[index, override.column] = override.value
        result.at[index, f"{override.column}_all"] = ";".join(
            unique_preserve([override.value, *split_multi(result.at[index, f"{override.column}_all"] )])
        )
        if old != override.value:
            changes.append({
                "char_id": result.at[index, "char_id"], "trad": result.at[index, "trad"],
                "key_char": override.key, "lang": override.column, "old": old,
                "new": override.value, "old_count": "override", "new_count": "override",
            })

    result["ko_final"] = result["ko"].map(hangul_final)
    result["vi_final"] = result["vi"].map(vietnamese_final)
    base_all_values = []
    for row in result.itertuples(index=False):
        values = split_multi(row.ko_all)
        kept = []
        for reading in values:
            removable = False
            for other in values:
                if other == reading:
                    continue
                if korean_base(reading, [other], 0) == other and ko_later.get(row.char_id, Counter()).get(reading, 0) == 0:
                    removable = True
                    break
            if not removable or reading == row.ko:
                kept.append(reading)
        base_all_values.append(";".join(unique_preserve([row.ko, *kept])))
    result["ko_base_all"] = base_all_values
    for row in result.itertuples(index=False):
        for lang in ["ko", "vi"]:
            if set(split_multi(getattr(row, f"{lang}_all"))) != original_sets[(row.char_id, lang)]:
                raise ValueError(f"D39 changed the {lang}_all set for {row.key_char}")
    return (
        result,
        pd.DataFrame(changes, columns=["char_id", "trad", "key_char", "lang", "old", "new", "old_count", "new_count"]),
        pd.DataFrame(no_evidence, columns=[
            "char_id", "trad", "key_char", "lang", "ko_law_form_suspect", "char_source_evidence",
        ]),
    )


def write_character_reports(chars: pd.DataFrame, word_chars: pd.DataFrame, words: pd.DataFrame) -> None:
    collisions = chars.loc[
        chars["trad"].duplicated(keep=False), ["trad", "key_char", "level"]
    ].rename(columns={"level": "source_level"}).sort_values(["trad", "key_char"], kind="stable")
    write_csv(collisions, FINAL / "char_key_collisions.csv")
    no_jp = chars.loc[chars["jp"].map(nfc) == "", ["char_id", "trad", "key_char", "simp", "level"]].copy()
    no_jp["reason"] = "no OpenCC/KANJIDIC2-valid Japanese form (D28)"
    write_csv(no_jp, FINAL / "no_jp_form.csv")

    by_char = chars.set_index("char_id")
    pairs: dict[tuple[str, str, str], str] = {}
    aligned_ids = set(words.loc[words["syl_aligned"], "word_id"])
    word_sources = words.set_index("word_id")["source_vi"].to_dict()
    for row in word_chars.loc[word_chars["word_id"].isin(aligned_ids)].itertuples(index=False):
        if not row.char_id or not row.ko_base or not row.vi_syllable:
            continue
        char = by_char.loc[row.char_id]
        source = nfc(char["source_vi"])
        if word_sources.get(row.word_id) in {"kaikki_han", "kaikki_en_han"}:
            source = word_sources[row.word_id]
        key = (row.char_id, row.ko_base, row.vi_syllable)
        if key not in pairs or source in {"kaikki_han", "kaikki_en_han"}:
            pairs[key] = source
    for row in chars.itertuples(index=False):
        ko_base_values = split_multi(row.ko_base_all)
        vi_values = split_multi(row.vi_all)
        if (
            len(ko_base_values) == 1
            and len(vi_values) == 1
            and row.source_vi in {"kaikki_aligned", "kaikki_en_char", "unihan_hvsyl"}
        ):
            pairs.setdefault((row.char_id, ko_base_values[0], vi_values[0]), row.source_vi)
    pair_frame = pd.DataFrame([
        {"char_id": key[0], "ko": key[1], "vi": key[2], "source_vi": source}
        for key, source in pairs.items()
    ])
    if pair_frame.empty:
        expanded = pd.DataFrame(columns=["char_id", "ko", "vi", "source_vi", "ko_final", "vi_final"])
    else:
        expanded = pair_frame.copy()
        expanded["ko_final"] = expanded["ko"].map(hangul_final).replace("", "(open)")
        expanded["vi_final"] = expanded["vi"].map(vietnamese_final).replace("", "(open)")
    pivot = pd.crosstab(expanded["ko_final"], expanded["vi_final"])
    vi_columns = ["(open)", "c", "ch", "p", "t", "n", "m", "ng", "nh"]
    pivot = pivot.reindex(columns=vi_columns, fill_value=0).reset_index()
    write_csv(pivot, FINAL / "rules_report.csv")
    examples = expanded.merge(
        chars[["char_id", "trad", "ja_on", "pinyin", "level"]],
        how="left", on="char_id", validate="many_to_one",
    ).sort_values(["ko_final", "vi_final", "level", "char_id"], kind="stable")
    write_csv(examples[["char_id", "trad", "ko", "vi", "ko_final", "vi_final", "ja_on", "pinyin", "level", "source_vi"]], FINAL / "rules_examples.csv")


def set_final_word_fields(words: pd.DataFrame, frequency: dict[str, int]) -> pd.DataFrame:
    result = words.copy()
    scores = [frequency_score(value, frequency) if nfc(value) else None for value in result["vi"]]
    result["freq_score"] = scores
    distinct = {score: rank for rank, score in enumerate(sorted({score for score in scores if score is not None}, reverse=True), start=1)}
    result["freq_vi"] = [distinct.get(score, "") for score in scores]
    hsk = result["source_level"] == "hsk30"
    result.loc[hsk & (result["vi"] != ""), "origin"] = "both"
    result.loc[hsk & (result["vi"] == ""), "origin"] = "hsk"
    result["card_eligible"] = (
        result["level"].map(lambda value: nfc(value) != "")
        & ((result["ja"] != "") | (result["ko"] != ""))
        & ((result["pinyin"] != "") | (result["vi"] != ""))
        & (result["origin"] != "ff_only")
    )
    result["verified"] = False
    result["ja_use"] = ""
    result["ko_use"] = ""
    result["vi_use"] = ""
    for column in [
        "meaning_ja__ja", "meaning_ja__ko", "meaning_ja__zh", "meaning_ja__vi",
        "note_ja", "false_friend",
    ]:
        result[column] = ""
    return result


def write_coverage(words: pd.DataFrame, chars: pd.DataFrame) -> None:
    rows = []
    for level, group in words.loc[words["source_level"] == "hsk30"].groupby("level", sort=True):
        total = len(group)
        fields = ["ja", "ko", "pinyin", "vi"]
        for field in fields:
            count = int((group[field] != "").sum())
            rows.append({
                "scope": "hsk_words", "level": level, "field": field, "count": count,
                "total": total, "percent": round(count * 100 / total, 2), "note": "",
            })
        all_four = int(group[fields].ne("").all(axis=1).sum())
        rows.append({
            "scope": "hsk_words", "level": level, "field": "all_4", "count": all_four,
            "total": total, "percent": round(all_four * 100 / total, 2), "note": "",
        })
    for field in ["jp", "ja_on", "ko", "pinyin", "vi"]:
        count = int((chars[field].map(nfc) != "").sum())
        rows.append({
            "scope": "chars", "level": "all", "field": field, "count": count,
            "total": len(chars), "percent": round(count * 100 / len(chars), 2), "note": "",
        })
    rows.append({
        "scope": "words", "level": "all", "field": "freq_vi_basis",
        "count": int((words["freq_vi"].map(nfc) != "").sum()), "total": len(words),
        "percent": "", "note": "syllable_min",
    })
    write_csv(pd.DataFrame(rows), FINAL / "coverage_report.csv")


def build_ff_candidates(
    words: pd.DataFrame,
    jmdict: pd.DataFrame,
    jmdict_index: dict[str, pd.DataFrame],
    cedict: pd.DataFrame,
    explicit: dict[str, pd.DataFrame],
    explicit_en: dict[str, pd.DataFrame],
    korean_index: dict[str, list[object]],
    graph: dict[str, list[str]],
    lookup: ReadingLookup,
    headwords: dict[str, dict[str, object]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    used = set(words["trad"]) | set(words["simp"]) | set(words["jp"])
    opencc = read_stage("opencc.csv")
    inverse: dict[str, list[str]] = defaultdict(list)
    for row in opencc.itertuples(index=False):
        inverse[row.jp_candidate].append(row.trad)
    cedict_by_trad: dict[str, list[dict[str, object]]] = defaultdict(list)
    cedict_by_simp: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in cedict.to_dict(orient="records"):
        cedict_by_trad[nfc(item["trad"])].append(item)
        cedict_by_simp[nfc(item["simp"])].append(item)
    forms = []
    vi_conflicts = []
    strict = jmdict.loc[
        jmdict["ke_pri"].map(strict_priority) | jmdict["re_pri"].map(strict_priority)
    ]
    for form, group in strict.groupby("keb", sort=False):
        if len(form) < 2 or not all_cjk(form) or form in used:
            continue
        if set(tag for value in group["ke_inf"] for tag in tags(value)) & {"iK", "oK", "rK", "sK"}:
            continue
        trad = "".join(inverse.get(char, [char])[0] for char in form)
        cc = pd.DataFrame(cedict_by_trad.get(trad, []))
        if cc.empty:
            cc = pd.DataFrame(cedict_by_simp.get(form, []))
        valid_cc = pd.DataFrame()
        if not cc.empty:
            blocked = r"^(?:surname|variant of|old variant|see |used in|abbr\. for)"
            valid_cc = cc.loc[
                ~cc["capitalized_pinyin"].map(lambda value: nfc(value).lower() == "true")
                & ~cc["first_gloss"].str.lower().str.match(blocked, na=False)
            ]
        if valid_cc.empty and trad not in explicit and form not in explicit:
            continue
        _matched_form, ranked = find_jmdict([form], jmdict_index)
        if ranked.empty:
            continue
        top = ranked.iloc[0]
        cc_first = valid_cc.iloc[0] if not valid_cc.empty else None
        simp = nfc(cc_first["simp"]) if cc_first is not None else form
        if {form, trad, simp} & used:
            continue
        pseudo = type("Word", (), {
            "trad": trad, "simp": simp,
            "pinyin": nfc(cc_first["pinyin"]) if cc_first is not None else "",
            "jp_form": form, "key_form": trad,
        })()
        ko_candidates, _ = korean_candidates(pseudo, korean_index, graph, lookup)
        all_vi_values = vi_candidates(pseudo, explicit, graph, lookup, headwords)
        vi_values = [value for value in all_vi_values if not value.get("rule_b_conflict", False)]
        conflicts = [value for value in all_vi_values if value.get("rule_b_conflict", False)]
        if not vi_values:
            vi_values = [
                value for value in kaikki_en_candidates(pseudo, explicit_en, graph)
                if not value.get("obsolete_only", False)
            ]
        if conflicts and len(vi_values) != 1:
            vi_conflicts.append({
                "word_key": f"ff|{form}", "word_id": "", "trad": trad,
                "pinyin": nfc(cc_first["pinyin"]) if cc_first is not None else "",
                "level": "", "candidates": ";".join(value["vi"] for value in conflicts),
                "reason": "rule_b_conflict",
            })
        forms.append({
            "form": form, "trad": trad, "simp": simp, "ja": nfc(top["reb"]),
            "gloss_ja_en": nfc(top["gloss_ja_en"]),
            "ko": ko_candidates[0]["reading"] if len(ko_candidates) == 1 else "",
            "source_ko": ko_candidates[0]["source"] if len(ko_candidates) == 1 else "",
            "pinyin": ";".join(unique_preserve(valid_cc["pinyin"])) if not valid_cc.empty else "",
            "gloss_en": ";".join(unique_preserve(valid_cc["gloss_en"])) if not valid_cc.empty else "",
            "vi": vi_values[0]["vi"] if len(vi_values) == 1 else "",
            "gloss_vi": vi_values[0]["gloss_vi"] if len(vi_values) == 1 else "",
            "source_vi": vi_values[0]["source"] if len(vi_values) == 1 else "",
        })
    frame = pd.DataFrame(forms, columns=[
        "form", "trad", "simp", "ja", "gloss_ja_en", "ko", "source_ko",
        "pinyin", "gloss_en", "vi", "gloss_vi", "source_vi",
    ])
    return (
        frame.drop_duplicates("form", keep="first"),
        pd.DataFrame(vi_conflicts, columns=REPORT_COLUMNS["vi_ambiguous"]),
    )


def main() -> None:
    print("stage3: loading contexts", flush=True)
    base_chars = pd.read_csv(FINAL / "chars.csv", encoding="utf-8", keep_default_na=False, dtype=str)
    existing_merges = pd.read_csv(FINAL / "merge_report.csv", encoding="utf-8", keep_default_na=False, dtype=str)
    merge_rows = existing_merges.to_dict(orient="records")

    hsk = attach_cedict(build_hsk_words(merge_rows), merge_rows)
    hsk["vi"] = ""
    hsk["source_vi"] = ""
    hsk["gloss_vi"] = ""
    lookup, kd, graph, _hv = make_lookup()
    jmdict = read_stage("jmdict.csv")
    jmdict_index = make_jmdict_index(jmdict)
    korean_index = libhangul_index()
    explicit = explicit_index()
    explicit_en = kaikki_en_index()
    headwords = headword_index()
    frequency_frame = read_stage("frequencywords.csv")
    frequency = dict(zip(frequency_frame["token"], frequency_frame["count"].astype(int)))
    phrases = phrase_inverse()

    print("stage3: selecting VI-only words", flush=True)
    vi_only, vi_only_report = select_vi_only(
        hsk, lookup, kd, graph, jmdict_index, korean_index, phrases,
        explicit, explicit_en, headwords, frequency, merge_rows,
    )
    words = pd.concat([hsk, vi_only], ignore_index=True, sort=False)
    print(f"stage3: selected {len(vi_only):,} VI-only rows", flush=True)
    ids = assign_ids("word", words["word_key"], "w", 5)
    words.insert(0, "word_id", words["word_key"].map(ids))
    vi_only_report["word_id"] = vi_only_report["word_key"].map(ids).fillna("")
    for column in ["freq_score", "rank", "level"]:
        vi_only_report[column] = vi_only_report[column].map(
            lambda value: str(int(float(value))) if nfc(value) else ""
        )
    vi_only_report = vi_only_report[[
        "han", "trad", "word_id", "vi_values", "source_vi", "selected", "reason",
        "freq_score", "rank", "level",
    ]]
    words = add_pinyin_segments(words)

    chars = grow_chars(words, base_chars, lookup, kd)
    chars["in_hsk_chars"] = chars["in_hsk_chars"].map(
        lambda value: value is True or nfc(value).lower() in {"true", "1"}
    )
    print(f"stage3: chars grown to {len(chars):,}", flush=True)
    links, char_ambiguous, char_simp_mismatch = link_word_chars(words, chars)
    merge_rows.extend([
        {"merge": "word_char_link", "status": "both", "count": int((links["char_id"] != "").sum()), "validate": "one char row per word position"},
        {"merge": "word_char_link", "status": "left_only", "count": int((links["char_id"] == "").sum()), "validate": "one char row per word position"},
    ])
    words, ko_cache, vi_cache = match_all_words(
        words, chars, lookup, graph, jmdict_index, korean_index,
        explicit, explicit_en, headwords, phrases, merge_rows,
    )
    print("stage3: word dictionaries matched", flush=True)
    overrides = load_overrides()
    words, override_vi_reports = apply_word_overrides(words, overrides, ko_cache, vi_cache)
    if not override_vi_reports.empty:
        vi_report = pd.read_csv(
            FINAL / "vi_ambiguous.csv", encoding="utf-8", keep_default_na=False, dtype=str
        )
        write_csv(
            pd.concat([vi_report, override_vi_reports], ignore_index=True),
            FINAL / "vi_ambiguous.csv",
        )
    words, word_chars, alignment_mismatches = align_word_readings(words, links, chars, ko_cache)
    chars, primary_changes, primary_no_evidence = apply_d39(chars, words, word_chars, lookup, overrides)
    print("stage3: alignments and D39 complete", flush=True)
    words = set_final_word_fields(words, frequency)

    # Recompute non-HSK character levels from the final word list.
    levels = words.set_index("word_id")["level"].astype(int).to_dict()
    linked_levels: dict[str, list[int]] = defaultdict(list)
    for row in word_chars.itertuples(index=False):
        if row.char_id:
            linked_levels[row.char_id].append(levels[row.word_id])
    for index in chars.index[~chars["in_hsk_chars"]]:
        values = linked_levels.get(chars.at[index, "char_id"], [])
        chars.at[index, "level"] = str(min(values)) if values else ""

    write_csv(vi_only_report, FINAL / "vi_only_report.csv", bool_columns=["selected"])
    write_csv(char_ambiguous, FINAL / "char_ambiguous.csv")
    write_csv(char_simp_mismatch, FINAL / "char_simp_mismatch.csv")
    write_csv(alignment_mismatches, FINAL / "alignment_mismatches.csv")
    write_csv(primary_changes, FINAL / "char_primary_changes.csv")
    write_csv(
        primary_no_evidence, FINAL / "char_primary_no_evidence.csv",
        bool_columns=["ko_law_form_suspect", "char_source_evidence"],
    )
    write_csv(pd.DataFrame(merge_rows), FINAL / "merge_report.csv")

    write_character_reports(chars, word_chars, words)
    write_coverage(words, chars)
    ff, ff_vi_conflicts = build_ff_candidates(
        words, jmdict, jmdict_index, read_stage("cedict.csv"), explicit, explicit_en,
        korean_index, graph, lookup, headwords,
    )
    if not ff_vi_conflicts.empty:
        vi_report = pd.read_csv(
            FINAL / "vi_ambiguous.csv", encoding="utf-8", keep_default_na=False, dtype=str
        )
        write_csv(pd.concat([vi_report, ff_vi_conflicts], ignore_index=True), FINAL / "vi_ambiguous.csv")
    print(f"stage3: false-friend candidates {len(ff):,}", flush=True)
    write_csv(ff, STAGING / "ff_candidates.csv")

    char_columns = [
        "char_id", "trad", "key_char", "simp", "jp", "ja_on", "ko", "pinyin", "vi",
        "ja_on_all", "ko_all", "pinyin_all", "vi_all", "ko_base_all", "ko_final", "vi_final",
        "in_hsk_chars", "level", "gloss_en", "source_ko", "source_vi", "source_ja", "source_pinyin",
    ]
    word_export = words.copy()
    for column in WORD_COLUMNS:
        if column not in word_export:
            word_export[column] = ""
    word_export = word_export[WORD_COLUMNS]
    chars_export = chars[char_columns].copy()
    word_chars_export = word_chars[[
        "word_id", "position", "char_id", "pinyin_syllable", "ko_syllable", "ko_base", "vi_syllable"
    ]].copy()
    for frame in [word_export, chars_export, word_chars_export]:
        for column in frame.select_dtypes(include=["object", "string"]).columns:
            frame[column] = frame[column].map(nfc)
        require_nfc(frame)
    if word_export["word_id"].duplicated().any() or word_export.duplicated(["trad", "pinyin"]).loc[word_export["source_level"] == "hsk30"].any():
        raise ValueError("Final word keys are not unique")
    if word_chars_export.duplicated(["word_id", "position"]).any():
        raise ValueError("word_chars key is not unique")
    if len(word_chars_export) != sum(len(value) for value in word_export["trad"]):
        raise ValueError("word_chars row count does not equal sum of word lengths")

    write_csv(word_export, FINAL / "words.csv", bool_columns=["ja_common", "card_eligible", "syl_aligned", "verified"])
    write_json(word_export.replace("", pd.NA), FINAL / "words.json")
    write_csv(chars_export, FINAL / "chars.csv", bool_columns=["in_hsk_chars"])
    write_json(chars_export.replace("", pd.NA), FINAL / "chars.json")
    write_csv(word_chars_export, FINAL / "word_chars.csv")
    write_json(word_chars_export.replace("", pd.NA), FINAL / "word_chars.json")

    summary = {
        "chars_before_growth": len(base_chars), "chars_after_growth": len(chars_export),
        "hsk_words": int((word_export["source_level"] == "hsk30").sum()),
        "vi_only_words": int((word_export["source_level"] == "vi_band").sum()),
        "ff_candidates": len(ff), "word_chars": len(word_chars_export),
        "char_ambiguous": len(char_ambiguous), "char_simp_mismatch": len(char_simp_mismatch),
        "alignment_mismatches": len(alignment_mismatches),
    }
    (FINAL / "build_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()







