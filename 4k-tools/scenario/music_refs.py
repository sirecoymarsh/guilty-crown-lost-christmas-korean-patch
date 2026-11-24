"""별칭 말고 다른 꼴로 곡을 부르는지: 이야기 대본 전체에서 lx004·lx010·lx018·lxsong 같은 이름이 나오는 줄. python -X utf8 music_refs.py <nss.npa>"""
import re, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

arc = NPA(Path(sys.argv[1]))
want = sys.argv[2].split(',') if len(sys.argv) > 2 else ['lx004', 'lx010', 'lx018', 'lxsong', 'lxbgm04', 'lxbgm10', 'lxbgm18']
for e in sorted(arc.entries, key=lambda e: e['name']):
    try:
        t = arc.read(e).decode('cp932', 'replace').replace('\r', '')
    except Exception:
        continue
    for ln in t.split('\n'):
        if any(w in ln for w in want):
            print(e['name'], '|', ln.strip()[:150])
