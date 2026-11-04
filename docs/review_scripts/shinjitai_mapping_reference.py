"""REFERENCE ONLY (Claude, Stage 1 review). Evidence for DECISIONS D28 (shinjitai mapping). Not pipeline code. Run from repo root."""
import gzip, re, sys, zipfile, collections, unicodedata
import pandas as pd
import xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8')
oc={}
for line in open('raw/opencc/JPShinjitaiCharacters.txt',encoding='utf-8'):
    p=line.rstrip('\n').split('\t')
    if len(p)==2: oc[p[0]]=p[1].split()
print('opencc keys',len(oc),'multi-target',sum(len(v)>1 for v in oc.values()))
print({k:v for k,v in oc.items() if len(v)>1})
inv=collections.defaultdict(list)
for k,v in oc.items():
    for x in v:
        if x!=k: inv[x].append(k)
print('inverse entries',len(inv),'with >1 shinjitai',{k:v for k,v in inv.items() if len(v)>1})
kd=set()
with gzip.open('raw/kanjidic2/kanjidic2.xml.gz','rb') as f:
    for ev,el in ET.iterparse(f):
        if el.tag=='character': kd.add(el.findtext('literal')); el.clear()
print('kanjidic chars',len(kd))
proto=[('経','經'),('発','發'),('気','氣'),('楽','樂'),('歴','歷'),('実','實'),('売','賣'),('読','讀'),('広','廣'),('対','對'),('学','學'),('国','國'),('会','會'),('電','電'),('話','話'),('語','語')]
ok=0
for jp,t in proto:
    cand=inv.get(t,[t]) if t in inv else [t]
    good = cand==[jp]
    ok+=good
    print(t,'->',cand,'expected',jp,'OK' if good else 'MISS', 'in KD' if cand[0] in kd else 'notKD')
print(ok,'/',len(proto))
# unihan variants for comparison
z=zipfile.ZipFile('raw/unihan/Unihan.zip'); sv={}; tv={}
for name in z.namelist():
    for line in z.read(name).decode('utf-8').splitlines():
        if line.startswith('#') or not line.strip(): continue
        cp,f,v=line.split('\t',2)
        if f=='kTraditionalVariant': tv[chr(int(cp[2:],16))]=[chr(int(x[2:],16)) for x in v.split()]
        if f=='kSimplifiedVariant': sv[chr(int(cp[2:],16))]=[chr(int(x[2:],16)) for x in v.split()]
for jp,t in proto:
    print(t,'unihan simp',sv.get(t),'| shinjitai',jp,'trad variants',tv.get(jp))
# on HSK: how many trad chars get a different jp via opencc inverse, and are those in KD
hc=pd.read_csv('raw/hsk30/hsk30-chars.csv',encoding='utf-8',keep_default_na=False,dtype=str)
ts=[ (r.Traditional.split('/')[0] or r.Hanzi) for r in hc.itertuples()]
chg=[(t,inv[t]) for t in ts if t in inv]
print('hsk chars with a shinjitai change via opencc',len(chg), 'multi',[c for c in chg if len(c[1])>1])
print('trad chars not in kanjidic',[t for t in ts if t not in kd][:40], sum(t not in kd and t not in inv for t in ts))
print('changed but jp not in KD',[c for c in chg if c[1][0] not in kd])
