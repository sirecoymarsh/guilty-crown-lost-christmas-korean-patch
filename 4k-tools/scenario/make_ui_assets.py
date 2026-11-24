"""회상·사운드 화면 그림(4배, 대본이 25% 로 줄여 그림 — 원작 4096x2304 그림과 같은 방식).
- kr_bars.png: 원작 CG 감상 위아래 은빛 띠(cglib/no001.png)에서 「1쪽」 글자만 지운 것. 상세·사운드 화면 틀.
- kr_snd_bg.png: 사운드 목록 바탕. 원작 환경 설정 화면(config/コンフィグ背景.png)의 줄 꼴 — 왼쪽 갈래 칸 · 이음줄 · 이름 칸 · 이음줄 · 번호 칸.
  곡 이름은 대본이 글자로 얹는다(열리기 전엔 「아직 듣지 않은 곡」). 아래 눈금 줄도 원작 화면에서 그대로 옮긴다.
python -X utf8 make_ui_assets.py <ui_survey 폴더> <출력 폴더>
배치(1배 좌표)는 SND_LAYOUT 하나로 정하고 gen_viewer.py 가 같은 값을 읽는다."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
survey, out = Path(sys.argv[1]), Path(sys.argv[2])
S = 4
SANS = r'P:\AI\gclx-codexrun\game\fonts\NotoSansKR-VF.ttf'
SERIF = r'P:\AI\gclx-codexrun\game\fonts\NotoSerifKR-VF.ttf'
# 사운드 줄 배치(1배): 두 기둥, 10줄, 줄 높이 26, 간격 44 — gen_viewer.py 가 같은 표를 쓴다
# 11-24 사용자 「사운드 모드에서 번호가 앞에 가고 음악 분류가 뒤에 가게 해줘」: 번호 칸(좁음)이 왼쪽, 갈래 칸(넓음)이 오른쪽.
# 이름 칸 자리(item_x·item_w)와 줄 전체 폭(row_w)은 그대로 — 대본의 글자·누름 자리가 바뀌지 않게.
SND_LAYOUT = {'col_x': [26, 524], 'row_y0': 58, 'pitch': 44, 'h': 26, 'tag_w': 64, 'item_x': 80, 'item_w': 316,
              'num_x': 0, 'num_w': 36, 'tag_x': 412, 'row_w': 476, 'rows': 10}
json.dump(SND_LAYOUT, open(HERE / 'snd_layout.json', 'w'), indent=1)


def font(path, px, weight):
    f = ImageFont.truetype(path, px * S)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


# ---------------------------------------------------------------- kr_bars.png
no1 = Image.open(survey / 'sys__extra__cglib__no001.png').convert('RGBA')
bars = no1.copy()
# 「1쪽」 는 아래 띠 왼쪽(1배 x 18~60, y 544~566). 띠는 가로로 고르니 오른쪽 같은 높이 열을 옮겨 덮는다.
x0, x1, y0, y1 = 18 * S, 64 * S, 540 * S, 570 * S
patch = no1.crop((x0 + 600 * S, y0, x1 + 600 * S, y1))
bars.paste(patch, (x0, y0))
bars.save(out / 'kr_bars.png')

# ---------------------------------------------------------------- kr_snd_bg.png
tracks = json.load(open(HERE / 'music_list.json', encoding='utf-8'))
L = SND_LAYOUT
bg = Image.new('RGBA', (1024 * S, 576 * S), (0, 0, 0, 255))
d = ImageDraw.Draw(bg)
ftag, fnum = font(SANS, 13, 600), font(SERIF, 15, 700)


def R(x0, y0, x1, y1, c):
    d.rectangle([round(x0 * S), round(y0 * S), round(x1 * S) - 1, round(y1 * S) - 1], fill=c)


for k, t in enumerate(tracks):
    cx, r = L['col_x'][k // L['rows']], k % L['rows']
    y = L['row_y0'] + r * L['pitch']; h = L['h']
    # 번호 칸(맨 앞): 채움 3C, 왼쪽 띠 30
    nx = cx + L['num_x']
    R(nx, y, nx + L['num_w'], y + h, (60, 60, 60, 255))
    R(nx, y, nx + 3, y + h, (48, 48, 48, 255))
    d.text(((nx + 1.5 + L['num_w'] / 2) * S, (y + h / 2) * S), f'{k + 1:02d}', font=fnum, fill=(208, 208, 208, 255), anchor='mm')
    # 이음줄 → 이름 칸
    R(nx + L['num_w'], y + h / 2 - 0.5, cx + L['item_x'], y + h / 2 + 0.5, (38, 38, 38, 255))
    # 이름 칸: 테두리 1B, 안 0B, 왼쪽 띠 1B, 오른쪽 덩이 26
    ix, iw = cx + L['item_x'], L['item_w']
    R(ix, y, ix + iw, y + h, (27, 27, 27, 255))
    R(ix + 2, y + 1, ix + iw - 10, y + h - 1, (11, 11, 11, 255))
    R(ix + iw - 10, y, ix + iw, y + h, (38, 38, 38, 255))
    # 이음줄 → 갈래 칸(맨 뒤, 원작 「소리」 칸 꼴): 채움 1B, 오른쪽 홈 15 + 덩이 26
    tx0 = cx + L['tag_x']
    R(ix + iw, y + h / 2 - 0.5, tx0, y + h / 2 + 0.5, (24, 24, 24, 255))
    R(tx0, y, tx0 + L['tag_w'], y + h, (27, 27, 27, 255))
    R(tx0 + L['tag_w'] - 7, y, tx0 + L['tag_w'] - 6, y + h, (21, 21, 21, 255))
    R(tx0 + L['tag_w'] - 6, y, tx0 + L['tag_w'], y + h, (38, 38, 38, 255))
    tag = '노래' if t['file'].startswith('lxsong') else '배경음'
    tw = d.textlength(tag, font=ftag)
    d.text(((tx0 + (L['tag_w'] - 7) / 2) * S - tw / 2, (y + h / 2) * S), tag, font=ftag, fill=(216, 216, 216, 255), anchor='lm')
# 아래 눈금 줄(원작 환경 설정 화면 y 505~545 의 오른쪽 눈금; 왼쪽 판 정보 글자는 빼고)
cfg = Image.open(survey / 'sys__config__コンフィグ背景.png').convert('RGBA')
tick = cfg.crop((360 * S, 506 * S, 1024 * S, 540 * S))
bg.paste(tick, (360 * S, 500 * S))
left = cfg.crop((0, 506 * S, 104 * S, 540 * S))
bg.paste(left, (0, 500 * S))
bg.save(out / 'kr_snd_bg.png')
print('kr_bars.png, kr_snd_bg.png ->', out)
