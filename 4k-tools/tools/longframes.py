"""긴 프레임마다: 그림 읽기 수·엔진 풀기 시간·마지막 읽기 뒤 빈틈. python -X utf8 longframes.py <log>"""
import re, sys, collections
from pathlib import Path
L = Path(sys.argv[1]).read_bytes().decode('cp932', 'replace').splitlines()
blocks, cur = [], []
for l in L:
    if l.startswith('trace '): cur.append(l)
    elif l.startswith('longframe'):
        blocks.append((l, cur)); cur = []
rows = []
for lf, tr in blocks:
    ms = float(re.search(r'longframe (\d+)ms', lf).group(1))
    ev = [(float(m.group(1)), m.group(2), m.group(3)) for m in (re.match(r'trace \+([\d.]+)ms (\S+) ?(\S*) t\d+', t) for t in tr) if m]
    loads = sum(1 for e in ev if e[1] == 'loadbegin')
    lastload = max((e[0] for e in ev if e[1] in ('load', 'loadbegin')), default=0)
    rows.append((ms, loads, lastload))
body = [r for r in rows if r[0] > 150][3:]
print('0.15초 넘는 프레임', len(body))
print('  그림 읽기 100번 넘는 프레임', sum(1 for r in body if r[1] > 100), '| 평균 길이', round(sum(r[0] for r in body) / max(1, len(body))))
print('  (길이, 읽기 수, 마지막 읽기 시각)', sorted(body, reverse=True)[:12])
