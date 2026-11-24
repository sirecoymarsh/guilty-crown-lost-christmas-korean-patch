import sys
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
import patch_seek as ps
from npa_assets import NPA
arc = NPA(Path(r'F:\AI\gclx-4k\release_1121\staging\nss_play.npa')); ent = {e['name']: e for e in arc.entries}
out = Path(r'Y:\AI\claude-work\gclx-scene\st')
out.mkdir(exist_ok=True)
for n in sys.argv[1:]:
    b = ps.rd(arc, ent[n])
    t = []
    for l in b.split(b'\r\n'):
        for enc in ('cp949', 'cp932'):
            try: t.append(l.decode(enc)); break
            except UnicodeDecodeError: pass
        else: t.append(l.decode('cp932', 'replace'))
    (out / (n + '.mix.txt')).write_text('\n'.join(t), 'utf-8')
    print(n, len(b))
