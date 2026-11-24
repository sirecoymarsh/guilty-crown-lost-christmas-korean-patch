"""巨獣 7곳(「거수」)의 대본 위치·앞뒤 바이트를 본다. python -X utf8 find_geosu.py <nss.npa>"""
import re, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

arc = NPA(Path(sys.argv[1]))
for e in arc.entries:
    if e['name'] not in ('lx0010.nss', 'lx0507_10.nss', 'lx0511_10.nss'):
        continue
    b = arc.read(e)
    for m in re.finditer('거수'.encode('cp949'), b):
        s = b.rfind(b'\n', 0, m.start() - 200 if m.start() > 200 else 0)
        line_start = b.rfind(b'\n', 0, m.start()) + 1
        line_end = b.find(b'\n', m.end())
        block = b.rfind(b'<PRE', 0, m.start())
        tag = b[block:b.find(b'>', block) + 1].decode('cp949', 'replace')
        print(e['name'], m.start(), tag, '|', b[line_start:line_end].decode('cp949', 'replace').strip())
