import sys, re
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
import patch_seek as ps
from npa_assets import NPA
arc = NPA(Path(r'P:\AI\gclx-codexrun\game\nss.npa')); ent = {e['name']: e for e in arc.entries}
for n in sorted(ent):
    if not n.endswith('.nss'): continue
    b = ps.rd(arc, ent[n])
    for m in re.finditer(rb'MovieSkipPlay\("([^"]+)","([^"]+)"\)', b):
        # 어떤 .ngs 인지: 같은 이름으로 만든 CreateMovie 를 앞에서 찾는다
        nm = m.group(1)
        pre = b[:m.start()]
        k = pre.rfind(b'"' + nm + b'"')
        mv = re.search(rb'"(dx/[^"]+)"', pre[k:k+300]) if k >= 0 else None
        print(n, m.group(2).decode(), mv.group(1).decode('cp932','replace') if mv else '?')
cg = ps.rd(arc, ent['extra_cglib.nss'])
for k in ['ev0206スクルージ重機エンドレイヴ撃破', 'ev0205重機エンドレイヴ登場', 'ev0209重機エンドレイヴ銃撃', 'ev0210スクルージキャロルダッシュ']:
    print(k, cg.count(k.encode('cp932')))
