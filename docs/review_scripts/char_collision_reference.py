"""REFERENCE ONLY (Claude, 2026-11-04). Evidence for DECISIONS D37/D38: many->one (shared trad) and one->many (several trad per simplified character) collision measurements on the HSK list. Not pipeline code. Run from repo root."""
import pandas as pd, zipfile, sys, unicodedata, collections, itertools
sys.stdout.reconfigure(encoding='utf-8')
n=lambda s: unicodedata.normalize('NFC',s.strip())
hc=pd.read_csv('raw/hsk30/hsk30-chars.csv',encoding='utf-8',keep_default_na=False,dtype=str)
hc['variants']=hc.Traditional.map(lambda s:[n(x) for x in s.split('/') if x])
hc['trad']=hc.apply(lambda r:(r.variants[0] if r.variants else n(r.Hanzi)),axis=1)
# unihan kHangul / kMandarin presence by char
z=zipfile.ZipFile('raw/unihan/Unihan.zip'); kh={}; kv={}; sv={}; tv={}
for name in z.namelist():
    for line in z.read(name).decode('utf-8').splitlines():
        if line.startswith('#') or not line.strip(): continue
        cp,f,v=line.split('\t',2); c=chr(int(cp[2:],16))
        if f=='kHangul': kh[c]=v
        if f=='kSimplifiedVariant': sv[c]=[chr(int(x[2:],16)) for x in v.split()]
        if f=='kTraditionalVariant': tv[c]=[chr(int(x[2:],16)) for x in v.split()]
# --- A) the key_char problem: lookup under Hanzi vs under trad
diff=hc[hc.Hanzi!=hc.trad]
print('rows',len(hc),'Hanzi!=trad',len(diff))
print('kHangul found under Hanzi (simplified):',sum(h in kh for h in diff.Hanzi),'of',len(diff),'| under trad:',sum(t in kh for t in diff.trad),'of',len(diff))
# --- B) one->many
multi=hc[hc.variants.map(len)>1]
print('HSK char rows with >1 traditional variant:',len(multi),'of',len(hc))
print('  with 2 variants:',(multi.variants.map(len)==2).sum(),' 3+:',(multi.variants.map(len)>=3).sum())
for h in '发 干 后 里 只 面 了 家 回 别'.split():
    r=hc[hc.Hanzi==h]
    if len(r): print('  ',h,r.iloc[0].Traditional,'Level',r.iloc[0].Level)
# words: which non-first variant chars actually occur in word trad strings
w=pd.read_csv('raw/hsk30/hsk30.csv',encoding='utf-8',keep_default_na=False,dtype=str)
wt=[n(t) for ts in w.Traditional for t in ts.split('|') if t]
allchars=collections.Counter(c for t in wt for c in t if '\u3400'<=c<='\u9fff')
extra=collections.Counter(); tradset=set(hc.trad)
nonfirst=set(v for vs in multi.variants for v in vs[1:])
used=[c for c in nonfirst if allchars[c]>0]
print('non-first variant chars total',len(nonfirst),'| used in HSK word trad strings',len(used))
print('  examples used:',[(c,allchars[c]) for c in sorted(used,key=lambda c:-allchars[c])[:15]])
# chars used in words that are not HSK-list trad keys (Stage 3 growth)
notin=[c for c in allchars if c not in tradset]
print('distinct word-trad chars',len(allchars),'not a chars-row trad key now',len(notin),' of which are non-first variants',len([c for c in notin if c in nonfirst]))
# one->many check: do unihan simplified variants of those extra chars point back to a Hanzi in list?
back=0; fwd=0
hz=set(hc.Hanzi)
for c in used:
    s=sv.get(c,[])
    if any(x in hz for x in s) or c in hz: back+=1
print('used non-first variants whose Unihan kSimplifiedVariant (or self) is an HSK Hanzi:',back,'of',len(used))
# many->one on simp inside chars rows after growth: simp shared by >1 trad
by=collections.defaultdict(set)
for r in hc.itertuples():
    by[r.Hanzi].add(r.trad)
    for v in r.variants: by[r.Hanzi].add(v)
print('simplified chars mapping to >1 traditional (HSK list, incl. all listed variants):',sum(len(v)>1 for v in by.values()))
# collisions many->one on trad
print('trad shared by >1 row:',hc.trad.duplicated(keep=False).sum(),sorted(set(hc.trad[hc.trad.duplicated(keep=False)])))
# does any non-first variant coincide with another row's trad key (collision after growth)?
clash=[(v,r.Hanzi) for r in multi.itertuples() for v in r.variants[1:] if v in tradset]
print('non-first variants that are ALSO the primary trad of another row:',clash[:20],len(clash))
# word-level explicit: e.g. 头发 trad
print(w[w.Simplified.isin(['头发','发展','发现','干净','后面','里面','只有','一只'])][['Simplified','Traditional','Pinyin']].to_string())
