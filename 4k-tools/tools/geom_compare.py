"""두 화면 찍기(원래 1배 엔진 / 4K)를 견줘 그림이 어긋나거나 늘어났는지 본다: 진한 글자·로고의 테두리 상자와 가로·세로 투영의 맞춤.
python -X utf8 geom_compare.py <원래.png> <4K.png>"""
import sys
import numpy as np
from PIL import Image


def load(p):
    return np.asarray(Image.open(p).convert('L')).astype(float)


def bbox(a, thr=60):
    ys, xs = np.where(a < thr)
    return xs.min(), ys.min(), xs.max(), ys.max()


def best_shift(p, q, rng=80):
    best = None
    for s in range(-rng, rng + 1):
        a = p[max(0, s):len(p) + min(0, s)]; b = q[max(0, -s):len(q) + min(0, -s)]
        e = float(np.mean((a - b) ** 2))
        if best is None or e < best[1]:
            best = (s, e)
    return best


a, b = load(sys.argv[1]), load(sys.argv[2])
print('size', a.shape, b.shape)
region = (slice(250, 1100), slice(500, 3600))            # the title logo band
print('logo bbox native', bbox(a[region]), '4K', bbox(b[region]))
ra, rb = a[:, 500:3600].mean(axis=1), b[:, 500:3600].mean(axis=1)
ca, cb = a[200:1900, :].mean(axis=0), b[200:1900, :].mean(axis=0)
print('vertical shift (rows)', best_shift(ra, rb), 'horizontal shift (cols)', best_shift(ca, cb))
for y0, y1 in ((0, 200), (900, 1100), (1960, 2160)):     # top band, middle, bottom band: per-band vertical shift shows a stretch
    print('band', y0, y1, best_shift(ra[max(0, y0 - 100):y1 + 100] if y0 else ra[:y1 + 100], rb[max(0, y0 - 100):y1 + 100] if y0 else rb[:y1 + 100], 60))
