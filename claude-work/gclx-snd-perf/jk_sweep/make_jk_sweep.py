"""J/K 음악 잇기 전수 시험판(11-24 사용자 「돌려 줘」): 새 게임이 <장면>에서 시작, 창 모드, 대사마다 trace.log 에 시각+$GameName.
python -I -X utf8 make_jk_sweep.py lx0106 [lx0303 …] → F:\AI\gclx-4k\release_1121\nss_variants\nss.test_jk_<장면>.npa
바탕: staging/nss_play.npa(= 놀이 사본 nss.npa + nss.fix.npa 의 실제 내용).
"""
import sys
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
import patch_seek as ps
from npa_assets import NPA
from npa_build import build

R = Path(r'F:\AI\gclx-4k\release_1121')
V = R / 'nss_variants'
src = R / 'staging/nss_play.npa'
arc = NPA(src); ent = {e['name']: e for e in arc.entries}
E = 'cp932'
route = NPA(V / 'nss.test_route_a.npa'); re_ = {e['name']: e for e in route.entries}
trace_png = route.read(re_['kr_cmd_trace.png'])
for scene in sys.argv[1:]:
    boot = ps.rd(arc, ent['0_boot.nss'])
    A = '\tif(!#N2Start){'.encode(E); assert boot.count(A) == 1
    boot = boot.replace(A, '\t#N2Start=true;#SYSTEM_window_full=false;\r\n'.encode(E) + A, 1)
    B = '\t\t\t$GameName="lx0010.nss";'.encode(E); assert boot.count(B) == 1
    boot = boot.replace(B, f'\t\t\t$GameName="{scene}.nss";'.encode(E), 1)
    fn = ps.rd(arc, ent['function.nss'])
    i = fn.index('function TypeBegin()'.encode(E))
    a = 'if(ExistSave(-947001)){Save(-947001);}'.encode(E)
    j = fn.index(a, i)
    fn = fn[:j] + 'CreateTexture("kr_trc",0,0,0,"nss/kr_cmd_trace.png");Delete("kr_trc");\r\n\t'.encode(E) + fn[j:]
    out = V / f'nss.test_jk_{scene}.npa'
    build(src, out, replace={'0_boot.nss': boot, 'function.nss': fn}, add={'kr_cmd_trace.png': trace_png})
    print(out.name)
