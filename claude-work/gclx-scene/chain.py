import sys, re
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
import patch_seek as ps
from npa_assets import NPA
arc = NPA(Path(r'P:\AI\gclx-codexrun\game\nss.npa')); ent = {e['name']: e for e in arc.entries}
for n in sorted(ent):
    if not re.match(r'lx0(0|1|2)', n): continue
    b = ps.rd(arc, ent[n])
    nx = [m.group(1).decode() for m in re.finditer(rb'\$GameName = "([^"]+)"', b)]
    print(n, '->', nx)
rec = Path('kr_scenario.u8.txt').read_text('utf-8')
for i in (10, 11, 12):
    m = re.search(r'\$KS_FILE\[%d\]=.*' % i, rec); print(m.group(0)[:900])
