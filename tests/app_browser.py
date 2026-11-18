"""Drive the real app in headless Chrome/Edge over the DevTools protocol (R1, D78).

Shared by the gate harness (``docs/review_scripts/stage5_gate_run.py``), the
benchmark (``tests/app_benchmark.py``), the render-equality test and the
screenshot script. Every run works on a *copy* of ``app/`` in a temporary
folder, blocks every network host name (offline, like a learner without a
connection) and opens the page either from ``file://`` or from
``http://127.0.0.1:<port>/`` served by Python's ``http.server`` (a secure
context like the https of GitHub Pages, RELEASE_PLAN §4.3). ``app/`` itself is
never changed.

Needs only the standard library plus ``websockets`` (already installed with the
Stage 4 requirements; see ``pipeline/README.md``).
"""

from __future__ import annotations

import base64
import contextlib
import functools
import http.server
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any, Iterator

from websockets.sync.client import connect

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
BROWSERS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]
MODES = ("file", "http")


def find_browser() -> Path | None:
    return next((path for path in BROWSERS if path.exists()), None)


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args: Any) -> None:  # keep test output clean
        pass


@contextlib.contextmanager
def serve(folder: Path) -> Iterator[str]:
    """Serve ``folder`` on 127.0.0.1 (random free port); yield the base URL."""
    handler = functools.partial(_QuietHandler, directory=str(folder))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/"
    finally:
        server.shutdown()
        server.server_close()


def copy_app(work: Path, extra_files: dict[str, str] | None = None, source: Path = APP) -> Path:
    """Copy ``app/`` (or ``source``) alone into ``work/copied/app`` (proves it runs standalone)."""
    app = work / "copied" / "app"
    shutil.copytree(source, app)
    for name, text in (extra_files or {}).items():
        (app / name).write_text(text, encoding="utf-8", newline="\n")
    return app


class Page:
    """A minimal synchronous CDP client for one page target."""

    def __init__(self, ws_url: str) -> None:
        self._connection = connect(ws_url, max_size=None, open_timeout=30)
        self.ws = self._connection.__enter__()  # websockets wants the context-manager form
        self.next_id = 0
        self.events: list[dict[str, Any]] = []
        self.errors: list[str] = []
        self.network_failures: list[str] = []

    def close(self) -> None:
        self._connection.__exit__(None, None, None)

    def _record(self, message: dict[str, Any]) -> None:
        method = message.get("method")
        params = message.get("params", {})
        if method == "Runtime.exceptionThrown":
            details = params.get("exceptionDetails", {})
            text = (details.get("exception") or {}).get("description") or details.get("text", "")
            self.errors.append(f"exception: {text} @{details.get('lineNumber')}")
        elif method == "Runtime.consoleAPICalled" and params.get("type") == "error":
            args = " ".join(str(a.get("value", a.get("description", ""))) for a in params.get("args", []))
            self.errors.append(f"console.error: {args}")
        elif method == "Log.entryAdded":
            entry = params.get("entry", {})
            if entry.get("level") == "error":
                # Blocked font hosts (offline) and a missing favicon are network
                # entries, not script errors; they are reported separately.
                if entry.get("source") == "network":
                    self.network_failures.append(entry.get("url") or entry.get("text", ""))
                else:
                    self.errors.append(f"log: {entry.get('text')}")
        self.events.append(message)

    def send(self, method: str, params: dict[str, Any] | None = None, timeout: float = 300) -> dict[str, Any]:
        self.next_id += 1
        message_id = self.next_id
        self.ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(method)
            message = json.loads(self.ws.recv(timeout=remaining))
            if message.get("id") == message_id:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message.get("result", {})
            self._record(message)

    def wait_event(self, method: str, timeout: float = 120) -> dict[str, Any]:
        for index, message in enumerate(self.events):
            if message.get("method") == method:
                del self.events[index]
                return message
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(method)
            message = json.loads(self.ws.recv(timeout=remaining))
            self._record(message)
            if message.get("method") == method:
                self.events.remove(message)
                return message

    def evaluate(self, expression: str, timeout: float = 300) -> Any:
        result = self.send(
            "Runtime.evaluate",
            {"expression": expression, "awaitPromise": True, "returnByValue": True},
            timeout=timeout,
        )
        if "exceptionDetails" in result:
            details = result["exceptionDetails"]
            text = (details.get("exception") or {}).get("description") or details.get("text")
            raise RuntimeError(f"evaluate failed: {text}")
        return result.get("result", {}).get("value")

    def navigate(self, url: str, timeout: float = 120) -> None:
        self.events.clear()
        self.send("Page.navigate", {"url": url})
        self.wait_event("Page.loadEventFired", timeout=timeout)

    def screenshot(self, path: Path | None = None) -> bytes:
        data = base64.b64decode(self.send("Page.captureScreenshot", {"format": "png"})["data"])
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return data


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextlib.contextmanager
def browser_page(work: Path, width: int = 1280, height: int = 800) -> Iterator[Page]:
    """Start a headless browser with a fresh profile under ``work``; yield a Page."""
    browser = find_browser()
    if browser is None:
        raise FileNotFoundError("Chrome or Edge not found")
    port = _free_port()
    profile = work / f"profile-{port}"
    command = [
        str(browser), "--headless=new", "--disable-gpu", "--no-first-run",
        "--no-default-browser-check", "--disable-extensions", "--hide-scrollbars",
        f"--user-data-dir={profile}", f"--remote-debugging-port={port}",
        # Offline: no host name resolves; only 127.0.0.1 (the local server of
        # the http mode) is excluded from the block.
        "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1",
        f"--window-size={width},{height}", "about:blank",
    ]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    page: Page | None = None
    try:
        deadline = time.monotonic() + 60
        targets: list[dict[str, Any]] = []
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=2) as response:
                    targets = json.loads(response.read())
                if any(t.get("type") == "page" for t in targets):
                    break
            except OSError:
                pass
            time.sleep(0.2)
        target = next(t for t in targets if t.get("type") == "page")
        page = Page(target["webSocketDebuggerUrl"])
        for domain in ("Page", "Runtime", "Log"):
            page.send(f"{domain}.enable")
        page.send("Emulation.setDeviceMetricsOverride",
                  {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False})
        yield page
    finally:
        if page is not None:
            with contextlib.suppress(Exception):
                page.send("Browser.close", timeout=10)
            with contextlib.suppress(Exception):
                page.close()
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            # never leave a headless browser behind: end the whole process tree
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            process.kill()
            process.wait(timeout=20)


@contextlib.contextmanager
def app_url(mode: str, page_name: str = "index.html",
            extra_files: dict[str, str] | None = None, source: Path = APP) -> Iterator[tuple[str, Path]]:
    """Yield (url, work folder) for a fresh copy of ``app/`` in ``mode``."""
    if mode not in MODES:
        raise ValueError(mode)
    with tempfile.TemporaryDirectory(prefix="kb-app-") as tmp:
        work = Path(tmp)
        app = copy_app(work, extra_files, source)
        if mode == "file":
            yield (app / page_name).resolve().as_uri(), work
        else:
            with serve(app) as base:
                yield base + page_name, work


def wait_for(page: Page, expression: str, timeout: float = 300, interval: float = 0.1) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if page.evaluate(expression):
            return
        time.sleep(interval)
    raise TimeoutError(expression)
