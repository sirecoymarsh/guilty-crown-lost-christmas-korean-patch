import sys, re
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek')
sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from patch_seek import rd
from npa_assets import NPA
src, name, out = sys.argv[1], sys.argv[2], sys.argv[3]
arc = NPA(src); ent = {e['name']: e for e in arc.entries}
b = rd(arc, ent[name])
open(out, 'wb').write(b)
n_pre = len(re.findall(rb'(?i)<PRE', b)); n_end = len(re.findall(rb'(?i)</PRE>', b))
print(name, len(b), 'PRE', n_pre, 'END', n_end)
