/* app v2 renderers, copied verbatim from app/index.html of app v2 (the Stage 5 gate baseline, D77)
   and renamed (renderFFList -> oldRenderFFList, renderGlyph -> oldRenderGlyph; the tile toggle calls
   oldRenderFFList instead of renderFF). Used only by tests/test_app_render_equality.py: the R1 renderer
   (chunked, RELEASE_PLAN 1.2) must produce exactly the same final DOM. Do not edit. */
function oldRenderFFList(){
  const list=FF.filter(f=>fff==='all'||f.traps.includes(fff));$('#fflist').className='tiles';
  $('#fflist').innerHTML=list.map(f=>{const o=ffopen.has(f.id);return `<div class="tile ${o?'open':''}" data-w="${f.id}" role="button" tabindex="0" aria-expanded="${o}">
    <div class="w han">${esc(f.w)}</div><div class="l">${f.rows.filter(row=>!row.trap).map(ffLine).join('')}</div>
    ${o?`<div class="trap">${f.rows.filter(row=>row.trap).map(ffLine).join('')}</div>${ffExamples(f)}`:'<div class="hint">実は…</div>'}</div>`}).join('');
  $$('#fflist .tile').forEach(b=>{const toggle=()=>{const id=b.dataset.w;ffopen.has(id)?ffopen.delete(id):ffopen.add(id);oldRenderFFList();const next=$(`#fflist .tile[data-w="${id}"]`);if(next)next.focus()};
    b.onclick=toggle;b.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();toggle()}}});
}
function oldRenderGlyph(){
  beginTableTest();const list=filteredGlyphs();
  const head='<div class="ghead"><span>日本</span><span>韓国・繁体</span><span>中国・簡体</span><span>読み</span></div>';
  $('#glyphbox').innerHTML=(gmode==='quiz'?`<div class="glyph-score" id="glyphscore"></div>`:'')+(list.length?head+list.map(g=>gmode==='quiz'?glyphQuizRow(g):glyphListRow(g)).join(''):'<div class="empty">該当する字はない</div>');
  if(gmode==='quiz'){bindTableTests($('#glyphbox'));updateGlyphScore()}bindUsagePanels();
}
