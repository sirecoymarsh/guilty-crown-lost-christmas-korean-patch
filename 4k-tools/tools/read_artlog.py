"""art.log 요약: 올린 4배 그림 이름·시간, 「바뀐 그림」으로 빠진 것. python -X utf8 read_artlog.py"""
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
H = Path(r'F:\AI\gclx-4k\hires')
m = json.loads((H / 'manifest.json').read_text('utf-8'))
lines = (H / 'art.log').read_bytes().decode('cp932', 'replace').splitlines()
last_match = None
for l in lines:
    if l.startswith('load ') and l.endswith('MATCH'):
        last_match = l
    if l.startswith('upload'):
        k = re.search(r'([0-9a-f]{12})\.jxl', l).group(1)
        print('올림', m.get(k, {}).get('name'), l.split('.jxl ')[1])
    if l.startswith('stale'):
        print('바뀐 그림으로 빠짐 (마지막 일치:', last_match, ')')
print([l for l in lines if l.startswith('shot')][-1])
