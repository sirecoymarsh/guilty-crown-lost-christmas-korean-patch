"""시험 폴더의 shot-*.bmp(4K, 한 장 33MB)를 작은 그림 한 장으로 모은다. --delete 를 주면 모은 뒤 BMP 를 지운다.
python -X utf8 shot_sheet.py <시험 이름> <출력.jpg> [--cols 3] [--width 960] [--delete] [--crop x0,y0,x1,y1(1024x576 좌표)]
"""
import argparse, sys
from pathlib import Path
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument('run'); ap.add_argument('out')
ap.add_argument('--cols', type=int, default=3); ap.add_argument('--width', type=int, default=960)
ap.add_argument('--delete', action='store_true'); ap.add_argument('--crop', default='')
a = ap.parse_args()
prof = Path(r'F:\AI\gclx-4k\testrun') / a.run / 'profile'
shots = sorted(prof.glob('shot-*.bmp'))
if not shots:
    raise SystemExit('shot 없음')
tiles = []
for p in shots:
    im = Image.open(p).convert('RGB')
    if a.crop:
        x0, y0, x1, y1 = [int(v) for v in a.crop.split(',')]
        sx, sy = im.width / 1024, im.height / 576
        im = im.crop((int(x0 * sx), int(y0 * sy), int(x1 * sx), int(y1 * sy)))
    h = round(im.height * a.width / im.width)
    im = im.resize((a.width, h), Image.LANCZOS)
    ImageDraw.Draw(im).text((8, 6), p.stem, fill=(255, 255, 0))
    tiles.append(im)
rows = (len(tiles) + a.cols - 1) // a.cols
W, H = a.width, tiles[0].height
sheet = Image.new('RGB', (W * a.cols, H * rows), (40, 40, 40))
for i, im in enumerate(tiles):
    sheet.paste(im, ((i % a.cols) * W, (i // a.cols) * H))
sheet.save(a.out, quality=88)
print(a.out, sheet.size, len(tiles), 'shots')
if a.delete:
    for p in shots:
        p.unlink()
    print('deleted', len(shots), 'bmp')
