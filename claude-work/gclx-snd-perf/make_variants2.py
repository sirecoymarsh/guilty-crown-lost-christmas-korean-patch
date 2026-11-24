"""사운드 화면 멈춤 원인 가르기: notext = 풀이 프로세스가 줄 계산만(글 만들기·지우기 없음), wait100 = 틱 간격 100ms."""
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
i = snd.index(b'\t\tKuHintDel();\r\n\t\tif($khT==""){'); j = snd.index(b'\t\t$KUH_DT=3;\r\n', i)
notext = snd[:i] + snd[j:]
build(src, V / 'nss.test_notext.npa', replace={'kr_sound.nss': notext})
a = b'\t\tKuHintTick();\r\n\t\tWait(16);'; assert snd.count(a) == 1
build(src, V / 'nss.test_wait100.npa', replace={'kr_sound.nss': snd.replace(a, b'\t\tKuHintTick();\r\n\t\tWait(100);')})
print('ok')
