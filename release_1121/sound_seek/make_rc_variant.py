"""시험판 하나 더: nss.test_seek.npa 에 「이미 읽은 글 하늘색」을 켠 것(nss.test_rc.npa). 숨긴 시험 rc 전용.
python -X utf8 make_rc_variant.py
"""
import sys
from pathlib import Path
W = Path(__file__).resolve().parents[1]
sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from npa_build import build
from npa_assets import NPA
import importlib.util
spec = importlib.util.spec_from_file_location('ps', str(W / 'sound_seek/patch_seek.py')); ps = importlib.util.module_from_spec(spec); spec.loader.exec_module(ps)
src = W / 'nss_variants/nss.test_seek.npa'
arc = NPA(src); ent = {e['name']: e for e in arc.entries}
boot = ps.rd(arc, ent['0_boot.nss'])
A = '\t#N2Start=true;#SYSTEM_window_full=false;'.encode('cp932'); assert boot.count(A) == 1, boot.count(A)
boot = boot.replace(A, '\t#SYSTEM_read_text_color_change=true;'.encode('cp932') + A, 1)
build(src, W / 'nss_variants/nss.test_rc.npa', replace={'0_boot.nss': boot})
print('ok')
