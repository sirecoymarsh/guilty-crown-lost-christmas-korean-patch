"""회상 「이 장면의 연출」(11-24 사용자 「그 연출 탭에 있는거 가능하면 회상 탭에서 스토리랑 함께 자연스럽게 재생되도록 할 수는 없는거야?」).
- 회상 「재생」은 원래부터 장면 파일을 통째로 돌려 연출도 이야기 순서대로 나온다(장면 12 lx0106 본문엔 조건문이 없음).
  모자랐던 것은 「어느 장면에 어떤 연출이 있는지」와 「그 자리부터 보기」 → 장면 상세 화면 CG 아래에 그 장면의 연출 단추(최대 6).
- 단추 = 연출 바로 앞부터 장면 끝까지(kr_rpNN.nss: stage_replay.build_module(…, end=None, cut_choice=False) —
  앞부분은 한순간에 만들고 본문은 원래 대본 그대로, 선택지도 그대로). 장면 첫머리에서 시작하는 연출은 「재생」과 같으므로 장면을 그대로 부른다.
  끝나면 회상 「재생」과 같이 붙은 장면($KS_ALSO, 결말 스태프 롤)까지 잇고 상세 화면으로 돌아온다.
- 장면 이름이 회상 목록에 없는 연출(lx0604_12 다른 결말)은 영상실 「연출」 쪽에만 있다.
- 대본 함정(kr_scenario 머리말): 함수에 식을 넘기지 않음, 좌표는 상수, 글의 반각 , . 는 &, &. 로.
"""
import re
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
K = 'cp949'
ITEMS = json.loads((HERE / 'stage_items.json').read_text('utf-8'))
MAXB = 6
BX = (24, 238, 452)
BY = (456, 494)


def _files(scn: bytes):
    return set(m.group(1).decode('ascii') for m in re.finditer(rb'\$KS_FILE\[\d+\]="([\w.]+)"', scn))


def plan(scn: bytes):
    """{장면 파일: [(번호 1~49, 제목, 모듈 이름 또는 '')]}"""
    files = _files(scn)
    per = {}
    for k, it in enumerate(ITEMS, 1):
        if it['file'] not in files:
            continue
        mod = '' if it['start'] is None else f'kr_rp{k:02d}.nss'
        per.setdefault(it['file'], []).append((k, it['title'], mod))
    assert max(len(v) for v in per.values()) <= MAXB
    return per


def _esc(s):
    return s.replace(',', '&,').replace('.', '&.')


def nss(per) -> str:
    s = ['', '//■ 이 장면의 연출(Claude 11-24): 장면 상세 화면 CG 아래 단추. 고르면 그 연출 바로 앞부터 장면 끝까지(kr_rpNN.nss).',
         'function KsSpData()', '{', '\t$ksp_n=0;']
    first = True
    for f, rows in per.items():
        body = f'$ksp_n={len(rows)};'
        for i, (k, t, m) in enumerate(rows):
            assert len(t) <= 11, t
            body += f'$ksp_t{i}="▶  {_esc(t)}";$ksp_m{i}="{m}";'
        s.append(f'\t{"if" if first else "else if"}($kd_file=="{f}"){{{body}}}')
        first = False
    s += ['}', '', 'function KsSpBtns()', '{', '\tKsSpData();', '\t$ksp_show=true;',
          '\tif($kd_en!=""){if(!$KS_SEEN){$ksp_show=false;}}',
          '\tif($ksp_show){if($ksp_n>0){',
          '\t\tSetFont("Noto Sans KR", 14, 8A8A8A, 000000, 500, RIGHTDOWN);',
          '\t\tKsText("ks_dsplb",2012,24,428,640,26,"이 장면의 연출 · 고르면 그 연출 바로 앞부터 장면 끝까지 이어서 봅니다");']
    for i in range(MAXB):
        x, y = BX[i % 3], BY[i // 3]
        c = f'KS_SP{i}'
        s += [f'\t\tif($ksp_n>{i}){{',
              f'\t\t\tCreateChoice("{c}");',
              f'\t\t\tCreateColor("{c}/MouseUsual/hit",2010,{x},{y},206,32,0x000000);',
              f'\t\t\tRequest("{c}/MouseUsual/hit",Erase);',
              f'\t\t\tCreateColor("{c}/MouseUsual/img",2010,{x},{y},206,32,0x2E2E2E);',
              f'\t\t\tCreateColor("ks_dspb{i}",2011,{x + 2},{y + 2},202,28,0x0B0B0B);',
              f'\t\t\tCreateColor("{c}/MouseOver/img",2012,{x + 2},{y + 2},202,28,0x163A36);',
              f'\t\t\tCreateColor("{c}/MouseClick/img",2012,{x + 2},{y + 2},202,28,0x2A6F63);',
              '\t\t\tSetFont("Noto Sans KR", 15, DADADA, 000000, 600, RIGHTDOWN);',
              f'\t\t\tKsText("ks_dspt{i}",2014,{x + 12},{y + 1},190,30,$ksp_t{i});',   # 숨긴 시험 rsp1: y+5 는 4px 처짐
              '\t\t}']
    s += ['\t}}', '}', '']
    return '\r\n'.join(s)


def _sub(b, old, new, count=1):
    o = old.encode(K)
    assert b.count(o) == count, (old, b.count(o))
    return b.replace(o, new.encode(K))


def patch_recall(b: bytes) -> bytes:
    per = plan(b)
    b = _sub(b, '$KS_SEL=-1;$KS_PAGE=-1;\r\n', '$KS_SEL=-1;$KS_PAGE=-1;$KS_FROM="";$ksp_n=0;\r\n')
    # 상세 화면: 안내 글 뒤(Fade("*/MouseOver/*") 앞)에 단추, 고르기에 case
    b = _sub(b, 'KsText("ks_dnote",2012,694,436,320,48,"끝까지 보면 이 화면으로 돌아옵니다&.");\r\n',
             'KsText("ks_dnote",2012,694,436,320,48,"끝까지 보면 이 화면으로 돌아옵니다&.");\r\n\tKsSpBtns();\r\n')
    cases = ''.join(f'\t\t\tcase KS_SP{i}{{Request("@ks_se_ok",Play);$KS_FROM=$ksp_m{i};KsPlay($kd_n);$KS_LOOP=false;}}\r\n'
                    for i in range(MAXB))
    b = _sub(b, '\t\t\tcase KS_PLAY{Request("@ks_se_ok",Play);KsPlay($kd_n);$KS_LOOP=false;}\r\n',
             '\t\t\tcase KS_PLAY{Request("@ks_se_ok",Play);$KS_FROM="";KsPlay($kd_n);$KS_LOOP=false;}\r\n' + cases)
    # 재생: 연출에서 시작이면 장면 대신 kr_rpNN.nss(앞부분을 덮는 검은 판 kz_spv 는 그 모듈이 걷는다 — 영상실 KmStagePlay 와 같음)
    b = _sub(b, '\t$ks_call="nss/"+$GameName+"->"+$GameName;\r\n\tcall_scene $ks_call;\r\n\tif($kp_also!=""){',
             '\tKsRouteState();\r\n'
             '\t$ks_call="nss/"+$GameName+"->"+$GameName;\r\n'
             '\tif($KS_FROM!=""){CreateColor("kz_spv",31000,0,0,1024,576,BLACK);SetAlias("kz_spv","kz_spv");$ks_call="nss/"+$KS_FROM+"->"+$KS_FROM;}\r\n'
             '\t$KS_FROM="";\r\n'
             '\tcall_scene $ks_call;\r\n\tif($kp_also!=""){')
    return b + nss(per).encode(K) + route_state()


# 회상은 장면을 혼자 부르므로 앞 장면·고른 선택을 모른다(11-24 사용자 「맞춰 줘」). 장면 본문이 그 값을 읽는 곳(전수 조사):
#  - $PreGameName: lx0304·lx0402a/b_01/02·lx0604_12/20 이 「앞 장면이 X 가 아니면 배경음·화면을 스스로 차린다」 → 회상은 늘 혼자 시작이므로 ""
#    (지금까지는 직전에 하던 게임의 값이 남아 있으면 배경음이 안 나오거나 화면이 검게 시작할 수 있었다).
#  - $lx0104a_00sl選択肢: lx0206 의 짧은 대화 한 토막. 원작은 이 변수를 lx0104a·lx0203·lx0204 선택이 차례로 덮어써서 lx0206 직전에 남는 값은
#    lx0204 선택(「풀어준다」=1 → lx0204a). 회상: lx0204a 를 읽었으면 1, lx0204b 만 읽었으면 0, 둘 다 안 읽었으면(검수용 모두 열기) 1.
#  - $LProcAK_*Act: 장면 안 움직임 프로세스가 끝났는지 표시. 원작은 true 로만 바꾸고 되돌리지 않음 → 같은 세션에서 두 번째 보면 정리 블록이 빠진다 → false.
#  이름에 일본어가 든 변수는 원작 대본과 같은 cp932 바이트로 쓴다(이 파일 kr_scenario 는 cp949).
LPROC = ['lx0500_01', 'lx0505_00', 'lx0506_00', 'lx0506_01', 'lx0506_02', 'lx0506_03', 'lx0506_10',
         'lx0508_01', 'lx0508_02a', 'lx0508_02b', 'lx0508_02c', 'lx0508_03', 'lx0508_04']


def lproc_reset() -> str:
    return ''.join(f'$LProcAK_{x}Act=false;' for x in LPROC)


def route_state() -> bytes:
    v = b'$lx0104a_00sl' + '選択肢'.encode('cp932')
    s = [b'', '//■ 회상 재생 전 이야기 상태 맞추기(Claude 11-24, movie_room/recall_sp.py route_state 머리말 참고)'.encode(K),
         b'function KsRouteState()', b'{',
         b'\t$PreGameName="";',
         b'\t' + lproc_reset().encode('ascii'),
         b'\t$krs_a=Conquest("nss/lx0204a.nss","lx0204a.nss",null);',
         b'\t$krs_b=Conquest("nss/lx0204b.nss","lx0204b.nss",null);',
         b'\t' + v + b'=1;',
         b'\tif(!$krs_a){if($krs_b){' + v + b'=0;}}',
         b'}', b'']
    return b'\r\n'.join(s)


def modules(scn: bytes, get_scene) -> dict:
    """kr_rpNN.nss — 연출 바로 앞부터 장면 끝까지(선택지 포함)."""
    import stage_replay as sr
    out = {}
    for f, rows in plan(scn).items():
        for k, t, m in rows:
            if not m:
                continue
            it = ITEMS[k - 1]
            mb, _ = sr.build_module(get_scene(f), f, it['start'], None, cut_choice=False)
            out[m] = mb.replace(b'scene kr_sp.nss', f'scene {m}'.encode())
    return out
