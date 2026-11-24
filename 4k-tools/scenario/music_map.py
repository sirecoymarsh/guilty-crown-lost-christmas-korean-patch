"""function.nss 안에서 lxbgm/lxsong 이 나오는 자리 앞뒤를 보여 준다(곡 이름 표가 있는지). python -X utf8 music_map.py <nss.npa>"""
import re, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

arc = NPA(Path(sys.argv[1])); ent = {e['name']: e for e in arc.entries}
t = arc.read(ent['function.nss']).decode('cp932', 'replace').replace('\r', '')
for m in re.finditer(r'lx(bgm|song)\d+', t):
    a = t.rfind('\n', 0, m.start() - 160)
    b = t.find('\n', m.end() + 60)
    print('----', m.group(0)); print(t[a + 1:b])
    if m.group(0) == 'lxbgm03':
        break
