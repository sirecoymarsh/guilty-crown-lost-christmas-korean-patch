"""환경 설정 셋째 쪽(한국어판 화면 설정) 배경 그림을 원래 첫째 쪽 그림(4096x2304, 대본이 Zoom 250 으로 줄여 씀)에서 만든다.
줄 0 「화면 | 화질 (F8) | 4K · 글자만 4K · 원본 | 01」, 줄 1 「화면 | 초당 프레임 | 60 · 120 | 02」, 아래에 짧은 설명.
글꼴·크기·색은 코덱스 build_ui.py 와 같다(Noto Sans KR VF 600, 1x 기준 줄 글 15px·분류 13px·칸 13px, 색 218).
강조는 원래 1x 강조 그림(흰색 α89 상자)을 그대로 쓰므로, 칸 너비는 그 그림 너비(87·111)에 맞춘다.
python -I -X utf8 make_cfg_page3.py  -> assets/kr_cfg_page3.png, assets/kr_cmd_*.png, qa/cfg_page3_preview.png
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
W = Path(__file__).resolve().parent
SRC = Path(r'F:\AI\gclx-4k\scenario\ui_survey\sys__config__コンフィグ背景page-01.png')
FONT = r'C:\Windows\Fonts\NotoSansKR-VF.ttf'
S = 4
(W / 'assets').mkdir(exist_ok=True); (W / 'qa').mkdir(exist_ok=True)

# 칸 배치 (1x 좌표): 행 i 의 칸 상자는 y=43+36i ~ 63+36i (원래 강조 그림 자리와 같다)
ROWS = [
    {'tag': '화면', 'label': '화질 (F8 키로도 전환)', 'cells': [(575, 87, '4K'), (676, 111, '글자만 4K'), (801, 87, '원본')]},
    {'tag': '화면', 'label': '초당 프레임', 'cells': [(637, 87, '60'), (738, 87, '120')]},
]
NOTES = ['화질 ― 4K: 그림과 글자 모두 고해상도  ·  글자만 4K: 그림은 원래 해상도  ·  원본: 원래 게임 화면',
         '초당 프레임 ― 120: 움직임이 더 부드럽습니다  ·  60: 원래 게임과 같습니다']


def font(px, weight=600):
    f = ImageFont.truetype(FONT, round(px * S))
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def text(d, s, slot, px, align='left', color=(218, 218, 218, 255)):
    x0, y0, x1, y1 = slot
    while True:
        f = font(px); b = d.textbbox((0, 0), s, font=f)
        if b[2] - b[0] <= (x1 - x0) * S or px <= 8:
            break
        px -= .25
    tw, th = b[2] - b[0], b[3] - b[1]
    x = x0 * S if align == 'left' else (x0 + x1) * S / 2 - tw / 2
    y = (y0 + y1) * S / 2 - th / 2
    d.text((round(x - b[0]), round(y - b[1])), s, font=f, fill=color)


src = Image.open(SRC).convert('RGBA'); a = np.array(src)
out = a.copy()
# 줄 2~11 을 지운다(바탕은 검정 0). 맨 아래 눈금자(y≈2080~2180)는 둔다.
out[(43 + 36 * 2 - 8) * S:(63 + 36 * 11 + 8) * S, :, :3] = 0
for i, row in enumerate(ROWS):
    y = 46 + 36 * i
    # 분류 칸·줄 글 칸의 글자를 그 칸 바탕색으로 지운다(코덱스와 같은 칸)
    out[y * S:(y + 18) * S, 10 * S:80 * S, :3] = 27
    out[y * S:(y + 18) * S, 137 * S:466 * S, :3] = 11
    # 오른쪽(이음선·칸): 막대 끝(1929) ~ 번호 칸 앞(3926)을 지우고 이음선을 다시 깐다
    top, bot = (43 + 36 * i - 8) * S, (63 + 36 * i + 8) * S
    out[top:bot, 1929:3927, :3] = 0
    ly = 207 + 144 * i
    line = a[ly:ly + 10, 2300:2301, :3]              # 원래 이음선 세로 단면(10px)
    out[ly:ly + 10, 1929:3927, :3] = line
    # 칸 묶음: 테두리 38, 안 0, 칸 사이 칸막이 38 (원래 켬·끔 묶음 꼴)
    x0 = row['cells'][0][0]; x1 = row['cells'][-1][0] + row['cells'][-1][1]
    c0, c1 = (43 + 36 * i) * S, (63 + 36 * i) * S
    out[c0:c1, x0 * S:x1 * S, :3] = 38
    for cx, cw, _ in row['cells']:
        out[c0 + 4:c1 - 4, cx * S + 4:(cx + cw) * S - 4, :3] = 0
img = Image.fromarray(out)
d = ImageDraw.Draw(img)
for i, row in enumerate(ROWS):
    y = 46 + 36 * i
    text(d, row['tag'], (10, y, 80, y + 18), 13, 'center')
    text(d, row['label'], (137, y, 466, y + 18), 15, 'left')
    for cx, cw, s in row['cells']:
        text(d, s, (cx + 2, 44 + 36 * i, cx + cw - 2, 61 + 36 * i), 13, 'center')
for k, s in enumerate(NOTES):
    y = 46 + 36 * (len(ROWS) + 1) + 26 * k
    text(d, s, (137, y, 960, y + 16), 12.5, 'left', (150, 150, 150, 255))
img.save(W / 'assets/kr_cfg_page3.png', optimize=True)

# 대본 → DLL 명령용 1x1 투명 그림(이름만 쓴다)
for n in ('q0', 'q1', 'q2', 'f60', 'f120', 'get'):
    Image.new('RGBA', (1, 1), (0, 0, 0, 0)).save(W / f'assets/kr_cmd_{n}.png')

# 미리보기: 1x 로 줄이고 강조 그림(화질 4K·프레임 120 선택)을 얹는다
pv = img.resize((1024, 576), Image.LANCZOS)
hi = lambda w: Image.new('RGBA', (w, 20), (255, 255, 255, 89))
pv.alpha_composite(hi(87), (575, 43)); pv.alpha_composite(hi(87), (738, 79))
pv.resize((2048, 1152), Image.LANCZOS).save(W / 'qa/cfg_page3_preview.png')
print('ok', img.size)
