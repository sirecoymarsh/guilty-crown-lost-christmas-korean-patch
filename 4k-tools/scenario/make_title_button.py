"""타이틀 단추 그림(768x144, 4배; 대본이 25% 로 줄여 그림)을 원래 단추와 같은 글꼴·크기·색으로 만든다.
원래 「불러오기」(load-001)에 Noto Sans KR(게임 동봉 VF) 굵기·크기·자리를 맞춘 뒤 같은 값으로 새 글자를 그린다.
python -X utf8 make_title_button.py <원래 load-001.png> <글자> <출력 앞머리>   → <앞머리>-001/002/003.png (회색·검정·파랑)"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = r'P:\AI\gclx-codexrun\game\fonts\NotoSansKR-VF.ttf'
ref = np.asarray(Image.open(sys.argv[1]).convert('RGBA'))[..., 3].astype(float) / 255
COLORS = [(76, 76, 76), (0, 0, 0), (23, 78, 129)]


def render(text, size, weight, x, y, color=(0, 0, 0)):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    im = Image.new('RGBA', (768, 144), color + (0,))
    ImageDraw.Draw(im).text((x, y), text, font=f, fill=color + (255,))
    return im


def score(size, weight):
    im = render('불러오기', size, weight, 0, 0)
    a = np.asarray(im)[..., 3]
    ys, xs = np.where(a > 128)
    ry, rx = np.where(ref > 0.5)
    dx, dy = rx.min() - xs.min(), ry.min() - ys.min()
    im = render('불러오기', size, weight, dx, dy)
    a = np.asarray(im)[..., 3].astype(float) / 255
    return float(np.abs(a - ref).sum()), dx, dy


best = None
for size in range(86, 104, 2):
    for weight in (400, 500, 600, 700):
        s, dx, dy = score(size, weight)
        if best is None or s < best[0]:
            best = (s, size, weight, dx, dy)
s, size, weight, dx, dy = best
for size2 in (size - 1, size, size + 1):
    for w2 in range(weight - 60, weight + 61, 20):
        s2, dx2, dy2 = score(size2, w2)
        if s2 < best[0]:
            best = (s2, size2, w2, dx2, dy2)
s, size, weight, dx, dy = best
print('match: size', size, 'weight', weight, 'offset', dx, dy, 'diff', round(s))
for i, c in enumerate(COLORS, 1):
    render(sys.argv[2], size, weight, dx, dy, c).save(f'{sys.argv[3]}-{i:03d}.png')
# hit picture (1x 192x36 opaque, like load-000) sized to the label
a = np.asarray(render(sys.argv[2], size, weight, dx, dy))[..., 3]
xs = np.where(a.max(axis=0) > 0)[0]
w1 = int(np.ceil((xs.max() + 16) / 4)); w1 = max(w1, 60)
Image.new('RGBA', (w1, 36), (0, 0, 0, 255)).save(f'{sys.argv[3]}-000.png')
print('hit width', w1)
