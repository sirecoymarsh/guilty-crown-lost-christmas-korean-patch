"""function_lx.nss 의 반복 곡 표: if($Loopナット=="lx001a"){ … $Loop音楽="lxbgm01"; … } → music_loops.json {이름: 파일}.
python -X utf8 music_loops.py <nss.npa>"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

here = Path(__file__).parent
arc = NPA(Path(sys.argv[1])); ent = {e['name']: e for e in arc.entries}
t = arc.read(ent['function_lx.nss']).decode('cp932', 'replace').replace('\r', '')
loops = {}
for m in re.finditer(r'\$Loop\S*?=="(lx\w+)"\)\s*\{', t):
    nxt = re.search(r'\$Loop音楽\s*=\s*"(\w+)"', t[m.end():m.end() + 400])
    stop = t.find('}', m.end())
    if nxt and m.end() + nxt.start() < stop:
        loops.setdefault(m.group(1), nxt.group(1))
json.dump(loops, open(here / 'music_loops.json', 'w', encoding='utf-8'), indent=1)
print(loops)
