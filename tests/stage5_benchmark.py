"""Build an offline browser benchmark for the committed Stage 5 payload.

This does not modify ``data/final`` or ``app``. It copies the exact generated
``data.js`` beside a temporary benchmark page that the user can open through
``file://`` in Chrome or Edge.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "data" / "final"


BENCHMARK_HTML = r'''<!doctype html>
<meta charset="utf-8">
<title>Kanji Bridge Stage 5 benchmark</title>
<script>performance.mark('kb-page-start')</script>
<script src="data.js"></script>
<style>.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px}.tile{padding:22px 20px;min-height:190px}.grow{display:grid;grid-template-columns:1fr 1fr 1fr 1.2fr;padding:18px 0}</style>
<body><pre id="result">running</pre><div id="target"></div>
<script>
const esc=s=>String(s??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]));
const split=s=>s?s.split(';'):[];
const langLabel={ja:'日',ko:'韓',zh:'中',vi:'越'};
const D=window.KB_DATA;

function buildAdapters(){
  const wc=new Map();
  for(const x of D.word_chars){let a=wc.get(x.word_id);if(!a)wc.set(x.word_id,a=[]);a.push(x)}
  const allWords=new Map();
  for(const x of D.words){
    const w={id:x.word_id,h:x.trad,j:x.jp||x.trad,z:x.simp||x.trad,p:x.pinyin||'',
      jr:x.ja?(x.ja_use==='rare'?`（${x.ja}）`:x.ja):'',
      k:x.ko?(x.ko_use==='rare'?`（${x.ko}）`:x.ko):'',v:x.vi||'',syl:!!x.syl_aligned};
    if(x.vi){const va=split(x.vi_alt);if(va.length)w.va=va}
    if(x.note_ja)w.note=x.note_ja;
    if(w.syl)w.wc=wc.get(x.word_id)||[];
    allWords.set(x.word_id,w);
  }
  const examples=new Map(D.examples.map(x=>[`${x[0]}:${x[1]}:${x[2]}`,x]));
  const notes=new Map(D.char_notes);
  const usage=new Map(D.usage.map(x=>[x[0],x.slice(1)]));
  const WORDS=D.words.filter(x=>x.card_eligible).sort((a,b)=>(a.level??99)-(b.level??99)||
    (a.freq_vi??Number.MAX_SAFE_INTEGER)-(b.freq_vi??Number.MAX_SAFE_INTEGER)||a.word_id.localeCompare(b.word_id))
    .map(x=>allWords.get(x.word_id));
  const byFF=new Map();
  for(const x of D.ff_meanings){let a=byFF.get(x.word_id);if(!a)byFF.set(x.word_id,a=[]);a.push(x)}
  const FF=[];
  for(const x of D.words){if(!x.false_friend)continue;const w=allWords.get(x.word_id);const rows=byFF.get(x.word_id)||[];
    const rd=r=>r.reading_display||(r.lang==='zh'&&w.z!==w.j&&w.z!==w.h?`${w.z} ${w.p}`:r.reading||'');
    const line=r=>[langLabel[r.lang],rd(r),r.meaning_ja||''];
    const langs=x.false_friend.split(';');FF.push({id:x.word_id,w:x.jp||x.trad,safe:rows.filter(r=>!r.is_trap).sort((a,b)=>['ja','ko','zh','vi'].indexOf(a.lang)-['ja','ko','zh','vi'].indexOf(b.lang)).map(line),trap:rows.filter(r=>r.is_trap).map(line),t:langs.includes('zh')?'zh':langs.includes('vi')?'vi':langs[0]})}
  const GLYPHS=D.chars.filter(x=>!(x.jp===x.key_char&&x.key_char===x.simp))
    .sort((a,b)=>(a.level??99)-(b.level??99)||a.char_id.localeCompare(b.char_id))
    .map(x=>[x.jp,x.key_char,x.simp,split(x.pinyin_all).join(' / '),split(x.ja_on_all).join(' / '),split(x.ko_base_all).join(' / '),split(x.vi_all).join(' / '),notes.get(x.char_id)||'',usage.get(x.char_id)||[[],[]]]);
  return {WORDS,FF,GLYPHS,examples};
}

function sample(fn,n){const values=[];for(let i=0;i<n;i++){const t=performance.now();fn();values.push(performance.now()-t)}values.sort((a,b)=>a-b);return {min:values[0],median:values[Math.floor(n/2)],p95:values[Math.floor(n*.95)],max:values[n-1]}}
addEventListener('load',()=>requestAnimationFrame(()=>requestAnimationFrame(()=>{
  let coldStart=performance.now();const A=buildAdapters();let coldAdapter=performance.now()-coldStart;
  const adapter=sample(buildAdapters,25),target=document.querySelector('#target');
  function renderFF(){target.className='tiles';target.innerHTML=A.FF.map(f=>`<div class="tile" data-w="${f.id}"><div>${esc(f.w)}</div><div>${f.safe.map(s=>`<div><b>${s[0]}</b>${esc(s[2]||s[1])}</div>`).join('')}</div><div>実は…</div></div>`).join('');target.querySelectorAll('.tile').forEach(b=>b.onclick=()=>{});void target.offsetHeight}
  function renderGlyph(){target.className='';target.innerHTML=`<div class="ghead"><span>日本</span><span>韓国・繁体</span><span>中国・簡体</span><span>読み</span></div>`+A.GLYPHS.map(g=>`<div class="grow"><div>${g[0]} ${g[4]}</div><div>${g[1]} ${g[5]}</div><div>${g[2]} ${g[3]}</div><div>${esc(g[6])}</div></div>`).join('');void target.offsetHeight}
  const ffRender=sample(renderFF,15),glyphRender=sample(renderGlyph,15),resource=performance.getEntriesByName('data.js')[0],nav=performance.getEntriesByType('navigation')[0];
  const result={userAgent:navigator.userAgent,counts:{deck:A.WORDS.length,falseFriends:A.FF.length,glyphs:A.GLYPHS.length},dataJs:{transferSize:resource?.transferSize??null,decodedBodySize:resource?.decodedBodySize??null,durationMs:resource?.duration??null},page:{domContentLoadedMs:nav?.domContentLoadedEventEnd??null,loadMs:nav?.loadEventEnd??null,benchmarkReadyMs:performance.now()},adapterColdMs:coldAdapter,adapter25:adapter,falseFriendsRender15:ffRender,glyphRender15:glyphRender};
  document.querySelector('#result').textContent=JSON.stringify(result,null,2);document.title='KB BENCHMARK DONE';
})));
</script>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, nargs="?", default=ROOT / ".stage5-benchmark")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FINAL / "data.js", args.output / "data.js")
    (args.output / "benchmark.html").write_text(BENCHMARK_HTML, encoding="utf-8", newline="\n")
    data_js = (args.output / "data.js").read_text(encoding="utf-8")
    payload = json.loads(data_js[len("window.KB_DATA = ") : -2])
    print(json.dumps({"bytes": (args.output / "data.js").stat().st_size, **payload["meta"]["counts"]}, indent=2))
    print(f"Open {(args.output / 'benchmark.html').resolve()} in Chrome or Edge.")


if __name__ == "__main__":
    main()
