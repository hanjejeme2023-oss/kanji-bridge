"""Parse Kaikki/English-Wiktionary Vietnamese evidence for D53 and D55."""

from __future__ import annotations

import json
import re
from collections import defaultdict

import pandas as pd

from common import RAW, STAGING, all_cjk, nfc, normalize_vietnamese, write_csv


ETYMOLOGY_RE = re.compile(
    r"Sino-Vietnamese word from ([\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0003ffff]+)"
)
CHAR_GLOSS_RE = re.compile(r"^chữ Hán form of (.+?)(?: \(|$)")
BLOCKED_POS = {"character", "name", "romanization"}
BLOCKED_SENSE_TAGS = {"alt-of", "abbreviation"}


def positional_han_forms(record: dict[str, object]) -> list[str]:
    forms: list[str] = []
    for template in record.get("etymology_templates") or []:
        if template.get("name") != "vi-etym-sino":
            continue
        args = template.get("args") or {}
        keys = sorted(
            (key for key in args if str(key).isdigit() and int(key) % 2 == 1),
            key=lambda key: int(key),
        )
        candidate = "".join(nfc(args[key]) for key in keys)
        if candidate and all_cjk(candidate):
            forms.append(candidate)
    match = ETYMOLOGY_RE.search(nfc(record.get("etymology_text")))
    if match:
        forms.append(nfc(match.group(1)))
    return list(dict.fromkeys(forms))


def first_gloss_and_tags(senses: list[dict[str, object]]) -> tuple[str, set[str]]:
    first_gloss = ""
    tags: set[str] = set()
    for sense in senses:
        tags.update(nfc(tag) for tag in (sense.get("tags") or []))
        glosses = sense.get("glosses") or []
        if glosses and not first_gloss:
            first_gloss = nfc(glosses[0])
    return first_gloss, tags


def main() -> None:
    pair_records: dict[tuple[str, str], dict[str, object]] = {}
    char_records: dict[tuple[str, str], dict[str, object]] = {}
    raw_pairs = 0
    source = RAW / "kaikki-enwiktionary" / "kaikki.org-dictionary-Vietnamese.jsonl"
    with source.open("r", encoding="utf-8") as handle:
        for source_order, line in enumerate(handle, start=1):
            record = json.loads(line)
            if record.get("lang_code") != "vi" or not record.get("word"):
                continue
            word = normalize_vietnamese(record["word"])
            senses = record.get("senses") or []
            first_gloss, tags = first_gloss_and_tags(senses)
            pos = nfc(record.get("pos"))

            if pos == "character" and len(nfc(record["word"])) == 1:
                for sense in senses:
                    for gloss in sense.get("glosses") or []:
                        match = CHAR_GLOSS_RE.match(nfc(gloss))
                        if not match:
                            continue
                        for value in re.split(r"\s*[,/]\s*", match.group(1)):
                            vi = normalize_vietnamese(value.strip("“”\" "))
                            if vi:
                                char_records.setdefault(
                                    (nfc(record["word"]), vi),
                                    {"char": nfc(record["word"]), "vi": vi, "source_order": source_order},
                                )
                continue

            forms = positional_han_forms(record)
            raw_pairs += len(forms)
            if pos in BLOCKED_POS or tags & BLOCKED_SENSE_TAGS:
                continue
            lowered_gloss = first_gloss.lower()
            if "given name" in lowered_gloss or "surname" in lowered_gloss:
                continue
            if not word:
                continue
            obsolete_only = bool(senses) and all(
                bool(set(nfc(tag) for tag in (sense.get("tags") or [])) & {"obsolete", "archaic"})
                for sense in senses
            )
            for form in forms:
                if len(word.split()) != len(form):
                    continue
                key = (form, word)
                existing = pair_records.get(key)
                candidate = {
                    "han": form,
                    "vi": word,
                    "pos": pos,
                    "gloss_vi": first_gloss,
                    "obsolete_only": obsolete_only,
                    "source_order": source_order,
                }
                if existing is None or (existing["obsolete_only"] and not obsolete_only):
                    pair_records[key] = candidate

    pairs = pd.DataFrame(
        sorted(pair_records.values(), key=lambda row: (row["source_order"], row["han"], row["vi"])),
        columns=["han", "vi", "pos", "gloss_vi", "obsolete_only", "source_order"],
    )
    chars = pd.DataFrame(
        sorted(char_records.values(), key=lambda row: (row["source_order"], row["char"], row["vi"])),
        columns=["char", "vi", "source_order"],
    )
    write_csv(pairs, STAGING / "kaikki_en.csv", bool_columns=["obsolete_only"])
    write_csv(chars, STAGING / "kaikki_en_char_readings.csv")
    print(
        f"kaikki-en: {raw_pairs:,} raw pairs; {len(pairs):,} filtered aligned pairs; "
        f"{pairs['han'].nunique():,} forms; {len(chars):,} chữ Hán character readings"
    )


if __name__ == "__main__":
    main()
