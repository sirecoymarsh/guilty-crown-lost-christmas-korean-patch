"""한 장면에서 바로 시작하는 시험 대본(완주 세 판이 못 지난 엇갈린 갈래용). 경로 A 변형을 바탕으로 시작 장면만 바꾼다.
python -I -X utf8 variant_scene.py lx0104a_02 lx0402a_02 lx0402b_01  -> nss_variants/nss.test_scene_<이름>.npa
"""
import sys
from pathlib import Path
W = Path(__file__).resolve().parent
sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA
from npa_build import build
E = 'cp932'
src = W / 'nss_variants/nss.test_route_a.npa'
a = NPA(src); e = {x['name']: x for x in a.entries}
boot0 = a.read(e['0_boot.nss'])
old = '$GameContiune=1;$GameName="lx0010.nss";'.encode(E)
assert boot0.count(old) == 1
for scene in sys.argv[1:]:
    boot = boot0.replace(old, f'$GameContiune=1;$GameName="{scene}.nss";'.encode(E), 1)
    build(src, W / f'nss_variants/nss.test_scene_{scene}.npa', replace={'0_boot.nss': boot})
    print('ok', scene)
