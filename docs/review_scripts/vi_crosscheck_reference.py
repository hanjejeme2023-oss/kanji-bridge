"""REFERENCE ONLY (Claude, Stage 1 review, 2026-11-04). Exploration script that produced the numbers in docs/STAGE1_REVIEW.md.
It is evidence for the rules in DECISIONS D24-D28, NOT pipeline code: Codex re-implements the rules in pipeline/ with tests.
Run from the repo root with a Python that has pandas: python docs/review_scripts/vi_crosscheck_reference.py
"""
import gzip, json, re, sys, zipfile, random, unicodedata, collections, itertools
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')
def nfc(s): return unicodedata.normalize('NFC',s).strip()
TONES={'̀','́','̃','̉','̣'}
def newstyle(s):
    d=unicodedata.normalize('NFD',nfc(s).lower())
    # find tone mark and the base letters; move from 2nd to 1st vowel in oa/oe/uy (uy not after q)
    chars=[]; 
    for ch in d:
        if unicodedata.combining(ch) and chars: chars[-1][1]+=ch
        else: chars.append([ch,''])
    def base(i): return unicodedata.normalize('NFD',chars[i][0])[0]
    for i in range(1,len(chars)):
        pair=base(i-1)+base(i)
        tone=[m for m in chars[i][1] if m in TONES]
        if tone and i==len(chars)-1 and pair in('oa','oe','uy') and not (pair=='uy' and i>=2 and base(i-2)=='q'):
            if not any(m in TONES for m in chars[i-1][1]):
                chars[i-1][1]+=tone[0]; chars[i][1]=chars[i][1].replace(tone[0],'')
            break
    return unicodedata.normalize('NFC',''.join(c+m for c,m in chars))
assert newstyle('lọan')=='lọan' and newstyle('loạn')=='loạn' and newstyle('toán')=='toán' and newstyle('thuỷ')=='thủy' and newstyle('hoà')=='hòa' and newstyle('quý')=='quý' and newstyle('khoẻ')=='khỏe' and newstyle('học')=='học'
CJK=r'[㐀-鿿\U00020000-\U0002ffff]'
A=collections.defaultdict(set); comp=collections.defaultdict(collections.Counter); allvi=set(); hvsyl=set()
with gzip.open('raw/kaikki-viwiktionary/vi-extract.jsonl.gz','rt',encoding='utf-8') as f:
    for line in f:
        d=json.loads(line)
        if d.get('lang_code')!='vi' or 'word' not in d: continue
        w=newstyle(d['word']); allvi.add(w)
        cats=' '.join(d.get('categories') or [])
        for t in d.get('etymology_texts') or []:
            first=t.split('\n')[0]
            m=re.match(r'^(?:Âm|Phiên âm) Hán-Việt của (?:chữ Hán )?(.+)$',first)
            if not m: continue
            body_nopar=re.sub(r'\(.*?\)','',m.group(1)); runs=re.findall(CJK+'+',body_nopar); syl=w.split()
            hvsyl.update(syl)
            if len(runs)==1 and not re.search(r'\bvà\b|hoặc',body_nopar):
                A[runs[0]].add(w)
                if len(runs[0])==len(syl):
                    for c,s in zip(runs[0],syl): comp[c][s]+=1
            elif len(runs)>=2 and re.search(r'\bvà\b',body_nopar) and all(len(r)==1 for r in runs) and len(runs)==len(syl):
                for c,s in zip(runs,syl): comp[c][s]+=1
print('hv syllables',len(hvsyl))
z=zipfile.ZipFile('raw/unihan/Unihan.zip'); uv={}
for name in z.namelist():
    for line in z.read(name).decode('utf-8').splitlines():
        if line.startswith('#') or not line.strip(): continue
        cp_,fld,val=line.split('\t',2)
        if fld=='kVietnamese': uv[chr(int(cp_[2:],16))]=[newstyle(x) for x in val.replace(',',' ').split()]
# cross-check: seeded 200 sample
random.seed(20261104); smp=random.sample(sorted(uv),200)
cov=[c for c in smp if c in comp]
ag=[c for c in cov if set(comp[c])&set(uv[c])]
print('200-sample: kaikki-covered',len(cov),'agree',len(ag))
for c in cov:
    if c not in ag: print('  DIS',c,uv[c],dict(comp[c]))
# also: unihan readings not in HV syllable set (Nôm suspects), over whole unihan
tot=sum(len(v) for v in uv.values()); nh=sum(1 for v in uv.values() for x in v if x not in hvsyl)
print('unihan readings',tot,'not in HV syllable set',nh)
ov=[c for c in uv if c in comp]
print('overlap',len(ov),'any-agree',sum(bool(set(comp[c])&set(uv[c])) for c in ov),'first-reading agree',sum(uv[c][0] in comp[c] for c in ov))
# first reading in hvsyl?
print('chars whose FIRST unihan reading is non-HV-syllable',sum(1 for v in uv.values() if v[0] not in hvsyl),'of',len(uv))
# among overlap, disagreements remaining
for c in [c for c in ov if not set(comp[c])&set(uv[c])][:12]: print('  DIS',c,uv[c],dict(comp[c]))
# restricted B
R=collections.defaultdict(list)
for c,l in uv.items(): R[c]=[x for x in l if x in hvsyl]
for c,cn in comp.items():
    for s in cn:
        if s not in R[c]: R[c].append(s)
h=pd.read_csv('raw/hsk30/hsk30.csv',encoding='utf-8',keep_default_na=False,dtype=str)
h['t']=h.Traditional.str.split('|').str[0]; h['s']=h.Simplified.str.split('|').str[0]
def B(t):
    if not all(R.get(c) for c in t): return []
    return [' '.join(p) for p in itertools.product(*[R[c] for c in t]) if ' '.join(p) in allvi]
rows=[]
for r in h.itertuples():
    a=sorted(A.get(r.t) or A.get(r.s) or []); b=B(r.t)
    rows.append((r.Level,len(r.t),a,b))
df=pd.DataFrame(rows,columns=['lv','n','a','b'])
df['final']=df.apply(lambda r: r.a[0] if len(r.a)==1 else (r.b[0] if len(r.b)==1 and not r.a else None),axis=1)
df['amb']=df.apply(lambda r:(len(r.a)>1) or (not r.a and len(r.b)>1),axis=1)
df['has']=df.final.notna()
print('resolved',df.has.sum(),'ambiguous',df.amb.sum(),'of',len(df))
print(df.groupby('lv').has.mean().round(2).to_dict())
print(df.groupby('n').has.agg(['mean','count']).head(5))
print(df[(~df.a.astype(bool))&df.has].sample(30,random_state=3)[['n']].join(h[['t']]).join(df['final']).to_string())
print('=========== char level')
hc=pd.read_csv('raw/hsk30/hsk30-chars.csv',encoding='utf-8',keep_default_na=False,dtype=str)
tot=0; ver_comp=0; ver_hv=0; unver=0; none=0; multi_amb=0
for r in hc.itertuples():
    ts=[t for t in r.Traditional.split('/') if t] or [r.Hanzi]
    t=ts[0]; tot+=1
    if t in comp: ver_comp+=1
    elif any(x in hvsyl for x in uv.get(t,[])): ver_hv+=1
    elif t in uv: unver+=1
    else: none+=1
print('hsk chars',tot,'kaikki-verified',ver_comp,'unihan∩HVsyl',ver_hv,'unihan only (unverified)',unver,'no unihan vi',none)
# ko/ja side sanity: how many hsk-trad chars have hangul in unihan
