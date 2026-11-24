import sys
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
import patch_seek as ps
from npa_assets import NPA
arc = NPA(Path(r'P:\AI\gclx-codexrun\game\nss.npa')); ent = {e['name']: e for e in arc.entries}
keys = [('엔드레이브','cp949'), ('エンドレイヴ','cp932'), ('ゴーチェ','cp932'), ('シュタイナー','cp932'), ('.ngs','ascii')]
for n in sorted(ent):
    if not n.startswith('lx'): continue
    b = ps.rd(arc, ent[n])
    r = []
    for k, e in keys:
        c = b.count(k.encode(e))
        if c: r.append(f'{k}:{c}')
    if r: print(n, ' '.join(r))
