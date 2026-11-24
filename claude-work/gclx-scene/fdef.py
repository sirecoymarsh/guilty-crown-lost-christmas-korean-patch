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
    i = b.find(b'function MovieSkipPlay')
    if i >= 0:
        print(n); print(b[i:i+1500].decode('cp932', 'replace'))
    for m in re.finditer(rb'lx0506_mv00|lx0106_mv01', b):
        print(n, b[max(0,m.start()-200):m.end()+60].decode('cp932','replace').replace('\r\n',' | ')[-300:])
