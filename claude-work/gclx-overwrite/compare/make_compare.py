"""원본 그림과 고화질 묶음 그림을 한 장면 안에서 반씩 나눠 비교하는 그림을 만든다.
- 왼쪽 반: 원본(1배) 그림을 게임처럼 4K 화면(4096x2304)에 선형 보간으로 키운 것 — 고화질 묶음 없이 보이는 모습
- 오른쪽 반: 고화질 묶음의 4배 그림
- 서 있는 그림은 배경 위에 1배끼리·4배끼리 얹은 뒤 나눈다.
출력: 장면마다 4K 원본 크기 PNG + 확대 조각, 그리고 한 장짜리 정리본(정리.png)
python -I -X utf8 make_compare.py
"""
import sys, io
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, r'P:\AI\Codex\projects\reconquista_flowchart_20261024\build\pylib')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
import imagecodecs
from npa_assets import NPA
GAME = Path(r'P:\AI\gclx-codexrun\game')
OUT = Path(r'Y:\AI\claude-work\gclx-overwrite\compare\out')
OUT.mkdir(parents=True, exist_ok=True)
FONT = str(GAME / 'fonts' / 'NotoSansKR-VF.ttf')
W4, H4 = 4096, 2304


def font(size, weight=500):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([weight])            # 가변 글꼴의 기본은 Thin(100)
    return f

idx = {}
for line in (GAME / 'hires' / 'index.tsv').read_bytes().splitlines():
    f = line.split(b'\t')
    if len(f) >= 7:
        idx[f[0].lower()] = f
cg = NPA(GAME / 'cg.npa')
ent = {bytes.fromhex(e['name_hex']).replace(b'\\', b'/').lower(): e for e in cg.entries if e['type'] == 2}


def orig(name):
    return Image.open(io.BytesIO(cg.read(ent[name.encode('cp932').lower()]))).convert('RGBA')


def hires(name):
    f = idx[name.encode('cp932').lower()]
    key, tiles = f[6].decode(), int(f[7]) if len(f) > 7 and f[7].strip() else 0
    parts = [GAME / 'hires' / f'{key}.jxl'] if tiles == 0 else sorted((GAME / 'hires').glob(f'{key}_*.jxl'), key=lambda p: int(p.stem.rsplit('_', 1)[1]))
    arrs = [imagecodecs.jpegxl_decode(p.read_bytes()) for p in parts]
    a = np.concatenate(arrs, axis=0)
    if a.ndim == 2:
        a = np.stack([a] * 3, -1)
    img = Image.fromarray(a[:, :, :4] if a.shape[2] >= 4 else a[:, :, :3])
    return img.convert('RGBA'), (int(f[3]), int(f[4]))


def scene(bg, st=None, st_x=None):
    """(키운 원본, 고화질) 4K 두 장. 서 있는 그림은 아래쪽에 붙여 st_x(1배 좌표의 가운데)에 둔다."""
    o = orig(bg)
    h, size = hires(bg)
    assert size == (W4, H4) and h.size == (W4, H4), (bg, size, h.size)
    if st:
        so = orig(st); sh, ssize = hires(st)
        assert sh.size == (so.width * 4, so.height * 4), (st, so.size, sh.size)
        x1 = st_x - so.width // 2; y1 = 576 - so.height
        o.alpha_composite(so, (x1, y1)); h.alpha_composite(sh, (x1 * 4, y1 * 4))
    return o.convert('RGB').resize((W4, H4), Image.BILINEAR), h.convert('RGB')


def split(lo, hi, x=None):
    x = W4 // 2 if x is None else x
    img = hi.copy(); img.paste(lo.crop((0, 0, x, H4)), (0, 0))
    d = ImageDraw.Draw(img); d.rectangle((x - 3, 0, x + 2, H4), fill=(255, 255, 255))
    return img


def label(img, left, right, size):
    d = ImageDraw.Draw(img); f = font(size, 600)
    for text, anchor_x, al in ((left, int(size * 0.6), 'la'), (right, img.width - int(size * 0.6), 'ra')):
        b = d.textbbox((anchor_x, int(size * 0.5)), text, font=f, anchor=al)
        d.rectangle((b[0] - size // 3, b[1] - size // 4, b[2] + size // 3, b[3] + size // 4), fill=(0, 0, 0))
        d.text((anchor_x, int(size * 0.5)), text, font=f, fill=(255, 255, 255), anchor=al)
    return img


SCENES = [
    # (파일 이름, 제목, 배경, 서 있는 그림, 서 있는 그림 가운데 x(1배), 확대할 곳 가운데(4K 좌표))
    ('1_롯폰기거리', '배경 — 롯폰기 거리', 'bg/bg001001_3_六本木街並み1.jpg', None, None, (2048, 900)),
    ('2_고속도로', '배경 — 무너진 고속도로', 'bg/bg001016_3_高速道路崩壊.jpg', None, None, (2048, 1000)),
    ('3_프레젠트', '인물 — 프레젠트', 'bg/bg001012_3_六本木街並み2崩壊.jpg', 'st/stプレゼント_通常_smile1.png', 512, None),
]
rows = []
for fname, title, bg, st, st_x, zc in SCENES:
    lo, hi = scene(bg, st, st_x)
    if zc is None:                                   # 인물은 얼굴 둘레: 서 있는 그림 위쪽 1/4
        so = orig(st); zc = (st_x * 4, (576 - so.height) * 4 + so.height * 4 // 5)
    full = label(split(lo, hi), '원본 (1024×576을 4K로 키움)', '고화질 묶음 (4096×2304)', 64)
    full.save(OUT / f'{fname}_4K.png', optimize=True)
    zw, zh = 1200, 675                                 # 4K 화소 1:1 조각
    x0 = max(0, min(W4 - zw, zc[0] - zw // 2)); y0 = max(0, min(H4 - zh, zc[1] - zh // 2))
    zl, zr = lo.crop((x0, y0, x0 + zw, y0 + zh)), hi.crop((x0, y0, x0 + zw, y0 + zh))
    zoom = zr.copy(); zoom.paste(zl.crop((0, 0, zw // 2, zh)), (0, 0))
    ImageDraw.Draw(zoom).rectangle((zw // 2 - 2, 0, zw // 2 + 1, zh), fill=(255, 255, 255))
    zoom = label(zoom, '원본', '고화질', 34)
    zoom.save(OUT / f'{fname}_확대.png', optimize=True)
    rows.append((title, full, zoom, (x0, y0, zw, zh)))
    print(fname, 'ok', (x0, y0))

# 한 장 정리본: 줄마다 [전체 반반(줄임)] [확대 조각 반반(1:1)]
PW = 1600; PH = PW * H4 // W4; ZW = rows[0][2].width * PH // rows[0][2].height
M, T = 40, 70
sheet = Image.new('RGB', (M * 3 + PW + ZW, 150 + len(rows) * (PH + T + M) + 90), (24, 24, 28))
d = ImageDraw.Draw(sheet)
fT, fS, fN = font(48, 700), font(30, 600), font(24, 400)
d.text((M, 40), '길티 크라운 로스트 크리스마스 — 원본 그림과 고화질 묶음 비교', font=fT, fill=(255, 255, 255))
d.text((M, 104), '각 그림의 왼쪽 반은 원본(1024×576)을 4K 화면에 키운 모습, 오른쪽 반은 고화질 묶음(4096×2304)입니다.', font=fN, fill=(190, 190, 200))
y = 150
for title, full, zoom, (x0, y0, zw, zh) in rows:
    d.text((M, y + 14), title, font=fS, fill=(255, 255, 255))
    d.text((M * 2 + PW, y + 20), '확대: 노란 네모 자리', font=fN, fill=(190, 190, 200))
    y += T
    small = full.resize((PW, PH), Image.LANCZOS); sd = ImageDraw.Draw(small); s = PW / W4
    sd.rectangle((x0 * s, y0 * s, (x0 + zw) * s, (y0 + zh) * s), outline=(255, 210, 0), width=3)
    sheet.paste(small, (M, y)); sheet.paste(zoom.resize((ZW, PH), Image.LANCZOS), (M * 2 + PW, y))
    y += PH + M
d.text((M, y + 10), '고화질 묶음이 없으면 대사·메뉴 글자만 4K로 나오고, 그림은 왼쪽 반처럼 원래 해상도를 키워서 보여 줍니다.', font=fN, fill=(190, 190, 200))
sheet.save(OUT / '정리.png', optimize=True)
print('sheet', sheet.size)
