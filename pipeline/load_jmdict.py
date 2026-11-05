"""Load JMdict written-form/reading pairs while retaining entity tag names (D42)."""

from __future__ import annotations

import gzip
import re
from xml.etree import ElementTree as ET

import pandas as pd

from common import RAW, STAGING, nfc, write_csv


ENTITY_RE = re.compile(r'<!ENTITY\s+([A-Za-z0-9_-]+)\s+"([^"]*)">')
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def texts(parent: ET.Element, path: str) -> list[str]:
    return [nfc(node.text) for node in parent.findall(path) if nfc(node.text)]


def main() -> None:
    path = RAW / "jmdict" / "JMdict_e.gz"
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        prefix = handle.read(2_000_000)
    entity_to_name = {description: name for name, description in ENTITY_RE.findall(prefix)}

    rows: list[dict[str, object]] = []
    with gzip.open(path, "rb") as handle:
        for _event, entry in ET.iterparse(handle, events=("end",)):
            if entry.tag != "entry":
                continue
            ent_seq = int(nfc(entry.findtext("ent_seq", "0")))
            kebs = []
            for keb_pos, node in enumerate(entry.findall("k_ele"), start=1):
                kebs.append({
                    "keb": nfc(node.findtext("keb", "")),
                    "ke_inf": [entity_to_name.get(v, v) for v in texts(node, "ke_inf")],
                    "ke_pri": [entity_to_name.get(v, v) for v in texts(node, "ke_pri")],
                    "keb_pos": keb_pos,
                })
            readings = []
            for reb_pos, node in enumerate(entry.findall("r_ele"), start=1):
                readings.append({
                    "reb": nfc(node.findtext("reb", "")),
                    "re_nokanji": node.find("re_nokanji") is not None,
                    "re_restr": texts(node, "re_restr"),
                    "re_inf": [entity_to_name.get(v, v) for v in texts(node, "re_inf")],
                    "re_pri": [entity_to_name.get(v, v) for v in texts(node, "re_pri")],
                    "reb_pos": reb_pos,
                })
            first_gloss = ""
            for sense in entry.findall("sense"):
                for gloss in sense.findall("gloss"):
                    if gloss.attrib.get(XML_LANG, "eng") == "eng" and nfc(gloss.text):
                        first_gloss = nfc(gloss.text)
                        break
                if first_gloss:
                    break
            for keb in kebs:
                for reading in readings:
                    if reading["re_nokanji"]:
                        continue
                    restrictions = reading["re_restr"]
                    if restrictions and keb["keb"] not in restrictions:
                        continue
                    rows.append({
                        "ent_seq": ent_seq, "keb": keb["keb"], "reb": reading["reb"],
                        "keb_pos": keb["keb_pos"], "reb_pos": reading["reb_pos"],
                        "ke_inf": ";".join(keb["ke_inf"]),
                        "ke_pri": ";".join(keb["ke_pri"]),
                        "re_inf": ";".join(reading["re_inf"]),
                        "re_pri": ";".join(reading["re_pri"]),
                        "gloss_ja_en": first_gloss,
                    })
            entry.clear()
    frame = pd.DataFrame(rows)
    write_csv(frame, STAGING / "jmdict.csv")
    print(f"jmdict: {len(frame):,} allowed written-form/reading pairs")


if __name__ == "__main__":
    main()
