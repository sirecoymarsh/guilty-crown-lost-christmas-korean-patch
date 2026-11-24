"""11-24 두 가지:
1) 「옵션에 실행할때 처음 로고 동영상들 스킵하는걸 넣어줘」 — 시작 때 니트로플러스 로고·주의(Attention)·경고(Caution) 화면
   (0_boot TitleLogoBase, 약 20초)을 건너뛰는 설정. 환경 설정 셋째 쪽에 셋째 줄 「시작 로고 · 보기 / 건너뛰기」, 값은 #KR_SKIPLOGO.
2) 「회상에서 휠을 굴리면 페이지 이동하게 해줘」 — 회상 목록(kr_scenario KsList)에서 휠 아래 = 다음 쪽, 위 = 이전 쪽.
대본은 cp932(sys_config·0_boot)·cp949(kr_scenario). 셋째 쪽 그림은 make_page3_image() 로 다시 그린다(make_cfg_page3.py 와 같은 법).
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np, io

E = 'cp932'


def one(b, old, new, enc=E):
    o, n = old.encode(enc), new.encode(enc)
    assert b.count(o) == 1, (b.count(o), old[:70])
    return b.replace(o, n)


def cell(name, x, y, img='バイリニア'):
    t = '\t\t'
    return (f'{t}CreateChoice("{name}");\r\n'
            f'{t}CreateTexture("{name}/MouseUsual/img",0,{x},{y},"cg/sys/config/{img}-切り.png");\r\n'
            f'{t}CreateTexture("{name}/MouseOver/img",0,{x},{y},"cg/sys/config/{img}-入り.png");\r\n'
            f'{t}CreateTexture("{name}/MouseClick/img",101000,{x},{y},"cg/sys/config/{img}-入り.png");\r\n'
            f'{t}CreateTexture("{name}_ON",101001,{x},{y},"cg/sys/config/{img}-入り.png");\r\n'
            f'{t}Fade("{name}_ON",0,0,null,false);\r\n\r\n')


def patch_config(b):
    # 고르기: 셋째 쪽 case 두 개
    tail = 'kr_cfg_cmd("nss/kr_cmd_f120.png");\r\n\t\t\t\t\tcf_sethilight();\r\n\t\t\t\t}\r\n'
    add = ''
    for name, v in (('CF_KR_L0', 'false'), ('CF_KR_L1', 'true')):
        add += (f'\t\t\t\tcase "{name}"\r\n\t\t\t\t{{\r\n\t\t\t\t\tRequest("決定音",Play);\r\n'
                f'\t\t\t\t\t#KR_SKIPLOGO={v};\r\n\t\t\t\t\tcf_sethilight();\r\n\t\t\t\t}}\r\n')
    b = one(b, tail, tail + add)
    # 칸 두 개(셋째 줄, y=115)
    a = 'Fade("CF_KR_F120_ON",0,0,null,false);\r\n\r\n'
    b = one(b, a, a + cell('CF_KR_L0', 637, 115) + cell('CF_KR_L1', 738, 115))
    # 강조
    a = 'if(#KR_fps==60){Fade("CF_KR_F60_ON",0,1000,null,false);}else{Fade("CF_KR_F120_ON",0,1000,null,false);}\r\n'
    b = one(b, a, a + '\t\tif(#KR_SKIPLOGO){Fade("CF_KR_L1_ON",0,1000,null,false);}else{Fade("CF_KR_L0_ON",0,1000,null,false);}\r\n')
    # 키보드 초점: 프레임 줄 아래 = 로고 줄, 로고 줄 아래 = 돌아가기
    sf = lambda x, y, d: f'SetNextFocus("{x}/MouseUsual/img","{y}/MouseUsual/img",{d});'
    b = one(b, sf('CF_KR_F60', 'CF_BACK', 'DOWN'), sf('CF_KR_F60', 'CF_KR_L0', 'DOWN'))
    b = one(b, sf('CF_KR_F120', 'CF_BACK', 'DOWN'),
            sf('CF_KR_F120', 'CF_KR_L1', 'DOWN') + '\r\n\t\t'
            + '\r\n\t\t'.join([sf('CF_KR_L0', 'CF_KR_L1', 'LEFT'), sf('CF_KR_L0', 'CF_KR_L1', 'RIGHT'), sf('CF_KR_L0', 'CF_KR_F60', 'UP'), sf('CF_KR_L0', 'CF_BACK', 'DOWN'),
                               sf('CF_KR_L1', 'CF_KR_L0', 'LEFT'), sf('CF_KR_L1', 'CF_KR_L0', 'RIGHT'), sf('CF_KR_L1', 'CF_KR_F120', 'UP'), sf('CF_KR_L1', 'CF_BACK', 'DOWN')]))
    b = one(b, sf('CF_BACK', 'CF_KR_F60', 'UP'), sf('CF_BACK', 'CF_KR_L0', 'UP'))
    b = one(b, sf('CF_EXIT', 'CF_KR_F120', 'UP'), sf('CF_EXIT', 'CF_KR_L1', 'UP'))
    return patch_config_readcolor(b, sf)


def patch_config_readcolor(b, sf):
    """11-24 사용자 「게임에서 이미 읽은 장면이라면 글자를 하늘색으로 표시하는 기능 어때?」 — 원작에 있다:
    #SYSTEM_read_text_color_change(기본 끔)·#SYSTEM_read_text_incolor=#41b3ff(하늘색). 1.10 에 넣은 기능인데 이 판의 환경 설정
    화면에는 단추가 없어(cf_sethilight 의 CF_既読色変更 만 남음) 켤 길이 없었다 → 셋째 쪽 넷째 줄 「읽은 글 · 그대로/하늘색」."""
    tail = '\t\t\t\t\t#KR_SKIPLOGO=true;\r\n\t\t\t\t\tcf_sethilight();\r\n\t\t\t\t}\r\n'
    add = ''
    for name, v in (('CF_KR_R0', 'false'), ('CF_KR_R1', 'true')):
        add += (f'\t\t\t\tcase "{name}"\r\n\t\t\t\t{{\r\n\t\t\t\t\tRequest("決定音",Play);\r\n'
                f'\t\t\t\t\t#SYSTEM_read_text_color_change={v};\r\n\t\t\t\t\tcf_sethilight();\r\n\t\t\t\t}}\r\n')
    b = one(b, tail, tail + add)
    a = 'Fade("CF_KR_L1_ON",0,0,null,false);\r\n\r\n'
    b = one(b, a, a + cell('CF_KR_R0', 637, 151) + cell('CF_KR_R1', 738, 151))
    a = '\t\tif(#KR_SKIPLOGO){Fade("CF_KR_L1_ON",0,1000,null,false);}else{Fade("CF_KR_L0_ON",0,1000,null,false);}\r\n'
    b = one(b, a, a + '\t\tif(#SYSTEM_read_text_color_change){Fade("CF_KR_R1_ON",0,1000,null,false);}else{Fade("CF_KR_R0_ON",0,1000,null,false);}\r\n')
    b = one(b, sf('CF_KR_L0', 'CF_BACK', 'DOWN'), sf('CF_KR_L0', 'CF_KR_R0', 'DOWN') + '\r\n\t\t' + '\r\n\t\t'.join([
        sf('CF_KR_R0', 'CF_KR_R1', 'LEFT'), sf('CF_KR_R0', 'CF_KR_R1', 'RIGHT'), sf('CF_KR_R0', 'CF_KR_L0', 'UP'), sf('CF_KR_R0', 'CF_BACK', 'DOWN'),
        sf('CF_KR_R1', 'CF_KR_R0', 'LEFT'), sf('CF_KR_R1', 'CF_KR_R0', 'RIGHT'), sf('CF_KR_R1', 'CF_KR_L1', 'UP'), sf('CF_KR_R1', 'CF_BACK', 'DOWN')]))
    b = one(b, sf('CF_KR_L1', 'CF_BACK', 'DOWN'), sf('CF_KR_L1', 'CF_KR_R1', 'DOWN'))
    b = one(b, sf('CF_BACK', 'CF_KR_L0', 'UP'), sf('CF_BACK', 'CF_KR_R0', 'UP'))
    b = one(b, sf('CF_EXIT', 'CF_KR_L1', 'UP'), sf('CF_EXIT', 'CF_KR_R1', 'UP'))
    return b


def patch_boot(b):
    a = '\t\tTitleLogoBase();\r\n\t}\r\n\r\n//\tTitleLogoBase();'
    return one(b, a, '\t\tif(!#KR_SKIPLOGO){TitleLogoBase();}   // Claude 11-24: settings page 3 \'start logos: skip\'\r\n\t}\r\n\r\n//\tTitleLogoBase();')


def patch_recall(b):
    a = ('\t$SYSTEM_r_button_down=false;\r\n\t$KS_LOOP=true;\r\n\twhile($KS_LOOP){\r\n\t\tselect{\r\n'
         '\t\t\tif($SYSTEM_r_button_down){$SYSTEM_r_button_down=false;$KS_LOOP=false;$KS_RUN=false;break;}\r\n')
    n = ('\t$SYSTEM_r_button_down=false;\r\n\t$SYSTEM_mousewheel_down=false;\r\n\t$SYSTEM_mousewheel_up=false;\r\n\t$KS_LOOP=true;\r\n\twhile($KS_LOOP){\r\n\t\tselect{\r\n'
         '\t\t\tif($SYSTEM_r_button_down){$SYSTEM_r_button_down=false;$KS_LOOP=false;$KS_RUN=false;break;}\r\n'
         '\t\t\t// Claude 11-24: 휠 아래 = 다음 쪽, 위 = 이전 쪽(사용자 「회상에서 휠을 굴리면 페이지 이동하게 해줘」)\r\n'
         '\t\t\tif($SYSTEM_mousewheel_down){$SYSTEM_mousewheel_down=false;Request("@ks_se_ok",Play);$KS_ARM=false;KsPageStep(1);break;}\r\n'
         '\t\t\tif($SYSTEM_mousewheel_up){$SYSTEM_mousewheel_up=false;Request("@ks_se_ok",Play);$KS_ARM=false;KsPageStep(-1);break;}\r\n')
    return one(b, a, n, 'cp949')


def patch_credits(b):
    """11-24 「첫장면 크레딧에 한자를 한국어로 로컬라이징하며 아래 붙는 발음용 글자가 그만 동어 반복이 됐어. 아래 작은 글자는 지워줘」
    lx0010 오프닝 크레딧의 작은 읽기 글(이름에 ルビ 가 든 CreateTextEX 16개, <SPAN size=1>…</SPAN>)을 빈 글로. 물체는 두어
    장면의 Fade·Move 는 그대로 돈다. lx0300 의 두 줄은 원래 주석이라 그대로."""
    import re
    pat = re.compile(rb'(CreateTextEX\("[^"]*\x83\x8b\x83\x72[^"]*",[^"\n]*)"<SPAN size=1>.*?</SPAN>"')
    lines = [l for l in b.split(b'\n') if pat.search(l) and not l.lstrip().startswith(b'//')]
    assert len(lines) == 16, len(lines)
    out, n = pat.subn(lambda m: m.group(1) + b'""' if not b[max(0, b.rfind(b'\n', 0, m.start())):m.start()].lstrip().startswith(b'//') else m.group(0), b)
    return out


# ---- 셋째 쪽 그림(make_cfg_page3.py 와 같은 그리기, 줄 하나 더)
SRC = Path(r'F:\AI\gclx-4k\scenario\ui_survey\sys__config__コンフィグ背景page-01.png')
FONT = r'C:\Windows\Fonts\NotoSansKR-VF.ttf'
S = 4
ROWS = [
    {'tag': '화면', 'label': '화질 (F8 키로도 전환)', 'cells': [(575, 87, '4K'), (676, 111, '글자만 4K'), (801, 87, '원본')]},
    {'tag': '화면', 'label': '초당 프레임', 'cells': [(637, 87, '60'), (738, 87, '120')]},
    {'tag': '시작', 'label': '시작 로고 (니트로플러스·주의 화면)', 'cells': [(637, 87, '보기'), (738, 87, '건너뛰기')]},
    {'tag': '글자', 'label': '이미 읽은 글', 'cells': [(637, 87, '그대로'), (738, 87, '하늘색')]},
]
NOTES = ['화질 ― 4K: 그림과 글자 모두 고해상도  ·  글자만 4K: 그림은 원래 해상도  ·  원본: 원래 게임 화면',
         '초당 프레임 ― 120: 움직임이 더 부드럽습니다  ·  60: 원래 게임과 같습니다',
         '시작 로고 ― 건너뛰기: 게임을 켜면 로고와 주의 화면 없이 바로 타이틀로 갑니다',
         '이미 읽은 글 ― 하늘색: 전에 읽은 대사를 하늘색 글자로 보여 줍니다(원작 기능)']


def _font(px, weight=600):
    f = ImageFont.truetype(FONT, round(px * S))
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def _text(d, s, slot, px, align='left', color=(218, 218, 218, 255)):
    x0, y0, x1, y1 = slot
    while True:
        f = _font(px); b = d.textbbox((0, 0), s, font=f)
        if b[2] - b[0] <= (x1 - x0) * S or px <= 8:
            break
        px -= .25
    tw, th = b[2] - b[0], b[3] - b[1]
    x = x0 * S if align == 'left' else (x0 + x1) * S / 2 - tw / 2
    y = (y0 + y1) * S / 2 - th / 2
    d.text((round(x - b[0]), round(y - b[1])), s, font=f, fill=color)


def make_page3_image():
    src = Image.open(SRC).convert('RGBA'); a = np.array(src)
    out = a.copy()
    out[(43 + 36 * len(ROWS) - 8) * S:(63 + 36 * 11 + 8) * S, :, :3] = 0
    for i, row in enumerate(ROWS):
        y = 46 + 36 * i
        out[y * S:(y + 18) * S, 10 * S:80 * S, :3] = 27
        out[y * S:(y + 18) * S, 137 * S:466 * S, :3] = 11
        top, bot = (43 + 36 * i - 8) * S, (63 + 36 * i + 8) * S
        out[top:bot, 1929:3927, :3] = 0
        ly = 207 + 144 * i
        line = a[207:217, 2300:2301, :3]
        out[ly:ly + 10, 1929:3927, :3] = line
        x0 = row['cells'][0][0]; x1 = row['cells'][-1][0] + row['cells'][-1][1]
        c0, c1 = (43 + 36 * i) * S, (63 + 36 * i) * S
        out[c0:c1, x0 * S:x1 * S, :3] = 38
        for cx, cw, _ in row['cells']:
            out[c0 + 4:c1 - 4, cx * S + 4:(cx + cw) * S - 4, :3] = 0
    img = Image.fromarray(out)
    d = ImageDraw.Draw(img)
    for i, row in enumerate(ROWS):
        y = 46 + 36 * i
        _text(d, row['tag'], (10, y, 80, y + 18), 13, 'center')
        _text(d, row['label'], (137, y, 466, y + 18), 15, 'left')
        for cx, cw, s in row['cells']:
            _text(d, s, (cx + 2, 44 + 36 * i, cx + cw - 2, 61 + 36 * i), 13, 'center')
    for k, s in enumerate(NOTES):
        y = 46 + 36 * (len(ROWS) + 1) + 26 * k
        _text(d, s, (137, y, 960, y + 16), 12.5, 'left', (150, 150, 150, 255))
    bio = io.BytesIO(); img.save(bio, format='PNG', optimize=True); return bio.getvalue()


if __name__ == '__main__':
    import sys
    Path(sys.argv[1]).write_bytes(make_page3_image())
