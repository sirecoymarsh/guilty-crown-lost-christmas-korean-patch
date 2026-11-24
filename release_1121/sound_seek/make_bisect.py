"""부팅 멈춤 가르기(11-24): 지금 시험판에서 한 파일씩 앞 판으로 되돌린 시험판 둘.
A = sys_config.nss 를 읽은 글 줄 없는 판으로, B = kr_movie.nss 를 가사판 원래 것으로.
"""
import sys
from pathlib import Path
W = Path(__file__).resolve().parents[1]
sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
sys.path.insert(0, str(W / 'sound_seek'))
from npa_build import build
import importlib.util
spec = importlib.util.spec_from_file_location('ps', str(W / 'sound_seek/patch_seek.py')); ps = importlib.util.module_from_spec(spec); spec.loader.exec_module(ps)
import logo_wheel
src = ps.NPA(W / 'staging/nss_lyrics.npa'); se = {e['name']: e for e in src.entries}
tv = W / 'nss_variants/nss.test_seek.npa'
# A: 읽은 글 줄 빼고
orig_rc = logo_wheel.patch_config_readcolor
logo_wheel.patch_config_readcolor = lambda b, sf: b
cfgA = logo_wheel.patch_config(ps.rd(src, se['sys_config.nss']))
logo_wheel.patch_config_readcolor = orig_rc
build(tv, W / 'nss_variants/nss.test_bA.npa', replace={'sys_config.nss': cfgA})
# B: 영상 감상 원래 것
build(tv, W / 'nss_variants/nss.test_bB.npa', replace={'kr_movie.nss': ps.rd(src, se['kr_movie.nss'])})
print('ok')
