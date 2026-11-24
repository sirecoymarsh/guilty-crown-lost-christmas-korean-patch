"""J/K 음악 시험판: 첫 대사부터 배경음악 lx001(βios)을 반복으로 틀어 둔다(시험 대본 nss.test_seek.npa 바탕).
TypeBegin 의 체크포인트(Save(-947001)) 뒤에 한 번만 — 다시 불러와도 $KRT_BGM 이 체크포인트에 담겨 다시 틀지 않는다.
python -I -X utf8 make_bgmtest.py → nss_variants/nss.test_bgm.npa
"""
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
fn = ps.rd(arc, ent['function.nss'])
E = 'cp932'
i = fn.index('function TypeBegin()'.encode(E))
a = 'if(ExistSave(-947001)){Save(-947001);}'.encode(E)
j = fn.index(a, i)   # 11-24: 체크포인트보다 앞에서 틀어야 체크포인트에 「재생 중」이 담긴다(실제 장면처럼)
ins = 'if(!$KRT_BGM){$KRT_BGM=true;SoundPlay("@lx001",0,1000,true);}\r\n\t'.encode(E)
fn = fn[:j] + ins + fn[j:]
build(src, V / 'nss.test_bgm.npa', replace={'function.nss': fn})
print('ok')
