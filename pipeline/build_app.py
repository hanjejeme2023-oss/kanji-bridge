"""Rebuild ``app/index.html`` from the frozen prototype plus Stage 5 adapters."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "prototype" / "index.html"
APP = ROOT / "app" / "index.html"


ADAPTERS = r'''/* ---------- data adapters (Stage 5) ---------- */
const KB=window.KB_DATA;
if(!KB)throw new Error('KB_DATA failed to load');
const splitVals=s=>s?s.split(';'):[];
const WC_BY_WORD=new Map();
KB.word_chars.forEach(x=>{if(!WC_BY_WORD.has(x.word_id))WC_BY_WORD.set(x.word_id,[]);WC_BY_WORD.get(x.word_id).push(x)});
const adaptWord=x=>{
  const w={id:x.word_id,h:x.trad,j:x.jp||x.trad,z:x.simp||x.trad,p:x.pinyin||'',
    jr:x.ja?(x.ja_use==='rare'?`（${x.ja}）`:x.ja):'',
    k:x.ko?(x.ko_use==='rare'?`（${x.ko}）`:x.ko):'',v:x.vi||'',
    syl:x.syl_aligned?(WC_BY_WORD.get(x.word_id)||[]):null};
  if(x.vi){const va=splitVals(x.vi_alt);if(va.length)w.va=va}
  if(x.note_ja)w.note=x.note_ja;
  return w;
};
const WORD_BY_ID=new Map(KB.words.map(x=>[x.word_id,adaptWord(x)]));
const WORDS=KB.words.filter(x=>x.card_eligible).sort((a,b)=>(a.level??99)-(b.level??99)||
  (a.freq_vi??Number.MAX_SAFE_INTEGER)-(b.freq_vi??Number.MAX_SAFE_INTEGER)||a.word_id.localeCompare(b.word_id))
  .map(x=>WORD_BY_ID.get(x.word_id));

const RULES=KB.rules;
const NONE_RULE={jong:0,vi:[''],label:'パッチムなし → 子音で終わらない'};

const LANG_LABEL={ja:'日',ko:'韓',zh:'中',vi:'越'}, LANG_ORDER=['ja','ko','zh','vi'];
const FF_ROWS=new Map();
KB.ff_meanings.forEach(x=>{if(!FF_ROWS.has(x.word_id))FF_ROWS.set(x.word_id,[]);FF_ROWS.get(x.word_id).push(x)});
const FF=KB.words.filter(x=>x.false_friend).map(x=>{
  const w=WORD_BY_ID.get(x.word_id), rows=(FF_ROWS.get(x.word_id)||[]).slice()
    .sort((a,b)=>LANG_ORDER.indexOf(a.lang)-LANG_ORDER.indexOf(b.lang));
  const display=r=>r.reading_display||(r.lang==='zh'&&w.z!==w.j&&w.z!==w.h?`${w.z} ${w.p}`:r.reading||'');
  const line=r=>[LANG_LABEL[r.lang],display(r),r.meaning_ja||''];
  const traps=x.false_friend.split(';');
  return {id:x.word_id,w:x.jp||x.trad,safe:rows.filter(r=>!r.is_trap).map(line),
    trap:rows.filter(r=>r.is_trap).map(line),t:traps.includes('zh')?'zh':traps.includes('vi')?'vi':traps[0]};
});

const PASSAGE_ROWS=KB.passages.slice().sort((a,b)=>(a.lang==='vi'?0:1)-(b.lang==='vi'?0:1)||
  a.level-b.level||a.passage_id.localeCompare(b.passage_id));
const PASSAGE_N={vi:0,zh:0};
const PASSAGES=PASSAGE_ROWS.map(p=>({id:p.passage_id,lang:p.lang,
  name:`${p.lang==='vi'?'越':'中'} ${++PASSAGE_N[p.lang]}`,tr:p.translation_ja,
  toks:p.tokens.map(t=>t.word_id?{t:t.t,w:WORD_BY_ID.get(t.word_id)}:
    t.gloss_ja?{t:t.t,g:t.gloss_ja}:{t:t.t,x:1})}));

const GLYPHS=KB.chars.filter(x=>!(x.jp===x.key_char&&x.key_char===x.simp)).sort((a,b)=>(a.level??99)-(b.level??99)||a.char_id.localeCompare(b.char_id))
  .map(x=>[x.jp,x.key_char,x.simp,splitVals(x.pinyin_all).join(' / '),splitVals(x.ja_on_all).join(' / '),
    splitVals(x.ko_base_all).join(' / '),splitVals(x.vi_all).join(' / ')]);
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one prototype match, found {count}")
    return text.replace(old, new, 1)


def build() -> str:
    text = PROTOTYPE.read_text(encoding="utf-8")
    text = replace_once(
        text,
        ".seg button.on{background:var(--paper);color:var(--ink);box-shadow:0 1px 2px rgba(22,24,29,.12)}",
        ".seg button.on{background:var(--paper);color:var(--ink);box-shadow:0 1px 2px rgba(22,24,29,.12)}\n#psel{flex-wrap:wrap}",
        "passage selector wrapping",
    )
    text = replace_once(
        text,
        "<script>\nconst S=",
        '<script src="data.js"></script>\n<script>\nconst S=',
        "data.js script tag",
    )

    data_start = text.index("/* ---------- data: words ---------- */")
    data_end = text.index("const $=", data_start)
    text = text[:data_start] + ADAPTERS + "\n\n" + text[data_end:]

    text = replace_once(
        text,
        """function judge(input,ans,py){
  if(!input||!input.trim())return null;
  let a=norm(ans),b=norm(input),sa=strip(a),sb=strip(b);
  if(py){a=a.replace(/ /g,'');b=b.replace(/ /g,'');sa=sa.replace(/ /g,'');sb=sb.replace(/ /g,'')}
  return a===b?'ok':sa===sb?'close':'ng';
}""",
        """function judge(input,ans,py){
  if(!input||!input.trim())return null;
  const answers=Array.isArray(ans)?ans:[ans];let close=false;
  for(const answer of answers){let a=norm(answer),b=norm(input),sa=strip(a),sb=strip(b);
    if(py){a=a.replace(/ /g,'');b=b.replace(/ /g,'');sa=sa.replace(/ /g,'');sb=sb.replace(/ /g,'')}
    if(a===b)return'ok';if(sa===sb)close=true}
  return close?'close':'ng';
}""",
        "alternate Vietnamese answers",
    )
    old_rule_tags = """function ruleTags(w){
  const ks=[...w.k],vs=w.v.split(' ');
  if(ks.length!==vs.length)return'';
  return ks.map((ch,i)=>{
    const code=ch.charCodeAt(0)-0xAC00;if(code<0||code>11171)return'';
    const jong=code%28;const r=jong===0?NONE_RULE:RULES.find(x=>x.jong===jong);if(!r)return'';
    const ok=r.vi.includes(viFinal(vs[i]));
    return `<span class="tag ${ok?'':'off'}"><span class="ko">${ch}</span> → ${esc(vs[i])}　${ok?esc(r.label):'例外'}</span>`;
  }).join('');
}"""
    new_rule_tags = """function ruleTags(w){
  if(!w.syl)return'';
  return w.syl.map(pair=>{
    const ch=(pair.ko_syllable||'').replace(/[（）()]/g,''),vi=pair.vi_syllable||'';
    const code=ch.charCodeAt(0)-0xAC00;if(code<0||code>11171)return'';
    const jong=code%28,r=jong===0?NONE_RULE:RULES.find(x=>x.jong===jong);if(!r)return'';
    const ok=r.vi.includes(viFinal(vi));
    return `<span class="tag ${ok?'':'off'}"><span class="ko">${ch}</span> → ${esc(vi)}　${ok?esc(r.label):'例外'}</span>`;
  }).join('');
}"""
    text = replace_once(text, old_rule_tags, new_rule_tags, "aligned sound tags")

    old_state = """let srs=S.get('kb_srs',{}), custom=S.get('kb_custom',[]), target=S.get('kb_target','vi');
let cur=null, flipped=false, guess={vi:'',zh:''}, doneToday=0;
const deck=()=>WORDS.concat(custom);
const due=()=>{const now=Date.now();return deck().filter(w=>!srs[w.h]||srs[w.h].due<=now).sort((a,b)=>((srs[a.h]||{}).due||0)-((srs[b.h]||{}).due||0))};
function topStat(){const d=deck();const learned=d.filter(w=>srs[w.h]&&srs[w.h].box>=3).length;$('#topstat').textContent=`今日 ${due().length} 枚　習得 ${learned}/${d.length}`}"""
    new_state = """const ALL_WORD_IDS=new Set(WORD_BY_ID.keys());
const rawSrs=S.get('kb_srs',{}), rawCustom=S.get('kb_custom',[]);
let srs=Object.fromEntries(Object.entries(rawSrs).filter(([id,v])=>ALL_WORD_IDS.has(id)&&v&&typeof v==='object'));
let custom=[...new Set(rawCustom.filter(id=>typeof id==='string'&&ALL_WORD_IDS.has(id)))];
let target=S.get('kb_target','vi');
const localDay=()=>{const d=new Date(),p=n=>String(n).padStart(2,'0');return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}`};
let newToday=S.get('kb_newtoday',{date:localDay(),ids:[]});
if(!newToday||newToday.date!==localDay()||!Array.isArray(newToday.ids))newToday={date:localDay(),ids:[]};
newToday.ids=[...new Set(newToday.ids.filter(id=>ALL_WORD_IDS.has(id)))];S.set('kb_newtoday',newToday);
let cur=null, flipped=false, guess={vi:'',zh:''}, doneToday=0;
const customWords=()=>custom.map(id=>WORD_BY_ID.get(id)).filter(Boolean);
const deck=()=>{const seen=new Set(WORDS.map(w=>w.id));return WORDS.concat(customWords().filter(w=>!seen.has(w.id)))};
const targetOk=w=>target==='vi'?!!w.v:target==='zh'?!!w.p:!!w.v&&!!w.p;
const due=()=>{const now=Date.now(),d=deck().filter(targetOk),introduced=new Set(newToday.ids);
  const reviews=d.filter(w=>srs[w.id]&&srs[w.id].due<=now);
  const pending=d.filter(w=>!srs[w.id]&&introduced.has(w.id));
  const slots=Math.max(0,20-introduced.size),fresh=d.filter(w=>!srs[w.id]&&!introduced.has(w.id)).slice(0,slots);
  return reviews.concat(pending,fresh).sort((a,b)=>((srs[a.id]||{}).due||0)-((srs[b.id]||{}).due||0))};
function introduce(w){if(srs[w.id]||newToday.ids.includes(w.id))return;newToday.ids.push(w.id);S.set('kb_newtoday',newToday)}
function topStat(){const d=deck();const learned=d.filter(w=>srs[w.id]&&srs[w.id].box>=3).length;$('#topstat').textContent=`今日 ${due().length} 枚　習得 ${learned}/${d.length}`}"""
    text = replace_once(text, old_state, new_state, "SRS and daily limit state")

    text = replace_once(
        text,
        "if(!cur||!q.find(w=>w.h===cur.h)&&!flipped){cur=q[0]||null;flipped=false;guess={vi:'',zh:''}}",
        "if(!cur||!q.find(w=>w.id===cur.id)&&!flipped){cur=q[0]||null;flipped=false;guess={vi:'',zh:''};if(cur)introduce(cur)}",
        "current card ID",
    )
    text = replace_once(
        text,
        "${showVi?`<div><div class=\"lang\">ベトナム語</div><div class=\"val\">${esc(w.v)}${spk(w.v,'vi')}</div>${yours(guess.vi)}${vt(judge(guess.vi,w.v,false))}</div>`:''}",
        "${showVi?`<div><div class=\"lang\">ベトナム語</div><div class=\"val\">${esc(w.v)}${spk(w.v,'vi')}</div>${yours(guess.vi)}${vt(judge(guess.vi,[w.v,...(w.va||[])],false))}</div>`:''}",
        "Vietnamese alternate judging",
    )
    text = replace_once(
        text,
        "function nextBox(r){const b=(srs[cur.h]||{box:0}).box;",
        "function nextBox(r){const b=(srs[cur.id]||{box:0}).box;",
        "next box ID",
    )
    text = replace_once(
        text,
        "  srs[cur.h]={box,due:",
        "  srs[cur.id]={box,due:",
        "rating ID",
    )
    text = replace_once(
        text,
        "const q=due().filter(w=>w.h!==cur.h);\n  if(r===0&&q.length===0)srs[cur.h].due=0;",
        "const q=due().filter(w=>w.id!==cur.id);\n  if(r===0&&q.length===0)srs[cur.id].due=0;",
        "rated-card filtering",
    )

    text = replace_once(text, "const o=ffopen.has(f.w);return `<div class=\"tile ${o?'open':''}\" data-w=\"${esc(f.w)}\"", "const o=ffopen.has(f.id);return `<div class=\"tile ${o?'open':''}\" data-w=\"${f.id}\"", "false-friend ID key")

    text = replace_once(text, "let pid='v1', selTok=null;", "let pid=(PASSAGES[0]||{}).id||'', selTok=null;", "default passage")
    text = replace_once(text, "const w=p.toks[selTok].w, inDeck=deck().some(x=>x.h===w.h);", "const w=p.toks[selTok].w, inDeck=deck().some(x=>x.id===w.id);", "custom-card membership")
    text = replace_once(text, "custom.push(w);S.set('kb_custom',custom)", "custom.push(w.id);S.set('kb_custom',custom)", "custom-card persistence")
    text = replace_once(
        text,
        "<div class=\"cell\"><span>中国語</span><div><span class=\"zh\">${esc(w.z)}</span> ${esc(w.p)}${spk(w.z,'zh')}</div></div>",
        "<div class=\"cell\"><span>中国語</span><div><span class=\"zh\">${esc(w.z)}</span> ${esc(w.p)}${w.p?spk(w.z,'zh'):''}</div></div>",
        "empty Chinese speech button",
    )
    text = replace_once(
        text,
        "<div class=\"cell\"><span>ベトナム語</span><div>${esc(w.v)}${spk(w.v,'vi')}</div></div>",
        "<div class=\"cell\"><span>ベトナム語</span><div>${esc(w.v)}${w.v?spk(w.v,'vi'):''}</div></div>",
        "empty Vietnamese speech button",
    )

    text = replace_once(
        text,
        "srs={};custom=[];rprog={};gscore={ok:0,n:0};doneToday=0;\n  S.set('kb_srs',{});S.set('kb_custom',[]);S.set('kb_rules',{});S.set('kb_glyph',gscore);",
        "srs={};custom=[];rprog={};gscore={ok:0,n:0};doneToday=0;newToday={date:localDay(),ids:[]};\n  S.set('kb_srs',{});S.set('kb_custom',[]);S.set('kb_newtoday',newToday);S.set('kb_rules',{});S.set('kb_glyph',gscore);",
        "reset new-card state",
    )
    return text


def main() -> None:
    APP.parent.mkdir(parents=True, exist_ok=True)
    APP.write_text(build(), encoding="utf-8", newline="\n")
    print(f"Built {APP.relative_to(ROOT)} from frozen prototype")


if __name__ == "__main__":
    main()
