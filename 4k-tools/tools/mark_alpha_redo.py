"""옛 alpha4(대비 2배를 전체에)로 투명도가 바뀐 그림을 다시 하도록 표시(manifest version=0, 옛 결과 파일은 새 결과가 나올 때까지 그대로).
기준: alpha_scan.json 에서 옛↔새 4배 투명도 평균 차이 ≥0.5 또는 옛 방식이 잃는 투명도 ≥0.5%. python -X utf8 mark_alpha_redo.py"""
import hashlib, json, os
from pathlib import Path
ROOT = Path(r'F:\AI\gclx-4k')
key = lambda n: hashlib.sha1(n.lower().encode('utf-8')).hexdigest()[:12]
scan = json.loads((ROOT / 'alpha_scan.json').read_text('utf-8'))
sel = [x['name'] for x in scan if x['old_new_diff'] >= 0.5 or x['lost_pct'] >= 0.5]
mp = ROOT / 'hires' / 'manifest.json'
m = json.loads(mp.read_text('utf-8'))
marked = [n for n in sel if key(n) in m and m[key(n)].get('version') != 0]
for n in marked:
    m[key(n)]['version'] = 0
    m[key(n)]['redo'] = 'alpha4 10-26'
tmp = mp.with_suffix('.json.tmp'); tmp.write_text(json.dumps(m, ensure_ascii=False, indent=0, sort_keys=True), 'utf-8'); os.replace(tmp, mp)
(ROOT / 'redo_alpha.json').write_text(json.dumps(sel, ensure_ascii=False, indent=0), 'utf-8')
print('대상', len(sel), '이번에 표시', len(marked))
