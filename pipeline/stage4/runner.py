"""Vertex AI runner for reproducible Stage 4 content generation."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.stage4 import builders
from pipeline.stage4.validators import RESPONSE_SCHEMAS, ValidationError, validate


ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content"
PROMPTS = CONTENT / "prompts"
INPUTS = CONTENT / "inputs"
GENERATED = CONTENT / "generated"
COST_LOG = CONTENT / "cost_log.csv"
PRICE_PATH = Path(__file__).with_name("prices.json")
MODEL_ID = "gemini-4-argon"
TEMPERATURE = 0.3
THINKING = "model_default"
MAX_OUTPUT_TOKENS = 65536
MAX_RETRIES = 2
REQUEST_TIMEOUT_SECONDS = 600
REQUEST_TIMEOUT_MS = REQUEST_TIMEOUT_SECONDS * 1000
ARGON_DEADLINE_UTC = "2026-12-01"
PROMPT_FILES = {
    1: PROMPTS / "task1_v2.md",
    2: PROMPTS / "task2_v2.md",
    3: PROMPTS / "task3_v2.md",
    4: PROMPTS / "task4_v1.md",
}
COST_FIELDS = [
    "timestamp", "task", "batch", "attempt", "model", "input_tokens",
    "output_tokens", "thinking_tokens", "total_token_count", "unreported_tokens",
    "duration_seconds", "usd",
]
FALLBACK_CHARGEABLE_OUTPUT_PER_ITEM = {1: 140, 2: 120, 3: 1600, 4: 100}


class Stage4Error(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def guard_api_keys(environ: dict[str, str] | None = None) -> None:
    environ = os.environ if environ is None else environ
    forbidden = [name for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY") if environ.get(name)]
    if forbidden:
        raise Stage4Error(
            "Refusing to run: " + ", ".join(forbidden)
            + " is set. Stage 4 must use Vertex AI with Application Default Credentials only."
        )


def vertex_settings(environ: dict[str, str] | None = None) -> tuple[str, str]:
    environ = os.environ if environ is None else environ
    project = environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    location = environ.get("GOOGLE_CLOUD_LOCATION", "").strip()
    if not project:
        raise Stage4Error("GOOGLE_CLOUD_PROJECT is not set")
    if not location:
        raise Stage4Error("GOOGLE_CLOUD_LOCATION is not set")
    return project, location


def create_client() -> Any:
    guard_api_keys()
    project, location = vertex_settings()
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise Stage4Error(
            "google-genai is not installed; run the Python 3.12 interpreter with "
            "-m pip install -r pipeline/requirements-stage4.txt"
        ) from exc
    return genai.Client(
        vertexai=True, project=project, location=location,
        http_options=types.HttpOptions(
            timeout=REQUEST_TIMEOUT_MS,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )


def load_prices() -> dict[str, Any]:
    return json.loads(PRICE_PATH.read_text(encoding="utf-8"))


def model_prices(model_id: str, at: datetime | None = None) -> dict[str, float]:
    prices = load_prices()
    day = (at or datetime.now(timezone.utc)).date().isoformat()
    for period in prices["models"][model_id]:
        if day <= period["through"]:
            return period
    raise Stage4Error(f"No active price configured for {model_id} on {day}")


def enforce_argon_deadline(
    model_id: str = MODEL_ID,
    allow_after_deadline: bool = False,
    now: datetime | None = None,
) -> None:
    day = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).date().isoformat()
    if model_id == "gemini-4-argon" and day >= ARGON_DEADLINE_UTC and not allow_after_deadline:
        raise Stage4Error(
            f"Argon deadline guard: UTC date {day} is on or after {ARGON_DEADLINE_UTC}; "
            "pass --allow-after-deadline only with the user's explicit approval"
        )


def calculate_cost(
    input_tokens: int, output_tokens: int, thinking_tokens: int,
    model_id: str = MODEL_ID, at: datetime | None = None,
    total_token_count: int | None = None,
    unreported_tokens: int | None = None,
) -> float:
    prices = model_prices(model_id, at)
    if unreported_tokens is None:
        unreported_tokens = max(
            int(total_token_count or 0) - input_tokens - output_tokens - thinking_tokens,
            0,
        )
    return (
        input_tokens * float(prices["input_per_million"])
        + (output_tokens + unreported_tokens) * float(prices["output_per_million"])
        + thinking_tokens * float(prices["thinking_per_million"])
    ) / 1_000_000


def existing_cost() -> float:
    if not COST_LOG.exists():
        return 0.0
    with COST_LOG.open(encoding="utf-8", newline="") as source:
        return sum(float(row["usd"]) for row in csv.DictReader(source) if row.get("usd"))


def append_cost(row: dict[str, Any]) -> None:
    COST_LOG.parent.mkdir(parents=True, exist_ok=True)
    exists = COST_LOG.exists()
    if exists:
        with COST_LOG.open(encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            old_fields = reader.fieldnames or []
            old_rows = list(reader)
        if old_fields != COST_FIELDS:
            with COST_LOG.open("w", encoding="utf-8", newline="") as target:
                writer = csv.DictWriter(target, fieldnames=COST_FIELDS, lineterminator="\n")
                writer.writeheader()
                writer.writerows(
                    {field: old_row.get(field, "") for field in COST_FIELDS}
                    for old_row in old_rows
                )
    with COST_LOG.open("a", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=COST_FIELDS, lineterminator="\n")
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in COST_FIELDS})


def prompt_text(task: int) -> str:
    return unicodedata.normalize("NFC", PROMPT_FILES[task].read_text(encoding="utf-8").strip())


def request_text(task: int, items: list[dict[str, Any]]) -> str:
    return prompt_text(task) + "\n\nINPUT JSONL:\n" + builders.jsonl_text(items)


def count_tokens(client: Any, contents: str, model_id: str = MODEL_ID) -> int:
    response = client.models.count_tokens(model=model_id, contents=contents)
    value = getattr(response, "total_tokens", None)
    if value is None:
        value = getattr(response, "total_token_count", None)
    if value is None:
        raise Stage4Error("count_tokens returned no total token count")
    return int(value)


def _successful_logs(task: int, model_id: str = MODEL_ID) -> list[dict[str, Any]]:
    logs: list[dict[str, Any]] = []
    for path in GENERATED.rglob("*.log.json") if GENERATED.exists() else []:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (value.get("task") == task and value.get("model") == model_id
                and value.get("validation", {}).get("ok") is True):
            logs.append(value)
    return logs


def estimated_chargeable_output(task: int, item_count: int, model_id: str = MODEL_ID) -> int:
    totals = []
    for log in _successful_logs(task, model_id):
        usage = log.get("usage", {})
        count = int(log.get("item_count", 0) or 0)
        if count:
            totals.append((
                int(usage.get("output_tokens", 0))
                + int(usage.get("thinking_tokens", 0))
                + int(usage.get("unreported_tokens", 0))
            ) / count)
    average = sum(totals) / len(totals) if totals else FALLBACK_CHARGEABLE_OUTPUT_PER_ITEM[task]
    return int(average * item_count + 0.999)


def enforce_ceiling(input_tokens: int, task: int, item_count: int, model_id: str = MODEL_ID) -> None:
    prices = load_prices()
    projected = existing_cost() + calculate_cost(
        input_tokens, estimated_chargeable_output(task, item_count, model_id), 0, model_id
    )
    ceiling = float(prices["hard_ceiling"])
    if projected > ceiling:
        raise Stage4Error(
            f"Hard cost ceiling: spent plus estimated request is ${projected:.6f}, above ${ceiling:.2f}"
        )


def generation_config(task: int) -> Any:
    from google.genai import types

    return types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=RESPONSE_SCHEMAS[task],
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        http_options=types.HttpOptions(
            timeout=REQUEST_TIMEOUT_MS,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )


def usage_from_response(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return {
            "input_tokens": 0, "output_tokens": 0, "thinking_tokens": 0,
            "total_token_count": 0, "unreported_tokens": 0,
        }
    input_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
    output_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
    thinking_tokens = int(getattr(usage, "thoughts_token_count", 0) or 0)
    total_token_count = int(getattr(usage, "total_token_count", 0) or 0)
    unreported_tokens = max(
        total_token_count - input_tokens - output_tokens - thinking_tokens,
        0,
    )
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "thinking_tokens": thinking_tokens,
        "total_token_count": total_token_count,
        "unreported_tokens": unreported_tokens,
    }


def finish_reason_from_response(response: Any) -> str:
    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        return "no_candidates"
    reason = getattr(candidates[0], "finish_reason", None)
    if reason is None:
        return "unknown"
    return str(getattr(reason, "value", reason))


def response_text_or_error(response: Any, usage: dict[str, int]) -> str:
    text = getattr(response, "text", None)
    if text:
        return text
    raise Stage4Error(
        "Vertex returned an empty response: "
        f"finish_reason={finish_reason_from_response(response)}, "
        f"input_tokens={usage['input_tokens']}, output_tokens={usage['output_tokens']}, "
        f"thinking_tokens={usage['thinking_tokens']}"
    )


def is_rate_limit(exc: BaseException) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    return code == 429 or "429" in text or "resource_exhausted" in text or "resource exhausted" in text


def is_fatal_vertex_access_error(exc: BaseException) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    code_text = str(getattr(code, "value", code)).lower()
    if code in {401, 403, 404} or code_text in {"401", "403", "404"}:
        return True
    markers = (
        "unauthenticated", "permission_denied", "permission denied",
        "billing", "account disabled", "model not found", "model is not found",
        "publisher model", "does not have access to model", "not authorized to use model",
    )
    if any(marker in text for marker in markers):
        return True
    return (code == 400 or code_text == "400" or "invalid_argument" in text) and "model" in text


def write_output(path: Path, task: int, output: Any) -> None:
    if task == 3:
        values = [output]
    else:
        values = output
    builders.write_jsonl(path, values)


def write_log(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )


def generate_batch(
    client: Any,
    task: int,
    batch_name: str,
    items: list[dict[str, Any]],
    output_path: Path,
    log_path: Path,
    model_id: str = MODEL_ID,
    allow_after_deadline: bool = False,
) -> dict[str, Any] | list[dict[str, Any]] | None:
    batch_started = time.perf_counter()
    enforce_argon_deadline(model_id, allow_after_deadline)
    _, location = vertex_settings()
    contents = request_text(task, items)
    input_text = builders.jsonl_text(items)
    prompt = prompt_text(task)
    counted_input = count_tokens(client, contents, model_id)
    enforce_ceiling(counted_input, task, len(items), model_id)
    attempts: list[dict[str, Any]] = []
    retry = 0
    rate_wait = 2
    while retry <= MAX_RETRIES:
        attempt_number = len(attempts) + 1
        timestamp = utc_now()
        attempt_started = time.perf_counter()
        try:
            enforce_argon_deadline(model_id, allow_after_deadline)
            response = client.models.generate_content(
                model=model_id, contents=contents, config=generation_config(task)
            )
            duration_seconds = time.perf_counter() - attempt_started
            usage = usage_from_response(response)
            usd = calculate_cost(**usage, model_id=model_id)
            append_cost({
                "timestamp": timestamp, "task": task, "batch": batch_name,
                "attempt": attempt_number, "model": model_id, **usage,
                "duration_seconds": f"{duration_seconds:.3f}", "usd": f"{usd:.8f}",
            })
            try:
                output = json.loads(response_text_or_error(response, usage))
                validate(task, output, items)
            except (json.JSONDecodeError, ValidationError, Stage4Error, TypeError, ValueError) as validation_exc:
                attempts.append({
                    "attempt": attempt_number, "timestamp": timestamp, "usage": usage,
                    "usd": usd, "duration_seconds": duration_seconds, "validation_ok": False,
                    "error": f"{type(validation_exc).__name__}: {validation_exc}",
                })
                retry += 1
                if retry <= MAX_RETRIES:
                    continue
                break
            attempts.append({
                "attempt": attempt_number, "timestamp": timestamp, "usage": usage,
                "usd": usd, "duration_seconds": duration_seconds, "validation_ok": True,
            })
            write_output(output_path, task, output)
            log = {
                "timestamp": timestamp, "task": task, "batch": batch_name,
                "model": model_id, "location": location,
                "settings": {
                    "temperature": TEMPERATURE, "thinking": THINKING,
                    "max_output_tokens": MAX_OUTPUT_TOKENS,
                    "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
                },
                "prompt_sha256": builders.sha256_text(prompt),
                "input_sha256": builders.sha256_text(input_text),
                "item_count": len(items), "counted_input_tokens": counted_input,
                "usage": usage, "usd": usd, "attempts": attempts,
                "wall_clock_seconds": time.perf_counter() - batch_started,
                "validation": {"ok": True, "error": ""},
            }
            write_log(log_path, log)
            print(
                f"task={task} batch={batch_name} ok input={usage['input_tokens']} "
                f"output={usage['output_tokens']} thinking={usage['thinking_tokens']} "
                f"total={usage['total_token_count']} unreported={usage['unreported_tokens']} "
                f"seconds={duration_seconds:.3f} usd=${usd:.6f}"
            )
            return output
        except Exception as exc:  # SDK exceptions vary by transport/version.
            duration_seconds = time.perf_counter() - attempt_started
            if is_fatal_vertex_access_error(exc):
                raise
            if is_rate_limit(exc):
                print(f"task={task} batch={batch_name} rate limited; waiting {rate_wait}s", file=sys.stderr)
                time.sleep(rate_wait)
                rate_wait = min(rate_wait * 2, 60)
                continue
            append_cost({
                "timestamp": timestamp, "task": task, "batch": batch_name,
                "attempt": attempt_number, "model": model_id, "input_tokens": 0,
                "output_tokens": 0, "thinking_tokens": 0, "total_token_count": 0,
                "unreported_tokens": 0, "duration_seconds": f"{duration_seconds:.3f}",
                "usd": "0.00000000",
            })
            attempts.append({
                "attempt": attempt_number, "timestamp": timestamp, "usage": {}, "usd": 0,
                "duration_seconds": duration_seconds, "validation_ok": False,
                "error": f"{type(exc).__name__}: {exc}",
            })
            retry += 1
            if retry <= MAX_RETRIES:
                continue
            break
    error = attempts[-1]["error"] if attempts else "unknown failure"
    log = {
        "timestamp": utc_now(), "task": task, "batch": batch_name,
        "model": model_id, "location": location,
        "settings": {
            "temperature": TEMPERATURE, "thinking": THINKING,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        },
        "prompt_sha256": builders.sha256_text(prompt),
        "input_sha256": builders.sha256_text(input_text),
        "item_count": len(items), "counted_input_tokens": counted_input,
        "usage": {
            "input_tokens": 0, "output_tokens": 0, "thinking_tokens": 0,
            "total_token_count": 0, "unreported_tokens": 0,
        },
        "usd": sum(float(item.get("usd", 0)) for item in attempts), "attempts": attempts,
        "wall_clock_seconds": time.perf_counter() - batch_started,
        "validation": {"ok": False, "error": error},
    }
    write_log(log_path, log)
    print(f"task={task} batch={batch_name} failed after {MAX_RETRIES + 1} attempts: {error}", file=sys.stderr)
    return None


def run_check(client: Any, allow_after_deadline: bool = False) -> None:
    from google.genai import types

    enforce_argon_deadline(MODEL_ID, allow_after_deadline)
    _, location = vertex_settings()
    contents = 'Return exactly this JSON object: {"ok":true}'
    counted = count_tokens(client, contents)
    schema = {
        "type": "object", "properties": {"ok": {"type": "boolean"}},
        "required": ["ok"], "additionalProperties": False,
    }
    enforce_ceiling(counted, 4, 1)
    timestamp = utc_now()
    request_started = time.perf_counter()
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json", response_schema=schema,
                temperature=TEMPERATURE, max_output_tokens=1024,
                http_options=types.HttpOptions(
                    timeout=REQUEST_TIMEOUT_MS,
                    retry_options=types.HttpRetryOptions(attempts=1),
                ),
            ),
        )
    except Exception:
        duration_seconds = time.perf_counter() - request_started
        append_cost({
            "timestamp": timestamp, "task": "check", "batch": "check", "attempt": 1,
            "model": MODEL_ID, "input_tokens": 0, "output_tokens": 0,
            "thinking_tokens": 0, "total_token_count": 0, "unreported_tokens": 0,
            "duration_seconds": f"{duration_seconds:.3f}", "usd": "0.00000000",
        })
        raise
    duration_seconds = time.perf_counter() - request_started
    usage = usage_from_response(response)
    usd = calculate_cost(**usage, model_id=MODEL_ID)
    append_cost({
        "timestamp": timestamp, "task": "check", "batch": "check", "attempt": 1,
        "model": MODEL_ID, **usage, "duration_seconds": f"{duration_seconds:.3f}",
        "usd": f"{usd:.8f}",
    })
    text = response_text_or_error(response, usage)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise Stage4Error(
            "Check returned invalid JSON: "
            f"finish_reason={finish_reason_from_response(response)}, "
            f"input_tokens={usage['input_tokens']}, output_tokens={usage['output_tokens']}, "
            f"thinking_tokens={usage['thinking_tokens']}; {exc}"
        ) from exc
    if value != {"ok": True}:
        raise Stage4Error(
            f"Check returned unexpected response: {value!r}; "
            f"finish_reason={finish_reason_from_response(response)}, "
            f"input_tokens={usage['input_tokens']}, output_tokens={usage['output_tokens']}, "
            f"thinking_tokens={usage['thinking_tokens']}"
        )
    print(f"model={MODEL_ID}")
    print(f"location={location}")
    print(f"token_count={usage['total_token_count']}")
    print(f"duration_seconds={duration_seconds:.3f}")


def read_generated_output(path: Path, task: int) -> Any:
    values = builders.read_jsonl_files([path])
    if task == 3:
        if len(values) != 1:
            raise ValueError(f"{path}: task 3 output must contain one JSON object")
        return values[0]
    return values


def validated_batch_exists(
    task: int,
    batch_name: str,
    items: list[dict[str, Any]],
    output_path: Path,
    log_path: Path,
    model_id: str = MODEL_ID,
) -> bool:
    if not output_path.is_file() or not log_path.is_file():
        return False
    try:
        log = json.loads(log_path.read_text(encoding="utf-8"))
        if not isinstance(log, dict) or log.get("validation", {}).get("ok") is not True:
            return False
        expected = {
            "task": task,
            "batch": batch_name,
            "model": model_id,
            "prompt_sha256": builders.sha256_text(prompt_text(task)),
            "input_sha256": builders.sha256_text(builders.jsonl_text(items)),
            "item_count": len(items),
        }
        if any(log.get(key) != value for key, value in expected.items()):
            return False
        output = read_generated_output(output_path, task)
        validate(task, output, items)
    except (OSError, json.JSONDecodeError, TypeError, ValueError, ValidationError):
        return False
    return True


def task1_outputs_from_generated() -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for number, items in enumerate(builders.build_task1_batches(), 1):
        name = f"b{number:03d}"
        output_path = GENERATED / "task1" / f"{name}.jsonl"
        log_path = GENERATED / "task1" / f"{name}.log.json"
        if validated_batch_exists(1, name, items, output_path, log_path):
            outputs.extend(read_generated_output(output_path, 1))
    if not outputs:
        raise Stage4Error("Validated task 1 generated output is required before task 2, 3 or 4")
    expected = {item["word_id"] for item in builders.build_task1_items()}
    actual = [str(item.get("word_id", "")) for item in outputs]
    missing = expected - set(actual)
    duplicates = len(actual) - len(set(actual))
    unexpected = set(actual) - expected
    if missing or duplicates or unexpected:
        raise Stage4Error(
            "Task 1 must be complete before task 2, 3 or 4: "
            f"expected={len(expected)}, loaded={len(actual)}, missing={len(missing)}, "
            f"duplicates={duplicates}, unexpected={len(unexpected)}"
        )
    return outputs


def run_task(
    client: Any,
    task: int,
    batch_number: int | None,
    dry_run: bool,
    allow_after_deadline: bool = False,
) -> int:
    outputs = task1_outputs_from_generated() if task in {2, 3, 4} else None
    batches = builders.task_batches(task, outputs)
    numbered = list(enumerate(batches, 1))
    if batch_number is not None:
        if batch_number < 1 or batch_number > len(batches):
            raise Stage4Error(f"Task {task} batch must be 1..{len(batches)}")
        numbered = [(batch_number, batches[batch_number - 1])]
    total_counted = 0
    failed = 0
    for number, items in numbered:
        name = f"b{number:03d}"
        input_path = INPUTS / f"task{task}" / f"{name}.jsonl"
        builders.write_jsonl(input_path, items)
        contents = request_text(task, items)
        if dry_run:
            counted = count_tokens(client, contents)
            total_counted += counted
            print(f"task={task} batch={name} input_tokens={counted}")
            continue
        output_path = GENERATED / f"task{task}" / f"{name}.jsonl"
        log_path = GENERATED / f"task{task}" / f"{name}.log.json"
        if batch_number is None and validated_batch_exists(
            task, name, items, output_path, log_path,
        ):
            print(f"task={task} batch={name} skipped=validated")
            continue
        result = generate_batch(
            client, task, name, items,
            output_path, log_path,
            allow_after_deadline=allow_after_deadline,
        )
        failed += result is None
    if dry_run:
        print(f"task={task} batches={len(numbered)} total_input_tokens={total_counted}")
    return failed


def run_pilot(client: Any, allow_after_deadline: bool = False) -> int:
    pilot_dir = GENERATED / "pilot_v2"
    pilot_inputs = INPUTS / "pilot_v2"
    failures = 0
    task1_input = builders.build_pilot_task1()
    task1_sha = builders.write_jsonl(pilot_inputs / "task1.jsonl", task1_input)
    first_pilot_input = INPUTS / "pilot" / "task1.jsonl"
    if first_pilot_input.is_file():
        first_sha = builders.sha256_text(first_pilot_input.read_text(encoding="utf-8"))
        if task1_sha != first_sha:
            raise Stage4Error(
                f"Pilot v2 task-1 input SHA differs from the first pilot: {task1_sha} != {first_sha}"
            )
    task1_output = generate_batch(
        client, 1, "pilot-v2-task1", task1_input,
        pilot_dir / "task1.jsonl", pilot_dir / "task1.log.json",
        allow_after_deadline=allow_after_deadline,
    )
    if task1_output is None:
        return 1
    task2_input = builders.build_pilot_task2(task1_output)
    builders.write_jsonl(pilot_inputs / "task2.jsonl", task2_input)
    failures += generate_batch(
        client, 2, "pilot-v2-task2", task2_input,
        pilot_dir / "task2.jsonl", pilot_dir / "task2.log.json",
        allow_after_deadline=allow_after_deadline,
    ) is None
    for lang, level in (("zh", 1), ("vi", 3)):
        items = builders.build_pilot_task3(lang, level, task1_output)
        label = f"task3-{lang}-l{level}"
        builders.write_jsonl(pilot_inputs / f"{label}.jsonl", items)
        failures += generate_batch(
            client, 3, f"pilot-v2-{label}", items,
            pilot_dir / f"{label}.jsonl", pilot_dir / f"{label}.log.json",
            allow_after_deadline=allow_after_deadline,
        ) is None
    task4_input = builders.build_pilot_task4()
    builders.write_jsonl(pilot_inputs / "task4.jsonl", task4_input)
    failures += generate_batch(
        client, 4, "pilot-v2-task4", task4_input,
        pilot_dir / "task4.jsonl", pilot_dir / "task4.log.json",
        allow_after_deadline=allow_after_deadline,
    ) is None
    return failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="make one tiny Vertex request")
    mode.add_argument("--pilot", action="store_true", help="run the five Stage 4b Argon re-pilot requests")
    mode.add_argument("--task", type=int, choices=range(1, 5), help="run one full task")
    parser.add_argument("--batch", type=int, help="run/rerun one 1-based batch")
    parser.add_argument("--dry-run", action="store_true", help="count inputs without generation")
    parser.add_argument(
        "--allow-after-deadline", action="store_true",
        help="explicitly allow Argon requests on/after 2026-12-01 UTC",
    )
    args = parser.parse_args(argv)
    if args.batch is not None and args.task is None:
        parser.error("--batch requires --task")
    if args.dry_run and args.task is None:
        parser.error("--dry-run requires --task")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        client = create_client()
        if args.check:
            run_check(client, args.allow_after_deadline)
            return 0
        if args.pilot:
            return 1 if run_pilot(client, args.allow_after_deadline) else 0
        return 1 if run_task(
            client, args.task, args.batch, args.dry_run, args.allow_after_deadline
        ) else 0
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
