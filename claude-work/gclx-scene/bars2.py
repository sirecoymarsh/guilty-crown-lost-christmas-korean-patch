import sys, re, json
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from pathlib import Path
from npa_assets import NPA
import patch_seek as ps
arc = NPA(Path(r'F:\AI\gclx-4k\release_1121\staging\nss_play.npa')); ent = {e['name']: e for e in arc.entries}
pat = re.compile(r'Create(?:Color|Texture)\w*\("([^"]+)"\s*,\s*-?\d+\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([^)]*)\)')
items = json.loads(Path(r'F:\AI\gclx-4k\release_1121\movie_room\stage_items.json').read_text('utf-8'))
for k in range(1, 10):
    t = ps.rd(arc, ent[f'kr_sp{k:02d}.nss']).decode('cp932', 'replace')
    hits = [(m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6)[:20]) for m in pat.finditer(t) if int(m.group(4)) >= 1000 and int(m.group(5)) <= 200]
    oth = sorted(set(re.findall(r'"(cg/[^"]*(?:帯|枠|シネマ|cinema|letter|band)[^"]*)"', t)))
    print(k, items[k-1]['title'], hits[:4], oth[:4])
