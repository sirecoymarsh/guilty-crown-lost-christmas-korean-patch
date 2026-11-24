"""켬/끔 같은 장면에서 선명도 차이가 가장 큰 곳을 1:1로 잘라 나란히. python -X utf8 crop_compare.py t9 t10 8:8 28:28 ..."""
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
R = Path(r'F:\AI\gclx-4k\testrun')
ta, tb = sys.argv[1], sys.argv[2]
W, H = 900, 640
rows = []
for pair in sys.argv[3:]:
    a, b = map(int, pair.split(':'))
    A = np.asarray(Image.open(R / ta / 'profile' / f'shot-{a:03d}.jpg').convert('RGB'))
    B = np.asarray(Image.open(R / tb / 'profile' / f'shot-{b:03d}.jpg').convert('RGB'))
    ga, gb = (cv2.cvtColor(x, cv2.COLOR_RGB2GRAY).astype(np.float32) for x in (A, B))
    gain = np.abs(cv2.Laplacian(ga, cv2.CV_32F)) - np.abs(cv2.Laplacian(gb, cv2.CV_32F))
    same = np.abs(cv2.GaussianBlur(ga, (31, 31), 0) - cv2.GaussianBlur(gb, (31, 31), 0)) < 12
    score = cv2.boxFilter(gain * same, -1, (W, H), normalize=False)
    score[:, :W // 2] = score[:, -W // 2:] = -1e18
    score[:H // 2] = score[-H // 2:] = -1e18
    score[int(2160 * 0.72):] = -1e18          # 글 상자 아래는 빼기
    y, x = np.unravel_index(np.argmax(score), score.shape)
    x0, y0 = x - W // 2, y - H // 2
    row = Image.new('RGB', (W * 2 + 10, H + 28), (30, 30, 30))
    row.paste(Image.fromarray(B[y0:y0 + H, x0:x0 + W]), (0, 28))
    row.paste(Image.fromarray(A[y0:y0 + H, x0:x0 + W]), (W + 10, 28))
    d = ImageDraw.Draw(row)
    d.text((6, 6), f'OFF (1x) {tb}#{b}  ({x0},{y0})', fill=(255, 255, 0))
    d.text((W + 16, 6), f'ON (4x) {ta}#{a}', fill=(255, 255, 0))
    rows.append(row)
    print(pair, x0, y0)
out = Image.new('RGB', (rows[0].width, sum(r.height for r in rows)))
yy = 0
for r in rows:
    out.paste(r, (0, yy)); yy += r.height
p = R / f'crop_{ta}_{tb}.png'
out.save(p)
print(p)
