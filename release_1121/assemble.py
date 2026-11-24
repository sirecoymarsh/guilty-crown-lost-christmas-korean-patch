"""최종 대본과 시험 대본 변형을 묶는다.
- staging/nss_final.npa = build_nss.py 의 새 번역 대본 + 환경 설정 셋째 쪽(patch_config) + 그 그림들
- nss_variants/ (run_test 의 GCLX_NSS_DIR): nss.normal.npa(=최종), nss.test_cfg.npa(타이틀 없이 lx0010, 자동 진행 없음 — C 키로 설정),
  nss.test_route_a.npa / nss.test_route_b.npa(처음부터 결말까지 건너뛰기로 자동 완주, 선택지는 경로대로 자동, 장면마다 trace)
python -I -X utf8 assemble.py
"""
import sys, shutil, hashlib
from pathlib import Path
W = Path(__file__).resolve().parent
sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools'); sys.path.insert(0, str(W))
from npa_adapter import NPA
from npa_build import build
import patch_config

E = 'cp932'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


src = W / 'staging/nss.npa'
arc = NPA(src); ent = {e['name']: e for e in arc.entries}
cfg = patch_config.apply(arc.read(ent['sys_config.nss']))
assets = {'kr_cfg_page3.png': (W / 'assets/kr_cfg_page3.png').read_bytes()}
for n in ('q0', 'q1', 'q2', 'f60', 'f120', 'get'):
    assets[f'kr_cmd_{n}.png'] = (W / f'assets/kr_cmd_{n}.png').read_bytes()
# 11-23 영상 감상(movie_room/patch_movie.py): 타이틀 「영상」 단추 + kr_movie.nss + 그림
sys.path.insert(0, str(W / 'movie_room'))
import patch_movie
boot = patch_movie.apply_boot(arc.read(ent['0_boot.nss']))
assets.update(patch_movie.assets())
assets['kr_movie.nss'] = patch_movie.kr_movie(arc.read(ent['lx0109.nss']), arc.read(ent['kr_sound.nss']))
# 11-23 사운드 화면 엔딩 노래 제목(사용자 「엔딩 노래 제목은 못 찾은거야?」): 스태프 롤의 엔딩 주제가 둘을 가사로 짝지음
# lxsong01(결말 1, function.nss ArrayEND 「グッド」) = 『ISOLATION』(이토 카나코, 가사 「隔離されてゆくこの世界」)
# lxsong02(결말 2, 「バッド」) = 『Where am I ?』(VERTUEUX, 가사 「Where am I?」) — 곡 이름은 그 결말을 본 뒤에만 보인다
snd = arc.read(ent['kr_sound.nss'])
for old, new in (('결말 1의 노래', 'ISOLATION'), ('결말 2의 노래', 'Where am I ?')):
    assert snd.count(old.encode('cp949')) == 1, old
    snd = snd.replace(old.encode('cp949'), new.encode('cp949'))
final = W / 'staging/nss_final.npa'
build(src, final, replace={'sys_config.nss': cfg, '0_boot.nss': boot, 'kr_sound.nss': snd}, add=assets)
chk = NPA(final); ce = {e['name']: e for e in chk.entries}
assert chk.read(ce['sys_config.nss']) == cfg and chk.read(ce['0_boot.nss']) == boot and chk.read(ce['kr_sound.nss']) == snd and all(chk.read(ce[n]) == b for n, b in assets.items())
print('final', sha(final)[:8])

V = W / 'nss_variants'; V.mkdir(exist_ok=True)
shutil.copy2(final, V / 'nss.normal.npa')
fa = NPA(final); fe = {e['name']: e for e in fa.entries}
boot0 = fa.read(fe['0_boot.nss'])
A = '\tif(!#N2Start){'.encode(E)
B = '\twhile(1)\r\n\t{\r\n\t\t$スクリプトバージョン'.encode(E)
assert boot0.count(A) == 1 and boot0.count(B) == 1


def boot_direct(extra=''):
    b = boot0.replace(A, ('\t#N2Start=true;#SYSTEM_window_full=false;' + extra + '\r\n').encode(E) + A, 1)
    return b.replace(B, '\t$GameContiune=1;$GameName="lx0010.nss";\r\n'.encode(E) + B, 1)


# 설정 시험: lx0010 에서 바로 시작, 자동 진행 없음
build(final, V / 'nss.test_cfg.npa', replace={'0_boot.nss': boot_direct()})

# 완주 시험: 건너뛰기(안 읽은 곳까지)로 끝까지, 선택지는 경로대로
fn = fa.read(fe['function.nss'])
G = 'function GameMainSet()\r\n{\r\n'.encode(E)
assert fn.count(G) == 1
fn = fn.replace(G, G + '\tif(#KR_TEST_ROUTE>0){#SYSTEM_skip_absolute=true;$SYSTEM_skip=true;CreateTexture("kr_trace",0,0,0,"nss/kr_cmd_trace.png");Delete("kr_trace");}\r\n'.encode(E), 1)
sel = fa.read(fe['function_select.nss'])
for n, picks in (('01', ('A01', 'A01')), ('02', ('A02', 'B02')), ('03', ('A03', 'B03'))):
    head = f'function WaitChoice{n}()\r\n{{\r\n'.encode(E)
    assert sel.count(head) == 1, n
    a_pick, b_pick = picks
    # 경로 A: 착한 점수 쪽(lx0507 만 둘째), 경로 B: 반대쪽. 고른 뒤 trace.
    # 경로 A 는 lx0604_10sl 에서도 둘째: 「산다」는 원작 설계상 같은 장면을 끝없이 되풀이한다(11-21 rel_route_a2 가 2시간 맴돎)
    code = (f'\tif(#KR_TEST_ROUTE==1){{if($GameName=="lx0507_00sl.nss"||$GameName=="lx0604_10sl.nss"){{Choice{b_pick}();}}else{{Choice{a_pick}();}}'
            f'CreateTexture("kr_trace",0,0,0,"nss/kr_cmd_tracepick.png");Delete("kr_trace");return;}}\r\n'
            f'\tif(#KR_TEST_ROUTE==2){{if($GameName=="lx0507_00sl.nss"){{Choice{a_pick}();}}else{{Choice{b_pick}();}}'
            f'CreateTexture("kr_trace",0,0,0,"nss/kr_cmd_tracepick.png");Delete("kr_trace");return;}}\r\n')
    sel = sel.replace(head, head + code.encode(E), 1)
T = 'function TitleSelect()\r\n{\r\n'.encode(E)
trace_assets = {f'kr_cmd_{n}.png': assets['kr_cmd_get.png'] for n in ('trace', 'tracepick', 'tracetitle')}
for route in (1, 2):
    boot = boot_direct(f'#KR_TEST_ROUTE={route};#SYSTEM_skip_absolute=true;$SYSTEM_skip=true;')
    assert boot.count(T) == 1
    boot = boot.replace(T, T + '\tCreateTexture("kr_trace",0,0,0,"nss/kr_cmd_tracetitle.png");Delete("kr_trace");\r\n'.encode(E), 1)
    build(final, V / f'nss.test_route_{"ab"[route - 1]}.npa',
          replace={'0_boot.nss': boot, 'function.nss': fn, 'function_select.nss': sel}, add=trace_assets)
for p in sorted(V.iterdir()):
    print(p.name, sha(p)[:8])
