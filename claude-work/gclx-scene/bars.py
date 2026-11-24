import sys, re
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from pathlib import Path
from npa_assets import NPA
import patch_seek as ps
arc = NPA(Path(r'F:\AI\gclx-4k\release_1121\staging\nss_play.npa')); ent = {e['name']: e for e in arc.entries}
pat = re.compile(rb'Create\w*\("([^"]+)"\s*,\s*\d+\s*,\s*0\s*,\s*(0|476|4\d\d)\s*,\s*1024\s*,\s*(\d+)\s*,\s*(BLACK|"?000000"?)')
for n in sorted(ent):
    if not n.endswith('.nss'): continue
    b = ps.rd(arc, ent[n])
    m = pat.findall(b)
    if m: print(n, len(m), [(x[0].decode('cp932','replace'), x[1].decode(), x[2].decode()) for x in m[:3]])
b = ps.rd(arc, ent['0_boot.nss']).decode('cp932', 'replace')
for k in [i.start() for i in re.finditer('上下枠', b)][:6]:
    print('BOOT', b[max(0, k-120):k+80].replace('\r\n', ' | '))
