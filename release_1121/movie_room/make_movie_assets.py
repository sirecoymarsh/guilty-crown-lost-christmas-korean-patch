"""영상 감상 화면 그림(사용자 11-23 「영상 감상. 오프닝, 중간 영상, 아이캐치를 타이틀에서 다시 봐」).
- kr_mov_bg.png: 사운드 목록 바탕(scenario/make_ui_assets.py 의 kr_snd_bg.png)과 같은 꼴로 세 줄(갈래 「영상」, 번호 01~03).
- kr_title_movie-000..003.png: 타이틀 「영상」 단추(scenario/make_title_button.py 로 만든 것을 그대로 가져옴).
python -I -X utf8 make_movie_assets.py
"""
import json, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SC = Path(r'F:\AI\gclx-4k\scenario')
OUT = HERE / 'assets'; OUT.mkdir(exist_ok=True)
S = 4
SANS = r'P:\AI\gclx-codexrun\game\fonts\NotoSansKR-VF.ttf'
SERIF = r'P:\AI\gclx-codexrun\game\fonts\NotoSerifKR-VF.ttf'
L = json.load(open(SC / 'snd_layout.json'))          # 사운드 화면과 같은 줄 자리
ROWS = 3


def font(path, px, weight):
    f = ImageFont.truetype(path, px * S)
    f.set_variation_by_axes([weight])
    return f


bg = Image.new('RGBA', (1024 * S, 576 * S), (0, 0, 0, 255))
d = ImageDraw.Draw(bg)
ftag, fnum = font(SANS, 13, 600), font(SERIF, 15, 700)


def R(x0, y0, x1, y1, c):
    d.rectangle([round(x0 * S), round(y0 * S), round(x1 * S) - 1, round(y1 * S) - 1], fill=c)


for k in range(ROWS):                               # make_ui_assets.py 의 줄 그리기와 같은 값
    cx, r = L['col_x'][0], k
    y = L['row_y0'] + r * L['pitch']; h = L['h']
    R(cx, y, cx + L['tag_w'], y + h, (27, 27, 27, 255))
    R(cx + L['tag_w'] - 7, y, cx + L['tag_w'] - 6, y + h, (21, 21, 21, 255))
    R(cx + L['tag_w'] - 6, y, cx + L['tag_w'], y + h, (38, 38, 38, 255))
    tag = '영상'
    tw = d.textlength(tag, font=ftag)
    d.text(((cx + (L['tag_w'] - 7) / 2) * S - tw / 2, (y + h / 2) * S), tag, font=ftag, fill=(216, 216, 216, 255), anchor='lm')
    R(cx + L['tag_w'], y + h / 2 - 0.5, cx + L['item_x'], y + h / 2 + 0.5, (38, 38, 38, 255))
    ix, iw = cx + L['item_x'], L['item_w']
    R(ix, y, ix + iw, y + h, (27, 27, 27, 255))
    R(ix + 2, y + 1, ix + iw - 10, y + h - 1, (11, 11, 11, 255))
    R(ix + iw - 10, y, ix + iw, y + h, (38, 38, 38, 255))
    R(ix + iw, y + h / 2 - 0.5, cx + L['num_x'], y + h / 2 + 0.5, (24, 24, 24, 255))
    nx = cx + L['num_x']
    R(nx, y, nx + L['num_w'], y + h, (60, 60, 60, 255))
    R(nx, y, nx + 3, y + h, (48, 48, 48, 255))
    d.text(((nx + 1.5 + L['num_w'] / 2) * S, (y + h / 2) * S), f'{k + 1:02d}', font=fnum, fill=(208, 208, 208, 255), anchor='mm')
# 아래 눈금 줄은 사운드 바탕에서 그대로 옮긴다(원작 환경 설정 화면에서 옮긴 것)
snd = Image.open(SC / 'build/kr_snd_bg.png').convert('RGBA')
bg.paste(snd.crop((0, 500 * S, 1024 * S, 540 * S)), (0, 500 * S))
bg.save(OUT / 'kr_mov_bg.png')
for i in range(4):
    shutil.copy2(Path(r'Y:\AI\claude-work\gclx-movie\assets') / f'kr_title_movie-{i:03d}.png', OUT / f'kr_title_movie-{i:03d}.png')
print('assets ->', OUT, sorted(p.name for p in OUT.iterdir()))
