"""Stage 4 gate part 4: app effect of task 5 after config/task5_review.csv (Claude, 2026-11-07).
Usage: python stage4d_part4_effects.py <table.pkl from stage4d_part4_reference.py with t1conf/t1low added>.
D68 rule: a rare/unsure ja/ko row becomes a fixed note; an entry leaves only if its false_friend list empties.
"""
import sys,json,glob,pandas as pd
df=pd.read_pickle(sys.argv[1])
rev=pd.read_csv('config/task5_review.csv',dtype=str,keep_default_na=False)
for _,r in rev.iterrows():
    m=df.key==r.key; c=r.lang+'_check'
    assert (df.loc[m,c]==r.check_generated).all() and m.sum()==1
    df.loc[m,c]=r.check_review
NOT={'rare','unsure'}; DROP={'rare','unsure','wrong_meaning'}
words=df[~df.is_row]
print('card words reviewed',len(words),' (b055 missing: 100 items)')
print('cards with (ko):',(words.ko_check.isin(NOT)).sum(),' ko wrong_meaning:',(words.ko_check=='wrong_meaning').sum())
print('cards with (ja):',(words.ja_check.isin(NOT)).sum(),' ja wrong_meaning:',(words.ja_check=='wrong_meaning').sum())
print('either:',(words.ko_check.isin(NOT)|words.ja_check.isin(NOT)).sum(),' both:',(words.ko_check.isin(NOT)&words.ja_check.isin(NOT)).sum())
print('vi literary:',(words.vi_use=='literary').sum(),'of',(words.vi_use!='').sum(),'; multi-char literary',((words.vi_use=='literary')&(words.trad.str.len()>1)).sum())
print('rows ko not used:',df[df.is_row].ko_check.isin(NOT).sum(),'wm',(df[df.is_row].ko_check=='wrong_meaning').sum())
# task 2
t2={}
for f in sorted(glob.glob('content/accepted/task2/b*.jsonl')):
    for l in open(f,encoding='utf-8'):
        o=json.loads(l); t2[o['key']]=o
r2=pd.read_csv('config/task2_review.csv',dtype=str,keep_default_na=False)
for _,r in r2.iterrows():
    o=t2[r.key]
    o['false_friend']=[x for x in r.false_friend_review.split(';') if x] if r.false_friend_review or r.action else o['false_friend']
    if r.action=='clear_vi': o['meanings']=[m for m in o['meanings'] if m['lang']!='vi']
static=set('勉強 工夫 手紙 汽車 愛人 大丈夫 小心 東西 娘 新聞 先生 博士'.split())
chk=df.set_index('key')
trad_of={k:(chk.loc[k,'trad'] if k in chk.index else k) for k in t2}
S={'entries_before':0,'entries_after':0,'leave':0,'leave_old_rule':0,'ja_note':0,'ko_note':0,'ja_dropped_wm':0,'ko_dropped_wm':0,'changed':0,'unchecked_b055':0}
leave=[];oldleave=[]
for k,o in t2.items():
    ff=list(o['false_friend'])
    if not ff: continue
    S['entries_before']+=1
    if trad_of[k] in static: S['entries_after']+=1; continue
    if k not in chk.index: S['unchecked_b055']+=1; S['entries_after']+=1; continue
    x=chk.loc[k]; langs={m['lang'] for m in o['meanings']}
    changed=False; use={}
    for lg in ('ja','ko'):
        c=x[lg+'_check'] if lg+'_check' in x else ''
        if lg in langs:
            if c in NOT: S[lg+'_note']+=1; changed=True; use[lg]=False
            elif c=='wrong_meaning': S[lg+'_dropped_wm']+=1; changed=True; use[lg]=None
            else: use[lg]=True
        if c in DROP and lg in ff: ff.remove(lg)
    if changed: S['changed']+=1
    if not ff: S['leave']+=1; leave.append((k,trad_of[k],o['false_friend'])); 
    else: S['entries_after']+=1
    if not ff or not any(v for v in use.values()) and use: 
        S['leave_old_rule']+=1; oldleave.append(trad_of[k])
print(S)
print('leave examples',leave[:25])
print('old-rule leave count',len(oldleave))
