"""감상 화면 「없음」(none.png, 768x432 4배, 투명 위 흰 글자)과 같은 글꼴·크기·자리로 새 칸 글자를 만든다.
python -X utf8 make_tile_label.py <none.png> <글자> <출력.png>"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = r'P:\AI\gclx-codexrun\game\fonts\NotoSansKR-VF.ttf'
ref = np.asarray(Image.open(sys.argv[1]).convert('RGBA'))[..., 3].astype(float) / 255
ry, rx = np.where(ref > 0.5)
rcx, rbot = (rx.min() + rx.max()) / 2, ry.max()


def render(text, size, weight, cx=None, bottom=None):
    f = ImageFont.truetype(FONT, size); f.set_variation_by_axes([weight])
    im = Image.new('RGBA', (768, 432), (255, 255, 255, 0))
    ImageDraw.Draw(im).text((0, 0), text, font=f, fill=(255, 255, 255, 255))
    a = np.asarray(im)[..., 3]; ys, xs = np.where(a > 128)
    if cx is None:
        return im, xs, ys
    dx = int(round(cx - (xs.min() + xs.max()) / 2)); dy = int(round(bottom - ys.max()))
    out = Image.new('RGBA', (768, 432), (255, 255, 255, 0))
    ImageDraw.Draw(out).text((dx, dy), text, font=f, fill=(255, 255, 255, 255))
    return out


best = None
for size in range(60, 96, 2):
    for weight in (500, 600, 700, 800, 900):
        im = render('없음', size, weight, rcx, rbot)
        s = float(np.abs(np.asarray(im)[..., 3].astype(float) / 255 - ref).sum())
        if best is None or s < best[0]:
            best = (s, size, weight)
print('match size', best[1], 'weight', best[2], 'diff', round(best[0]))
render(sys.argv[2], best[1], best[2], rcx, rbot).save(sys.argv[3])
