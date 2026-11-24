"""사운드 화면 느림 A/B: 시험판(nss.test_seek.npa)에서 풀이 프로세스만 뺀 판(nohint), 막대 프로세스까지 뺀 판(noproc)."""
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
a = b'\tKuHintRow();\r\n'; assert snd.count(a) == 1
nohint = snd.replace(a, b'\t$KUH_ON=false;\r\n')
build(src, V / 'nss.test_nohint.npa', replace={'kr_sound.nss': nohint})
c = b'\tKuSeekRow();\r\n'; assert nohint.count(c) == 1
build(src, V / 'nss.test_noproc.npa', replace={'kr_sound.nss': nohint.replace(c, b'\t$KUS_ON=false;\r\n')})
print('ok')
