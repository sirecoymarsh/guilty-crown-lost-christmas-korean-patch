"""noseek = 막대 프로세스만 뺌(풀이 그대로), merged = 두 일을 프로세스 하나에서."""
import sys
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
import patch_seek as ps
from npa_assets import NPA
from npa_build import build
V = Path(r'F:\AI\gclx-4k\release_1121\nss_variants')
src = V / 'nss.test_seek.npa'
arc = NPA(src); ent = {e['name']: e for e in arc.entries}
snd = ps.rd(arc, ent['kr_sound.nss'])
c = b'\tKuSeekRow();\r\n'; assert snd.count(c) == 1
build(src, V / 'nss.test_noseek.npa', replace={'kr_sound.nss': snd.replace(c, b'\t$KUS_ON=false;\r\n')})
a = b'\t\tCreateProcess($kxPN,150,0,0,"KuSeekLoop");\r\n\t\tRequest($kxPN,Start);\r\n'; assert snd.count(a) == 1, snd.count(a)
b = b'\t\tKuHintTick();\r\n\t\tWait(16);'; assert snd.count(b) == 1
m = snd.replace(a, b'').replace(b, b'\t\tKuHintTick();\r\n\t\tif($KUS_ON){KuSeekTick();}\r\n\t\tWait(16);')
build(src, V / 'nss.test_merged.npa', replace={'kr_sound.nss': m})
print('ok')
