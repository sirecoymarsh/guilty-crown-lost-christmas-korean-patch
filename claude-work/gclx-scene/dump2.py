import sys
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
import patch_seek as ps, re
from npa_assets import NPA
arc = NPA(Path(r'P:\AI\gclx-codexrun\game\nss.npa')); ent = {e['name']: e for e in arc.entries}
names = sorted(n for n in ent if n.startswith('lx01') or n.startswith('lx02'))
print(names)
rec = ps.rd(arc, ent['kr_scenario.nss']).decode('cp949', 'replace')
Path('kr_scenario.u8.txt').write_text(rec, 'utf-8')
listed = re.findall(r'\$KS_FILE\[(\d+)\]="([^"]+)"', rec)
print(listed[:30])
