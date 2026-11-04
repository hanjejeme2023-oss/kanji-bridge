"""Generate docs/SOURCE_PROFILES.md from the immutable files under raw/.

This is a Stage 1 inspection tool, not a loader for final tables.  It applies
the project's text-loading rules (explicit UTF-8, no default NA conversion,
strip + NFC normalization) and records counts, schemas, samples, and observed
quality risks without changing raw inputs.
"""

from __future__ import annotations

import gzip
import json
import re
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
OUTPUT = ROOT / "docs" / "SOURCE_PROFILES.md"
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0003134f]+")


def clean(value: object) -> str:
    return unicodedata.normalize("NFC", str(value).strip())


def clip(value: object, limit: int = 78) -> str:
    text = clean(value).replace("\r", " ").replace("\n", " ").replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def md_table(columns: list[str], rows: list[dict[str, object]]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(clip(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def normalize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    for column in frame.select_dtypes(include=["object", "string"]).columns:
        frame[column] = frame[column].astype("string").str.strip().str.normalize("NFC")
    return frame


def profile_unihan() -> dict[str, object]:
    fields = {"kHangul", "kVietnamese", "kMandarin", "kDefinition", "kSimplifiedVariant", "kTraditionalVariant"}
    counts: Counter[str] = Counter()
    codepoints: set[str] = set()
    samples: list[dict[str, str]] = []
    with zipfile.ZipFile(RAW / "unihan" / "Unihan.zip") as archive:
        members = [name for name in archive.namelist() if name.endswith(".txt")]
        for member in members:
            with archive.open(member) as binary:
                for raw_line in binary:
                    line = raw_line.decode("utf-8").strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("\t", 2)
                    if len(parts) != 3 or parts[1] not in fields:
                        continue
                    code, field, value = map(clean, parts)
                    counts[field] += 1
                    codepoints.add(code)
                    if len(samples) < 10:
                        samples.append(
                            {
                                "codepoint": code,
                                "char": chr(int(code[2:], 16)),
                                "field": field,
                                "value": value,
                            }
                        )
    return {"members": len(members), "counts": counts, "codepoints": len(codepoints), "samples": samples}


def profile_kanjidic2() -> dict[str, object]:
    count = 0
    samples: list[dict[str, str]] = []
    variants = 0
    with gzip.open(RAW / "kanjidic2" / "kanjidic2.xml.gz", "rb") as handle:
        for _event, element in ET.iterparse(handle, events=("end",)):
            if element.tag != "character":
                continue
            count += 1
            literal = clean(element.findtext("literal", ""))
            readings = [
                clean(node.text or "")
                for node in element.findall("./reading_meaning/rmgroup/reading")
                if node.attrib.get("r_type") == "ja_on"
            ]
            variant_values = [clean(node.text or "") for node in element.findall("./misc/variant")]
            variants += len(variant_values)
            meanings = [
                clean(node.text or "")
                for node in element.findall("./reading_meaning/rmgroup/meaning")
                if "m_lang" not in node.attrib
            ]
            if len(samples) < 10:
                samples.append(
                    {
                        "literal": literal,
                        "ja_on": "; ".join(readings),
                        "variants": "; ".join(variant_values),
                        "meaning_en": "; ".join(meanings[:2]),
                    }
                )
            element.clear()
    return {"rows": count, "variant_values": variants, "samples": samples}


def profile_hsk30() -> dict[str, object]:
    words = normalize_frame(
        pd.read_csv(RAW / "hsk30" / "hsk30.csv", encoding="utf-8", keep_default_na=False)
    )
    chars = normalize_frame(
        pd.read_csv(RAW / "hsk30" / "hsk30-chars.csv", encoding="utf-8", keep_default_na=False)
    )
    sample_columns = ["ID", "Simplified", "Traditional", "Pinyin", "POS", "Level"]
    samples = words.loc[:, sample_columns].head(10).to_dict("records")
    return {
        "word_rows": len(words),
        "char_rows": len(chars),
        "word_columns": list(words.columns),
        "char_columns": list(chars.columns),
        "word_duplicate_ids": int(words["ID"].duplicated().sum()),
        "char_levels": chars["Level"].value_counts(dropna=False).sort_index().to_dict(),
        "samples": samples,
    }


def profile_cedict() -> dict[str, object]:
    pattern = re.compile(r"^(\S+) (\S+) \[(.+?)\] /(.+)/$")
    count = 0
    failures = 0
    samples: list[dict[str, str]] = []
    header: list[str] = []
    with gzip.open(RAW / "cc-cedict" / "cedict_1_0_ts_utf-8_mdbg.txt.gz", "rt", encoding="utf-8") as handle:
        for raw_line in handle:
            line = clean(raw_line)
            if not line:
                continue
            if line.startswith("#"):
                if len(header) < 12:
                    header.append(line.lstrip("# "))
                continue
            count += 1
            match = pattern.match(line)
            if match is None:
                failures += 1
                continue
            if len(samples) < 10:
                trad, simp, pinyin, gloss = match.groups()
                samples.append({"trad": trad, "simp": simp, "pinyin": pinyin, "gloss": gloss})
    return {"rows": count, "parse_failures": failures, "header": header, "samples": samples}


def profile_jmdict() -> dict[str, object]:
    count = 0
    common = 0
    samples: list[dict[str, str]] = []
    with gzip.open(RAW / "jmdict" / "JMdict_e.gz", "rb") as handle:
        for _event, element in ET.iterparse(handle, events=("end",)):
            if element.tag != "entry":
                continue
            count += 1
            keb = [clean(node.text or "") for node in element.findall("./k_ele/keb")]
            reb = [clean(node.text or "") for node in element.findall("./r_ele/reb")]
            pri = [clean(node.text or "") for node in element.findall("./k_ele/ke_pri")]
            pri += [clean(node.text or "") for node in element.findall("./r_ele/re_pri")]
            if pri:
                common += 1
            glosses = [clean(node.text or "") for node in element.findall("./sense/gloss")]
            if len(samples) < 10:
                samples.append(
                    {
                        "ent_seq": clean(element.findtext("ent_seq", "")),
                        "kanji": "; ".join(keb),
                        "reading": "; ".join(reb),
                        "priority": "; ".join(dict.fromkeys(pri)),
                        "gloss_en": "; ".join(glosses[:2]),
                    }
                )
            element.clear()
    return {"rows": count, "common_entries": common, "samples": samples}


def profile_libhangul() -> dict[str, object]:
    count = 0
    malformed = 0
    samples: list[dict[str, str]] = []
    readings: Counter[str] = Counter()
    pairs: Counter[tuple[str, str]] = Counter()
    with (RAW / "libhangul" / "hanja.txt").open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = clean(raw_line)
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            if len(parts) < 3:
                malformed += 1
                continue
            reading, hanja, comment = parts[0], parts[1], ":".join(parts[2:])
            count += 1
            readings[reading] += 1
            pairs[(reading, hanja)] += 1
            if len(samples) < 10:
                samples.append({"reading": reading, "hanja": hanja, "comment": comment})
    return {
        "rows": count,
        "malformed": malformed,
        "readings": len(readings),
        "duplicate_pairs": sum(value - 1 for value in pairs.values() if value > 1),
        "samples": samples,
    }


def read_opencc(path: Path, kind: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = clean(raw_line)
            if not line or line.startswith("#"):
                continue
            key, values = line.split("\t", 1)
            rows.append({"candidate": kind, "key": key, "values": values})
    return rows


def profile_opencc() -> dict[str, object]:
    chars = read_opencc(RAW / "opencc" / "JPShinjitaiCharacters.txt", "character")
    phrases = read_opencc(RAW / "opencc" / "JPShinjitaiPhrases.txt", "phrase")
    return {
        "char_rows": len(chars),
        "phrase_rows": len(phrases),
        "samples": (chars[:5] + phrases[:5]),
    }


def profile_kaikki() -> dict[str, object]:
    total = 0
    vi_total = 0
    hanviet = 0
    with_han_form = 0
    keys: Counter[str] = Counter()
    samples: list[dict[str, str]] = []
    seen_pairs: Counter[tuple[str, str]] = Counter()
    with gzip.open(
        RAW / "kaikki-viwiktionary" / "vi-extract.jsonl.gz", "rt", encoding="utf-8"
    ) as handle:
        for raw_line in handle:
            total += 1
            row = json.loads(raw_line)
            if row.get("lang_code") != "vi":
                continue
            vi_total += 1
            keys.update(row.keys())
            word = clean(row.get("word", ""))
            pos = clean(row.get("pos", ""))
            seen_pairs[(word, pos)] += 1
            categories = [clean(value) for value in row.get("categories", [])]
            etymologies = [clean(value) for value in row.get("etymology_texts", [])]
            is_hanviet = any("Hán-Việt" in value for value in categories + etymologies)
            if not is_hanviet:
                continue
            hanviet += 1
            joined = " ".join(etymologies)
            han_forms = CJK_RE.findall(joined)
            if han_forms:
                with_han_form += 1
            if len(samples) < 10:
                glosses = [
                    clean(gloss)
                    for sense in row.get("senses", [])
                    for gloss in sense.get("glosses", [])
                ]
                samples.append(
                    {
                        "word": word,
                        "pos": pos,
                        "han_form": "; ".join(dict.fromkeys(han_forms)),
                        "gloss_vi": "; ".join(glosses[:2]),
                    }
                )
    duplicates = sum(value - 1 for value in seen_pairs.values() if value > 1)
    return {
        "total": total,
        "vi_total": vi_total,
        "hanviet": hanviet,
        "with_han_form": with_han_form,
        "duplicates": duplicates,
        "keys": [key for key, _count in keys.most_common()],
        "samples": samples,
    }


def profile_frequencywords() -> dict[str, object]:
    frame = pd.read_csv(
        RAW / "frequencywords-vi" / "vi_50k.txt",
        sep=r"\s+",
        names=["word", "count"],
        encoding="utf-8",
        keep_default_na=False,
    )
    frame = normalize_frame(frame)
    numeric = pd.to_numeric(frame["count"], errors="coerce")
    samples = frame.head(10).to_dict("records")
    return {
        "rows": len(frame),
        "duplicate_words": int(frame["word"].duplicated().sum()),
        "bad_counts": int(numeric.isna().sum()),
        "samples": samples,
    }


def main() -> None:
    unihan = profile_unihan()
    kanjidic = profile_kanjidic2()
    hsk = profile_hsk30()
    cedict = profile_cedict()
    jmdict = profile_jmdict()
    libhangul = profile_libhangul()
    opencc = profile_opencc()
    kaikki = profile_kaikki()
    frequency = profile_frequencywords()

    sections: list[str] = []
    sections.append(
        "# SOURCE PROFILES\n\n"
        "Generated by `python pipeline/profile_sources.py` from the files locked in the committed "
        "`pipeline/source_manifest.csv` (mirrored at runtime to `raw/MANIFEST.csv`). Raw inputs are never modified. Text is read as explicit UTF-8, "
        "trimmed and NFC-normalized for inspection; pandas loads tabular word data with "
        "`keep_default_na=False`. Counts below are from the 2026-11-04 download.\n\n"
        "The ten-row samples are diagnostic excerpts, not curated facts and not pipeline overrides."
    )

    sections.append(
        "## 1. Unihan database\n\n"
        f"- **URL / license:** `unicode.org/Public/UCD/latest/ucd/Unihan.zip`; Unicode License v3 "
        "(`licenses/UNICODE-LICENSE.txt`).\n"
        f"- **Format / encoding:** ZIP containing {unihan['members']} UTF-8 tab-separated long-form files; "
        "comment lines begin with `#`.\n"
        f"- **Profiled scope:** {unihan['codepoints']:,} distinct code points across the six needed fields. "
        f"Field row counts: {dict(unihan['counts'])}.\n"
        "- **Key columns:** code point (`U+XXXX`), property, value. Canonical character is decoded from the code point.\n"
        "- **Quality problems:** readings are character-level, may be multi-valued, and are not aligned across languages; "
        "`kHangul` values carry source suffixes such as `:0E`; variant properties are many-to-many and are not a clean "
        "Japanese shinjitai mapping. `kVietnamese` needs the planned independent cross-check.\n\n"
        + md_table(["codepoint", "char", "field", "value"], unihan["samples"])
    )

    sections.append(
        "## 2. KANJIDIC2\n\n"
        "- **URL / license:** `edrdg.org/pub/Nihongo/kanjidic2.xml.gz`; EDRDG General Dictionary Licence, "
        "CC BY-SA 4.0 (`licenses/KANJIDIC2-EDRDG-LICENSE.html`).\n"
        f"- **Format / encoding / rows:** gzip-compressed UTF-8 XML; {kanjidic['rows']:,} `<character>` rows.\n"
        f"- **Key columns/elements:** `literal`; `reading_meaning/rmgroup/reading` with `r_type=ja_on`; "
        f"English `meaning`; `misc/variant`. Observed {kanjidic['variant_values']:,} variant values.\n"
        "- **Quality problems:** several readings and written variants can occur per character; variant elements use several "
        "dictionary-code schemes and do not by themselves identify the preferred traditional Chinese form. The licence has "
        "special notices for some lookup-code fields; this project only needs readings/forms.\n\n"
        + md_table(["literal", "ja_on", "variants", "meaning_en"], kanjidic["samples"])
    )

    sections.append(
        "## 3. ivankra/hsk30\n\n"
        "- **URL / license:** `github.com/ivankra/hsk30`; repository MIT licence "
        "(`licenses/HSK30-MIT-LICENSE.txt`). The README states that CSV data derive largely from two MIT repositories but "
        "also flags uncertainty around copyright in the underlying PRC Ministry of Education list; Claude must review this.\n"
        f"- **Format / encoding / rows:** UTF-8 CSV; {hsk['word_rows']:,} vocabulary rows and {hsk['char_rows']:,} character rows.\n"
        f"- **Vocabulary columns:** {', '.join(hsk['word_columns'])}.\n"
        f"- **Character columns:** {', '.join(hsk['char_columns'])}. Per-character `Level` is present; counts by level: "
        f"{hsk['char_levels']}.\n"
        f"- **Key / integrity:** `ID` is the vocabulary key; duplicate IDs: {hsk['word_duplicate_ids']}.\n"
        "- **Quality problems:** some headwords encode alternatives or examples using punctuation; `Traditional` may contain "
        "multiple variants and is described upstream as heuristic at high levels. HSK 7–9 is a combined band, not three "
        "separate official levels. The README's government-work provenance needs a licence judgment.\n\n"
        + md_table(["ID", "Simplified", "Traditional", "Pinyin", "POS", "Level"], hsk["samples"])
    )

    sections.append(
        "## 4. CC-CEDICT\n\n"
        "- **URL / license:** MDBG rolling UTF-8 export; CC-CEDICT CC BY-SA 4.0 "
        "(`licenses/CC-CEDICT-LICENSE.html`, full code in `licenses/CC-BY-SA-4.0.txt`).\n"
        f"- **Format / encoding / rows:** gzip-compressed UTF-8 text; {cedict['rows']:,} data rows. "
        f"Parser failures against `trad simp [numbered pinyin] /gloss/`: {cedict['parse_failures']}.\n"
        "- **Key columns:** traditional, simplified, numbered pinyin, slash-separated English definitions.\n"
        "- **Quality problems:** multiple entries can share written forms but differ by pronunciation/sense; pinyin is "
        "tone-number form and must be normalized later; classifier/cross-reference syntax occurs inside definitions. "
        "It is a rolling export, so the manifest checksum is the snapshot lock.\n\n"
        + md_table(["trad", "simp", "pinyin", "gloss"], cedict["samples"])
    )

    sections.append(
        "## 5. JMdict (English subset)\n\n"
        "- **URL / license:** `edrdg.org/pub/Nihongo/JMdict_e.gz`; EDRDG General Dictionary Licence, "
        "CC BY-SA 4.0 (`licenses/JMDICT-EDRDG-LICENSE.html`).\n"
        f"- **Format / encoding / rows:** gzip-compressed UTF-8 XML; {jmdict['rows']:,} `<entry>` rows, "
        f"of which {jmdict['common_entries']:,} carry at least one priority tag.\n"
        "- **Key columns/elements:** `ent_seq`; one or more `k_ele/keb`; one or more `r_ele/reb`; reading restrictions; "
        "priority tags; senses and English glosses.\n"
        "- **Quality problems:** entries are one-to-many across spellings, readings and senses; restrictions must be honored "
        "when pairing written form to reading. Commonness is encoded by several priority tags, not one boolean. "
        "Kana-only and non-Han entries are normal.\n\n"
        + md_table(["ent_seq", "kanji", "reading", "priority", "gloss_en"], jmdict["samples"])
    )

    sections.append(
        "## 6. libhangul `hanja.txt`\n\n"
        "- **URL / license:** `github.com/libhangul/libhangul/data/hanja/hanja.txt`; the file's own header is BSD "
        "3-Clause, Copyright (c) 2005,2006 Choe Hwanjin "
        "(`licenses/LIBHANGUL-HANJA-BSD-3-CLAUSE.txt`). The repository as a whole is LGPL-2.1.\n"
        f"- **Format / encoding / rows:** UTF-8 colon-separated text after a comment header; {libhangul['rows']:,} records, "
        f"{libhangul['readings']:,} distinct reading keys, {libhangul['malformed']} malformed rows.\n"
        f"- **Key columns:** Hangul reading, Hanja word/form, optional comment. Duplicate `(reading, hanja)` pairs: "
        f"{libhangul['duplicate_pairs']}.\n"
        "- **Quality problems:** the table is ordered for input-method lookup rather than lexical frequency; it contains "
        "characters, compounds, grammatical labels, symbols, and proper-name material together. The data file's BSD header "
        "is clear, but Claude should confirm the per-file licence and compatibility with share-alike outputs.\n\n"
        + md_table(["reading", "hanja", "comment"], libhangul["samples"])
    )

    sections.append(
        "## 7. `ryanphung/chinese-hanviet-cognates` — excluded\n\n"
        "- **URL:** `github.com/ryanphung/chinese-hanviet-cognates`.\n"
        "- **License:** none. The repository provides no licence grant. Its README also says `vietphrases.txt` has "
        "`source missing`, and states that source data remain owned by their respective owners.\n"
        "- **Decision:** excluded by the user on 2026-11-04. No file from this repository was downloaded or used. "
        "It cannot feed readings, frequency, or validation.\n"
        "- **Former output shape (documentation only):** TSV columns shown in its README are index, Chinese rank, "
        "frequency, simplified, traditional, pinyin, Hán-Việt, meaning. No sample rows are reproduced because the source "
        "has no usable licence."
    )

    sections.append(
        "## 7A. Vietnamese replacement candidate: Kaikki / Vietnamese Wiktionary\n\n"
        "- **URL / license:** `kaikki.org/viwiktionary/rawdata.html`; Wiktionary-derived data under CC BY-SA and GFDL "
        "(`licenses/KAIKKI-VIWIKTIONARY-LICENSE.html`). Downloaded raw Wiktextract JSONL snapshot.\n"
        f"- **Format / encoding / rows:** gzip-compressed UTF-8 JSON Lines; {kaikki['total']:,} entries across languages "
        f"in the Vietnamese-edition extract; {kaikki['vi_total']:,} entries have `lang_code=vi`.\n"
        f"- **Candidate coverage:** {kaikki['hanviet']:,} Vietnamese entries are explicitly marked `Hán-Việt` in category "
        f"or etymology metadata; {kaikki['with_han_form']:,} of those expose at least one CJK string in `etymology_texts`.\n"
        f"- **Observed columns:** {', '.join(kaikki['keys'])}.\n"
        f"- **Key / integrity:** proposed inspection key is `(word, pos)`; repeated rows beyond that key: "
        f"{kaikki['duplicates']} (senses/etymologies require resolution, not blind dedupe).\n"
        "- **Potential use:** Hán-Việt word reading (`word`) linked to source Han spelling parsed from explicit etymology "
        "text; Vietnamese glosses are also present. This source does **not** provide corpus frequency ranks.\n"
        "- **Quality problems:** community-edited coverage is incomplete; some Hán-Việt categories say the Han etymon "
        "article is missing; CJK strings in prose need conservative parsing; Nôm and Hán forms coexist; multiple POS/sense "
        "rows occur. Any loader must require explicit evidence and report ambiguity.\n\n"
        + md_table(["word", "pos", "han_form", "gloss_vi"], kaikki["samples"])
    )

    sections.append(
        "## 7B. Vietnamese replacement candidate: FrequencyWords / OpenSubtitles 2018\n\n"
        "- **URL / license:** `github.com/hermitdave/FrequencyWords/content/2018/vi/vi_50k.txt`; upstream README declares "
        "content CC BY-SA 4.0 (`licenses/FREQUENCYWORDS-CONTENT-LICENSE.md`; full code already in "
        "`licenses/CC-BY-SA-4.0.txt`).\n"
        f"- **Format / encoding / rows:** UTF-8 space-separated `token count`; {frequency['rows']:,} rows.\n"
        f"- **Key / integrity:** token; duplicate tokens: {frequency['duplicate_words']}; non-numeric counts: "
        f"{frequency['bad_counts']}.\n"
        "- **Potential use:** frequency evidence/rank for Vietnamese tokens. It supplies frequency only, not Hán-Việt "
        "etymology or Han spellings.\n"
        "- **Quality problems:** subtitle-domain counts favor conversational language and names; the list is tokenized into "
        "space-delimited syllable tokens, so it does not directly rank multi-syllable Vietnamese words such as `học sinh`; "
        "foreign tokens and orthographic noise occur. Joining compound readings would need a documented frequency rule.\n\n"
        + md_table(["word", "count"], frequency["samples"])
    )

    sections.append(
        "## 8. Shinjitai ↔ traditional mapping candidates\n\n"
        "No method is selected in Stage 1. The downloaded candidates are:\n\n"
        f"1. **OpenCC `JPShinjitaiCharacters.txt` / `JPShinjitaiPhrases.txt`** — Apache 2.0 "
        f"(`licenses/OPENCC-APACHE-2.0-LICENSE.txt`); UTF-8 tab-separated; "
        f"{opencc['char_rows']:,} character rows and {opencc['phrase_rows']:,} phrase rows. It is the most explicit "
        "Japanese old/new-form candidate, but some keys map to multiple values and upstream labels the broader Japanese "
        "conversion configs exploratory.\n"
        "2. **KANJIDIC2 variants** — already profiled above; licensed CC BY-SA 4.0. Variants are typed with several "
        "dictionary reference codes, but not a direct traditional-Chinese preference map.\n"
        "3. **Unihan `kTraditionalVariant` / `kSimplifiedVariant`** — already profiled above; Unicode License v3. "
        "They cover CJK variants broadly and are many-to-many, not specifically Japanese shinjitai.\n\n"
        + md_table(["candidate", "key", "values"], opencc["samples"])
    )

    sections.append(
        "## Review questions for Claude\n\n"
        "1. Confirm that the BSD 3-Clause header embedded in libhangul `hanja.txt` governs the extracted data and that "
        "combining its values with CC BY-SA sources is acceptable when final data are released under CC BY-SA.\n"
        "2. Confirm the hsk30 licence/provenance judgment: the repository declares MIT, but its README flags uncertainty "
        "around the PRC Ministry of Education source.\n"
        "3. The hsk30 character list **does** have per-character `Level` (first appearance / reading level). Confirm it "
        "should feed `chars.level` before the Stage 3 minimum-word-level fallback.\n"
        "4. Select the Vietnamese replacement input(s), or reject both: Kaikki supplies explicit Hán-Việt entries and "
        "Han-form evidence under Wiktionary CC BY-SA/GFDL; FrequencyWords supplies CC BY-SA subtitle token counts but "
        "not multi-syllable word ranks. Decide the join/frequency rule and source priority before Stage 3.\n"
        "5. Perform the planned 200-character Unihan `kVietnamese` cross-check against the selected licensed Vietnamese "
        "reading data. Kaikki is word-oriented and may not support the intended character-level sample without a separate "
        "licensed character dictionary; decide whether another source is required.\n"
        "6. Choose the shinjitai mapping method among OpenCC, KANJIDIC2 variants and Unihan variants, including the "
        "tie-break rule for multiple OpenCC targets.\n"
        "7. Set source priority per output column.\n"
        "8. Confirm all share-alike implications: EDRDG, CC-CEDICT, Kaikki/Wiktionary and FrequencyWords candidates all "
        "require attribution/share-alike handling if selected or used in final output."
    )

    OUTPUT.write_text("\n\n".join(sections).rstrip() + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
