"""두 시험의 profile.log 비교: 스레드별 EXE 안 표본·바쁜 함수 묶음(0x100 단위). python -X utf8 prof_compare.py nat4 k3"""
import re, sys, collections
from pathlib import Path
R = Path(r'F:\AI\gclx-4k\testrun')


def load(name):
    t = (R / name / 'profile' / 'profile.log').read_text(errors='replace')
    rounds = int(re.search(r'rounds (\d+)', t).group(1))
    threads = []
    for b in t.split('\n== ')[1:]:
        m = re.match(r'thread (\d+)( \(render\))? samples (\d+), in exe (\d+)', b)
        mods = dict((n.strip(), int(c)) for c, n in re.findall(r'^\s+(\d+) (\S[^\n]*)$', b.split('-- exe eip')[0], re.M))
        eips = [(int(c), int(a, 16)) for c, a in re.findall(r'^\s+(\d+) ([0-9a-f]{8})$', b.split('-- exe eip')[1].split('-- exe return')[0], re.M)]
        threads.append(dict(tid=m.group(1), render=bool(m.group(2)), samples=int(m.group(3)), exe=int(m.group(4)), mods=mods, eips=eips))
    return rounds, threads


for name in sys.argv[1:]:
    rounds, th = load(name)
    busy = sorted(th, key=lambda x: -(x['samples'] - x['mods'].get('ntdll.dll', 0) - x['mods'].get('win32u.dll', 0)))
    print(f'== {name}: rounds {rounds}, threads {len(th)}')
    fn = collections.Counter()
    for x in th:
        for c, a in x['eips']:
            fn[a & ~0xff] += c
    for x in busy[:6]:
        work = x['samples'] - x['mods'].get('ntdll.dll', 0) - x['mods'].get('win32u.dll', 0)
        top = sorted(((c, m) for m, c in x['mods'].items() if m not in ('ntdll.dll', 'win32u.dll')), reverse=True)[:4]
        print(f"  thread {x['tid']}{' (render)' if x['render'] else ''}: busy {100 * work / rounds:.1f}% of one core, exe {100 * x['exe'] / rounds:.1f}%  {top}")
    print('  exe hot 0x100 blocks:', [(hex(a), c) for a, c in fn.most_common(10)])
