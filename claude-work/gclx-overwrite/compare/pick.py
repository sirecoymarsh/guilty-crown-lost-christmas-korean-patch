"""첫 장면(lx0010) 앞부분에 나오는 그림 중 고화질본이 있는 것을 나온 차례로 보인다(스포일러 없는 고르기)."""
import re
from pathlib import Path
s = open(r'Y:\AI\claude-work\gclx-overwrite\nss_dump\lx0010.nss', 'rb').read()
idx = {}
for line in open(r'P:\AI\gclx-codexrun\game\hires\index.tsv', 'rb').read().splitlines():
    f = line.split(b'\t')
    if len(f) >= 7:
        idx[f[0].lower()] = f
seen = set()
for m in re.finditer(rb'cg/((?:ev|bg|st)/[^"\s]+?\.(?:jpg|png))', s):
    name = m.group(1)
    if name in seen:
        continue
    seen.add(name)
    hit = idx.get(name.lower())
    pct = 100 * m.start() / len(s)
    print(f'{pct:5.1f}%', name.decode('cp932'), '4x' if hit else '-', (hit[1] + b'x' + hit[2]).decode() if hit else '')
