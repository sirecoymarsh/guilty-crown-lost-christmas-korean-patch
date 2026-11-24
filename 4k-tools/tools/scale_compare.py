"""같은 장면의 두 화면(예: F8 원본 그림 / 4K 그림)에서 그림이 늘어났거나 밀렸는지: 띠마다 세로·가로로 가장 잘 맞는 밀림을 찾고,
밀림이 위치에 따라 바뀌면(위 띠와 아래 띠가 다르면) 늘어난 것이다. 흐림 차이를 줄이려 둘 다 1/4 로 줄여 견준다.
python -X utf8 scale_compare.py <A.bmp|png> <B.bmp|png> [y0 y1]   (y0..y1: 견줄 세로 범위, 기본은 글 창 위 0..1400)"""
import sys
import numpy as np
from PIL import Image


def load(p):
    im = Image.open(p).convert('L')
    return np.asarray(im.resize((im.width // 4, im.height // 4), Image.BOX)).astype(float)


def shift2d(a, b, rng=12):
    best = None
    for dy in range(-rng, rng + 1):
        for dx in range(-rng, rng + 1):
            A = a[max(0, dy):a.shape[0] + min(0, dy), max(0, dx):a.shape[1] + min(0, dx)]
            B = b[max(0, -dy):b.shape[0] + min(0, -dy), max(0, -dx):b.shape[1] + min(0, -dx)]
            e = float(np.mean((A - B) ** 2))
            if best is None or e < best[2]:
                best = (dy, dx, round(e, 1))
    return best


a, b = load(sys.argv[1]), load(sys.argv[2])
y0, y1 = (int(sys.argv[3]) // 4, int(sys.argv[4]) // 4) if len(sys.argv) > 4 else (0, 1400 // 4)
x0, x1 = 40, a.shape[1] - 40
print('whole', shift2d(a[y0:y1, x0:x1], b[y0:y1, x0:x1]))
h = (y1 - y0) // 3
for i in range(3):
    ya, yb = y0 + i * h, y0 + (i + 1) * h
    print(f'band y {ya * 4}-{yb * 4}', shift2d(a[ya:yb, x0:x1], b[ya:yb, x0:x1]))
w = (x1 - x0) // 3
for i in range(3):
    xa, xb = x0 + i * w, x0 + (i + 1) * w
    print(f'band x {xa * 4}-{xb * 4}', shift2d(a[y0:y1, xa:xb], b[y0:y1, xa:xb]))
