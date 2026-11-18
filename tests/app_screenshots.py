"""Screenshots and a short demo GIF of the real app (R1, RELEASE_PLAN §3.3 / §5.1).

Opens a copy of ``app/`` in headless Chrome/Edge (``tests/app_browser.py``),
offline (every host blocked, so the Google Fonts fall back to system fonts as
for an offline learner), with a fresh profile, at 1280×800, and writes:

* ``docs/screenshots/<n>-<view>.png``: one per view (カード answered,
  音のルール, 偽の友達 with one tile open, 読解 with a tapped word, 字体
  with a 使われ方 panel open), 1280×800 PNG;
* ``docs/screenshots/demo.gif``: about 15 s, at most 3 MB: typing a reading in
  カード and the result, a 字体 quiz answer, a 偽の友達 tile opening.

Needs Pillow (``pip install -r tests/requirements-browser.txt``). The app is
driven like a learner (clicks, typed text, Enter); nothing in ``app/`` changes.

Usage (repository root):
    python -X utf8 tests/app_screenshots.py
"""

from __future__ import annotations

import io
import sys
import unicodedata
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app_browser import ROOT, app_url, browser_page, wait_for  # noqa: E402

OUT = ROOT / "docs" / "screenshots"
WIDTH, HEIGHT = 1280, 800
GIF_SCALE = 0.625  # 800×500 frames keep the GIF small
GIF_LIMIT = 3 * 1024 * 1024
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
                "requestAnimationFrame(()=>requestAnimationFrame(r)):setTimeout(w,30);w()})")

    def click(self, selector: str) -> None:
        self.js(f"document.querySelector({selector!r}).click()")
        self.settle()

    def type(self, text: str, frames: list | None = None, hold: int = 110) -> None:
        for char in text:
            self.page.send("Input.insertText", {"text": char})
            if frames is not None:
                self.settle()
                frames.append((self.shot(), hold))

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


def demo_frames(d: Driver) -> list[tuple[Image.Image, int]]:
    frames: list[tuple[Image.Image, int]] = []
    # カード: front, type, Enter, result
    d.top()
    frames.append((d.shot(), 1400))
    card = d.js("({v:cur.v})")
    d.js("document.querySelector('#gvi').focus()")
    d.type(strip_tones(card["v"]), frames)
    d.key("Enter")
    d.top()
    frames.append((d.shot(), 2600))
    # 字体 quiz: answer the first Chinese reading
    d.click('#nav button[data-v="glyph"]')
    d.click('#gmode button[data-g="quiz"]')
    frames.append((d.shot(), 1200))
    target = d.js("glyphTargets(filteredGlyphs()[0],'zh')[0]")
    d.js("document.querySelector('#glyphbox input[data-test-cell]').focus()")
    letters = "".join(ch for ch in unicodedata.normalize("NFD", target) if unicodedata.category(ch) != "Mn")
    d.type(letters, frames, hold=160)
    d.key("Enter")
    frames.append((d.shot(), 2400))
    # 偽の友達: list, then a tile opens
    d.click('#nav button[data-v="ff"]')
    d.top()
    frames.append((d.shot(), 1300))
    d.click("#fflist .tile")
    frames.append((d.shot(), 2800))
    return frames


def write_gif(frames: list[tuple[Image.Image, int]]) -> Path:
    size = (round(WIDTH * GIF_SCALE), round(HEIGHT * GIF_SCALE))
    small = [image.resize(size, Image.LANCZOS) for image, _ in frames]
    durations = [duration for _, duration in frames]
    palette_source = Image.new("RGB", (size[0], size[1] * len(small)))
    for index, image in enumerate(small):
        palette_source.paste(image, (0, size[1] * index))
    palette = palette_source.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    quantized = [image.quantize(palette=palette, dither=Image.Dither.NONE) for image in small]
    path = OUT / "demo.gif"
    quantized[0].save(path, save_all=True, append_images=quantized[1:], duration=durations,
                      loop=0, optimize=True, disposal=1)
    total = sum(durations) / 1000
    if total > 15.5 or path.stat().st_size > GIF_LIMIT:
        raise SystemExit(f"demo.gif too long or too large: {total:.1f} s, {path.stat().st_size:,} bytes")
    print(f"demo.gif: {len(quantized)} frames, {total:.1f} s, {path.stat().st_size:,} bytes, {size[0]}x{size[1]}")
    return path


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    with app_url("file") as (url, work):
        with browser_page(work, WIDTH, HEIGHT) as page:
            page.navigate(url)
            wait_for(page, "!!document.querySelector('#cardbox > *')", timeout=120)
            driver = Driver(page)
            driver.settle()
            for path in screenshots(driver):
                print(f"{path.relative_to(ROOT).as_posix()}: {Image.open(path).size}, {path.stat().st_size:,} bytes")
            errors += page.errors
    with app_url("file") as (url, work):  # a fresh profile: the GIF starts on a new card
        with browser_page(work, WIDTH, HEIGHT) as page:
            page.navigate(url)
            wait_for(page, "!!document.querySelector('#cardbox > *')", timeout=120)
            driver = Driver(page)
            driver.settle()
            write_gif(demo_frames(driver))
            errors += page.errors
    if errors:
        print("console errors:", errors)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
