import sys, re
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
import patch_seek as ps
from npa_assets import NPA
arc = NPA(Path(r'P:\AI\gclx-codexrun\game\nss.npa')); ent = {e['name']: e for e in arc.entries}
for n in sorted(ent):
    if not re.match(r'lx0(1|2)', n): continue
    b = ps.rd(arc, ent[n])
    evs = []
    for m in re.finditer(rb'"((?:cg/ev|dx)/[^"]+)"', b):
        s = m.group(1).decode('cp932', 'replace')
        if s not in evs: evs.append(s)
    print(n, evs)
