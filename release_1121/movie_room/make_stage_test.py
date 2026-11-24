"""연출 다시 보기 전수 시험 대본(시험 전용): 영상실을 열면 「연출」 49곳을 차례로 저절로 재생하고 trace.log 에 시작·끝을 남긴다.
- 시작: kr_cmd_trace.png(+$GameName), 끝: kr_cmd_tracepick.png, 다 끝나면 kr_cmd_tracetitle.png(run_test --stop-trace tracetitle).
- 창 모드·모두 열기(사용자 기록 사본 안 씀). 대사는 자동 진행 + run_test --key-every Enter.
python -I -X utf8 make_stage_test.py [처음 번호(0부터)] → nss_variants/nss.test_stage.npa
"""
import sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_assets import NPA
from npa_build import build
import patch_seek as ps

W = Path(__file__).resolve().parents[1]
first = int(sys.argv[1]) if len(sys.argv) > 1 else 0
src = W / 'staging/nss_play.npa'
arc = NPA(src); ent = {e['name']: e for e in arc.entries}
boot = ps.rd(arc, ent['0_boot.nss'])
A = '\tif(!#N2Start){'.encode('cp932'); assert boot.count(A) == 1
boot = boot.replace(A, '\t#N2Start=true;#SYSTEM_window_full=false;#KS_ALLOPEN=true;\r\n'.encode('cp932') + A, 1)
mov = ps.rd(arc, ent['kr_movie.nss'])
K = 'cp949'


def sub(b, old, new):
    o = old.encode(K); assert b.count(o) == 1, (old, b.count(o)); return b.replace(o, new.encode(K))


mov = sub(mov, '\t$KM_TAB=0;$KMS_PAGE=1;', f'\t$KM_TAB=1;$KMT_I={first};$KMS_PAGE=1;')
mov = sub(mov, 'function KmStageList()\r\n{\r\n',
          'function KmStageList()\r\n{\r\n'
          '\tif($KMT_I<$KMS_N){$KMS_SEL=$KMT_I;$KMT_I++;CreateTexture("kr_trace",0,0,0,"nss/kr_cmd_trace.png");Delete("kr_trace");'
          'KmStagePlay();CreateTexture("kr_trace",0,0,0,"nss/kr_cmd_tracepick.png");Delete("kr_trace");return;}\r\n'
          '\tif($KMT_I==$KMS_N){$KMT_I++;CreateTexture("kr_trace",0,0,0,"nss/kr_cmd_tracetitle.png");Delete("kr_trace");}\r\n')
mov = sub(mov, '\t$SYSTEM_text_auto=false;\r\n\t$SYSTEM_text_auto_lock=false;\r\n\t$SYSTEM_text_erase=false;\r\n\t$SYSTEM_text_waitkey=true;\r\n\tCreateWindow',
          '\t$SYSTEM_text_auto=true;\r\n\t$SYSTEM_text_auto_lock=false;\r\n\t$SYSTEM_text_erase=false;\r\n\t$SYSTEM_text_waitkey=true;\r\n\tCreateWindow')
route = NPA(W / 'nss_variants/nss.test_route_a.npa'); re_ = {e['name']: e for e in route.entries}
add = {n: route.read(re_[n]) for n in ('kr_cmd_trace.png', 'kr_cmd_tracepick.png', 'kr_cmd_tracetitle.png')}
out = W / 'nss_variants/nss.test_stage.npa'
build(src, out, replace={'0_boot.nss': boot, 'kr_movie.nss': mov}, add=add)
print(out.name, 'first', first)
