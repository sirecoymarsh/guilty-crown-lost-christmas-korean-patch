"""art.log 의 올림 크기: 가장 큰 성공·실패, 그리고 결과가 4096x2304 보다 큰 그림 수."""
import json, re, sys
from pathlib import Path
H = Path(r'F:\AI\gclx-4k\hires')
m = json.loads((H / 'manifest.json').read_text('utf-8'))
ok, bad = [], []
for l in (H / 'art.log').read_bytes().decode('cp932', 'replace').splitlines():
    mm = re.match(r'upload .*?([0-9a-f]{12})\.jxl (\d+)x(\d+) (\d+)ms (ok|FAIL)', l)
    if mm:
        (ok if mm.group(5) == 'ok' else bad).append((int(mm.group(2)) * int(mm.group(3)), mm.group(1), int(mm.group(4))))
ok.sort(reverse=True)
print('가장 큰 성공', [(round(a / 1e6, 1), k, m[k]['alpha'], t) for a, k, t in ok[:6]])
print('실패', sorted(set((round(a / 1e6, 1), k) for a, k, t in bad)))
big = sorted(((v['out'][0] * v['out'][1], k, v['name'], v['alpha']) for k, v in m.items() if v['out'][0] * v['out'][1] > 4096 * 2304), reverse=True)
print('결과가 4096x2304(9.4MP) 보다 큰 그림', len(big))
for a, k, n, al in big[:15]:
    print(' ', round(a / 1e6, 1), k, n, '투명' if al else '')
