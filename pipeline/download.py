"""Download and verify every Stage 1 dictionary source.

URL-level SHA-256 hashes are committed in pipeline/source_manifest.csv and
mirrored to raw/MANIFEST.csv. Later runs use that manifest as a lock: matching
files are not downloaded, and a missing file is accepted only when the newly
downloaded bytes match the recorded hash. Use --refresh only for a deliberate
source update.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
LICENSES = ROOT / "licenses"
MANIFEST = RAW / "MANIFEST.csv"
LOCKFILE = ROOT / "pipeline" / "source_manifest.csv"
MANIFEST_FIELDS = ["source", "url", "date", "sha256", "bytes", "path", "role"]
USER_AGENT = "kanji-bridge-data-pipeline/1.0 (+local reproducible research build)"


@dataclass(frozen=True)
class Download:
    source: str
    filename: str
    url: str
    role: str = "data"
    license_copy: str | None = None

    @property
    def path(self) -> Path:
        return RAW / self.source / self.filename


DOWNLOADS = [
    Download(
        "unihan",
        "Unihan.zip",
        "https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip",
    ),
    Download(
        "unihan",
        "license.txt",
        "https://www.unicode.org/license.txt",
        "license",
        "UNICODE-LICENSE.txt",
    ),
    Download(
        "kanjidic2",
        "kanjidic2.xml.gz",
        "https://www.edrdg.org/pub/Nihongo/kanjidic2.xml.gz",
    ),
    Download(
        "kanjidic2",
        "LICENSE.html",
        "https://www.edrdg.org/edrdg/newlic.html",
        "license",
        "KANJIDIC2-EDRDG-LICENSE.html",
    ),
    Download(
        "hsk30",
        "hsk30.csv",
        "https://raw.githubusercontent.com/ivankra/hsk30/master/hsk30.csv",
    ),
    Download(
        "hsk30",
        "hsk30-chars.csv",
        "https://raw.githubusercontent.com/ivankra/hsk30/master/hsk30-chars.csv",
    ),
    Download(
        "hsk30",
        "README.md",
        "https://raw.githubusercontent.com/ivankra/hsk30/master/README.md",
        "documentation",
    ),
    Download(
        "hsk30",
        "LICENSE",
        "https://raw.githubusercontent.com/ivankra/hsk30/master/LICENSE",
        "license",
        "HSK30-MIT-LICENSE.txt",
    ),
    Download(
        "cc-cedict",
        "cedict_1_0_ts_utf-8_mdbg.txt.gz",
        "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz",
    ),
    Download(
        "cc-cedict",
        "LICENSE.html",
        "https://cc-cedict.org/wiki/start",
        "license",
        "CC-CEDICT-LICENSE.html",
    ),
    Download(
        "cc-cedict",
        "CC-BY-SA-4.0.txt",
        "https://creativecommons.org/licenses/by-sa/4.0/legalcode.txt",
        "license",
        "CC-BY-SA-4.0.txt",
    ),
    Download(
        "jmdict",
        "JMdict_e.gz",
        "https://www.edrdg.org/pub/Nihongo/JMdict_e.gz",
    ),
    Download(
        "jmdict",
        "LICENSE.html",
        "https://www.edrdg.org/edrdg/newlic.html",
        "license",
        "JMDICT-EDRDG-LICENSE.html",
    ),
    Download(
        "libhangul",
        "hanja.txt",
        "https://raw.githubusercontent.com/libhangul/libhangul/master/data/hanja/hanja.txt",
    ),
    # Candidate material only. Claude selects the mapping method in review.
    Download(
        "opencc",
        "JPShinjitaiCharacters.txt",
        "https://raw.githubusercontent.com/BYVoid/OpenCC/master/data/dictionary/JPShinjitaiCharacters.txt",
        "mapping-candidate",
    ),
    Download(
        "opencc",
        "JPShinjitaiPhrases.txt",
        "https://raw.githubusercontent.com/BYVoid/OpenCC/master/data/dictionary/JPShinjitaiPhrases.txt",
        "mapping-candidate",
    ),
    Download(
        "opencc",
        "LICENSE",
        "https://raw.githubusercontent.com/BYVoid/OpenCC/master/LICENSE",
        "license",
        "OPENCC-APACHE-2.0-LICENSE.txt",
    ),
    # Licensed Vietnamese replacement candidates. They are downloaded and
    # profiled in Stage 1, but are not selected as pipeline inputs here.
    Download(
        "kaikki-viwiktionary",
        "vi-extract.jsonl.gz",
        "https://kaikki.org/viwiktionary/raw-wiktextract-data.jsonl.gz",
        "candidate-data",
    ),
    Download(
        "kaikki-viwiktionary",
        "LICENSE.html",
        "https://kaikki.org/viwiktionary/index.html",
        "license",
        "KAIKKI-VIWIKTIONARY-LICENSE.html",
    ),
    Download(
        "frequencywords-vi",
        "vi_50k.txt",
        "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/vi/vi_50k.txt",
        "candidate-data",
    ),
    Download(
        "frequencywords-vi",
        "README.md",
        "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/README.md",
        "license",
        "FREQUENCYWORDS-CONTENT-LICENSE.md",
    ),
    Download(
        "frequencywords-vi",
        "CC-BY-SA-4.0.txt",
        "https://creativecommons.org/licenses/by-sa/4.0/legalcode.txt",
        "license",
        None,
    ),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest() -> dict[str, dict[str, str]]:
    manifest_path = MANIFEST if MANIFEST.exists() else LOCKFILE
    if not manifest_path.exists():
        return {}
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row["path"]: row for row in rows}


def fetch(item: Download, expected: str | None) -> None:
    item.path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(item.url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(1, 4):
        temp_name: str | None = None
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status} for {item.url}")
                with tempfile.NamedTemporaryFile(
                    dir=item.path.parent, prefix=item.filename + ".", suffix=".tmp", delete=False
                ) as temp:
                    temp_name = temp.name
                    shutil.copyfileobj(response, temp, length=1024 * 1024)
            temp_path = Path(temp_name)
            actual = sha256(temp_path)
            if expected and actual != expected:
                temp_path.unlink(missing_ok=True)
                raise RuntimeError(
                    f"Checksum drift for {item.url}: expected {expected}, downloaded {actual}. "
                    "Run with --refresh only after reviewing the upstream change."
                )
            temp_path.replace(item.path)
            return
        except (OSError, urllib.error.URLError, RuntimeError) as error:
            last_error = error
            if temp_name:
                Path(temp_name).unlink(missing_ok=True)
            if attempt < 3:
                time.sleep(attempt * 2)
    raise RuntimeError(f"Failed to download {item.url}: {last_error}") from last_error


def extract_libhangul_license() -> Path:
    """Copy the BSD-3-Clause header that governs hanja.txt into its own file."""
    source = RAW / "libhangul" / "hanja.txt"
    destination = RAW / "libhangul" / "LICENSE-hanja.txt"
    header: list[str] = []
    with source.open("r", encoding="utf-8", errors="strict") as handle:
        for line in handle:
            if not line.startswith("#"):
                break
            header.append(line[1:].lstrip())
    text = "".join(header).strip() + "\n"
    if "Redistribution and use" not in text or "Choe Hwanjin" not in text:
        raise RuntimeError("libhangul hanja.txt no longer has the expected BSD license header")
    destination.write_text(text, encoding="utf-8", newline="\n")
    shutil.copy2(destination, LICENSES / "LIBHANGUL-HANJA-BSD-3-CLAUSE.txt")
    return destination


def sync_licenses() -> None:
    LICENSES.mkdir(parents=True, exist_ok=True)
    for item in DOWNLOADS:
        if item.license_copy:
            shutil.copy2(item.path, LICENSES / item.license_copy)
    extract_libhangul_license()


def write_manifest(items: list[Download], old: dict[str, dict[str, str]], refresh: bool) -> None:
    today = date.today().isoformat()
    rows: list[dict[str, str | int]] = []
    for item in items:
        rel = item.path.relative_to(ROOT).as_posix()
        prior = old.get(rel)
        rows.append(
            {
                "source": item.source,
                "url": item.url,
                "date": today if refresh or prior is None else prior["date"],
                "sha256": sha256(item.path),
                "bytes": item.path.stat().st_size,
                "path": rel,
                "role": item.role,
            }
        )
    # The derived per-file licence is also part of the reproducible raw inventory.
    derived = RAW / "libhangul" / "LICENSE-hanja.txt"
    derived_rel = derived.relative_to(ROOT).as_posix()
    derived_prior = old.get(derived_rel)
    rows.append(
        {
            "source": "libhangul",
            "url": "derived-from:raw/libhangul/hanja.txt#comment-header",
            "date": today if refresh or derived_prior is None else derived_prior["date"],
            "sha256": sha256(derived),
            "bytes": derived.stat().st_size,
            "path": derived_rel,
            "role": "license",
        }
    )
    for manifest_path in (MANIFEST, LOCKFILE):
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with manifest_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="download every URL again and replace recorded checksums after review",
    )
    args = parser.parse_args()
    old = load_manifest()

    for item in DOWNLOADS:
        rel = item.path.relative_to(ROOT).as_posix()
        prior = old.get(rel)
        expected = None if args.refresh or prior is None else prior["sha256"]
        if item.path.exists() and not args.refresh:
            actual = sha256(item.path)
            if expected is None or actual == expected:
                print(f"ok       {rel}")
                continue
            raise RuntimeError(
                f"Local checksum mismatch for {rel}: expected {expected}, found {actual}"
            )
        print(f"download {item.url}")
        fetch(item, expected)

    sync_licenses()
    write_manifest(DOWNLOADS, old, args.refresh)
    print(
        f"wrote    {MANIFEST.relative_to(ROOT).as_posix()} and "
        f"{LOCKFILE.relative_to(ROOT).as_posix()}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, urllib.error.URLError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
