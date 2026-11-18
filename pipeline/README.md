# pipeline/

Rebuilds every Kanji Bridge table and the app from the licensed sources with one command. No step sends a network request except `download.py`, and nothing here calls an AI model: the accepted Gemini content is an input under `content/accepted/` (Stage 4 generation lives in `pipeline/stage4/` and is never imported by `run_all.py`).

## Quick start

```
pip install -r pipeline/requirements.txt      # pandas (Python 3.12)
python pipeline/download.py                   # recreate raw/ (≈ 300 MB) and verify checksums
python pipeline/run_all.py                    # full rebuild, ≈ 4.5 min on a quiet PC
```

On Windows use `python -X utf8 …` if the console is not UTF-8. `raw/` is git-ignored; `download.py` recreates it from the URLs and SHA-256 hashes in `pipeline/source_manifest.csv` (a lock: matching files are not downloaded again, a changed upstream file stops the run).

## Inputs and outputs

| Kind | Path | Notes |
|---|---|---|
| Sources (read-only) | `raw/<source>/` | recreated by `download.py`; licences copied to `licenses/` |
| Accepted AI content | `content/accepted/task1`–`task6` | Gemini output reviewed at the Stage 4 gates |
| Review overlays and settings | `config/*.csv`, `config/*.json` | every overlay row is applied exactly once or the build stops (fail-closed) |
| Stable IDs | `pipeline/id_map.csv` | `c00001`, `w00001`, `p0001`; assigned once, reused by every rebuild |
| One-off corrections | `pipeline/overrides.csv` | each row has a reason |
| Rebuilt (deleted and recreated) | `data/staging/`, `data/final/` | tables as CSV + JSON (UTF-8, NFC) and review reports |
| App | `data/final/data.js` → `app/data.js`, `app/index.html` | `app/` runs alone from disk (`file://`) or a web server |

## Run order (`run_all.py`)

1. `download.py`: verify (or fetch) every source against the lock. Skipped with `--skip-download`.
2. Clean `data/staging/` and `data/final/` (nothing else is deleted).
3. Loaders, one per source → `data/staging/`:
   `load_unihan.py` (Unihan readings and variants), `load_kanjidic2.py` (Japanese on-readings), `load_hsk30.py` (HSK 3.0 words and characters), `load_opencc.py` (Japanese ↔ traditional forms), `load_libhangul.py` (Korean hanja readings and words), `load_kaikki.py` (Vietnamese Wiktionary Hán-Việt evidence; skips the records in `config/kaikki_exclusions.csv`), `load_kaikki_en.py` (English Wiktionary Vietnamese evidence), `load_frequencywords.py` (Vietnamese token counts), `load_cedict.py` (CC-CEDICT), `load_jmdict.py` (JMdict).
4. `build_chars.py`: the HSK character table and its reports.
5. `build_words.py`: words (HSK backbone + Vietnamese-only additions), aligned `word_chars`, characters extended to every word, `overrides.csv`, sound-rule reports, `ff_candidates.csv`, coverage. Uses `stage3_match.py` and `common.py`.
6. `merge_stage4.py`: accepted content (tasks 1–5) and its review overlays → meanings, false friends, passages, usage flags.
7. `merge_task6.py`: accepted task-6 example sentences and character notes.
8. `export_app_data.py`: the reduced offline payload `data/final/data.js` (copied byte-identically to `app/data.js`).
9. `build_app.py`: `app/index.html` from the frozen `prototype/index.html` (never edited) plus the data adapters and the approved app changes.

Typical times (2026-11-12, quiet PC): whole run ≈ 273 s, of which `build_words` 126 s, `merge_stage4` 47 s, `merge_task6` 46 s. Rebuilding twice gives byte-identical output (`tests/test_rebuild.py`).

Other scripts: `profile_sources.py` writes `docs/SOURCE_PROFILES.md`; `extract_prototype_config.py` extracts the frozen prototype content used as config; `refresh_check.py` (below); `stage4_generate.py` + `stage4/` are the Stage 4 Vertex AI runner (needs `requirements-stage4.txt` and credentials; it refuses tasks 1–6, which are accepted).

## Options

| Command | What it does |
|---|---|
| `python pipeline/run_all.py --skip-download` | rebuild without verifying `raw/` (used by the determinism tests) |
| `python pipeline/run_all.py --skip-stage4-merge` | stop after the Stage 3 tables (used by one test) |
| `python pipeline/download.py --refresh` | download every source again and record the new checksums and dates (only after reviewing upstream changes) |
| `python pipeline/download.py --refresh --only kanjidic2,jmdict` | refresh only the named sources; the others are verified against the lock and keep their dates |
| `python pipeline/refresh_check.py` | after a refresh and rebuild: fails if any `word_id` was added, removed or re-keyed; writes the Japanese changes to `data/refresh_report.csv` |

## EDRDG update (every 3 months, RELEASE_PLAN §6.3)

The EDRDG licence asks users of KANJIDIC2 and JMdict to update from the latest files regularly:

```
python pipeline/download.py --refresh --only kanjidic2,jmdict
python pipeline/run_all.py --skip-download
python pipeline/refresh_check.py          # compares with the committed tables (git HEAD)
python -m unittest discover -s tests -p "test_*.py"
```

`refresh_check.py` must pass (the word list is frozen, D46): no `word_id` changes. Claude checks every row of `data/refresh_report.csv` (words whose Japanese form or reading changed, characters whose Japanese form or on-readings changed). The CHANGELOG records the EDRDG file dates from `pipeline/source_manifest.csv`.

## Tests and browser checks

```
python -m unittest discover -s tests -p "test_*.py"     # non-rebuild suite (test_rebuild.py rebuilds 3 times, ≈ 14 min)
python docs/review_scripts/stage5_gate_run.py            # gate harness, file:// and http://127.0.0.1
python tests/app_benchmark.py [--mode file|http]         # real-app timings, median of 3 runs
python tests/app_screenshots.py                          # docs/screenshots/*.png and demo.gif
```

The browser checks need Chrome or Edge and `pip install -r tests/requirements-browser.txt`:
`websockets` (DevTools protocol; already installed with `requirements-stage4.txt`) and **Pillow** (added in R1, 2026-11-14, for the screenshots and the demo GIF only). They copy `app/` to a temporary folder, block every network host and never change `app/`. `tests/test_app_render_equality.py` is skipped when no browser is installed.
