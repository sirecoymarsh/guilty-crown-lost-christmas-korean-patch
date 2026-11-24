import sys
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
from npa_assets import NPA
names = []
for a in ('cg.npa', 'cg1.npa', 'cg.fix.npa'):
    p = Path(r'P:\AI\gclx-codexrun\game') / a
    try:
        arc = NPA(p)
    except Exception as e:
        print('skip', a, e); continue
    for e in arc.entries:
        n = bytes.fromhex(e['name_hex']).decode('cp932', 'replace') if 'name_hex' in e else e['name']
        if 'thum' in n: names.append((a, n))
print(len(names))
Path('thum_list.txt').write_text('\n'.join(f'{a}\t{n}' for a, n in names), 'utf-8')
