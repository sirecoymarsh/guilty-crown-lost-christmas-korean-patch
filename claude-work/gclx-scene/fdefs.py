import sys, re
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
import patch_seek as ps
from npa_assets import NPA
arc = NPA(Path(r'F:\AI\gclx-4k\release_1121\staging\nss_play.npa')); ent = {e['name']: e for e in arc.entries}
want = sys.argv[1:]
for n in sorted(ent):
    if not n.startswith('function'): continue
    t = ps.rd(arc, ent[n]).decode('cp932', 'replace')
    for w in want:
        i = t.find('function ' + w + '(')
        if i >= 0:
            j = t.find('\nfunction ', i + 10)
            body = t[i:j if j > 0 else i + 3000]
            print('==', n, w, len(body)); print(body[:900])
