"""Stage 4b: Flash vs Argon pilot comparison (task 1 and task 2). Run from the repo root with PYTHONIOENCODING=utf-8."""
import json,sys
def load(p): return {json.loads(l)['word_id']:json.loads(l) for l in open(p,encoding='utf-8') if l.strip()}
I=load('content/inputs/pilot/task1.jsonl'); F=load('content/generated/pilot/task1.jsonl'); A=load('content/generated/pilot/argon/task1.jsonl')
from collections import Counter
for name,M in (('Flash',F),('Argon',A)):
    print(name, Counter(v['vi_check'] for v in M.values()), 'low',sum(v['confidence']=='low' for v in M.values()), 'differ',sum(v['meanings_differ'] for v in M.values()), Counter(v['low_reason'] for v in M.values() if v['low_reason']).most_common(6))
print()
for w in I:
    f,a,i=F[w],A[w],I[w]
    if f['vi_check']!=a['vi_check'] or f['meanings_differ']!=a['meanings_differ'] or f['confidence']!=a['confidence'] or bool(f['meaning_ja__vi'])!=bool(a['meaning_ja__vi']):
        print('=====',w,i['trad'],'ja',i['ja'],'ko',i['ko'],'py',i['pinyin'],'vi',i['vi'],'src',i['source_vi'],'L',i['level'])
        print('  en:',i['gloss_en'][:90],'| ja_en:',i['gloss_ja_en'][:60],'| ko:',i['gloss_ko'][:40],'| vi:',i['gloss_vi'][:90])
        for n,m in (('F',f),('A',a)):
            print(f"  {n}: vic={m['vi_check']} diff={m['meanings_differ']} conf={m['confidence']} lr={m['low_reason']} | ja={m['meaning_ja__ja']} | ko={m['meaning_ja__ko']} | zh={m['meaning_ja__zh']} | vi={m['meaning_ja__vi']} | r={m['vi_check_reason'][:80]}")

print("\n######## TASK 2\n")
import json
def load(p): return {json.loads(l)['key']:json.loads(l) for l in open(p,encoding='utf-8') if l.strip()}
I=load('content/inputs/pilot/task2.jsonl'); F=load('content/generated/pilot/task2.jsonl'); A=load('content/generated/pilot/argon/task2.jsonl')
print('Flash ff',sum(bool(v['false_friend']) for v in F.values()),'low',sum(v['confidence']=='low' for v in F.values()))
print('Argon ff',sum(bool(v['false_friend']) for v in A.values()),'low',sum(v['confidence']=='low' for v in A.values()))
for k,i in I.items():
    f,a=F[k],A[k]
    same = sorted(f['false_friend'])==sorted(a['false_friend'])
    print('=====','DIFF' if not same else 'same',k, {x:i[x] for x in i if x not in('key',) and i[x] and 'gloss' not in x and 'meaning' not in x})
    if not same or f['false_friend']:
        print('   in:', {x:str(i[x])[:70] for x in i if ('gloss' in x or 'meaning' in x) and i[x]})
        for n,m in (('F',f),('A',a)):
            print(f"   {n}: ff={m['false_friend']} conf={m['confidence']} {m['low_reason']} | "+' | '.join(f"{e['lang']}{'*' if e['is_trap'] else ''}={e['meaning_ja']}" for e in m['meanings']))
