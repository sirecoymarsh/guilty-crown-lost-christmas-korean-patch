"""최종 대본(nss_final)을 풀어 grep 할 수 있게 둔다. python -I -X utf8 dump_nss.py"""
import sys, os
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from npa_assets import NPA
a = NPA(r'F:\AI\gclx-4k\release_1121\staging\nss_final.npa')
out = r'Y:\AI\claude-work\gclx-overwrite\nss_dump'
types = {}
for e in a.entries:
    types[e['type']] = types.get(e['type'], 0) + 1
    if e['type'] != 2:
        continue
    try:
        b = a.read(e)
    except Exception as x:
        print('fail', e['name'], e['type'], e['size'], x)
        continue
    p = os.path.join(out, *e['name'].split('\\'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(b)
    if not e['name'].endswith('.nss'):
        print('non-nss', e['name'], e['size'])
print(types, len(a.entries))
