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
    pt:x.pt||'',syl:x.syl_aligned?(WC_BY_WORD.get(x.word_id)||[]):null};
  if(x.vi){const va=splitVals(x.vi_alt);if(va.length)w.va=va}
  if(x.note_ja)w.note=x.note_ja;
  return w;
};
const WORD_BY_ID=new Map(KB.words.map(x=>[x.word_id,adaptWord(x)]));
const WORDS=KB.words.filter(x=>x.card_eligible&&[...x.trad].length>1).sort((a,b)=>(a.level??99)-(b.level??99)||
  (a.freq_vi??Number.MAX_SAFE_INTEGER)-(b.freq_vi??Number.MAX_SAFE_INTEGER)||a.word_id.localeCompare(b.word_id))
  .map(x=>WORD_BY_ID.get(x.word_id));

const EXAMPLES=new Map(KB.examples.map(x=>[`${x[0]}:${x[1]}:${x[2]}`,
  {wordId:x[0],lang:x[1],use:x[2],sentence:x[3],pinyin:x[4],translation:x[5],start:x[6],len:x[7]}]));

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

const CHAR_BY_ID=new Map(KB.chars.map(x=>[x.char_id,x]));
const GLYPHS=KB.glyphs.map(row=>{const x=CHAR_BY_ID.get(row[0]);return [x.jp,x.key_char,x.simp,
  splitVals(x.pinyin_all).join(' / '),splitVals(x.ja_on_all).join(' / '),
  splitVals(x.ko_base_all).join(' / '),splitVals(x.vi_all).join(' / '),row[0],row[1],row[2],row[3],row[4]]})
  .filter(x=>!(x[0]===x[1]&&x[1]===x[2]));
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
        ".seg button.on{background:var(--paper);color:var(--ink);box-shadow:0 1px 2px rgba(22,24,29,.12)}\n"
        "#psel{flex-wrap:wrap}\n.tabcount{font-size:11px;opacity:.75;margin-left:4px}\n"
        ".tab-explain{color:var(--sub);font-size:13px;margin:-20px 0 28px}\n"
        ".tone-hint{font-size:12px;color:var(--sub);text-align:center;margin-top:3px}\n"
        ".examples{max-width:620px;margin:30px auto 0;display:grid;gap:14px;text-align:left}\n"
        ".example{border-top:1px solid var(--line);padding-top:13px;font-size:14px}\n"
        ".example mark{background:var(--indigo-soft);color:var(--indigo);padding:1px 2px;border-radius:3px}\n"
        ".example .translation{color:var(--sub);font-size:13px}",
        "passage selector wrapping",
    )
    text = replace_once(
        text,
        """<button data-v="cards" class="on">カード</button>
      <button data-v="rules">音のルール</button>
      <button data-v="ff">偽の友達</button>
      <button data-v="read">読解</button>
      <button data-v="glyph">字体</button>""",
        """<button data-v="cards" class="on">カード <span class="tabcount" id="count-cards"></span></button>
      <button data-v="rules">音のルール <span class="tabcount" id="count-rules"></span></button>
      <button data-v="ff">偽の友達 <span class="tabcount" id="count-ff"></span></button>
      <button data-v="read">読解 <span class="tabcount" id="count-read"></span></button>
      <button data-v="glyph">字体 <span class="tabcount" id="count-glyph"></span></button>""",
        "tab item counts",
    )
    text = replace_once(
        text,
        """</nav>
    <div class="today" id="topstat"></div>""",
        """</nav>
    <button class="toggle" id="mute" type="button"><i></i>ミュート</button>
    <div class="today" id="topstat"></div>""",
        "global mute toggle",
    )
    explanations = {
        '<section id="v-cards">': '2字以上の単語を、日本語と韓国語を手がかりに中国語・ベトナム語で答える',
        '<section id="v-rules" class="hidden">': '韓国語のパッチムからベトナム語の語末を推測するルール',
        '<section id="v-ff" class="hidden">': '同じ漢字でも言語によって意味が違う、間違えやすい単語',
        '<section id="v-read" class="hidden">': '短い中国語・ベトナム語の文を読み、わからない語をタップして確認する',
        '<section id="v-glyph" class="hidden">': '1字の漢字の形（日本・繁体・簡体）と読み、使われ方',
    }
    for section, explanation in explanations.items():
        text = replace_once(
            text, section, f'{section}\n  <p class="tab-explain">{explanation}</p>',
            f"{section} explanation",
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
        """const PY_TONE_MARKS=/[\\u0304\\u0301\\u030c\\u0300]/g;
const VI_TONE_MARKS=/[\\u0301\\u0300\\u0309\\u0303\\u0323]/g;
const VI_SHAPED=/[ăâêôơưđáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]/i;
function telexSyllable(raw){
  let s=raw.toLocaleLowerCase('vi');
  if(VI_SHAPED.test(s))return s;
  s=s.replace(/dd/g,'đ').replace(/uwow/g,'ươ').replace(/uow/g,'ươ')
    .replace(/aa/g,'â').replace(/ee/g,'ê').replace(/oo/g,'ô')
    .replace(/aw/g,'ă').replace(/ow/g,'ơ').replace(/uw/g,'ư');
  while(s.includes('w')){const i=s.indexOf('w'),before=s.slice(0,i);let changed=before;
    const uo=before.lastIndexOf('uo');
    if(uo>=0)changed=before.slice(0,uo)+'ươ'+before.slice(uo+2);
    else{let pos=-1;for(let j=0;j<before.length;j++)if(/[aou]/.test(before[j]))pos=j;
      if(pos>=0){const map={a:'ă',o:'ơ',u:'ư'};changed=before.slice(0,pos)+map[before[pos]]+before.slice(pos+1)}
      else changed=before+'ư'}
    s=changed+s.slice(i+1);
  }
  const first=[...s].findIndex(ch=>/[aeiouyăâêôơư]/.test(ch));
  if(first>=0)s=[...s].filter((ch,i)=>!(i>first&&/[sfrxjz]/.test(ch))).join('');
  return s;
}
const pyKey=s=>String(s).toLocaleLowerCase().replace(/u:|v/g,'ü').normalize('NFD')
  .replace(PY_TONE_MARKS,'').replace(/[ '\u2019-]/g,'');
const viKey=(s,typed=false)=>{
  let value=String(s).toLocaleLowerCase('vi').normalize('NFC');
  if(typed)value=value.replace(/\\p{L}+/gu,telexSyllable);
  return value.normalize('NFD').replace(VI_TONE_MARKS,'').normalize('NFC').replace(/\\s+/g,'');
};
function judge(input,lang,accepted,viAlt=[],several=false){
  if(!input||!input.trim())return null;
  const answers=(Array.isArray(accepted)?accepted:[accepted]).filter(Boolean);
  const alternates=lang==='vi'?(Array.isArray(viAlt)?viAlt:[viAlt]).filter(Boolean):[];
  const parts=several?input.split(/[,/，／、]/).map(x=>x.trim()).filter(Boolean):[input];
  if(!parts.length)return null;
  const expected=lang==='zh'?answers.map(pyKey):answers.concat(alternates).map(x=>viKey(x,false));
  return parts.every(part=>expected.includes(lang==='zh'?pyKey(part):viKey(part,true)))?'ok':'ng';
}
const PY_TONE_NAME={1:'1声',2:'2声',3:'3声',4:'4声',5:'軽声'};
const VI_TONE_NAME={'\\u0301':'sắc','\\u0300':'huyền','\\u0309':'hỏi','\\u0303':'ngã','\\u0323':'nặng'};
function markedTone(syllable,lang){
  const marks=[...String(syllable).normalize('NFD')];
  if(lang==='zh'){const order='\\u0304\\u0301\\u030c\\u0300',mark=marks.find(ch=>order.includes(ch));
    return mark?PY_TONE_NAME[order.indexOf(mark)+1]:'軽声'}
  const mark=marks.find(ch=>VI_TONE_NAME[ch]);return mark?VI_TONE_NAME[mark]:'ngang';
}
function toneHint(lang,readings,tones=''){
  const values=(Array.isArray(readings)?readings:[readings]).filter(Boolean);
  return values.map(reading=>{
    if(lang==='zh'&&tones&&values.length===1)return [...tones].map(x=>PY_TONE_NAME[x]).filter(Boolean).join('・');
    const syllables=String(reading).split(/\\s+|['\u2019-]+/).filter(Boolean);
    return syllables.map(x=>markedTone(x,lang)).join('・');
  }).join(' / ');
}""",
        "shared reading judging and tone hints",
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

    text = replace_once(
        text,
        """const TTS={ok:typeof window.speechSynthesis!=='undefined',voices:[],warned:new Set()};
const LNAME={zh:'中国語',vi:'ベトナム語'};""",
        """const TTS={ok:typeof window.speechSynthesis!=='undefined',voices:[],warned:new Set()};
const LNAME={zh:'中国語',vi:'ベトナム語'};
let mute=S.get('kb_mute',false);
function syncMute(){$('#mute').classList.toggle('on',mute);$('#mute').setAttribute('aria-pressed',mute)}
$('#mute').onclick=()=>{mute=!mute;S.set('kb_mute',mute);if(mute)stopSpeech();syncMute()};syncMute();""",
        "mute state",
    )
    text = replace_once(
        text,
        """function speak(text,lang,btn,quiet){
  if(!TTS.ok)""",
        """function speak(text,lang,btn,quiet){
  if(mute)return;
  if(!TTS.ok)""",
        "mute speech guard",
    )
    text = replace_once(
        text,
        """function render(){({cards:renderCards,rules:renderRules,ff:renderFF,read:renderRead,glyph:renderGlyph})[view]();topStat()}""",
        """function filteredGlyphs(){return GLYPHS.filter(g=>gfil==='all'||pat(g)===gfil)}
function updateCounts(){
  const counts={cards:deck().filter(targetOk).length,
    rules:(RULES.find(x=>x.id===ruleSel)||{ex:[]}).ex.length,
    ff:FF.filter(f=>fff==='all'||f.t===fff).length,read:PASSAGES.length,glyph:filteredGlyphs().length};
  Object.entries(counts).forEach(([key,value])=>{const el=$(`#count-${key}`);if(el)el.textContent=value.toLocaleString('ja-JP')});
}
function render(){({cards:renderCards,rules:renderRules,ff:renderFF,read:renderRead,glyph:renderGlyph})[view]();topStat();updateCounts()}""",
        "per-tab item counts",
    )

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
const due=()=>{const now=Date.now(),d=deck().filter(targetOk),available=new Set(d.map(w=>w.id)),introduced=new Set(newToday.ids.filter(id=>available.has(id)));
  const reviews=d.filter(w=>srs[w.id]&&srs[w.id].due<=now);
  const pending=d.filter(w=>!srs[w.id]&&introduced.has(w.id));
  const slots=Math.max(0,20-introduced.size),fresh=d.filter(w=>!srs[w.id]&&!introduced.has(w.id)).slice(0,slots);
  return reviews.concat(pending,fresh).sort((a,b)=>((srs[a.id]||{}).due||0)-((srs[b.id]||{}).due||0))};
function introduce(w){if(srs[w.id]||newToday.ids.includes(w.id))return;newToday.ids.push(w.id);S.set('kb_newtoday',newToday)}
function topStat(){const d=deck();const learned=d.filter(w=>srs[w.id]&&srs[w.id].box>=3).length;$('#topstat').textContent=`今日 ${due().length} 枚　習得 ${learned}/${d.length}`}"""
    text = replace_once(text, old_state, new_state, "SRS and daily limit state")
    text = replace_once(
        text,
        """$$('#target button').forEach(b=>{b.classList.toggle('on',b.dataset.t===target);b.onclick=()=>{target=b.dataset.t;S.set('kb_target',target);$$('#target button').forEach(x=>x.classList.toggle('on',x===b));flipped=false;renderCards()}});""",
        """$$('#target button').forEach(b=>{b.classList.toggle('on',b.dataset.t===target);b.onclick=()=>{target=b.dataset.t;S.set('kb_target',target);$$('#target button').forEach(x=>x.classList.toggle('on',x===b));flipped=false;renderCards();topStat();updateCounts()}});""",
        "card target count update",
    )
    text = replace_once(
        text,
        "function renderCards(){",
        """const markedTarget=x=>`${esc(x.sentence.slice(0,x.start))}<mark>${esc(x.sentence.slice(x.start,x.start+x.len))}</mark>${esc(x.sentence.slice(x.start+x.len))}`;
function cardExample(w,lang){const x=EXAMPLES.get(`${w.id}:${lang}:card`);if(!x)return'';
  return `<div class="example"><div class="small sub">${lang==='zh'?'中国語':'ベトナム語'}</div><div class="${lang==='zh'?'zh':''}">${markedTarget(x)}</div>${lang==='zh'?`<div>${esc(x.pinyin)}</div>`:''}<div class="translation">${esc(x.translation)}</div></div>`}
const cardExamples=(w,showVi,showZh)=>{const rows=[showZh?cardExample(w,'zh'):'',showVi?cardExample(w,'vi'):''].filter(Boolean);return rows.length?`<div class="examples">${rows.join('')}</div>`:''};
function renderCards(){""",
        "card example helpers",
    )
    text = replace_once(
        text,
        """${showVi?`<label class="field"><span>ベトナム語</span><input id="gvi" autocomplete="off" spellcheck="false" placeholder="読みを予想"></label>`:''}
        ${showZh?`<label class="field"><span>中国語（ピンイン）</span><input id="gzh" autocomplete="off" spellcheck="false" placeholder="読みを予想"></label>`:''}""",
        """${showVi?`<label class="field"><span>ベトナム語</span><div class="tone-hint">${toneHint('vi',[w.v])}</div><input id="gvi" autocomplete="off" spellcheck="false" placeholder="読みを予想"></label>`:''}
        ${showZh?`<label class="field"><span>中国語（ピンイン）</span><div class="tone-hint">${toneHint('zh',[w.p],w.pt)}</div><input id="gzh" autocomplete="off" spellcheck="false" placeholder="読みを予想"></label>`:''}""",
        "card tone hints",
    )
    text = replace_once(
        text,
        """const vt=r=>r===null?'<div class="you sub">入力なし</div>':r==='ok'?'<div class="you ok">正解</div>':r==='close'?'<div class="you close">声調・記号だけ違う</div>':'<div class="you ng">違う</div>';""",
        """const vt=(r,answer)=>r===null?'<div class="you sub">入力なし</div>':r==='ok'?'<div class="you ok">正解</div>':`<div class="you ng">${esc(answer)}</div>`;""",
        "card judging result",
    )

    text = replace_once(
        text,
        "if(!cur||!q.find(w=>w.h===cur.h)&&!flipped){cur=q[0]||null;flipped=false;guess={vi:'',zh:''}}",
        "if(!cur||!q.find(w=>w.id===cur.id)&&!flipped){cur=q[0]||null;flipped=false;guess={vi:'',zh:''};if(cur)introduce(cur)}",
        "current card ID",
    )
    text = replace_once(
        text,
        "${showVi?`<div><div class=\"lang\">ベトナム語</div><div class=\"val\">${esc(w.v)}${spk(w.v,'vi')}</div>${yours(guess.vi)}${vt(judge(guess.vi,w.v,false))}</div>`:''}",
        "${showVi?`<div><div class=\"lang\">ベトナム語</div><div class=\"val\">${esc(w.v)}${spk(w.v,'vi')}</div>${yours(guess.vi)}${vt(judge(guess.vi,'vi',[w.v],w.va||[]),w.v)}</div>`:''}",
        "Vietnamese card judging",
    )
    text = replace_once(
        text,
        "${showZh?`<div><div class=\"lang\">中国語</div><div class=\"val\"><span class=\"zh\">${esc(w.z)}</span> ${esc(w.p)}${spk(w.z,'zh')}</div>${yours(guess.zh)}${vt(judge(guess.zh,w.p,true))}</div>`:''}",
        "${showZh?`<div><div class=\"lang\">中国語</div><div class=\"val\"><span class=\"zh\">${esc(w.z)}</span> ${esc(w.p)}${spk(w.z,'zh')}</div>${yours(guess.zh)}${vt(judge(guess.zh,'zh',[w.p]),w.p)}</div>`:''}",
        "Chinese card judging",
    )
    text = replace_once(
        text,
        """<div class="meta">${metaRule}${metaGlyph}</div>
      <div class="rate">""",
        """<div class="meta">${metaRule}${metaGlyph}</div>
      ${cardExamples(w,showVi,showZh)}
      <div class="rate">""",
        "card examples",
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
    text = replace_once(
        text,
        """$$('#fffilter button').forEach(b=>b.onclick=()=>{fff=b.dataset.f;$$('#fffilter button').forEach(x=>x.classList.toggle('on',x===b));renderFF()});""",
        """$$('#fffilter button').forEach(b=>b.onclick=()=>{fff=b.dataset.f;$$('#fffilter button').forEach(x=>x.classList.toggle('on',x===b));renderFF();updateCounts()});""",
        "false-friend count update",
    )
    text = replace_once(
        text,
        """$$('#rulebar button').forEach(b=>b.onclick=()=>{ruleSel=b.dataset.id;quiz=null;renderRules()});""",
        """$$('#rulebar button').forEach(b=>b.onclick=()=>{ruleSel=b.dataset.id;quiz=null;renderRules();updateCounts()});""",
        "rule count update",
    )

    text = replace_once(text, "let pid='v1', selTok=null;", "let pid=(PASSAGES[0]||{}).id||'', selTok=null;", "default passage")
    text = replace_once(text, "const w=p.toks[selTok].w, inDeck=deck().some(x=>x.h===w.h);", "const w=p.toks[selTok].w, inDeck=deck().some(x=>x.id===w.id);", "custom-card membership")
    text = replace_once(text, "custom.push(w);S.set('kb_custom',custom)", "custom.push(w.id);S.set('kb_custom',custom);updateCounts()", "custom-card persistence")
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
        """$$('#gfilter button').forEach(b=>b.onclick=()=>{gfil=b.dataset.p;$$('#gfilter button').forEach(x=>x.classList.toggle('on',x===b));renderGlyph()});""",
        """$$('#gfilter button').forEach(b=>b.onclick=()=>{gfil=b.dataset.p;$$('#gfilter button').forEach(x=>x.classList.toggle('on',x===b));renderGlyph();updateCounts()});""",
        "glyph count update",
    )
    text = replace_once(
        text,
        """const list=GLYPHS.filter(g=>gfil==='all'||pat(g)===gfil);""",
        """const list=filteredGlyphs();""",
        "shared glyph filter",
    )
    text = replace_once(
        text,
        """el.onclick=pick;el.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();pick()}}""",
        """el.onclick=pick;el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();pick()}}""",
        "reading Enter and Space",
    )
    text = replace_once(
        text,
        """if(view==='rules'&&quiz){
    if(!quiz.ans&&n>=0&&n<quiz.opts.length){e.preventDefault();pickRule(quiz.opts[n]);return}
    if(quiz.ans&&e.key==='Enter'){e.preventDefault();quiz=null;renderRules();return}
  }""",
        """if(view==='cards'&&!flipped&&cur&&(e.key==='Enter'||e.key===' ')){e.preventDefault();doFlip();return}
  if(view==='rules'&&quiz){
    if(!quiz.ans&&n>=0&&n<quiz.opts.length){e.preventDefault();pickRule(quiz.opts[n]);return}
    if(quiz.ans&&(e.key==='Enter'||e.key===' ')){e.preventDefault();quiz=null;renderRules();return}
  }""",
        "global card and rule Enter Space",
    )
    text = replace_once(
        text,
        """if(gq.ans&&e.key==='Enter'){e.preventDefault();gq=null;renderGlyph();return}""",
        """if(gq.ans&&(e.key==='Enter'||e.key===' ')){e.preventDefault();gq=null;renderGlyph();return}""",
        "glyph Enter and Space",
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
