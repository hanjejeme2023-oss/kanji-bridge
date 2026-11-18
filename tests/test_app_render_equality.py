"""R1 render-time fix (RELEASE_PLAN §1.2): the chunked renderer's final DOM equals app v2's.

The app v2 renderers are kept verbatim in ``tests/fixtures/app_v2_renderers.js``
(renamed ``oldRenderGlyph`` / ``oldRenderFFList``). In headless Chrome/Edge, on
a copy of ``app/`` opened from ``file://`` with the network blocked, every case
renders the list with the new renderer, lets the idle-time chunks finish (or
completes them), and compares ``innerHTML`` with the old renderer's output for
the same state: 字体 すべて / a level filter / 間違えた字だけ in 一覧 and クイズ,
and 偽の友達 with a tile closed, opened and closed again (the single-tile toggle).
Skipped when no Chrome/Edge is installed.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app_browser import app_url, browser_page, find_browser, wait_for  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "app_v2_renderers.js"

CASES = r"""
(async()=>{
const out={},settle=async()=>{for(let i=0;i<1200&&CHUNKS.size;i++)await new Promise(r=>setTimeout(r,25))};
const show=v=>{view=v;document.querySelectorAll('main>section').forEach(s=>s.classList.toggle('hidden',s.id!=='v-'+v))};
async function glyphCase(name,mode,filter,natural){
  show('glyph');gmode=mode;gfil=filter;renderGlyph();
  const first=document.querySelectorAll('#glyphbox .grow').length;
  if(natural)await settle();else flushChunks();
  const fresh=document.querySelector('#glyphbox').innerHTML;
  oldRenderGlyph();const old=document.querySelector('#glyphbox').innerHTML;
  out[name]={equal:fresh===old,firstRows:first,rows:filteredGlyphs().length,length:old.length,
    firstDiff:fresh===old?null:[...fresh].findIndex((c,i)=>c!==old[i])};
}
await glyphCase('glyph_all_list','list','all',true);
await glyphCase('glyph_all_quiz','quiz','all',true);
await glyphCase('glyph_level3_list','list','level-3',false);
await glyphCase('glyph_level3_quiz','quiz','level-3',false);
[GLYPHS[3],GLYPHS[400],GLYPHS[2000]].forEach((g,i)=>{gresults[g[7]]=i===1?{vi:0}:{zh:0}});
gresults[GLYPHS[10][7]]={zh:1,vi:1};
await glyphCase('glyph_wrong_list','list','wrong',false);
await glyphCase('glyph_wrong_quiz','quiz','wrong',true);
gresults={};await glyphCase('glyph_empty','list','wrong',false);
await glyphCase('glyph_jz_list','list','jz',false);
async function ffCase(name,natural){
  if(natural)await settle();else flushChunks();
  const fresh=document.querySelector('#fflist').innerHTML;
  oldRenderFFList();const old=document.querySelector('#fflist').innerHTML;
  out[name]={equal:fresh===old,tiles:document.querySelectorAll('#fflist .tile').length,open:[...ffopen],
    firstDiff:fresh===old?null:[...fresh].findIndex((c,i)=>c!==old[i])};
  renderFF();
}
show('ff');ffmode='list';fff='all';ffopen=new Set();renderFF();
out.ff_first_tiles=document.querySelectorAll('#fflist .tile').length;
await ffCase('ff_all_closed',true);
flushChunks();
const pao=FF.find(f=>f.w==='包子'),last=FF[FF.length-1];
document.querySelector(`#fflist .tile[data-w="${pao.id}"]`).click();
document.querySelector(`#fflist .tile[data-w="${last.id}"]`).click();
out.toggle_focus=document.activeElement&&document.activeElement.dataset.w===last.id;
ffopen=new Set(ffopen);const opened=[...ffopen];
// compare the toggled DOM (single-tile updates) with a full old render of the same state
{const fresh=document.querySelector('#fflist').innerHTML;oldRenderFFList();const old=document.querySelector('#fflist').innerHTML;
 out.ff_two_open_toggled={equal:fresh===old,open:opened,firstDiff:fresh===old?null:[...fresh].findIndex((c,i)=>c!==old[i])}}
renderFF();flushChunks();
document.querySelector(`#fflist .tile[data-w="${pao.id}"]`).click();
{const fresh=document.querySelector('#fflist').innerHTML;oldRenderFFList();const old=document.querySelector('#fflist').innerHTML;
 out.ff_closed_again_toggled={equal:fresh===old,open:[...ffopen],firstDiff:fresh===old?null:[...fresh].findIndex((c,i)=>c!==old[i])}}
fff='zh';renderFF();await ffCase('ff_zh_filter_open',true);
fff='vi';ffopen=new Set();renderFF();await ffCase('ff_vi_filter_closed',false);
return out})()
"""


@unittest.skipIf(find_browser() is None, "Chrome or Edge not installed")
class RenderEqualityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with app_url("file") as (url, work):
            with browser_page(work) as page:
                page.navigate(url)
                wait_for(page, "!!document.querySelector('#cardbox > *')", timeout=120)
                page.evaluate(FIXTURE.read_text(encoding="utf-8") + "\n;true")
                cls.result = page.evaluate(CASES, timeout=600)
                cls.errors = page.errors

    def test_no_script_errors(self) -> None:
        self.assertEqual(self.errors, [])

    def test_glyph_final_dom_equals_app_v2(self) -> None:
        for name in ("glyph_all_list", "glyph_all_quiz", "glyph_level3_list", "glyph_level3_quiz",
                     "glyph_wrong_list", "glyph_wrong_quiz", "glyph_empty", "glyph_jz_list"):
            with self.subTest(name):
                self.assertTrue(self.result[name]["equal"], self.result[name])
        self.assertEqual(self.result["glyph_all_list"]["rows"], 2164)
        self.assertEqual(self.result["glyph_wrong_list"]["rows"], 3)
        self.assertEqual(self.result["glyph_empty"]["rows"], 0)

    def test_first_screen_is_small(self) -> None:
        self.assertLessEqual(self.result["glyph_all_list"]["firstRows"], 30)
        self.assertLessEqual(self.result["ff_first_tiles"], 30)

    def test_false_friend_final_dom_equals_app_v2(self) -> None:
        for name in ("ff_all_closed", "ff_two_open_toggled", "ff_closed_again_toggled",
                     "ff_zh_filter_open", "ff_vi_filter_closed"):
            with self.subTest(name):
                self.assertTrue(self.result[name]["equal"], self.result[name])
        self.assertEqual(self.result["ff_all_closed"]["tiles"], 1242)
        self.assertEqual(len(self.result["ff_two_open_toggled"]["open"]), 2)
        self.assertEqual(len(self.result["ff_closed_again_toggled"]["open"]), 1)
        self.assertTrue(self.result["toggle_focus"])


if __name__ == "__main__":
    unittest.main()
