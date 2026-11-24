import sys
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
import patch_seek as ps
from npa_assets import NPA
arc = NPA(Path(r'P:\AI\gclx-codexrun\game\nss.npa')); ent = {e['name']: e for e in arc.entries}
out = Path(r'Y:\AI\claude-work\gclx-scene')
for n in sys.argv[1:]:
    b = ps.rd(arc, ent[n])
    (out / (n + '.txt')).write_text(b.decode('cp932', 'replace'), 'utf-8')
    print(n, len(b))
if not sys.argv[1:]:
    print(sorted(ent)[:400])
