"""회상 「이 장면의 연출」 시험 대본(시험 전용): 회상을 열면 바로 장면 상세(번호 sel, 0부터)를 띄우고, 재생은 자동 진행.
trace.log: 재생 시작 kr_cmd_trace.png, 상세로 돌아옴 kr_cmd_tracepick.png(run_test --stop-trace tracepick).
창 모드·모두 열기(사용자 기록 사본 안 씀).
python -I -X utf8 make_recall_test.py [sel=11] → nss_variants/nss.test_recall.npa
"""
import sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_assets import NPA
from npa_build import build
import patch_seek as ps

W = Path(__file__).resolve().parents[1]
sel = int(sys.argv[1]) if len(sys.argv) > 1 else 11
src = W / 'staging/nss_play.npa'
arc = NPA(src); ent = {e['name']: e for e in arc.entries}
boot = ps.rd(arc, ent['0_boot.nss'])
A = '\tif(!#N2Start){'.encode('cp932'); assert boot.count(A) == 1
boot = boot.replace(A, '\t#N2Start=true;#SYSTEM_window_full=false;#KS_ALLOPEN=true;\r\n'.encode('cp932') + A, 1)
# 11-24 route_state 시험: 직전에 하던 게임 값이 남은 상황을 흉내(회상 KsRouteState 가 덮어써야 함) — argv[2]=$PreGameName, argv[3]=$lx0104a_00sl選択肢
if len(sys.argv) > 2:
    stale = f'\t$PreGameName="{sys.argv[2]}";$lx0104a_00sl選択肢={sys.argv[3] if len(sys.argv) > 3 else 0};\r\n'.encode('cp932')
    boot = boot.replace(A, stale + A, 1)
rec = ps.rd(arc, ent['kr_scenario.nss'])
K = 'cp949'


def sub(b, old, new):
    o = old.encode(K); assert b.count(o) == 1, (old, b.count(o)); return b.replace(o, new.encode(K))


rec = sub(rec, '\t$KS_PAGE=$KS_MAXP;\r\n\t$KS_SEL=-1;', f'\t$KS_PAGE=$KS_MAXP;\r\n\t$KS_SEL={sel};')
rec = sub(rec, '\t$SYSTEM_text_auto=false;\r\n\t$SYSTEM_text_auto_lock=false;', '\t$SYSTEM_text_auto=true;\r\n\t$SYSTEM_text_auto_lock=false;')
rec = sub(rec, '\t$KS_FROM="";\r\n\tcall_scene $ks_call;\r\n',
          '\t$KS_FROM="";\r\n\tCreateTexture("kr_trace",0,0,0,"nss/kr_cmd_trace.png");Delete("kr_trace");\r\n\tcall_scene $ks_call;\r\n')
rec = sub(rec, '\tKsCover();\r\n\tDelete("kz_black");\r\n\tKsBgm();\r\n}',
          '\tKsCover();\r\n\tDelete("kz_black");\r\n\tKsBgm();\r\n\tCreateTexture("kr_trace",0,0,0,"nss/kr_cmd_tracepick.png");Delete("kr_trace");\r\n}')
route = NPA(W / 'nss_variants/nss.test_route_a.npa'); re_ = {e['name']: e for e in route.entries}
add = {n: route.read(re_[n]) for n in ('kr_cmd_trace.png', 'kr_cmd_tracepick.png')}
out = W / 'nss_variants/nss.test_recall.npa'
build(src, out, replace={'0_boot.nss': boot, 'kr_scenario.nss': rec}, add=add)
print(out.name, 'sel', sel)
