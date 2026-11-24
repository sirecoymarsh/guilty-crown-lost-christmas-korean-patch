"""nss.npa 안 대본(.nss)에서 낱말이 나오는 줄을 찾는다(읽기만; 줄 내용은 코드 줄만 - 대사 덩어리 <PRE> 안은 건너뜀).
python -I -X utf8 grep_nss.py <npa> <낱말> [낱말...] [--dump 이름]"""
import re, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
import npa_adapter as A

args = sys.argv[1:]
npa = args.pop(0)
dump = None
if '--dump' in args:
    i = args.index('--dump'); dump = args[i + 1]; del args[i:i + 2]
arc = A.NPA(Path(npa))
for e in arc.entries:
    n = e['name']
    if not n.lower().endswith('.nss'):
        continue
    if dump:
        if n == dump:
            b = arc.read(e)
            try:
                print(b.decode('cp949'))
            except UnicodeDecodeError:
                print(b.decode('cp932', 'replace'))
        continue
    try:
        b = arc.read(e)
    except Exception as ex:
        print(f'=== {n}: 못 읽음({type(ex).__name__})')
        continue
    if len(sys.argv) > 2 and '--only-kr' in sys.argv and not n.startswith('kr_'):
        continue
    hits = []
    inpre = False
    for ln, line in enumerate(b.split(b'\n'), 1):
        if b'<PRE' in line:
            inpre = True
        if not inpre and any(w.encode() in line for w in args):
            hits.append((ln, line.strip().decode('cp932', 'replace')[:200]))
        if b'</PRE>' in line:
            inpre = False
    if hits:
        print(f'=== {n}: {len(hits)}')
        for ln, t in hits[:12]:
            print(f'  {ln}: {t}')
        if len(hits) > 12:
            print(f'  ... +{len(hits) - 12}')
