"""환경 설정에 셋째 쪽(화질·초당 프레임)을 넣는다. sys_config.nss 를 바이트로 고친다(일본어 이름은 cp932 그대로).
둘째 쪽의 흐린 「다음」을 진짜 「다음」으로 바꾸고, 셋째 쪽은 둘째 쪽과 같은 짜임(배경·강조·초점·고르기)으로 만든다.
대본 → DLL: CreateTexture 로 nss/kr_cmd_<명령>.png 를 읽게 하면 DLL 의 그림 로더 갈고리가 이름을 보고 처리하고,
#KR_quality(0 4K, 1 글자만 4K, 2 원본)·#KR_fps(120/60)에 지금 값을 적어 준다.
apply(b) -> 고친 바이트. 따로 돌리면 staging/nss.npa 의 sys_config.nss 에 걸어 보고 바뀐 곳 수만 보인다.
"""
import re

E = 'cp932'


def one(b, old, new):
    assert b.count(old) == 1, (b.count(old), old[:80])
    return b.replace(old, new)


def L(*lines, tabs=0):
    return ''.join(('\t' * tabs + s if s else '') + '\r\n' for s in lines)


Q = [('CF_KR_Q0', 575, 'バイリニア'), ('CF_KR_Q1', 676, 'ハードウェア補間'), ('CF_KR_Q2', 801, 'バイリニア')]
F = [('CF_KR_F60', 637, 'バイリニア'), ('CF_KR_F120', 738, 'バイリニア')]


def cell(name, x, y, img):
    return L(f'CreateChoice("{name}");',
             f'CreateTexture("{name}/MouseUsual/img",0,{x},{y},"cg/sys/config/{img}-切り.png");',
             f'CreateTexture("{name}/MouseOver/img",0,{x},{y},"cg/sys/config/{img}-入り.png");',
             f'CreateTexture("{name}/MouseClick/img",101000,{x},{y},"cg/sys/config/{img}-入り.png");',
             f'CreateTexture("{name}_ON",101001,{x},{y},"cg/sys/config/{img}-入り.png");',
             f'Fade("{name}_ON",0,0,null,false);', '', tabs=2)


def apply(b):
    # 1) 고르기 고리: 둘째 쪽에 「다음」, 셋째 쪽 고르기 덩어리
    b = one(b, L('case "CF_BACK"', '{', '\tRequest("決定音",Play);', '\t$CF_Page = 1;', tabs=4).encode(E),
            (L('case "CF_NEXT"', '{', '\tRequest("決定音",Play);', '\t$CF_Page = 3;', '\tinitConfig();', '}', tabs=4)
             + L('case "CF_BACK"', '{', '\tRequest("決定音",Play);', '\t$CF_Page = 1;', tabs=4)).encode(E))
    page3 = L('else if($CF_Page==3)', '{', '\tselect', '\t{',
              '\t\tif(($SYSTEM_keydown_esc||$SYSTEM_buttondown_close)&&!$Title_Config){', '\t\t\tcall_chapter nss/sys_close.nss;', '\t\t}',
              '\t\tif($SYSTEM_r_button_down||$SYSTEM_keydown_c){', '\t\t\t$SYSTEM_menu_config_enable=false;', '\t\t\t$SYSTEM_keydown_c=false;', '\t\t\tbreak;', '\t\t}', tabs=2)
    for name, cmd in (('CF_KR_Q0', 'q0'), ('CF_KR_Q1', 'q1'), ('CF_KR_Q2', 'q2'), ('CF_KR_F60', 'f60'), ('CF_KR_F120', 'f120')):
        page3 += L(f'case "{name}"', '{', '\tRequest("決定音",Play);', f'\tkr_cfg_cmd("nss/kr_cmd_{cmd}.png");', '\tcf_sethilight();', '}', tabs=4)
    page3 += L('case "CF_BACK"', '{', '\tRequest("決定音",Play);', '\t$CF_Page = 2;', '\tinitConfig();', '}',
               'case "CF_EXIT"', '{', '\tRequest("決定音",Play);', '\t$SYSTEM_menu_config_enable=false;', '}', tabs=4)
    page3 += L('\t}', '}', tabs=2)
    b = one(b, L('Wait(32);', tabs=2).encode(E), page3.encode(E) + L('Wait(32);', tabs=2).encode(E))

    # 2) initConfig: 둘째 쪽 분기 이름 붙이기, 흐린 「다음」 → 진짜 「다음」, 셋째 쪽 만들기
    b = one(b, L('else', '{', '', '\tCreateChoice("CF_BGM再生設定_ON");', tabs=1).encode(E),
            L('else if($CF_Page==2)', '{', '', '\tCreateChoice("CF_BGM再生設定_ON");', tabs=1).encode(E))
    nextreal = (L('CreateChoice("CF_NEXT");', 'CreateTexture("CF_NEXT/MouseUsual/img", 0, 798, 516, "cg/sys/config/ko_hit_next.png");', tabs=2)
                + L('CreateTexture("CF_VIS_NEXT", 101000, 798, 516, "cg/sys/config/next-001.png");', tabs=1)
                + L('SetVertex("CF_VIS_NEXT", 0, 0);', 'Zoom("CF_VIS_NEXT", 0, 250, 250, null, false);', tabs=2)
                + L('Request("CF_VIS_NEXT", Smoothing);', tabs=1)
                + L('CreateTexture("CF_NEXT/MouseOver/img", 101001, 798, 516, "cg/sys/config/next-002.png");', 'SetVertex("CF_NEXT/MouseOver/img", 0, 0);', 'Zoom("CF_NEXT/MouseOver/img", 0, 250, 250, null, false);', tabs=2)
                + L('Request("CF_NEXT/MouseOver/img", Smoothing);', tabs=1)
                + L('CreateTexture("CF_NEXT/MouseClick/img", 101001, 798, 516, "cg/sys/config/next-003.png");', 'SetVertex("CF_NEXT/MouseClick/img", 0, 0);', 'Zoom("CF_NEXT/MouseClick/img", 0, 250, 250, null, false);', tabs=2)
                + L('Request("CF_NEXT/MouseClick/img", Smoothing);', tabs=1))
    dummy = (L('CreateTexture("CF_NEXT_Dummy", 101000, 798, 516, "cg/sys/config/next-001.png");', 'SetVertex("CF_NEXT_Dummy", 0, 0);', 'Zoom("CF_NEXT_Dummy", 0, 250, 250, null, false);', tabs=2)
             + L('Request("CF_NEXT_Dummy", Smoothing);', tabs=1))
    back = (L('CreateChoice("CF_BACK");', 'CreateTexture("CF_BACK/MouseUsual/img", 0, 700, 516, "cg/sys/config/ko_hit_back.png");', tabs=2)
            + L('CreateTexture("CF_VIS_BACK", 101000, 700, 516, "cg/sys/config/back-001.png");', tabs=1)
            + L('SetVertex("CF_VIS_BACK", 0, 0);', 'Zoom("CF_VIS_BACK", 0, 250, 250, null, false);', tabs=2)
            + L('Request("CF_VIS_BACK", Smoothing);', tabs=1)
            + L('CreateTexture("CF_BACK/MouseOver/img", 101001, 700, 516, "cg/sys/config/back-002.png");', 'SetVertex("CF_BACK/MouseOver/img", 0, 0);', 'Zoom("CF_BACK/MouseOver/img", 0, 250, 250, null, false);', tabs=2)
            + L('Request("CF_BACK/MouseOver/img", Smoothing);', tabs=1)
            + L('CreateTexture("CF_BACK/MouseClick/img", 101001, 700, 516, "cg/sys/config/back-003.png");', 'SetVertex("CF_BACK/MouseClick/img", 0, 0);', 'Zoom("CF_BACK/MouseClick/img", 0, 250, 250, null, false);', tabs=2)
            + L('Request("CF_BACK/MouseClick/img", Smoothing);', tabs=1))
    b = one(b, (dummy + '\r\n' + back + L('}', '', 'CreateChoice("CF_EXIT");', tabs=1)).encode(E),
            (nextreal + '\r\n' + back + L('}', tabs=1)
             + L('else', '{', tabs=1)
             + L('CreateTexture("CF_BG03", 101000, 0, 0, "nss/kr_cfg_page3.png");', 'SetVertex("CF_BG03", 0, 0);', 'Zoom("CF_BG03", 0, 250, 250, null, false);', tabs=2)
             + L('Request("CF_BG03", Smoothing);', '#KR_quality=0;', '#KR_fps=120;', 'kr_cfg_cmd("nss/kr_cmd_get.png");', '', tabs=2)
             + ''.join(cell(n, x, 43, img) for n, x, img in Q) + ''.join(cell(n, x, 79, img) for n, x, img in F)
             + dummy + '\r\n' + back + L('}', '', 'CreateChoice("CF_EXIT");', tabs=1)).encode(E))

    # 3) cf_sethilight: 둘째 쪽은 진짜 「다음」을 보이고, 셋째 쪽 강조
    b = one(b, L('else', '{', '\tFade("CF_背景02",0,1000,null,false);', tabs=1).encode(E),
            L('else if($CF_Page == 2)', '{', '\tFade("CF_背景02",0,1000,null,false);', tabs=1).encode(E))
    tail = (L('Fade("CF_NEXT_Dummy",0,500,null,false);', 'Fade("CF_BACK/MouseUsual/img",0,1000,null,false);', tabs=2)
            + L('Fade("CF_VIS_BACK",0,1000,null,false);', '}', 'Fade("CF_Waku",0,1000,null,false);', tabs=1))
    hl = L('else', '{', tabs=1) + L('Fade("CF_BG03",0,1000,null,false);',
                                    'if(#KR_quality==0){Fade("CF_KR_Q0_ON",0,1000,null,false);}',
                                    'if(#KR_quality==1){Fade("CF_KR_Q1_ON",0,1000,null,false);}',
                                    'if(#KR_quality==2){Fade("CF_KR_Q2_ON",0,1000,null,false);}',
                                    'if(#KR_fps==60){Fade("CF_KR_F60_ON",0,1000,null,false);}else{Fade("CF_KR_F120_ON",0,1000,null,false);}',
                                    'Fade("CF_NEXT_Dummy",0,500,null,false);', 'Fade("CF_BACK/MouseUsual/img",0,1000,null,false);', tabs=2) \
        + L('Fade("CF_VIS_BACK",0,1000,null,false);', '}', 'Fade("CF_Waku",0,1000,null,false);', tabs=1)
    b = one(b, tail.encode(E),
            (L('Fade("CF_NEXT/MouseUsual/img",0,1000,null,false);', tabs=2) + L('Fade("CF_VIS_NEXT",0,1000,null,false);', tabs=1)
             + L('Fade("CF_BACK/MouseUsual/img",0,1000,null,false);', tabs=2) + L('Fade("CF_VIS_BACK",0,1000,null,false);', '}', tabs=1) + hl).encode(E))

    # 4) cf_setfocus: 둘째 쪽 끝에 「다음」 초점, 셋째 쪽 초점
    end2 = L('SetNextFocus("CF_ユーザ登録/MouseUsual/img","CF_HP/MouseUsual/img",RIGHT);', '', tabs=2) + '\t}\r\n}\r\n'
    sf = lambda a, c, d: f'SetNextFocus("{a}/MouseUsual/img","{c}/MouseUsual/img",{d});'
    f2 = L(sf('CF_BACK', 'CF_NEXT', 'RIGHT'), sf('CF_NEXT', 'CF_BACK', 'LEFT'), sf('CF_NEXT', 'CF_EXIT', 'RIGHT'), sf('CF_EXIT', 'CF_NEXT', 'LEFT'),
           sf('CF_NEXT', 'CF_バイリニア', 'UP'), sf('CF_NEXT', 'CF_BGM再生設定_OFF', 'DOWN'), tabs=2)
    q = ['CF_KR_Q0', 'CF_KR_Q1', 'CF_KR_Q2']; f = ['CF_KR_F60', 'CF_KR_F120']
    f3 = []
    for i, n in enumerate(q):
        f3 += [sf(n, q[i - 1], 'LEFT'), sf(n, q[(i + 1) % 3], 'RIGHT'), sf(n, 'CF_BACK', 'UP'), sf(n, f[min(i, 1)], 'DOWN')]
    for i, n in enumerate(f):
        f3 += [sf(n, f[1 - i], 'LEFT'), sf(n, f[1 - i], 'RIGHT'), sf(n, q[i], 'UP'), sf(n, 'CF_BACK', 'DOWN')]
    f3 += [sf('CF_BACK', 'CF_EXIT', 'LEFT'), sf('CF_BACK', 'CF_EXIT', 'RIGHT'), sf('CF_BACK', 'CF_KR_F60', 'UP'), sf('CF_BACK', 'CF_KR_Q0', 'DOWN'),
           sf('CF_EXIT', 'CF_BACK', 'LEFT'), sf('CF_EXIT', 'CF_BACK', 'RIGHT'), sf('CF_EXIT', 'CF_KR_F120', 'UP'), sf('CF_EXIT', 'CF_KR_Q0', 'DOWN')]
    b = one(b, end2.encode(E), (L('SetNextFocus("CF_ユーザ登録/MouseUsual/img","CF_HP/MouseUsual/img",RIGHT);', '', tabs=2) + f2
                               + '\t}\r\n' + L('else', '{', tabs=1) + L(*f3, tabs=2) + '\t}\r\n}\r\n').encode(E))
    # cf_setfocus 의 첫 분기 이름: if( $CF_Page == 1 ) ... else → else if( $CF_Page == 2 )
    i = b.index(b'function cf_setfocus(){'); j = b.index(b'\r\n\telse\r\n\t{\r\n', i)
    assert j < b.index(b'function cf_voiceset()')
    b = b[:j] + b'\r\n\telse if( $CF_Page == 2 )\r\n\t{\r\n' + b[j + len(b'\r\n\telse\r\n\t{\r\n'):]

    # 5) 명령 함수(파일 끝)
    b += L('', 'function kr_cfg_cmd($kr_file)', '{',
           '\t// Claude 11-21: the runtime DLL reads this picture name (kr_cmd_*) and writes #KR_quality / #KR_fps.',
           '\tCreateTexture("CF_KR_CMD", 0, 0, 0, $kr_file);', '\tDelete("CF_KR_CMD");', '}').encode(E)
    return b


if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, r'P:\AI\gclx-fix\tools')
    from npa_adapter import NPA
    a = NPA(Path(__file__).resolve().parent / 'staging/nss.npa')
    src = [a.read(e) for e in a.entries if e['name'] == 'sys_config.nss'][0]
    out = apply(src)
    print(len(src), '->', len(out))
    Path(Path(__file__).resolve().parent / 'src/sys_config.patched.cp932.txt').write_text(out.decode('cp932', 'replace'), encoding='utf-8')
