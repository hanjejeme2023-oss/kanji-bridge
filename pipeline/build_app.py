"""Rebuild ``app/index.html`` from the frozen prototype plus Stage 5 adapters."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "prototype" / "index.html"
APP = ROOT / "app" / "index.html"


# Credits panel (RELEASE_PLAN §2.6; text by Claude, approved by the user in R0 answer 4, 2026-11-14).
# The only addition to the frozen UI besides the D71/D76 features (Global Rule 10 exception, D78 item 7).
REPOSITORY_URL = "https://github.com/hanjejeme2023-oss/kanji-bridge"
ABOUT_PANEL = (
    '<div class="about hidden" id="aboutpanel" role="region" aria-label="このアプリについて">'
    "<p><b>このアプリについて</b></p>"
    "<p>漢字ブリッジは、日本語と韓国語を知っている人が中国語とベトナム語を学ぶための個人の非営利の学習ツール。</p>"
    "<p><b>データ</b>：Unihan（Unicode, Inc.）、KANJIDIC2・JMdict（EDRDG、CC BY-SA 4.0）、"
    "CC-CEDICT（MDBG、CC BY-SA 4.0）、Wiktionary（Kaikki/Wiktextract 経由、CC BY-SA 4.0）、"
    "FrequencyWords（OpenSubtitles 2018、CC BY-SA 4.0）、libhangul hanja.txt（BSD-3-Clause）、"
    "ivankra/hsk30（MIT）、OpenCC（Apache 2.0）。</p>"
    "<p>This app uses the JMdict and KANJIDIC2 dictionary files. These files are the property of the "
    "Electronic Dictionary Research and Development Group, and are used in conformance with the Group's licence.</p>"
    "<p>データは CC BY-SA 4.0、プログラムは MIT ライセンスで公開している。詳しくは"
    f'<a href="{REPOSITORY_URL}" target="_blank" rel="noopener">{REPOSITORY_URL.removeprefix("https://")}</a>。</p>'
    "<p>例文と一部の意味は AI（Google Gemini）が作ったもので、誤りを含むことがある。</p>"
    "<p>データは集めていない。学習の記録はこのブラウザの中だけに保存される。</p>"
    "</div>"
)
ABOUT_SCRIPT = """/* about (RELEASE_PLAN 2.6): the footer link opens and closes the panel; Esc closes it */
function setAbout(open){$('#aboutpanel').classList.toggle('hidden',!open);$('#about').setAttribute('aria-expanded',open);
  if(open)$('#aboutpanel').scrollIntoView({block:'nearest'})}
$('#about').onclick=()=>setAbout($('#aboutpanel').classList.contains('hidden'));
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('#aboutpanel').classList.contains('hidden')){setAbout(false);$('#about').focus()}});

/* reset */"""


ADAPTERS = r'''/* ---------- data adapters (Stage 5) ---------- */
const KB=window.KB_DATA;
if(!KB)throw new Error('KB_DATA failed to load');
const splitVals=s=>s?s.split(';'):[];
const WC_BY_WORD=new Map();
KB.word_chars.forEach(x=>{if(!WC_BY_WORD.has(x.word_id))WC_BY_WORD.set(x.word_id,[]);WC_BY_WORD.get(x.word_id).push(x)});
const RAW_WORD_BY_ID=new Map(KB.words.map(x=>[x.word_id,x]));
const adaptWord=x=>{
  const w={id:x.word_id,h:x.trad,j:x.jp||x.trad,z:x.simp||x.trad,p:x.pinyin||'',
    jr:x.ja?(x.ja_use==='rare'?`（${x.ja}）`:x.ja):'',
    k:x.ko?(x.ko_use==='rare'?`（${x.ko}）`:x.ko):'',v:x.vi||'',ff:x.false_friend||'',lit:!!x.lit,
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
  const line=r=>({lang:r.lang,label:LANG_LABEL[r.lang],reading:display(r),meaning:r.meaning_ja||'',trap:!!r.is_trap});
  const traps=x.false_friend.split(';');
  return {id:x.word_id,w:x.jp||x.trad,word:w,rows:rows.map(line),traps};
});

const PASSAGE_ROWS=KB.passages.slice().sort((a,b)=>(a.lang==='vi'?0:1)-(b.lang==='vi'?0:1)||
  a.level-b.level||a.passage_id.localeCompare(b.passage_id));
const PASSAGE_N={vi:0,zh:0};
const PASSAGES=PASSAGE_ROWS.map(p=>({id:p.passage_id,lang:p.lang,
  name:`${p.lang==='vi'?'越':'中'} ${++PASSAGE_N[p.lang]}`,tr:p.translation_ja,
  toks:p.tokens.map(t=>t.word_id?{t:t.t,w:WORD_BY_ID.get(t.word_id)}:
    t.gloss_ja?{t:t.t,g:t.gloss_ja}:{t:t.t,x:1})}));

const CHAR_BY_ID=new Map(KB.chars.map(x=>[x.char_id,x]));
const CHAR_NOTES=new Map(KB.char_notes);
const USAGE=new Map(KB.usage.map(x=>[x[0],{zh:x[1],vi:x[2]}]));
const GLYPHS=KB.glyphs.map(row=>{const x=CHAR_BY_ID.get(row[0]);return [x.jp,x.key_char,x.simp,
  splitVals(x.pinyin_all).join(' / '),splitVals(x.ja_on_all).join(' / '),
  splitVals(x.ko_base_all).join(' / '),splitVals(x.vi_all).join(' / '),row[0],row[1],row[2],row[3],row[4]]});
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one prototype match, found {count}")
    return text.replace(old, new, 1)


def replace_between_once(text: str, start: str, end: str, new: str, label: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise RuntimeError(f"{label}: expected one start and end marker")
    left = text.index(start)
    right = text.index(end, left)
    return text[:left] + new + "\n\n" + text[right:]


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
        ".example .translation{color:var(--sub);font-size:13px}\n"
        ".table-test{display:grid;gap:3px;min-width:120px}\n"
        ".table-test input{width:100%;box-sizing:border-box;border:1px solid var(--line);border-radius:8px;padding:8px;background:var(--paper);font:inherit;color:var(--ink)}\n"
        ".table-test input.ok{border-color:var(--right);background:var(--right-soft)}\n"
        ".table-test input.ng{border-color:var(--wrong);background:var(--wrong-soft)}\n"
        ".test-result{font-size:12px;min-height:17px}.test-result.ok{color:var(--right)}.test-result.ng{color:var(--wrong)}\n"
        ".glyph-filters{display:flex;flex-wrap:wrap;gap:6px}\n"
        ".glyph-score{color:var(--sub);font-size:13px;margin:0 0 10px;text-align:right}\n"
        ".grow.quiz{grid-template-columns:1fr 1fr 1.25fr 1.25fr}\n"
        ".grow .usage{grid-column:1/-1;text-align:left;margin-top:12px}\n"
        ".grow .usage summary{cursor:pointer;color:var(--indigo);font-size:13px}\n"
        ".usage-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:12px;padding:16px;background:var(--mist);border-radius:12px}\n"
        ".usage-lang{font-size:12px;color:var(--sub);margin-bottom:7px}.usage-item{font-size:14px;margin-top:8px}\n"
        ".usage-item mark{background:var(--indigo-soft);color:var(--indigo);padding:1px 2px;border-radius:3px}\n"
        ".usage-note{grid-column:1/-1;border-top:1px solid var(--line);padding-top:10px;font-size:13px}\n"
        ".mini-mark{border:none;background:var(--wrong-soft);color:var(--wrong);border-radius:10px;padding:2px 7px;font-size:11px;cursor:pointer;margin-left:6px}\n"
        ".ff-reading{color:var(--sub);font-size:12px;margin-left:4px}\n"
        ".ff-card{max-width:620px;margin:24px auto 0;border:1px solid var(--line);border-radius:20px;padding:34px;text-align:center}\n"
        ".ff-card .front-lines,.ff-card .back-line{margin:20px auto;text-align:left;max-width:440px;line-height:1.9}\n"
        ".ff-card .back-line{color:var(--wrong)}\n"
        ".ff-card .rate{margin-top:28px}\n"
        ".tile .examples{margin-top:18px}.tile .example{font-size:12px}.tile .example .translation{font-size:12px}\n"
        ".unknown-review{margin:22px auto 0;max-width:760px;text-align:center}\n"
        ".unknown-review .review-list{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:8px}\n"
        ".foot-links{display:flex;gap:16px}\n"
        ".about{flex-basis:100%;margin-top:4px;padding:20px 24px;background:var(--mist);border-radius:20px;color:var(--ink);font-size:13px;line-height:1.8}\n"
        ".about p{margin:0 0 8px}.about p:last-child{margin:0}.about a{color:var(--indigo)}\n"
        "@media(max-width:700px){.usage-grid{grid-template-columns:1fr}.usage-note{grid-column:auto}}",
        "passage selector wrapping",
    )
    text = replace_once(
        text,
        "<title>漢字ブリッジ（試作版）</title>",
        "<title>漢字ブリッジ</title>",
        "release window title (R0 answer 4; recorded as a decision in R2)",
    )
    text = replace_once(
        text,
        """<footer>
  <span>試作版。学習記録はこのブラウザにだけ保存されます。</span>
  <button id="reset">記録をリセット</button>
</footer>""",
        f"""<footer>
  <span>学習記録はこのブラウザにだけ保存されます。</span>
  <span class="foot-links"><button id="about" type="button" aria-expanded="false" aria-controls="aboutpanel">このアプリについて</button><button id="reset">記録をリセット</button></span>
  {ABOUT_PANEL}
</footer>""",
        "about link and panel (RELEASE_PLAN 2.6); footer without 「試作版。」 (R2, D79: user input B)",
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
        """<div class="toolbar">
    <div class="seg" id="fffilter">
      <button data-f="all" class="on">すべて</button>
      <button data-f="zh">中国語</button>
      <button data-f="vi">ベトナム語</button>
    </div>
    <div class="sub small">タップすると本当の意味</div>
  </div>
  <div class="tiles" id="fflist"></div>""",
        """<div class="toolbar">
    <div class="seg" id="ffmode">
      <button data-m="list" class="on">一覧</button>
      <button data-m="cards">フラッシュカード</button>
    </div>
    <div class="seg" id="fffilter">
      <button data-f="all" class="on">すべて</button>
      <button data-f="zh">中国語</button>
      <button data-f="vi">ベトナム語</button>
    </div>
    <div class="seg" id="fflang" style="display:none">
      <button data-l="zh" class="on">中国語</button>
      <button data-l="vi">ベトナム語</button>
    </div>
    <div class="sub small" id="ffhelp">タップすると本当の意味</div>
  </div>
  <div class="tiles" id="fflist"></div>""",
        "false-friend list and flashcard controls",
    )
    text = replace_once(
        text,
        '<div class="trans" id="ptrans"></div>\n  <div id="tokdetail"></div>',
        '<div class="trans" id="ptrans"></div>\n  <div class="unknown-review" id="unknownreview"></div>\n  <div id="tokdetail"></div>',
        "reading unknown review list",
    )
    text = replace_once(
        text,
        """<div class="seg" id="gfilter">
      <button data-p="all" class="on">すべて</button>
      <button data-p="diff">3つとも違う</button>
      <button data-p="jz">日本＝中国</button>
      <button data-p="jk">日本＝韓国</button>
    </div>""",
        """<div class="seg glyph-filters" id="gfilter">
      <button data-p="all" class="on">すべて</button>
      <button data-p="diff">3つとも違う</button>
      <button data-p="jz">日本＝中国</button>
      <button data-p="jk">日本＝韓国</button>
      <button data-p="level-1">レベル1</button>
      <button data-p="level-2">レベル2</button>
      <button data-p="level-3">レベル3</button>
      <button data-p="level-4">レベル4</button>
      <button data-p="level-5">レベル5</button>
      <button data-p="level-6">レベル6</button>
      <button data-p="level-7">レベル7</button>
      <button data-p="wrong">間違えた字だけ</button>
    </div>""",
        "glyph level and wrong filters",
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
}
const resultValue=v=>v===1||v===0?v:null;
function cleanTestResults(value,knownKeys=null){
  if(!value||typeof value!=='object'||Array.isArray(value))return {};
  return Object.fromEntries(Object.entries(value).filter(([key,row])=>(!knownKeys||knownKeys.has(key))&&row&&typeof row==='object'&&!Array.isArray(row))
    .map(([key,row])=>[key,Object.fromEntries(['zh','vi'].filter(lang=>resultValue(row[lang])!==null).map(lang=>[lang,row[lang]]))])
    .filter(([,row])=>Object.keys(row).length));
}
let TABLE_TEST_CELLS=new Map();
function beginTableTest(){TABLE_TEST_CELLS=new Map()}
function tableTestCell(key,lang,readings,viAlt,saved,several,onAnswer){
  const id=`${key}:${lang}`,state=resultValue(saved),values=(readings||[]).filter(Boolean);
  TABLE_TEST_CELLS.set(id,{lang,readings:values,viAlt:viAlt||[],several:!!several,onAnswer});
  return `<div class="table-test"><div class="tone-hint">${esc(toneHint(lang,values))}</div><input data-test-cell="${esc(id)}" class="${state===1?'ok':state===0?'ng':''}" autocomplete="off" spellcheck="false"><div class="test-result"></div></div>`;
}
function focusNextTest(input){let all=[...document.querySelectorAll('input[data-test-cell]')];const i=all.indexOf(input);
  if(i>=0&&!all[i+1]){for(const job of CHUNKS.values())if(job.box.contains(input))appendChunk(job,job.size);all=[...document.querySelectorAll('input[data-test-cell]')]}
  if(i>=0&&all[i+1])all[i+1].focus()}
function answerTableCell(input){
  const cfg=TABLE_TEST_CELLS.get(input.dataset.testCell);if(!cfg||!input.value.trim())return null;
  const right=judge(input.value,cfg.lang,cfg.readings,cfg.viAlt,cfg.several)==='ok',value=right?1:0;
  input.classList.remove('ok','ng');input.classList.add(right?'ok':'ng');input.dataset.judged='1';
  const out=input.parentElement.querySelector('.test-result');out.className=`test-result ${right?'ok':'ng'}`;out.textContent=right?'正解':cfg.readings.join(' / ');
  cfg.onAnswer(value,input.value);return value;
}
function bindTableTests(root){
  const inputs=[...root.querySelectorAll('input[data-test-cell]')];
  inputs.forEach(input=>{input.oninput=()=>{delete input.dataset.judged;const out=input.parentElement.querySelector('.test-result');out.className='test-result';out.textContent=''};
    input.onblur=()=>{if(!input.dataset.judged)answerTableCell(input)};
    input.onkeydown=e=>{if(e.key==='Enter'||(e.key===' '&&input.dataset.judged)){e.preventDefault();if(input.dataset.judged)focusNextTest(input);else answerTableCell(input)}};
  });
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
        """$$('#nav button').forEach(b=>b.onclick=()=>{
  view=b.dataset.v;stopSpeech();
  $$('#nav button').forEach(x=>x.classList.toggle('on',x===b));
  $$('main>section').forEach(s=>s.classList.toggle('hidden',s.id!=='v-'+view));
  render();
});""",
        """$$('#nav button').forEach(b=>b.onclick=()=>{
  if(view==='read'&&b.dataset.v!=='read')markPassageRead(pid);
  view=b.dataset.v;stopSpeech();
  $$('#nav button').forEach(x=>x.classList.toggle('on',x===b));
  $$('main>section').forEach(s=>s.classList.toggle('hidden',s.id!=='v-'+view));
  render();
});""",
        "reading leave mark on tab switch",
    )
    text = replace_once(
        text,
        """function render(){({cards:renderCards,rules:renderRules,ff:renderFF,read:renderRead,glyph:renderGlyph})[view]();topStat()}""",
        """function clearUnknown(wordId){const rows=S.get('kb_unknown',[]),next=Array.isArray(rows)?rows.filter(id=>id!==wordId):[];S.set('kb_unknown',next)}
function filteredGlyphs(){return GLYPHS.filter(g=>{
  if(gfil==='all')return true;
  if(gfil==='wrong')return Object.values(gresults[g[7]]||{}).some(value=>value===0);
  if(gfil.startsWith('level-'))return g[9]===+gfil.slice(6);
  return pat(g)===gfil;
})}
function updateCounts(){
  const counts={cards:deck().filter(targetOk).length,
    rules:(RULES.find(x=>x.id===ruleSel)||{ex:[]}).ex.length,
    ff:ffmode==='cards'?ffPool(fflang).length:FF.filter(f=>fff==='all'||f.traps.includes(fff)).length,
    read:PASSAGES.length,glyph:filteredGlyphs().length};
  Object.entries(counts).forEach(([key,value])=>{const el=$(`#count-${key}`);if(el)el.textContent=value.toLocaleString('ja-JP')});
}
/* chunked list rendering (R1, RELEASE_PLAN 1.2): the first screen at once, the rest in short
   idle-time steps; the final DOM equals one innerHTML of the whole list */
const CHUNKS=new Map();
function cancelChunks(name){(name?[name]:[...CHUNKS.keys()]).forEach(k=>{const job=CHUNKS.get(k);if(job){clearTimeout(job.timer);CHUNKS.delete(k)}})}
function appendChunk(job,count){const end=Math.min(job.items.length,job.next+count);if(end<=job.next)return;
  const t=document.createElement('template');t.innerHTML=job.items.slice(job.next,end).map(job.row).join('');
  job.bind(t.content);job.box.appendChild(t.content);job.next=end}
function chunkStep(name){const job=CHUNKS.get(name);if(!job)return;const now=performance.now();
  /* the gap since the last step includes the browser's layout of that step: aim at about 50 ms per step */
  if(job.last)job.size=Math.max(20,Math.min(500,Math.round(job.size*50/Math.max(now-job.last,1))));job.last=now;
  appendChunk(job,job.size);
  if(job.next<job.items.length)job.timer=setTimeout(()=>chunkStep(name),0);else CHUNKS.delete(name)}
function renderChunked(name,box,lead,items,row,bind){
  cancelChunks(name);const first=Math.min(items.length,30);
  box.innerHTML=lead+items.slice(0,first).map(row).join('');bind(box);
  if(first<items.length){const job={box,items,row,bind,next:first,size:100,last:0,timer:0};CHUNKS.set(name,job);job.timer=setTimeout(()=>chunkStep(name),0)}}
function flushChunks(name){(name?[name]:[...CHUNKS.keys()]).forEach(k=>{const job=CHUNKS.get(k);if(!job)return;clearTimeout(job.timer);appendChunk(job,job.items.length);CHUNKS.delete(k)})}
function ensureChunk(name,index){const job=CHUNKS.get(name);if(job&&index>=job.next)appendChunk(job,index+1-job.next)}
function render(){cancelChunks();({cards:renderCards,rules:renderRules,ff:renderFF,read:renderRead,glyph:renderGlyph})[view]();topStat();updateCounts()}""",
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
    text = replace_once(
        text,
        "function doFlip(){guess.vi=($('#gvi')||{}).value||'';guess.zh=($('#gzh')||{}).value||'';flipped=true;renderCards();",
        "function doFlip(){guess.vi=($('#gvi')||{}).value||'';guess.zh=($('#gzh')||{}).value||'';\n"
        "  const viRight=target==='zh'||judge(guess.vi,'vi',[cur.v],cur.va||[])==='ok',zhRight=target==='vi'||judge(guess.zh,'zh',[cur.p])==='ok';\n"
        "  if(viRight&&zhRight)clearUnknown(cur.id);flipped=true;renderCards();",
        "correct card clears unknown mark",
    )

    text = replace_once(
        text,
        """$$('#rulebar button').forEach(b=>b.onclick=()=>{ruleSel=b.dataset.id;quiz=null;renderRules()});""",
        """$$('#rulebar button').forEach(b=>b.onclick=()=>{ruleSel=b.dataset.id;quiz=null;renderRules();updateCounts()});""",
        "rule count update",
    )
    text = replace_between_once(
        text,
        "/* 2. rules */",
        "/* 3. false friends */",
        r'''/* 2. rules */
let ruleSel='k', rprog=S.get('kb_rules',{}), quiz=null, ruleTest=false;
let ruleResults=cleanTestResults(S.get('kb_ruletest',{}));
function saveRuleResult(key,lang,value){const row=ruleResults[key]||{};row[lang]=value;ruleResults[key]=row;S.set('kb_ruletest',ruleResults)}
function renderRules(){
  beginTableTest();
  $('#rulebar').innerHTML=RULES.map(r=>{const d=(rprog[r.id]||[]).length;
    return `<button class="${r.id===ruleSel?'on':''}" data-id="${r.id}"><div class="r"><span class="ko">${r.kr}</span> → ${r.vi.map(v=>'-'+v).join('/')}</div><div class="p">${d}/${r.ex.length}</div></button>`}).join('');
  $$('#rulebar button').forEach(b=>b.onclick=()=>{ruleSel=b.dataset.id;quiz=null;renderRules();updateCounts()});
  const r=RULES.find(x=>x.id===ruleSel);
  if(!quiz)newQuiz(r);
  const e=quiz.e;
  const rows=r.ex.map(x=>{const key=`${r.id}:${x[0]}`,stored=ruleResults[key]||{};
    return `<tr><td class="han" style="font-size:22px">${x[0]}</td><td class="ko">${x[1]}</td><td>${x[2]}</td><td>${ruleTest?tableTestCell(key,'vi',[x[3]],[],stored.vi,false,(value)=>saveRuleResult(key,'vi',value)):`<b style="font-weight:600">${esc(x[3])}</b>${spk(x[3],'vi')}`}</td><td class="sub">${ruleTest?tableTestCell(key,'zh',[x[4]],[],stored.zh,false,(value)=>saveRuleResult(key,'zh',value)):`${esc(x[4])}${spk(x[0],'zh')}`}</td></tr>`}).join('');
  $('#ruledetail').innerHTML=`
    <div class="rulehead"><h2>パッチム <span class="ko">${r.kr}</span> は ${r.vi.map(v=>'-'+v).join(' / ')} になる</h2>
      <p>日本語では${esc(r.jp)}。中国語では${esc(r.zh)}。</p></div>
    <div class="qcard">
      <div class="giant han">${e[0]}</div>
      <div class="readings"><span class="ko">${e[1]}</span><span class="sub">${e[2]}</span></div>
      <div class="opts">${quiz.opts.map((o,i)=>`<button class="pill ${quiz.ans?(o===e[3]?'right':(o===quiz.ans?'wrong':'')):''}" data-o="${esc(o)}"><span class="key">${i+1}</span>${esc(o)}</button>`).join('')}</div>
      <div class="after">${quiz.ans?`<div style="margin-bottom:16px" class="small sub">ベトナム語 ${esc(e[3])}${spk(e[3],'vi')}　　中国語 ${esc(e[4])}${spk(e[0],'zh')}</div><button class="pill dark" id="qnext">次へ<span class="key">Enter</span></button>`:'<span class="sub small">ベトナム語の読みはどれ？</span>'}</div>
    </div>
    <div style="margin:24px 0 10px;text-align:right"><button class="pill" id="ruletest" type="button">${ruleTest?'テストをやめる':'テストする'}</button></div>
    <details ${ruleTest||S.get('kb_ex_open',false)?'open':''}><summary>このルールの例をすべて見る</summary>
      <table><tr><th>漢字</th><th>韓国語</th><th>日本語</th><th>ベトナム語</th><th>中国語</th></tr>${rows}</table></details>`;
  $$('#ruledetail .opts button').forEach(b=>b.onclick=()=>pickRule(b.dataset.o));
  $('#ruledetail details').ontoggle=ev=>{if(!ruleTest)S.set('kb_ex_open',ev.target.open)};
  $('#ruletest').onclick=()=>{ruleTest=!ruleTest;renderRules()};
  if(ruleTest)bindTableTests($('#ruledetail'));
  const n=$('#qnext');if(n){n.onclick=()=>{quiz=null;renderRules()};n.focus({preventScroll:true})}
}
function pickRule(o){
  if(quiz.ans)return;quiz.ans=o;
  if(autoplay){stopSpeech();speak(quiz.e[3],'vi',null,true)}
  if(o===quiz.e[3]){const a=rprog[ruleSel]||[];if(!a.includes(quiz.e[0]))a.push(quiz.e[0]);rprog[ruleSel]=a;S.set('kb_rules',rprog)}
  renderRules();
}
function newQuiz(r){
  const done=rprog[r.id]||[];const pool=r.ex.filter(e=>!done.includes(e[0]));const src=pool.length?pool:r.ex;
  const e=src[Math.floor(Math.random()*src.length)];
  const stem=e[3].replace(/(ng|nh|ch|c|p|t|n|m)$/,'');
  const alts=shuffle(['c','p','t','n','m','ng'].filter(f=>!r.vi.includes(f))).slice(0,2).map(f=>stem+f);
  quiz={e,opts:shuffle([e[3],...alts]),ans:null};
}''',
        "sound-rule typing test",
    )

    text = replace_between_once(
        text,
        "/* 3. false friends */",
        "/* 5. glyph */",
        r'''/* 3. false friends */
function cleanFFStats(value){
  if(!value||typeof value!=='object'||Array.isArray(value))return {};
  return Object.fromEntries(Object.entries(value).filter(([,row])=>row&&typeof row==='object'&&!Array.isArray(row))
    .map(([key,row])=>[key,{miss:Number.isInteger(row.miss)&&row.miss>=0?row.miss:0,ok:Number.isInteger(row.ok)&&row.ok>=0?row.ok:0}]));
}
function orderedFFPool(entries,lang,stats){return entries.filter(f=>f.traps.includes(lang)).slice().sort((a,b)=>{
  const ar=stats[`${a.id}:${lang}`],br=stats[`${b.id}:${lang}`],am=(ar||{}).miss||0,bm=(br||{}).miss||0;
  return bm-am||Number(!!ar)-Number(!!br)||a.id.localeCompare(b.id);
})}
const newFFRoundIds=(entries,lang,stats)=>orderedFFPool(entries,lang,stats).slice(0,20).map(f=>f.id);
const appendFFMiss=(queue,id)=>queue.concat([id]);
const ffExampleRow=(examples,wordId,lang)=>examples.get(`${wordId}:${lang}:ff`)||examples.get(`${wordId}:${lang}:card`)||null;
function ffLine(row){const reading=row.reading?(row.meaning&&!/^（.*）$/.test(row.reading)?`（${row.reading}）`:row.reading):'';
  return `<div><b>${row.label}</b>${esc(row.meaning)}${reading?`<span class="ff-reading">${esc(reading)}</span>`:''}</div>`}
function ffExampleMarkup(f,lang){const x=ffExampleRow(EXAMPLES,f.id,lang);if(!x)return'';
  return `<div class="example"><div class="small sub">${lang==='zh'?'中国語':'ベトナム語'}</div><div class="${lang==='zh'?'zh':''}">${markedTarget(x)}</div>${lang==='zh'?`<div>${esc(x.pinyin)}</div>`:''}<div class="translation">${esc(x.translation)}</div></div>`;
}
function ffExamples(f,onlyLang=null){const langs=onlyLang?[onlyLang]:['zh','vi'],rows=langs.map(lang=>ffExampleMarkup(f,lang)).filter(Boolean);return rows.length?`<div class="examples">${rows.join('')}</div>`:''}
function passageChecked(p,reads,unknown){return reads.has(p.id)&&!p.toks.some(t=>t.w&&unknown.has(t.w.id))}

let ffmode='list',fff='all',fflang='zh',ffopen=new Set(),ffstats=cleanFFStats(S.get('kb_ffcard',{})),ffround=null,ffflipped=false;
const ffPool=lang=>orderedFFPool(FF,lang,ffstats);
function startFFRound(){const ids=newFFRoundIds(FF,fflang,ffstats);ffround={ids,queue:ids.slice()};ffflipped=false}
function syncFFControls(){
  $$('#ffmode button').forEach(b=>b.classList.toggle('on',b.dataset.m===ffmode));
  $('#fffilter').style.display=ffmode==='list'?'flex':'none';$('#fflang').style.display=ffmode==='cards'?'flex':'none';
  $$('#fffilter button').forEach(b=>b.classList.toggle('on',b.dataset.f===fff));
  $$('#fflang button').forEach(b=>b.classList.toggle('on',b.dataset.l===fflang));
  $('#ffhelp').textContent=ffmode==='list'?'タップすると本当の意味':'';
}
$$('#ffmode button').forEach(b=>b.onclick=()=>{ffmode=b.dataset.m;if(ffmode==='cards'&&!ffround)startFFRound();renderFF();updateCounts()});
$$('#fffilter button').forEach(b=>b.onclick=()=>{fff=b.dataset.f;renderFF();updateCounts()});
$$('#fflang button').forEach(b=>b.onclick=()=>{fflang=b.dataset.l;startFFRound();renderFF();updateCounts()});
const FF_BY_ID=new Map(FF.map(f=>[f.id,f]));
function ffTile(f){const o=ffopen.has(f.id);return `<div class="tile ${o?'open':''}" data-w="${f.id}" role="button" tabindex="0" aria-expanded="${o}">
    <div class="w han">${esc(f.w)}</div><div class="l">${f.rows.filter(row=>!row.trap).map(ffLine).join('')}</div>
    ${o?`<div class="trap">${f.rows.filter(row=>row.trap).map(ffLine).join('')}</div>${ffExamples(f)}`:'<div class="hint">実は…</div>'}</div>`}
function bindFFTiles(root){root.querySelectorAll('.tile').forEach(b=>{const toggle=()=>toggleFFTile(b.dataset.w);
    b.onclick=toggle;b.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();toggle()}}})}
function toggleFFTile(id){ffopen.has(id)?ffopen.delete(id):ffopen.add(id);
  const old=$(`#fflist .tile[data-w="${id}"]`),f=FF_BY_ID.get(id);
  if(old&&f){const t=document.createElement('template');t.innerHTML=ffTile(f);bindFFTiles(t.content);const tile=t.content.firstElementChild;old.replaceWith(tile);tile.focus();return}
  renderFF();const next=$(`#fflist .tile[data-w="${id}"]`);if(next)next.focus()}
function renderFFList(){
  const list=FF.filter(f=>fff==='all'||f.traps.includes(fff));$('#fflist').className='tiles';
  renderChunked('ff',$('#fflist'),'',list,ffTile,bindFFTiles);
}
function renderFFCard(){
  if(!ffround||!ffround.queue.length)startFFRound();const id=(ffround.queue||[])[0],f=FF.find(row=>row.id===id);$('#fflist').className='';
  if(!f){$('#fflist').innerHTML='<div class="empty">該当する単語はない</div>';return}
  const target=f.rows.find(row=>row.lang===fflang&&row.trap),others=f.rows.filter(row=>row.lang!==fflang);
  $('#fflist').innerHTML=`<div class="ff-card" data-ff-card="${f.id}" role="button" tabindex="0"><div class="giant han">${esc(f.w)}</div>
    ${ffflipped?`<div class="back-line">${target?ffLine(target):''}${target?spk(fflang==='zh'?f.word.z:target.reading,fflang):''}</div>${ffExamples(f,fflang)}
      <div class="rate"><button class="pill" data-ff-rate="miss">まだ<span class="key">1</span></button><button class="pill dark" data-ff-rate="ok">わかった<span class="key">2</span></button></div>`:
      `<div class="front-lines">${others.map(ffLine).join('')}</div><div class="hint">実は…</div>`}</div>`;
  const card=$('[data-ff-card]');if(!ffflipped){const flip=()=>{ffflipped=true;renderFF()};card.onclick=flip;card.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();flip()}}}
  $$('[data-ff-rate]').forEach(b=>b.onclick=e=>{e.stopPropagation();rateFFCard(b.dataset.ffRate==='ok')});
}
function rateFFCard(right){if(!ffround||!ffflipped||!ffround.queue.length)return;const id=ffround.queue[0],key=`${id}:${fflang}`,row=ffstats[key]||{miss:0,ok:0};right?row.ok++:row.miss++;ffstats[key]=row;S.set('kb_ffcard',ffstats);
  const rest=ffround.queue.slice(1);ffround.queue=right?rest:appendFFMiss(rest,id);ffflipped=false;if(!ffround.queue.length)startFFRound();renderFF()}
function renderFF(){cancelChunks('ff');syncFFControls();ffmode==='cards'?renderFFCard():renderFFList()}
function showFFWord(wordId){ffmode='list';fff='all';ffopen=new Set([wordId]);view='ff';stopSpeech();$$('#nav button').forEach(x=>x.classList.toggle('on',x.dataset.v==='ff'));$$('main>section').forEach(s=>s.classList.toggle('hidden',s.id!=='v-ff'));render();ensureChunk('ff',FF.findIndex(f=>f.id===wordId));const tile=$(`#fflist .tile[data-w="${wordId}"]`);if(tile)tile.focus()}

/* 4. reading */
const PASSAGE_IDS=new Set(PASSAGES.map(p=>p.id));
let pid=(PASSAGES[0]||{}).id||'',selTok=null;
let readIds=new Set((Array.isArray(S.get('kb_read',[]))?S.get('kb_read',[]):[]).filter(id=>PASSAGE_IDS.has(id)));
const unknownIds=()=>new Set((Array.isArray(S.get('kb_unknown',[]))?S.get('kb_unknown',[]):[]).filter(id=>ALL_WORD_IDS.has(id)));
function markUnknown(wordId){const ids=unknownIds();ids.add(wordId);S.set('kb_unknown',[...ids])}
function markPassageRead(passageId){if(!PASSAGE_IDS.has(passageId))return;readIds.add(passageId);S.set('kb_read',[...readIds])}
$('#showann').onchange=renderRead;
function renderRead(){
  const unknown=unknownIds();
  $('#psel').innerHTML=PASSAGES.map(p=>`<button data-p="${p.id}" class="${p.id===pid?'on':''}">${p.name}${passageChecked(p,readIds,unknown)?' ✓':''}</button>`).join('');
  $$('#psel button').forEach(b=>b.onclick=()=>{if(b.dataset.p!==pid){markPassageRead(pid);pid=b.dataset.p;selTok=null}renderRead()});
  const p=PASSAGES.find(x=>x.id===pid),ann=$('#showann').checked;
  $('#passage').className='passage '+(p.lang==='zh'?'zh':'');
  $('#passage').innerHTML=p.toks.map((t,i)=>{
    if(t.x)return'';const nx=p.toks[i+1],tail=nx&&nx.x?`<span class="pt">${esc(nx.t)}</span>`:'';
    if(t.g)return `<span class="tok func"><span class="w"><span class="s">${esc(t.t)}</span>${tail}</span><span class="a">${ann?esc(t.g):''}</span></span>`;
    const a=p.lang==='vi'?t.w.h:`${t.w.jr}　${t.w.k}`;
    return `<span class="tok sino ${selTok===i?'sel':''}" data-i="${i}"><span class="w"><span class="s" tabindex="0" role="button">${esc(t.t)}</span>${tail}</span><span class="a ${p.lang==='vi'?'han zh':''}">${ann?esc(a):''}</span></span>`;
  }).join('');
  const sent=p.lang==='vi'?p.toks.map(t=>t.t).join(' ').replace(/ ([.,])/g,'$1'):p.toks.map(t=>t.t).join('');$('#ptrans').innerHTML=`${esc(p.tr)}${spk(sent,p.lang)}`;
  $$('.tok.sino .s').forEach(el=>{const pick=()=>{selTok=+el.closest('.tok').dataset.i;markUnknown(p.toks[selTok].w.id);renderRead()};el.onclick=pick;el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();pick()}}});
  const marked=[],seen=new Set();p.toks.forEach((t,i)=>{if(t.w&&unknownIds().has(t.w.id)&&!seen.has(t.w.id)){seen.add(t.w.id);marked.push([i,t.w])}});
  $('#unknownreview').innerHTML=marked.length?`<div class="sub small">わからない</div><div class="review-list">${marked.map(([i,w])=>`<button class="pill" data-review-i="${i}">${esc(w.j||w.h)}</button>`).join('')}</div>`:'';
  $$('[data-review-i]').forEach(b=>b.onclick=()=>{selTok=+b.dataset.reviewI;renderRead()});
  const d=$('#tokdetail');if(selTok===null){d.innerHTML='<div class="empty">下線の単語をタップすると、4つの言語の対応が出る</div>';return}
  const w=p.toks[selTok].w,inDeck=deck().some(x=>x.id===w.id);d.innerHTML=`<div class="sheet">
    <div class="top"><div class="han" style="font-size:44px;line-height:1.1">${esc(w.h)}</div><button class="pill ${inDeck?'':'dark'}" id="addcard" ${inDeck?'disabled':''}>${inDeck?'カードに追加済み':'カードに追加'}</button></div>
    <div class="grid"><div class="cell"><span>日本語</span><div>${esc(w.jr)}</div></div><div class="cell"><span>韓国語</span><div class="ko">${esc(w.k)}</div></div>
      <div class="cell"><span>中国語</span><div><span class="zh">${esc(w.z)}</span> ${esc(w.p)}${w.p?spk(w.z,'zh'):''}</div></div><div class="cell"><span>ベトナム語</span><div>${esc(w.v)}${w.v?spk(w.v,'vi'):''}</div></div></div>
    ${w.note?`<p class="sub small" style="margin:16px 0 0">${esc(w.note)}</p>`:''}<div style="margin-top:14px">${ruleTags(w)}</div></div>`;
  if(!inDeck)$('#addcard').onclick=()=>{custom.push(w.id);S.set('kb_custom',custom);updateCounts();renderRead();topStat()};
}''',
        "false-friend cards and reading unknown marks",
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
    text = replace_between_once(
        text,
        "/* 5. glyph */",
        "/* keyboard */",
        r'''/* 5. glyph */
let gmode='list', gfil='all';
const GLYPH_IDS=new Set(GLYPHS.map(g=>g[7]));
let gresults=cleanTestResults(S.get('kb_glyphquiz',{}),GLYPH_IDS),glyphOpened=new Set();
const pat=g=>g[0]===g[2]&&g[0]!==g[1]?'jz':g[0]===g[1]&&g[0]!==g[2]?'jk':g[0]!==g[1]&&g[1]!==g[2]&&g[0]!==g[2]?'diff':'same';
const glyphTargets=(g,lang)=>g[lang==='zh'?10:11]||[];
function glyphDisplay(g,lang){const targets=glyphTargets(g,lang),all=splitVals(g[lang==='zh'?3:6]);return [...targets,...all.filter(x=>!targets.includes(x))].join(' / ')}
const glyphViAlt=g=>[...new Set(g[8].flatMap(id=>(WORD_BY_ID.get(id)||{}).va||[]))];
function glyphScore(){let ok=0,answered=0;filteredGlyphs().forEach(g=>{const row=gresults[g[7]]||{};['zh','vi'].forEach(lang=>{if(glyphTargets(g,lang).length&&resultValue(row[lang])!==null){answered++;if(row[lang]===1)ok++}})});return {ok,answered}}
function updateGlyphScore(){const el=$('#glyphscore');if(el){const score=glyphScore();el.textContent=`${score.ok} / ${score.answered} 正解`}}
function markPosition(text,position){const chars=[...String(text)],i=position-1;if(i<0||i>=chars.length)return esc(text);return `${esc(chars.slice(0,i).join(''))}<mark>${esc(chars[i])}</mark>${esc(chars.slice(i+1).join(''))}`}
function markSyllable(text,position){const parts=String(text).split(' '),i=position-1;if(i<0||i>=parts.length)return esc(text);return parts.map((part,n)=>n===i?`<mark>${esc(part)}</mark>`:esc(part)).join(' ')}
const ffMark=w=>w.ff?`<button class="mini-mark" type="button" data-ff-word="${w.id}">偽の友達</button>`:'';
function usageBody(g){const use=USAGE.get(g[7])||{zh:[],vi:[]},note=CHAR_NOTES.get(g[7])||'';
  const zh=use.zh.length?use.zh.map(([id,pos,pinyin])=>{const w=WORD_BY_ID.get(id),raw=RAW_WORD_BY_ID.get(id);return `<div class="usage-item"><span class="zh">${markPosition((raw.simp||raw.trad),pos)}</span>${ffMark(w)}<br>${markSyllable(pinyin,pos)}</div>`}).join(''):'<div class="sub">例なし</div>';
  const vi=use.vi.length?use.vi.map(([id,pos])=>{const w=WORD_BY_ID.get(id),raw=RAW_WORD_BY_ID.get(id);return `<div class="usage-item">${markPosition((raw.jp||raw.trad),pos)}${raw.lit?'<span class="tag off">文語</span>':''}${ffMark(w)}<br>${markSyllable(raw.vi||'',pos)}</div>`}).join(''):'<div class="sub">例なし</div>';
  return `<div class="usage-grid"><div><div class="usage-lang">中国語</div>${zh}</div><div><div class="usage-lang">ベトナム語</div>${vi}</div>${note?`<div class="usage-note">${esc(note)}</div>`:''}</div>`;
}
function usagePanel(g){const open=gmode==='quiz'&&glyphOpened.has(g[7]);return `<details class="usage" data-usage="${g[7]}" ${open?'open':''}><summary>使われ方</summary><div class="usage-body">${open?usageBody(g):''}</div></details>`}
function bindUsagePanels(root=$('#glyphbox')){
  root.querySelectorAll('details[data-usage]').forEach(d=>d.ontoggle=()=>{if(d.open&&!d.querySelector('.usage-body').innerHTML){const g=GLYPHS.find(row=>row[7]===d.dataset.usage);d.querySelector('.usage-body').innerHTML=usageBody(g)}});
  $('#glyphbox').onclick=e=>{const b=e.target.closest&&e.target.closest('[data-ff-word]');if(!b)return;e.preventDefault();e.stopPropagation();showFFWord(b.dataset.ffWord)};
}
function clearGlyphWords(g,lang,input){const parts=input.split(/[,/，／、]/).map(x=>x.trim()).filter(Boolean);g[8].forEach(id=>{const w=WORD_BY_ID.get(id);if(!w)return;const accepted=lang==='zh'?[w.p]:[w.v],alts=lang==='vi'?(w.va||[]):[];if(parts.some(part=>judge(part,lang,accepted,alts)==='ok'))clearUnknown(id)})}
function saveGlyphResult(g,lang,value,input){const row=gresults[g[7]]||{};row[lang]=value;gresults[g[7]]=row;S.set('kb_glyphquiz',gresults);if(value===1)clearGlyphWords(g,lang,input);glyphOpened.add(g[7]);
  const d=$(`#glyphbox details[data-usage="${g[7]}"]`);if(d){d.open=true;const body=d.querySelector('.usage-body');if(!body.innerHTML)body.innerHTML=usageBody(g)}updateGlyphScore();if(gfil==='wrong'&&value===1){renderGlyph();updateCounts()}}
function glyphListRow(g){return `<div class="grow">
  <div><div class="g han">${g[0]}</div><div class="lbl">${g[4]}</div></div>
  <div><div class="g han ko">${g[1]}</div><div class="lbl ko">${g[5]}</div></div>
  <div class="zhcol"><div class="g han zh">${g[2]}</div><div class="lbl">${esc(glyphDisplay(g,'zh'))}${glyphTargets(g,'zh').length?spk(g[2],'zh'):''}</div></div>
  <div class="rd">${esc(glyphDisplay(g,'vi'))}${glyphTargets(g,'vi').length?spk(glyphTargets(g,'vi').join(', '),'vi'):''}</div>${usagePanel(g)}</div>`}
function glyphQuizRow(g){const stored=gresults[g[7]]||{},py=glyphTargets(g,'zh'),vi=glyphTargets(g,'vi');return `<div class="grow quiz">
  <div><div class="g han">${g[0]}</div><div class="lbl">${g[4]}</div></div>
  <div><div class="g han ko">${g[1]}</div><div class="lbl ko">${g[5]}</div></div>
  <div class="zhcol"><div class="g han zh">${g[2]}</div>${py.length?tableTestCell(g[7],'zh',py,[],stored.zh,true,(value,input)=>saveGlyphResult(g,'zh',value,input)):`<div class="rd">${esc(glyphDisplay(g,'zh'))}</div>`}</div>
  <div>${vi.length?tableTestCell(g[7],'vi',vi,glyphViAlt(g),stored.vi,true,(value,input)=>saveGlyphResult(g,'vi',value,input)):`<div class="rd">${esc(glyphDisplay(g,'vi'))}</div>`}</div>${usagePanel(g)}</div>`}
$$('#gmode button').forEach(b=>b.onclick=()=>{gmode=b.dataset.g;$$('#gmode button').forEach(x=>x.classList.toggle('on',x===b));renderGlyph();updateCounts()});
$$('#gfilter button').forEach(b=>b.onclick=()=>{gfil=b.dataset.p;$$('#gfilter button').forEach(x=>x.classList.toggle('on',x===b));renderGlyph();updateCounts()});
function renderGlyph(){
  beginTableTest();const list=filteredGlyphs(),quiz=gmode==='quiz';
  const head='<div class="ghead"><span>日本</span><span>韓国・繁体</span><span>中国・簡体</span><span>読み</span></div>';
  renderChunked('glyph',$('#glyphbox'),(quiz?`<div class="glyph-score" id="glyphscore"></div>`:'')+(list.length?head:'<div class="empty">該当する字はない</div>'),
    list,quiz?glyphQuizRow:glyphListRow,root=>{if(quiz)bindTableTests(root);bindUsagePanels(root)});
  if(quiz)updateGlyphScore();
}''',
        "glyph rows typing quiz and usage",
    )
    text = replace_once(
        text,
        """if(view==='rules'&&quiz){
    if(!quiz.ans&&n>=0&&n<quiz.opts.length){e.preventDefault();pickRule(quiz.opts[n]);return}
    if(quiz.ans&&e.key==='Enter'){e.preventDefault();quiz=null;renderRules();return}
  }""",
        """if(view==='cards'&&!flipped&&cur&&(e.key==='Enter'||e.key===' ')){e.preventDefault();doFlip();return}
  if(view==='ff'&&ffmode==='cards'){
    if(!ffflipped&&(e.key==='Enter'||e.key===' ')){e.preventDefault();ffflipped=true;renderFF();return}
    if(ffflipped&&(e.key==='1'||e.key==='2')){e.preventDefault();rateFFCard(e.key==='2');return}
  }
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
        """  if(view==='glyph'&&gmode==='quiz'&&gq){
    if(!gq.ans&&n>=0&&n<gq.opts.length){e.preventDefault();pickGlyph(gq.opts[n]);return}
    if(gq.ans&&(e.key==='Enter'||e.key===' ')){e.preventDefault();gq=null;renderGlyph();return}
  }
""",
        "",
        "remove old glyph multiple-choice shortcuts",
    )

    text = replace_once(
        text,
        "srs={};custom=[];rprog={};gscore={ok:0,n:0};doneToday=0;\n  S.set('kb_srs',{});S.set('kb_custom',[]);S.set('kb_rules',{});S.set('kb_glyph',gscore);",
        "srs={};custom=[];rprog={};ruleResults={};gresults={};glyphOpened.clear();ffstats={};ffround=null;ffflipped=false;readIds.clear();doneToday=0;newToday={date:localDay(),ids:[]};\n  S.set('kb_srs',{});S.set('kb_custom',[]);S.set('kb_newtoday',newToday);S.set('kb_rules',{});S.set('kb_glyph',{});S.set('kb_ruletest',{});S.set('kb_glyphquiz',{});S.set('kb_unknown',[]);S.set('kb_read',[]);S.set('kb_ffcard',{});",
        "reset Part C and D state",
    )
    text = replace_once(text, "/* reset */", ABOUT_SCRIPT, "about panel script")
    return text


def main() -> None:
    APP.parent.mkdir(parents=True, exist_ok=True)
    APP.write_text(build(), encoding="utf-8", newline="\n")
    print(f"Built {APP.relative_to(ROOT)} from frozen prototype")


if __name__ == "__main__":
    main()
