"""Screenshots and a short demo GIF of the real app (R1, RELEASE_PLAN §3.3 / §5.1).

Opens a copy of ``app/`` in headless Chrome/Edge (``tests/app_browser.py``)
with a fresh profile, at 1280×800. Every host is blocked except the two Google
Fonts hosts (R2: the pictures show the real fonts, as on the website); the
script waits for the fonts before each picture and fails if none loaded. Writes:

* ``docs/screenshots/<n>-<view>.png``: one per view (カード answered,
  音のルール, 偽の友達 with one tile open, 読解 with a tapped word, 字体
  with a 使われ方 panel open), 1280×800 PNG;
* ``docs/screenshots/demo.gif`` (R2): 960 px wide, 10 frames per second (every
  frame 100 ms; identical frames are merged by the GIF writer), 12–20 s, at
  most 5 MB: typing a reading in カード letter by letter and the result, a 字体
  quiz answer, a 偽の友達 tile opening. Frames are taken in real time, so the
  app's own 0.28 s fade-in shows.

Both browser runs end with the headless browser closed (``browser_page``); the
file:// mode starts no http.server.

Needs Pillow (``pip install -r tests/requirements-browser.txt``). The app is
driven like a learner (clicks, typed text, Enter); nothing in ``app/`` changes.

Usage (repository root):
    python -X utf8 tests/app_screenshots.py
"""

from __future__ import annotations

import io
import sys
import time
import unicodedata
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app_browser import FONT_HOSTS, ROOT, app_url, browser_page, wait_for  # noqa: E402

OUT = ROOT / "docs" / "screenshots"
WIDTH, HEIGHT = 1280, 800
GIF_SCALE = 0.75  # 960×600
GIF_LIMIT = 5 * 1024 * 1024
FRAME_MS = 100  # 10 frames per second
GIF_SECONDS = (12, 20)
TONE_MARKS = "̣́̀̉̃"


def strip_tones(text: str) -> str:
    """Vietnamese letters without the five tone marks (what the learner types)."""
    decomposed = unicodedata.normalize("NFD", text)
    return unicodedata.normalize("NFC", "".join(ch for ch in decomposed if ch not in TONE_MARKS))


class Driver:
    def __init__(self, page) -> None:
        self.page = page

    def js(self, expression: str):
        return self.page.evaluate(expression)

    def settle(self) -> None:
        self.js("new Promise(r=>{const w=()=>(typeof CHUNKS==='undefined'||!CHUNKS.size)?"
                "requestAnimationFrame(()=>requestAnimationFrame(r)):setTimeout(w,30);w()})"
                ".then(()=>document.fonts.ready)")

    def click(self, selector: str) -> None:
        self.js(f"document.querySelector({selector!r}).click()")
        self.settle()

    def type(self, text: str, film: "Film | None" = None, hold: int = 200) -> None:
        for char in text:
            self.page.send("Input.insertText", {"text": char})
            if film is not None:
                film.hold(hold)

    def key(self, key: str) -> None:
        code = {"Enter": 13, "Escape": 27}[key]
        for kind in ("rawKeyDown", "keyUp"):
            self.page.send("Input.dispatchKeyEvent", {
                "type": kind, "key": key, "code": key, "windowsVirtualKeyCode": code,
                "nativeVirtualKeyCode": code})
        self.settle()

    def scroll_to(self, selector: str, block: str = "start", offset: int = 0) -> None:
        self.js(f"(()=>{{const e=document.querySelector({selector!r});e.scrollIntoView({{block:{block!r}}});"
                f"window.scrollBy(0,{offset})}})()")
        self.settle()

    def top(self) -> None:
        self.js("window.scrollTo(0,0)")
        self.settle()

    def shot(self) -> Image.Image:
        return Image.open(io.BytesIO(self.page.screenshot())).convert("RGB")

    def fonts_loaded(self) -> list[str]:
        return self.js("[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family)")


class Film:
    """Real-time frames at 10 per second (one picture every 100 ms of wall time)."""

    def __init__(self, driver: Driver) -> None:
        self.driver = driver
        self.frames: list[Image.Image] = []

    def hold(self, ms: int) -> None:
        for _ in range(max(1, round(ms / FRAME_MS))):
            started = time.monotonic()
            self.frames.append(self.driver.shot())
            time.sleep(max(0.0, FRAME_MS / 1000 - (time.monotonic() - started)))


def screenshots(d: Driver) -> list[Path]:
    written = []

    def save(name: str) -> None:
        path = OUT / name
        image = d.shot()
        if image.size != (WIDTH, HEIGHT):
            raise SystemExit(f"{name}: unexpected size {image.size}")
        image.save(path, optimize=True)
        written.append(path)

    # 1. カード: type the Vietnamese reading without tone marks, Enter -> 正解 and examples
    card = d.js("({v:cur.v})")
    d.js("document.querySelector('#gvi').focus()")
    d.type(strip_tones(card["v"]))
    d.key("Enter")
    d.top()
    save("1-cards.png")
    # 2. 音のルール
    d.click('#nav button[data-v="rules"]')
    d.top()
    save("2-rules.png")
    # 3. 偽の友達: open the first tile
    d.click('#nav button[data-v="ff"]')
    d.click("#fflist .tile")
    d.top()
    save("3-false-friends.png")
    # 4. 読解: tap the second linked word, show passage and the 4-language sheet
    d.click('#nav button[data-v="read"]')
    d.js("document.querySelectorAll('.tok.sino .s')[1].click()")
    d.settle()
    d.scroll_to("#passage", "start", -110)
    save("4-reading.png")
    # 5. 字体: open the first row's 使われ方 panel
    d.click('#nav button[data-v="glyph"]')
    d.js("(()=>{const x=document.querySelector('#glyphbox details[data-usage]');x.open=true})()")
    d.settle()
    d.top()
    save("5-glyphs.png")
    return written


def demo_frames(d: Driver) -> list[Image.Image]:
    film = Film(d)
    # カード: front, the reading typed letter by letter, Enter, result
    d.top()
    film.hold(1500)
    card = d.js("({v:cur.v})")
    d.js("document.querySelector('#gvi').focus()")
    film.hold(300)
    d.type(strip_tones(card["v"]), film)
    film.hold(300)
    d.key("Enter")
    d.top()
    film.hold(2600)
    # 字体 quiz: answer the first Chinese reading
    d.click('#nav button[data-v="glyph"]')
    d.click('#gmode button[data-g="quiz"]')
    film.hold(1300)
    target = d.js("glyphTargets(filteredGlyphs()[0],'zh')[0]")
    d.js("document.querySelector('#glyphbox input[data-test-cell]').focus()")
    film.hold(300)
    letters = "".join(ch for ch in unicodedata.normalize("NFD", target) if unicodedata.category(ch) != "Mn")
    d.type(letters, film, hold=300)
    film.hold(300)
    d.key("Enter")
    film.hold(2200)
    # 偽の友達: list, then a tile opens
    d.click('#nav button[data-v="ff"]')
    d.top()
    film.hold(1500)
    d.click("#fflist .tile")
    film.hold(3000)
    return film.frames


def write_gif(frames: list[Image.Image]) -> Path:
    size = (round(WIDTH * GIF_SCALE), round(HEIGHT * GIF_SCALE))
    small = [image.resize(size, Image.LANCZOS) for image in frames]
    sample = small[:: max(1, len(small) // 24)]
    palette_source = Image.new("RGB", (size[0], size[1] * len(sample)))
    for index, image in enumerate(sample):
        palette_source.paste(image, (0, size[1] * index))
    palette = palette_source.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    quantized = [image.quantize(palette=palette, dither=Image.Dither.NONE) for image in small]
    path = OUT / "demo.gif"
    quantized[0].save(path, save_all=True, append_images=quantized[1:], duration=FRAME_MS,
                      loop=0, optimize=True, disposal=1)
    total = len(quantized) * FRAME_MS / 1000
    with Image.open(path) as check:
        stored = check.n_frames
    size_bytes = path.stat().st_size
    if not GIF_SECONDS[0] <= total <= GIF_SECONDS[1] or size_bytes > GIF_LIMIT or size[0] != 960:
        raise SystemExit(f"demo.gif out of range: {total:.1f} s, {size_bytes:,} bytes, {size}")
    print(f"demo.gif: {len(quantized)} frames of {FRAME_MS} ms ({1000 // FRAME_MS} per second; "
          f"{stored} stored after merging identical frames), {total:.1f} s, {size_bytes:,} bytes, "
          f"{size[0]}x{size[1]}")
    return path


def open_app(page) -> Driver:
    driver = Driver(page)
    wait_for(page, "!!document.querySelector('#cardbox > *')", timeout=120)
    driver.settle()
    fonts = driver.fonts_loaded()
    if not fonts:
        raise SystemExit("no Google Font loaded (fonts.googleapis.com / fonts.gstatic.com unreachable?)")
    print("fonts loaded:", ", ".join(sorted(set(fonts))))
    return driver


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    with app_url("file") as (url, work):
        with browser_page(work, WIDTH, HEIGHT, allow_hosts=FONT_HOSTS) as page:
            page.navigate(url)
            driver = open_app(page)
            for path in screenshots(driver):
                print(f"{path.relative_to(ROOT).as_posix()}: {Image.open(path).size}, {path.stat().st_size:,} bytes")
            errors += page.errors
    with app_url("file") as (url, work):  # a fresh profile: the GIF starts on a new card
        with browser_page(work, WIDTH, HEIGHT, allow_hosts=FONT_HOSTS) as page:
            page.navigate(url)
            driver = open_app(page)
            write_gif(demo_frames(driver))
            errors += page.errors
    if errors:
        print("console errors:", errors)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
