"""문장 끝 아이콘 고해상도 다시 그리기 시안(사용자 11-24 「문장 끝에 나타나는 아이콘인 광물과 유전자가 저해상도야 그것도 고해상도 움짤로
다시 그려줘」 → 「시안 만들어줘」). 원본 cg/sys/icon/通常(광물, 34장)·auto(유전자, 16장)는 26x26.
- 광물: 테두리 모양은 원본 34장 알파를 합쳐 매끈하게 키운 것(실루엣 그대로). 속은 면을 나눈 결정(보로노이 면, 면마다 밝기),
  가장자리 면은 푸른 기, 가운데 초록 핵과 소용돌이 무늬. 색 순환은 원본 각 장의 평균 밝기를 그대로 따라감(흰 → 청록 → 남색 4장 → 되돌아옴).
- 유전자: 세로 이중나선(반 바퀴 남짓)을 16장에 반 바퀴 돌림(이중나선은 180도 돌리면 같아 끊김 없이 돎) + 아래쪽 가로 나선과 가로대.
  앞은 희고 밝게, 뒤는 푸르고 어둡게(깊이 순서로 그림).
4배(104x104)로 내되 16배(416)로 그려서 줄인다.
python -I -X utf8 draw_icons.py <출력 폴더>
"""
import math, sys, random
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ORIG = HERE / 'orig'
S = 416          # drawing size (16x)
OUT = 104        # 4x of 26


def lerp(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def pal(keys, t):
    """keys: [(t, color)], piecewise linear."""
    for (t0, c0), (t1, c1) in zip(keys, keys[1:]):
        if t <= t1:
            return lerp(c0, c1, 0 if t1 == t0 else (t - t0) / (t1 - t0))
    return keys[-1][1]


# ------------------------------------------------------------------ crystal
def crystal_mask():
    acc = np.zeros((26, 26), np.float32)
    for i in range(34):
        a = np.asarray(Image.open(ORIG / f'通常_{i:03d}.png').convert('RGBA'))[:, :, 3].astype(np.float32)
        acc = np.maximum(acc, a)
    m = Image.fromarray(acc.astype(np.uint8)).resize((S, S), Image.BICUBIC).filter(ImageFilter.GaussianBlur(7))
    m = m.point(lambda v: 255 if v > 120 else 0).filter(ImageFilter.GaussianBlur(2.2))
    return m


def crystal_states():
    """t per frame from the original mean brightness: 0 white .. ~0.6 teal .. 1 navy."""
    vals = []
    for i in range(34):
        a = np.asarray(Image.open(ORIG / f'通常_{i:03d}.png').convert('RGBA')).astype(np.float32)
        sel = a[:, :, 3] > 200
        vals.append(a[:, :, :3][sel].mean())
    hi, lo = max(vals), min(vals)
    return [(hi - v) / (hi - lo) for v in vals]


def voronoi_cells(mask, n, seed):
    rnd = random.Random(seed)
    m = np.asarray(mask) > 128
    ys, xs = np.nonzero(m)
    pts = []
    while len(pts) < n:
        k = rnd.randrange(len(xs)); p = (xs[k], ys[k])
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > (S * 0.095) ** 2 for q in pts):
            pts.append(p)
    yy, xx = np.mgrid[0:S, 0:S]
    d = np.stack([(xx - px) ** 2 + (yy - py) ** 2 for px, py in pts])
    lab = d.argmin(0)
    return pts, lab


def draw_crystal(t, mask, cells):
    pts, lab = cells
    m = np.asarray(mask).astype(np.float32) / 255
    rnd = random.Random(7)
    n = len(pts)
    # per facet: shade from a fake normal; rim facets (touching the outline) bluer
    edge = np.asarray(mask.filter(ImageFilter.MinFilter(41))) < 128
    rim = [bool(((lab == i) & edge & (m > 0.5)).any()) for i in range(n)]
    light = np.array([-0.55, -0.7, 0.45]); light /= np.linalg.norm(light)
    shade = []
    for i in range(n):
        nx, ny = rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8)
        v = np.array([nx, ny, 1.0]); v /= np.linalg.norm(v)
        shade.append(0.55 + 0.45 * max(0.0, float(v @ light)))
    face = pal([(0, (246, 249, 253)), (0.35, (200, 238, 232)), (0.62, (134, 220, 192)), (1, (40, 62, 122))], t)
    rimc = pal([(0, (168, 194, 230)), (0.62, (78, 136, 206)), (1, (46, 62, 168))], t)
    core = pal([(0, (214, 236, 236)), (0.35, (120, 214, 176)), (0.62, (64, 186, 132)), (1, (58, 150, 104))], t)
    glyph = pal([(0, (176, 214, 214)), (0.62, (30, 120, 86)), (1, (20, 60, 52))], t)
    img = np.zeros((S, S, 3), np.float32)
    cx, cy = S * 0.5, S * 0.56
    yy, xx = np.mgrid[0:S, 0:S]
    rcore = np.sqrt(((xx - cx) / (S * 0.30)) ** 2 + ((yy - cy) / (S * 0.28)) ** 2)
    corew = np.clip(1.2 - rcore, 0, 1) ** 1.2
    grad = []
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi); grad.append((math.cos(a), math.sin(a)))
    for i in range(n):
        sel = lab == i
        base = np.array(rimc if rim[i] else face, np.float32)
        gx, gy = grad[i]; px, py = pts[i]
        gv = ((xx - px) * gx + (yy - py) * gy) / (S * 0.12)
        k = np.clip(shade[i] + 0.22 * gv, 0.35, 1.18)
        img[sel] = (base[None, :] * k[sel][:, None])
    img = img * (1 - corew[..., None] * 0.85) + np.array(core, np.float32) * corew[..., None] * 0.85
    # swirl mark (の-like) in the core
    g = Image.new('L', (S, S), 0); gd = ImageDraw.Draw(g)
    path = []
    for k in range(160):
        u = k / 159
        x = cx + S * 0.13 * math.sin(u * math.pi * 1.6 + 0.4) * (1 - 0.3 * u)
        y = cy - S * 0.17 + S * 0.32 * u
        path.append((x, y))
    gd.line(path, fill=255, width=int(S * 0.05), joint='curve')
    gm = np.asarray(g.filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255 * (0.12 + 0.55 * min(1, t / 0.6))
    img = img * (1 - gm[..., None]) + np.array(glyph, np.float32) * gm[..., None]
    # facet edges: thin bright line on one side, dark on the other
    e = np.zeros((S, S), np.float32)
    e[:, 1:] += (lab[:, 1:] != lab[:, :-1]); e[1:, :] += (lab[1:, :] != lab[:-1, :])
    ei = Image.fromarray((np.clip(e, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    ea = np.asarray(ei).astype(np.float32) / 255
    edgec = np.array(pal([(0, (130, 170, 220)), (0.62, (40, 96, 170)), (1, (16, 24, 80))], t), np.float32)
    # facet edges: a bright line (light catching the edge) with a dark line beside it
    bright = np.array(pal([(0, (255, 255, 255)), (0.62, (210, 246, 240)), (1, (150, 190, 255))], t), np.float32)
    img = img * (1 - ea[..., None] * 0.5) + edgec * ea[..., None] * 0.5
    eb = np.asarray(ei.filter(ImageFilter.GaussianBlur(0.8)).transform((S, S), Image.AFFINE, (1, 0, 2, 0, 1, 2))).astype(np.float32) / 255
    img = img * (1 - eb[..., None] * 0.55) + bright * eb[..., None] * 0.55
    nz = np.asarray(Image.effect_noise((S, S), 40).filter(ImageFilter.GaussianBlur(1.6))).astype(np.float32)
    nz = (nz - nz.mean()) / (nz.std() + 1e-6)
    img = img * (1 + 0.07 * nz[..., None])
    # highlight upper-left, outline darker
    hl = np.clip(1 - np.sqrt(((xx - S * 0.36) / (S * 0.22)) ** 2 + ((yy - S * 0.30) / (S * 0.16)) ** 2), 0, 1) ** 2
    img = img + hl[..., None] * (255 - img) * (0.55 * (1 - 0.6 * t))
    inner = np.asarray(mask.filter(ImageFilter.MinFilter(13)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32) / 255
    outl = np.clip(m - inner, 0, 1)
    img = img * (1 - outl[..., None] * 0.55) + edgec * outl[..., None] * 0.55
    rgba = np.dstack([np.clip(img, 0, 255), m * 255]).astype(np.uint8)
    return Image.fromarray(rgba, 'RGBA').resize((OUT, OUT), Image.LANCZOS)


# ------------------------------------------------------------------ DNA
def tube_points(fn, n):
    return [fn(k / (n - 1)) for k in range(n)]


def draw_dna(k, frames=16):
    th = math.pi * k / frames           # half a turn over the loop (a double helix repeats every 180 degrees)
    big = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    items = []                          # (z, x, y, r, color)
    W = S
    # vertical double helix, about 0.62 of a turn over the height
    turns = 0.62; R = W * 0.37; r0 = W * 0.017
    for s in range(2):
        for sub, dr in enumerate((-0.035, 0.0, 0.035)):
            for j in range(260):
                u = j / 259
                ph = th + 2 * math.pi * turns * u + s * math.pi + dr * 2.2
                x = W / 2 + R * (1 + dr) * math.cos(ph); z = math.sin(ph); y = W * (0.04 + 0.92 * u) + dr * W * 0.25
                items.append((z - 0.08 * abs(sub - 1), x, y, r0 * (0.7 + 0.3 * (z + 1) / 2) * (1.25 if sub == 1 else 0.8)))
    # horizontal helix band in the lower part, with rungs
    band = []
    for s in range(2):
        for j in range(240):
            u = j / 239
            ph = th * 2 + 2 * math.pi * 2.6 * u + s * math.pi
            x = W * (0.03 + 0.94 * u); y = W * 0.73 + W * 0.115 * math.sin(ph); z = math.cos(ph)
            band.append((z * 0.6 - 0.15, x, y, W * 0.014 * (0.75 + 0.25 * (z + 1) / 2)))
    rungs = []
    for j in range(26):
        u = (j + 0.5) / 26; ph = th * 2 + 2 * math.pi * 2.6 * u
        x = W * (0.03 + 0.94 * u)
        y1 = W * 0.73 + W * 0.115 * math.sin(ph); y2 = W * 0.73 + W * 0.115 * math.sin(ph + math.pi)
        rungs.append((x, y1, y2, math.cos(ph)))
    d = ImageDraw.Draw(big)

    def col(z):
        t = (z + 1) / 2
        return pal([(0, (40, 70, 96)), (0.45, (92, 150, 176)), (0.75, (168, 222, 232)), (1, (244, 252, 255))], t)
    for x, y1, y2, z in rungs:
        c = col(0.35 + 0.4 * z)
        d.line([(x, y1), (x, y2)], fill=c + (210,), width=int(W * 0.011))
    for z, x, y, r in sorted(band + items):
        c = col(z)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c + (255,))
    glow = big.filter(ImageFilter.GaussianBlur(W * 0.02))
    out = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ga = np.asarray(glow).astype(np.float32); ga[:, :, 3] *= 0.85
    out.alpha_composite(Image.fromarray(ga.astype(np.uint8), 'RGBA'))
    out.alpha_composite(big)
    return out.resize((OUT, OUT), Image.LANCZOS)


def main(outdir):
    out = Path(outdir); (out / 'crystal').mkdir(parents=True, exist_ok=True); (out / 'dna').mkdir(parents=True, exist_ok=True)
    mask = crystal_mask(); cells = voronoi_cells(mask, 30, 11)
    ts = crystal_states()
    for i, t in enumerate(ts):
        draw_crystal(t, mask, cells).save(out / 'crystal' / f'{i:03d}.png')
    for k in range(16):
        draw_dna(k).save(out / 'dna' / f'{k:03d}.png')
    print('frames', len(ts), 16)


if __name__ == '__main__':
    main(sys.argv[1])
