"""원작이 단계(PHASE)마다 띄우는 이름 → phase_names.json {번호: 이름}. python -X utf8 phase_names.py <nss.npa>
(사용자가 플레이 중 — 뒤 단계 이름을 채팅에 옮기지 말 것)"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

arc = NPA(Path(sys.argv[1]))
names = {}
for e in sorted(arc.entries, key=lambda e: e['name']):
    if not e['name'].startswith('lx'):
        continue
    b = arc.read(e)
    num = re.search(rb'\$PHASE_num\s*=\s*(\d+)\s*;', b)
    nm = re.search(rb'\$PHASE_name\s*=\s*"([^"]*)"', b)
    if num and nm:
        names.setdefault(int(num.group(1)), (e['name'], nm.group(1).decode('cp949', 'replace')))
json.dump({k: v[1] for k, v in sorted(names.items())}, open(Path(__file__).parent / 'phase_names.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, (f, n) in sorted(names.items()):
    print(k, f, len(n), 'chars', n if k <= 2 else '(가림)')
