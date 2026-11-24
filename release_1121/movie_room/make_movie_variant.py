"""영상 감상 숨긴 시험 대본: 최종 대본의 타이틀 그대로 + 시작 때 창 모드 강제 · 회상 「모두 열기」 켬(영상 셋 다 열림).
사용자 기록 사본(전체 화면 설정이 따라옴)을 쓰지 않으려고 만든다(11-23 시험 창이 사용자 화면을 덮은 사고).
python -I -X utf8 make_movie_variant.py → nss_variants/nss.test_movie.npa
"""
import sys
from pathlib import Path
sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA
from npa_build import build
W = Path(__file__).resolve().parents[1]
final = W / 'staging/nss_final.npa'
fa = NPA(final); fe = {e['name']: e for e in fa.entries}
boot0 = fa.read(fe['0_boot.nss'])
A = '\tif(!#N2Start){'.encode('cp932')
assert boot0.count(A) == 1
boot = boot0.replace(A, '\t#N2Start=true;#SYSTEM_window_full=false;#KS_ALLOPEN=true;\r\n'.encode('cp932') + A, 1)
out = W / 'nss_variants/nss.test_movie.npa'
build(final, out, replace={'0_boot.nss': boot})
print(out.name)
