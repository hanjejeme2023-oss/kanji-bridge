"""Vertex AI runner for reproducible Stage 4 content generation."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.stage4 import builders
from pipeline.stage4.validators import (
    RESPONSE_SCHEMAS, ValidationError, validate, validate_task6_items,
)


ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content"
PROMPTS = CONTENT / "prompts"
INPUTS = CONTENT / "inputs"
GENERATED = CONTENT / "generated"
ACCEPTED = CONTENT / "accepted"
COST_LOG = CONTENT / "cost_log.csv"
LOCK_PATH = CONTENT / ".stage4.lock"
PRICE_PATH = Path(__file__).with_name("prices.json")
MODEL_ID = "gemini-4-argon"
TEMPERATURE = 0.3
THINKING = "model_default"
MAX_OUTPUT_TOKENS = 65536
MAX_RETRIES = 2
API_ERROR_RETRY_WAITS = (30, 60)
REQUEST_TIMEOUT_SECONDS = 600
REQUEST_TIMEOUT_MS = REQUEST_TIMEOUT_SECONDS * 1000
ARGON_DEADLINE_UTC = "2026-12-01"
CREDIT_DEADLINE_UTC = datetime(2026, 11, 16, 8, 0, 0, tzinfo=timezone.utc)
PROMPT_FILES = {
    1: PROMPTS / "task1_v2.md",
    2: PROMPTS / "task2_v2.md",
    4: PROMPTS / "task4_v1.md",
    5: PROMPTS / "task5_v1.md",
}
TASK6_PROMPT_FILES = {
    "zh": PROMPTS / "task6_zh_v1.md",
    "vi": PROMPTS / "task6_vi_v1.md",
    "note": PROMPTS / "task6_note_v1.md",
}
TASK3_PROMPT_FILES = {
    "zh": PROMPTS / "task3_v2.md",
    "vi": PROMPTS / "task3_v3.md",
}
COST_FIELDS = [
    "timestamp", "task", "batch", "attempt", "model", "input_tokens",
    "output_tokens", "thinking_tokens", "total_token_count", "unreported_tokens",
    "duration_seconds", "usd",
]
FALLBACK_CHARGEABLE_OUTPUT_PER_ITEM = {1: 140, 2: 120, 3: 1600, 4: 100, 5: 120, 6: 200}
DRY_RUN_OUTPUT_PER_ITEM = {"zh": 150, "vi": 120, "note": 80}
TASK5_ESTIMATED_INPUT_TOKENS = 1_650_000
ACCEPTED_BATCH_COUNTS = {1: 86, 2: 79, 3: 14, 4: 5, 5: 104}


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


def enforce_credit_deadline(
    allow_after_credit_deadline: bool = False,
    now: datetime | None = None,
) -> None:
    instant = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if instant >= CREDIT_DEADLINE_UTC and not allow_after_credit_deadline:
        raise Stage4Error(
            "Vertex Free Trial credit deadline 2026-11-16T08:00:00Z has passed; "
            "after upgrading, pass --allow-after-credit-deadline"
        )


def create_client(allow_after_credit_deadline: bool = False) -> Any:
    enforce_credit_deadline(allow_after_credit_deadline)
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


def process_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        process_query_limited_information = 0x1000
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.OpenProcess(
            process_query_limited_information, False, pid
        )
        if not handle:
            return False
        kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@contextmanager
def stage4_lock(path: Path = LOCK_PATH):
    """Own the Stage 4 generator lock, replacing only a stale process lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pid = os.getpid()
    while True:
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError:
            try:
                owner = int(path.read_text(encoding="ascii").strip())
            except (OSError, ValueError):
                owner = -1
            if process_is_running(owner):
                raise Stage4Error(
                    f"Stage 4 is already running with PID {owner}; lock: {path}"
                )
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            continue
        with os.fdopen(descriptor, "w", encoding="ascii", newline="\n") as target:
            target.write(f"{pid}\n")
        break
    try:
        yield
    finally:
        try:
            owner = int(path.read_text(encoding="ascii").strip())
        except (FileNotFoundError, OSError, ValueError):
            owner = None
        if owner == pid:
            try:
                path.unlink()
            except FileNotFoundError:
                pass


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


def task6_kind(items: list[dict[str, Any]]) -> str:
    kinds = set()
    for item in items:
        key = str(item.get("key", ""))
        if key.endswith(":note"):
            kinds.add("note")
        else:
            parts = key.split(":")
            if len(parts) >= 3 and parts[-2] in {"zh", "vi"}:
                kinds.add(parts[-2])
    if len(kinds) != 1:
        raise Stage4Error("Task 6 prompt requires exactly one zh, vi or note kind")
    return next(iter(kinds))


def prompt_path(task: int, items: list[dict[str, Any]] | None = None) -> Path:
    if task == 6:
        return TASK6_PROMPT_FILES[task6_kind(items or [])]
    if task != 3:
        return PROMPT_FILES[task]
    languages = {
        str(item.get("language", "")).strip()
        for item in (items or [])
    }
    if len(languages) != 1 or next(iter(languages), "") not in TASK3_PROMPT_FILES:
        raise Stage4Error("Task 3 prompt requires exactly one zh or vi cell")
    return TASK3_PROMPT_FILES[next(iter(languages))]


def prompt_text(task: int, items: list[dict[str, Any]] | None = None) -> str:
    path = prompt_path(task, items)
    return unicodedata.normalize("NFC", path.read_text(encoding="utf-8").strip())


def request_text(task: int, items: list[dict[str, Any]]) -> str:
    input_text = builders.ordered_jsonl_text(items) if task == 6 else builders.jsonl_text(items)
    return prompt_text(task, items) + "\n\nINPUT JSONL:\n" + input_text


def count_tokens(client: Any, contents: str, model_id: str = MODEL_ID) -> int:
    response = client.models.count_tokens(model=model_id, contents=contents)
    value = getattr(response, "total_tokens", None)
    if value is None:
        value = getattr(response, "total_token_count", None)
    if value is None:
        raise Stage4Error("count_tokens returned no total token count")
    return int(value)


def _successful_logs(
    task: int,
    model_id: str = MODEL_ID,
    prompt_sha256: str | None = None,
) -> list[dict[str, Any]]:
    logs: list[dict[str, Any]] = []
    for path in GENERATED.rglob("*.log.json") if GENERATED.exists() else []:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (value.get("task") == task and value.get("model") == model_id
                and value.get("validation", {}).get("ok") is True
                and (prompt_sha256 is None or value.get("prompt_sha256") == prompt_sha256)):
            logs.append(value)
    return logs


def estimated_chargeable_output(
    task: int,
    item_count: int,
    model_id: str = MODEL_ID,
    prompt_sha256: str | None = None,
) -> int:
    if task == 6:
        return FALLBACK_CHARGEABLE_OUTPUT_PER_ITEM[6] * item_count
    totals = []
    for log in _successful_logs(task, model_id, prompt_sha256):
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


def enforce_ceiling(
    input_tokens: int,
    task: int,
    item_count: int,
    model_id: str = MODEL_ID,
    prompt_sha256: str | None = None,
) -> None:
    prices = load_prices()
    projected = existing_cost() + calculate_cost(
        input_tokens,
        estimated_chargeable_output(task, item_count, model_id, prompt_sha256),
        0,
        model_id,
    )
    ceiling = float(prices["hard_ceiling"])
    if projected > ceiling:
        raise Stage4Error(
            f"Hard cost ceiling: spent plus estimated request is ${projected:.6f}, above ${ceiling:.2f}"
        )


def generation_config(task: int, kind: str | None = None) -> Any:
    from google.genai import types

    return types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=(RESPONSE_SCHEMAS[task][kind] if task == 6 else RESPONSE_SCHEMAS[task]),
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
    if task == 6:
        builders.write_ordered_jsonl(path, values)
    else:
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
    allow_after_credit_deadline: bool = False,
) -> dict[str, Any] | list[dict[str, Any]] | None:
    batch_started = time.perf_counter()
    enforce_argon_deadline(model_id, allow_after_deadline)
    enforce_credit_deadline(allow_after_credit_deadline)
    _, location = vertex_settings()
    contents = request_text(task, items)
    input_text = builders.jsonl_text(items)
    prompt = prompt_text(task, items)
    prompt_sha256 = builders.sha256_text(prompt)
    counted_input: int | None = None
    attempts: list[dict[str, Any]] = []
    retry = 0
    rate_wait = 2
    while retry <= MAX_RETRIES:
        attempt_number = len(attempts) + 1
        timestamp = utc_now()
        attempt_started = time.perf_counter()
        operation = "count_tokens" if counted_input is None else "generate_content"
        try:
            enforce_argon_deadline(model_id, allow_after_deadline)
            enforce_credit_deadline(allow_after_credit_deadline)
            if counted_input is None:
                enforce_credit_deadline(allow_after_credit_deadline)
                counted_input = count_tokens(client, contents, model_id)
                enforce_ceiling(
                    counted_input, task, len(items), model_id, prompt_sha256
                )
            operation = "generate_content"
            enforce_credit_deadline(allow_after_credit_deadline)
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
                reason_warnings = validate(task, output, items)
            except (json.JSONDecodeError, ValidationError, Stage4Error, TypeError, ValueError) as validation_exc:
                attempts.append({
                    "attempt": attempt_number, "timestamp": timestamp, "usage": usage,
                    "usd": usd, "duration_seconds": duration_seconds, "validation_ok": False,
                    "operation": "validation",
                    "error": f"{type(validation_exc).__name__}: {validation_exc}",
                })
                retry += 1
                if retry <= MAX_RETRIES:
                    continue
                break
            attempts.append({
                "attempt": attempt_number, "timestamp": timestamp, "usage": usage,
                "usd": usd, "duration_seconds": duration_seconds, "validation_ok": True,
                "operation": "validation",
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
                "prompt_sha256": prompt_sha256,
                "input_sha256": builders.sha256_text(input_text),
                "item_count": len(items), "counted_input_tokens": counted_input,
                "usage": usage, "usd": usd, "attempts": attempts,
                "wall_clock_seconds": time.perf_counter() - batch_started,
                "reason_warnings": reason_warnings,
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
            if isinstance(exc, Stage4Error):
                raise
            if is_fatal_vertex_access_error(exc):
                raise
            if is_rate_limit(exc):
                print(
                    f"task={task} batch={batch_name} {operation} rate limited; "
                    f"waiting {rate_wait}s",
                    file=sys.stderr,
                )
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
                "operation": operation,
                "error": f"{type(exc).__name__}: {exc}",
            })
            retry += 1
            if retry <= MAX_RETRIES:
                wait_seconds = API_ERROR_RETRY_WAITS[retry - 1]
                print(
                    f"task={task} batch={batch_name} {operation} API/transport error; "
                    f"waiting {wait_seconds}s before retry {retry}",
                    file=sys.stderr,
                )
                time.sleep(wait_seconds)
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
        "prompt_sha256": prompt_sha256,
        "input_sha256": builders.sha256_text(input_text),
        "item_count": len(items), "counted_input_tokens": counted_input or 0,
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


def _task6_api_request(
    client: Any,
    batch_name: str,
    attempt_label: str,
    items: list[dict[str, Any]],
    kind: str,
    allow_after_deadline: bool,
    allow_after_credit_deadline: bool,
) -> tuple[Any | None, dict[str, Any]]:
    """Make one logical task-6 request, with transport retries only."""
    contents = request_text(6, items)
    prompt_sha = builders.sha256_text(prompt_text(6, items))
    counted: int | None = None
    errors: list[str] = []
    for transport_try in range(MAX_RETRIES + 1):
        started = time.perf_counter()
        timestamp = utc_now()
        operation = "count_tokens" if counted is None else "generate_content"
        try:
            enforce_argon_deadline(MODEL_ID, allow_after_deadline)
            enforce_credit_deadline(allow_after_credit_deadline)
            if counted is None:
                counted = count_tokens(client, contents, MODEL_ID)
                enforce_ceiling(counted, 6, len(items), MODEL_ID, prompt_sha)
            operation = "generate_content"
            enforce_credit_deadline(allow_after_credit_deadline)
            response = client.models.generate_content(
                model=MODEL_ID, contents=contents, config=generation_config(6, kind)
            )
            duration = time.perf_counter() - started
            usage = usage_from_response(response)
            usd = calculate_cost(**usage, model_id=MODEL_ID)
            append_cost({
                "timestamp": timestamp, "task": 6, "batch": batch_name,
                "attempt": attempt_label, "model": MODEL_ID, **usage,
                "duration_seconds": f"{duration:.3f}", "usd": f"{usd:.8f}",
            })
            try:
                output = json.loads(response_text_or_error(response, usage))
                # This call enforces the whole-batch contract. Item errors are returned.
                validate_task6_items(output, items, kind)
            except (json.JSONDecodeError, ValidationError, Stage4Error, TypeError, ValueError) as exc:
                return None, {
                    "type": "repair" if "r" in attempt_label else "full",
                    "attempt": attempt_label, "keys": [item["key"] for item in items],
                    "counted_input_tokens": counted, "usage": usage, "usd": usd,
                    "duration_seconds": duration, "validation_ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            return output, {
                "type": "repair" if "r" in attempt_label else "full",
                "attempt": attempt_label, "keys": [item["key"] for item in items],
                "counted_input_tokens": counted, "usage": usage, "usd": usd,
                "duration_seconds": duration, "validation_ok": True, "error": "",
            }
        except Exception as exc:  # SDK exception classes vary.
            duration = time.perf_counter() - started
            if isinstance(exc, Stage4Error) or is_fatal_vertex_access_error(exc):
                raise
            errors.append(f"{type(exc).__name__}: {exc}")
            append_cost({
                "timestamp": timestamp, "task": 6, "batch": batch_name,
                "attempt": attempt_label, "model": MODEL_ID, "input_tokens": 0,
                "output_tokens": 0, "thinking_tokens": 0, "total_token_count": 0,
                "unreported_tokens": 0, "duration_seconds": f"{duration:.3f}",
                "usd": "0.00000000",
            })
            if transport_try < MAX_RETRIES:
                wait = API_ERROR_RETRY_WAITS[transport_try]
                print(
                    f"task=6 batch={batch_name} {operation} API/transport error; "
                    f"waiting {wait}s before retry {transport_try + 1}", file=sys.stderr,
                )
                time.sleep(wait)
    return None, {
        "type": "repair" if "r" in attempt_label else "full",
        "attempt": attempt_label, "keys": [item["key"] for item in items],
        "counted_input_tokens": counted or 0, "usage": {}, "usd": 0,
        "duration_seconds": 0, "validation_ok": False,
        "error": errors[-1] if errors else "unknown request failure",
    }


def generate_task6_batch(
    client: Any,
    batch_name: str,
    kind: str,
    items: list[dict[str, Any]],
    output_path: Path,
    log_path: Path,
    allow_after_deadline: bool = False,
    allow_after_credit_deadline: bool = False,
) -> list[dict[str, Any]] | None:
    """Generate a task-6 batch, retaining valid items across item repairs/resume."""
    started = time.perf_counter()
    _, location = vertex_settings()
    prompt_sha = builders.sha256_text(prompt_text(6, items))
    input_text = builders.ordered_jsonl_text(items)
    valid_map: dict[str, dict[str, Any]] = {}
    failed_errors: dict[str, str] = {}
    warnings: list[dict[str, str]] = []
    requests: list[dict[str, Any]] = []
    batch_attempt = 1
    pending = list(items)
    resumed = False
    if output_path.is_file() and log_path.is_file():
        try:
            old_log = json.loads(log_path.read_text(encoding="utf-8"))
            if (old_log.get("validation", {}).get("state") == "partial"
                    and old_log.get("model") == MODEL_ID
                    and old_log.get("prompt_sha256") == prompt_sha
                    and old_log.get("input_sha256") == builders.sha256_text(input_text)
                    and old_log.get("item_count") == len(items)):
                old_values = read_generated_output(output_path, 6)
                old_keys = [value.get("key", "") for value in old_values]
                old_inputs = [item for item in items if item["key"] in old_keys]
                checked, old_errors, _ = validate_task6_items(old_values, old_inputs, kind)
                if old_errors or len(checked) != len(old_values):
                    raise ValueError("Stored partial task-6 output no longer validates")
                for value in checked:
                    valid_map[value["key"]] = value
                failed_errors = {
                    str(key): str(error) for key, error in old_log.get("failed_errors", {}).items()
                }
                failed_keys = old_log.get("failed_keys", [])
                pending = [item for item in items if item["key"] in failed_keys]
                batch_attempt = int(old_log.get("batch_attempt", 1)) + 1
                resumed = bool(pending)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            valid_map = {}
            failed_errors = {}
            pending = list(items)

    if not resumed:
        output = None
        for full_attempt in range(1, MAX_RETRIES + 2):
            batch_attempt = full_attempt
            output, request_log = _task6_api_request(
                client, batch_name, str(full_attempt), items, kind,
                allow_after_deadline, allow_after_credit_deadline,
            )
            requests.append(request_log)
            if output is not None:
                pending = list(items)
                break
        if output is None:
            failed_errors = {item["key"]: requests[-1]["error"] for item in items}
            pending = list(items)
        else:
            valid, failed_errors, warnings = validate_task6_items(output, items, kind)
            valid_map.update({value["key"]: value for value in valid})
            pending = [item for item in items if item["key"] in failed_errors]
    else:
        warnings = list(old_log.get("warnings", []))

    for repair_number in range(1, 3):
        if not pending:
            break
        repair_items = [
            {**item, "previous_error": failed_errors.get(item["key"], "previous item validation failed")}
            for item in pending
        ]
        output, request_log = _task6_api_request(
            client, batch_name, f"{batch_attempt}r{repair_number}", repair_items, kind,
            allow_after_deadline, allow_after_credit_deadline,
        )
        requests.append(request_log)
        if output is None:
            failed_errors = {item["key"]: request_log["error"] for item in pending}
            continue
        valid, failed_errors, repair_warnings = validate_task6_items(output, repair_items, kind)
        warnings.extend(repair_warnings)
        valid_map.update({value["key"]: value for value in valid})
        pending = [item for item in pending if item["key"] in failed_errors]

    ordered_valid = [valid_map[item["key"]] for item in items if item["key"] in valid_map]
    failed_keys = [item["key"] for item in items if item["key"] not in valid_map]
    state = "validated" if not failed_keys else ("partial" if ordered_valid else "failed")
    if ordered_valid:
        write_output(output_path, 6, ordered_valid)
    total_usage = {
        field: sum(int(request.get("usage", {}).get(field, 0) or 0) for request in requests)
        for field in ("input_tokens", "output_tokens", "thinking_tokens", "total_token_count", "unreported_tokens")
    }
    log = {
        "timestamp": utc_now(), "task": 6, "batch": batch_name, "kind": kind,
        "batch_attempt": batch_attempt, "model": MODEL_ID, "location": location,
        "settings": {
            "temperature": TEMPERATURE, "thinking": THINKING,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        },
        "prompt_sha256": prompt_sha, "input_sha256": builders.sha256_text(input_text),
        "item_count": len(items), "usage": total_usage,
        "usd": sum(float(request.get("usd", 0) or 0) for request in requests),
        "requests": requests, "warnings": warnings, "failed_keys": failed_keys,
        "failed_errors": {key: failed_errors.get(key, "item failed") for key in failed_keys},
        "wall_clock_seconds": time.perf_counter() - started,
        "validation": {"ok": state == "validated", "state": state,
                       "error": "" if state == "validated" else f"{len(failed_keys)} failed item(s)"},
    }
    write_log(log_path, log)
    print(
        f"task=6 batch={batch_name} kind={kind} state={state} "
        f"valid={len(ordered_valid)} failed={len(failed_keys)} usd=${log['usd']:.6f}"
    )
    return ordered_valid if state == "validated" else None


def run_check(
    client: Any, allow_after_deadline: bool = False,
    allow_after_credit_deadline: bool = False,
) -> None:
    from google.genai import types

    enforce_argon_deadline(MODEL_ID, allow_after_deadline)
    enforce_credit_deadline(allow_after_credit_deadline)
    _, location = vertex_settings()
    contents = 'Return exactly this JSON object: {"ok":true}'
    enforce_credit_deadline(allow_after_credit_deadline)
    counted = count_tokens(client, contents)
    schema = {
        "type": "object", "properties": {"ok": {"type": "boolean"}},
        "required": ["ok"], "additionalProperties": False,
    }
    enforce_ceiling(counted, 4, 1)
    timestamp = utc_now()
    request_started = time.perf_counter()
    try:
        enforce_credit_deadline(allow_after_credit_deadline)
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
    kind: str | None = None,
) -> bool:
    if not output_path.is_file() or not log_path.is_file():
        return False
    try:
        log = json.loads(log_path.read_text(encoding="utf-8"))
        if not isinstance(log, dict) or log.get("validation", {}).get("ok") is not True:
            return False
        input_text = builders.ordered_jsonl_text(items) if task == 6 else builders.jsonl_text(items)
        expected = {
            "task": task,
            "batch": batch_name,
            "model": model_id,
            "prompt_sha256": builders.sha256_text(prompt_text(task, items)),
            "input_sha256": builders.sha256_text(input_text),
            "item_count": len(items),
        }
        if any(log.get(key) != value for key, value in expected.items()):
            return False
        output = read_generated_output(output_path, task)
        validate(task, output, items, kind)
    except (OSError, json.JSONDecodeError, TypeError, ValueError, ValidationError):
        return False
    return True


def accepted_task_batches(task: int) -> list[list[dict[str, Any]]]:
    batches: list[list[dict[str, Any]]] = []
    for number in range(1, ACCEPTED_BATCH_COUNTS[task] + 1):
        path = ACCEPTED / f"task{task}" / "inputs" / f"b{number:03d}.jsonl"
        batches.append(builders.read_jsonl_files([path]) if path.is_file() else [])
    return batches


def accepted_task_states(task: int) -> dict[str, int]:
    counts = {"validated": 0, "failed": 0, "missing": 0}
    for number, items in enumerate(accepted_task_batches(task), 1):
        name = f"b{number:03d}"
        if not items:
            counts["missing"] += 1
            continue
        state = batch_state(
            task, name, items,
            ACCEPTED / f"task{task}" / f"{name}.jsonl",
            ACCEPTED / f"task{task}" / f"{name}.log.json",
        )
        counts[state] += 1
    return counts


def require_accepted_layout() -> None:
    failures = []
    for task, expected in ACCEPTED_BATCH_COUNTS.items():
        counts = accepted_task_states(task)
        if counts["validated"] != expected:
            failures.append(
                f"task {task}: {counts['validated']}/{expected} validated, "
                f"{counts['failed']} failed, {counts['missing']} missing"
            )
    if failures:
        raise Stage4Error("D65 accepted-content layout is incomplete: " + "; ".join(failures))


def _local_token_estimate(text: str) -> int:
    """Conservative offline estimate; never constructs a client or calls count_tokens."""
    ascii_count = sum(ord(char) < 128 for char in text)
    han_count = sum(0x3400 <= ord(char) <= 0x9FFF or 0x20000 <= ord(char) <= 0x2FFFF for char in text)
    other = len(text) - ascii_count - han_count
    return max(1, (ascii_count + 3) // 4 + han_count + (other + 1) // 2)


def write_pilot6_inputs() -> dict[str, list[dict[str, Any]]]:
    pilot = builders.build_pilot_task6()
    directory = INPUTS / "pilot_task6"
    for kind, items in pilot.items():
        builders.write_ordered_jsonl(directory / f"{kind}.jsonl", items)
    return pilot


def dry_run_task6() -> int:
    batches = builders.build_task6_batches()
    pilot = write_pilot6_inputs()
    summary: dict[str, dict[str, Any]] = {}
    for name, kind, items in batches:
        builders.write_ordered_jsonl(INPUTS / "task6" / f"{name}.jsonl", items)
        estimate = _local_token_estimate(request_text(6, items))
        current = summary.setdefault(kind, {
            "items": 0, "batches": 0, "input_tokens": 0,
            "output_tokens": 0, "first": name, "last": name,
        })
        current["items"] += len(items)
        current["batches"] += 1
        current["input_tokens"] += estimate
        current["output_tokens"] += len(items) * DRY_RUN_OUTPUT_PER_ITEM[kind]
        current["last"] = name
    total_cost = 0.0
    for kind in ("zh", "vi", "note"):
        current = summary[kind]
        cost = calculate_cost(current["input_tokens"], current["output_tokens"], 0)
        total_cost += cost
        print(
            f"task=6 kind={kind} items={current['items']} batches={current['batches']} "
            f"range={current['first']}-{current['last']} "
            f"estimated_input_tokens={current['input_tokens']} "
            f"estimated_output_tokens={current['output_tokens']} estimated_cost=${cost:.6f}"
        )
    print(
        f"task=6 total_items={sum(value['items'] for value in summary.values())} "
        f"total_batches={len(batches)} estimated_cost=${total_cost:.6f}"
    )
    print("pilot6 inputs: " + ", ".join(f"{kind}={len(items)}" for kind, items in pilot.items()))
    return 0


def run_task6(
    client: Any | None,
    batch_number: int | None,
    dry_run: bool,
    allow_after_deadline: bool = False,
    allow_after_credit_deadline: bool = False,
) -> int:
    require_accepted_layout()
    if dry_run:
        if client is not None:
            raise Stage4Error("Task 6 dry-run must not construct a Vertex client")
        return dry_run_task6()
    if client is None:
        raise Stage4Error("Task 6 generation requires a Vertex client")
    batches = builders.build_task6_batches()
    numbered = list(enumerate(batches, 1))
    if batch_number is not None:
        if batch_number < 1 or batch_number > len(batches):
            raise Stage4Error(f"Task 6 batch must be 1..{len(batches)}")
        numbered = [(batch_number, batches[batch_number - 1])]
    failed = 0
    for number, (name, kind, items) in numbered:
        output_path = GENERATED / "task6" / f"{name}.jsonl"
        log_path = GENERATED / "task6" / f"{name}.log.json"
        if batch_number is None and validated_batch_exists(
            6, name, items, output_path, log_path, kind=kind,
        ):
            print(f"task=6 batch={name} skipped=validated")
            continue
        builders.write_ordered_jsonl(INPUTS / "task6" / f"{name}.jsonl", items)
        result = generate_task6_batch(
            client, name, kind, items, output_path, log_path,
            allow_after_deadline, allow_after_credit_deadline,
        )
        failed += result is None
    return failed


def run_pilot6(
    client: Any,
    allow_after_deadline: bool = False,
    allow_after_credit_deadline: bool = False,
) -> int:
    pilot = write_pilot6_inputs()
    failures = 0
    for kind in ("zh", "vi", "note"):
        items = pilot[kind]
        failures += generate_task6_batch(
            client, f"pilot6-{kind}", kind, items,
            GENERATED / "pilot_task6" / f"{kind}.jsonl",
            GENERATED / "pilot_task6" / f"{kind}.log.json",
            allow_after_deadline, allow_after_credit_deadline,
        ) is None
    return failures


def rerun_task6(
    client: Any,
    round_number: int,
    allow_after_deadline: bool = False,
    allow_after_credit_deadline: bool = False,
) -> int:
    path = ROOT / "config" / "task6_rerun.csv"
    if not path.is_file():
        raise Stage4Error(f"Task 6 rerun file is missing: {path}")
    with path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != ["round", "key", "reason"]:
            raise Stage4Error("task6_rerun.csv columns must be round,key,reason")
        rows = [row for row in reader if row["round"] == str(round_number)]
    if not rows:
        raise Stage4Error(f"Task 6 rerun round {round_number} has no rows")
    built = builders.build_task6_items()
    by_key = {item["key"]: (kind.split("_", 1)[0] if kind != "note" else "note", item)
              for kind, items in built.items() for item in items}
    unknown = sorted({row["key"] for row in rows} - set(by_key))
    if unknown:
        raise Stage4Error(f"Task 6 rerun has unknown key(s): {unknown}")
    selected: dict[str, list[dict[str, Any]]] = {"zh": [], "vi": [], "note": []}
    seen: set[str] = set()
    for row in rows:
        if row["key"] in seen:
            raise Stage4Error(f"Task 6 rerun has duplicate key: {row['key']}")
        seen.add(row["key"])
        kind, item = by_key[row["key"]]
        selected[kind].append({**item, "review_feedback": row["reason"]})
    directory = GENERATED / "task6" / f"rerun{round_number}"
    input_dir = INPUTS / "task6" / f"rerun{round_number}"
    failures = 0
    number = 1
    for kind in ("zh", "vi", "note"):
        for items in builders.chunked(selected[kind], 50):
            name = f"b{number:03d}"
            builders.write_ordered_jsonl(input_dir / f"{name}.jsonl", items)
            failures += generate_task6_batch(
                client, name, kind, items,
                directory / f"{name}.jsonl", directory / f"{name}.log.json",
                allow_after_deadline, allow_after_credit_deadline,
            ) is None
            number += 1
    return failures


def run_task(
    client: Any,
    task: int,
    batch_number: int | None,
    dry_run: bool,
    allow_after_deadline: bool = False,
    allow_after_credit_deadline: bool = False,
) -> int:
    if task in ACCEPTED_BATCH_COUNTS:
        raise Stage4Error(
            f"D65 refusal: task {task} is accepted and its stale inputs must never be regenerated"
        )
    if task == 6:
        return run_task6(
            client, batch_number, dry_run, allow_after_deadline,
            allow_after_credit_deadline,
        )
    require_accepted_layout()
    outputs = None
    batches = builders.task_batches(task, outputs)
    numbered = list(enumerate(batches, 1))
    if batch_number is not None:
        if batch_number < 1 or batch_number > len(batches):
            raise Stage4Error(f"Task {task} batch must be 1..{len(batches)}")
        numbered = [(batch_number, batches[batch_number - 1])]
    total_counted = 0
    counted_batches = 0
    failed = 0
    for number, items in numbered:
        name = f"b{number:03d}"
        output_path = GENERATED / f"task{task}" / f"{name}.jsonl"
        log_path = GENERATED / f"task{task}" / f"{name}.log.json"
        if batch_number is None and validated_batch_exists(
            task, name, items, output_path, log_path,
        ):
            print(f"task={task} batch={name} skipped=validated")
            continue
        input_path = INPUTS / f"task{task}" / f"{name}.jsonl"
        builders.write_jsonl(input_path, items)
        contents = request_text(task, items)
        if dry_run:
            counted = count_tokens(client, contents)
            total_counted += counted
            counted_batches += 1
            print(f"task={task} batch={name} input_tokens={counted}")
            continue
        result = generate_batch(
            client, task, name, items,
            output_path, log_path,
            allow_after_deadline=allow_after_deadline,
        )
        failed += result is None
    if dry_run:
        print(f"task={task} batches={counted_batches} total_input_tokens={total_counted}")
    return failed


def batch_state(
    task: int,
    batch_name: str,
    items: list[dict[str, Any]],
    output_path: Path,
    log_path: Path,
    kind: str | None = None,
) -> str:
    if validated_batch_exists(task, batch_name, items, output_path, log_path, kind=kind):
        return "validated"
    if task == 6 and log_path.is_file():
        try:
            log = json.loads(log_path.read_text(encoding="utf-8"))
            expected = {
                "task": 6, "batch": batch_name, "model": MODEL_ID,
                "prompt_sha256": builders.sha256_text(prompt_text(6, items)),
                "input_sha256": builders.sha256_text(builders.ordered_jsonl_text(items)),
                "item_count": len(items),
            }
            if (log.get("validation", {}).get("state") == "partial"
                    and all(log.get(key) == value for key, value in expected.items())):
                return "partial"
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    if output_path.exists() or log_path.exists():
        return "failed"
    return "missing"


def task_states(task: int, batches: list[list[dict[str, Any]]]) -> dict[str, int]:
    counts = {"validated": 0, "failed": 0, "missing": 0}
    for number, items in enumerate(batches, 1):
        name = f"b{number:03d}"
        state = batch_state(
            task,
            name,
            items,
            GENERATED / f"task{task}" / f"{name}.jsonl",
            GENERATED / f"task{task}" / f"{name}.log.json",
        )
        counts[state] += 1
    return counts


def print_task_status(task: int, counts: dict[str, int]) -> None:
    total = sum(counts.values())
    print(
        f"task {task}: {counts['validated']}/{total} validated, "
        f"{counts['failed']} failed, {counts['missing']} missing"
    )


def run_status() -> None:
    """Print resume-aware status without constructing a Vertex client or making API calls."""
    for task in ACCEPTED_BATCH_COUNTS:
        print_task_status(task, accepted_task_states(task))
    task6_counts = {
        kind: {"validated": 0, "partial": 0, "failed": 0, "missing": 0}
        for kind in ("zh", "vi", "note")
    }
    for name, kind, items in builders.build_task6_batches():
        state = batch_state(
            6, name, items,
            GENERATED / "task6" / f"{name}.jsonl",
            GENERATED / "task6" / f"{name}.log.json",
            kind,
        )
        task6_counts[kind][state] += 1
    for kind in ("zh", "vi", "note"):
        counts = task6_counts[kind]
        total = sum(counts.values())
        print(
            f"task 6 {kind}: {counts['validated']}/{total} validated, "
            f"{counts['partial']} partial, {counts['failed']} failed, {counts['missing']} missing"
        )
    spent = existing_cost()
    ceiling = float(load_prices()["hard_ceiling"])
    print(f"spend to date: ${spent:.8f}")
    print(f"room under ${ceiling:.2f} ceiling: ${max(ceiling - spent, 0):.8f}")
    remaining = CREDIT_DEADLINE_UTC - datetime.now(timezone.utc)
    seconds = max(int(remaining.total_seconds()), 0)
    print(
        "credit deadline: 2026-11-16T08:00:00Z; "
        f"time left: {seconds // 86400}d {(seconds % 86400) // 3600}h {(seconds % 3600) // 60}m"
    )


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
    mode.add_argument("--pilot6", action="store_true", help="run the three task-6 pilot requests")
    mode.add_argument("--task", type=int, choices=range(1, 7), help="run one full task")
    mode.add_argument("--status", action="store_true", help="show offline resume status")
    parser.add_argument("--batch", type=int, help="run/rerun one 1-based batch")
    parser.add_argument("--dry-run", action="store_true", help="count inputs without generation")
    parser.add_argument("--rerun-round", type=int, help="run one task-6 review rerun round")
    parser.add_argument(
        "--allow-after-deadline", action="store_true",
        help="explicitly allow Argon requests on/after 2026-12-01 UTC",
    )
    parser.add_argument(
        "--allow-after-credit-deadline", action="store_true",
        help="allow requests after 2026-11-16T08:00:00Z only after upgrading",
    )
    args = parser.parse_args(argv)
    if args.batch is not None and args.task is None:
        parser.error("--batch requires --task")
    if args.dry_run and args.task is None:
        parser.error("--dry-run requires --task")
    if args.rerun_round is not None and args.task != 6:
        parser.error("--rerun-round requires --task 6")
    if args.rerun_round is not None and args.rerun_round < 1:
        parser.error("--rerun-round must be positive")
    if args.batch is not None and args.rerun_round is not None:
        parser.error("--batch and --rerun-round cannot be combined")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.status:
            run_status()
            return 0
        if args.task in ACCEPTED_BATCH_COUNTS:
            raise Stage4Error(
                f"D65 refusal: task {args.task} is accepted and its stale inputs must never be regenerated"
            )
        if args.pilot:
            raise Stage4Error("D65 refusal: the tasks 1-4 pilot is accepted and must not be regenerated")
        if args.task == 6 and args.dry_run:
            with stage4_lock():
                return run_task6(None, args.batch, True)
        with stage4_lock():
            enforce_credit_deadline(args.allow_after_credit_deadline)
            client = create_client(args.allow_after_credit_deadline)
            if args.check:
                run_check(client, args.allow_after_deadline, args.allow_after_credit_deadline)
                return 0
            if args.pilot:
                return 1 if run_pilot(client, args.allow_after_deadline) else 0
            if args.pilot6:
                return 1 if run_pilot6(
                    client, args.allow_after_deadline, args.allow_after_credit_deadline,
                ) else 0
            if args.rerun_round is not None:
                return 1 if rerun_task6(
                    client, args.rerun_round, args.allow_after_deadline,
                    args.allow_after_credit_deadline,
                ) else 0
            return 1 if run_task(
                client, args.task, args.batch, args.dry_run, args.allow_after_deadline,
                args.allow_after_credit_deadline,
            ) else 0
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
