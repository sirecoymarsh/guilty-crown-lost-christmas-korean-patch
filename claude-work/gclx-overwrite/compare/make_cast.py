"""인물 얼굴 한가운데를 반으로 나눠 원본(왼쪽)과 고화질 묶음(오른쪽)을 비교한다(사용자 11-23 「인물의 얼굴을 반씩」).
- 인물 그림을 배경 위에 1배끼리·4배끼리 얹되, 얼굴 가운데가 화면 가운데(1배 x=512)에 오게 둔다 → 나누는 선이 얼굴을 지난다.
- 왼쪽 반: 1배 장면을 4K(4096x2304)로 선형 확대(고화질 묶음 없이 보이는 모습), 오른쪽 반: 4배 그림 그대로.
- 사용자 11-23 「밝아서 대비가 선명한 인물을 몇 개, 회상에서」: 회상 「모두 열기」가 켜져 있어 뒤 장면 인물도 씀(서 있는 그림만).
python -I -X utf8 make_faces.py
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
OUT = Path(r'Y:\AI\claude-work\gclx-overwrite\compare\out_cast')
OUT.mkdir(parents=True, exist_ok=True)
FONT = str(GAME / 'fonts' / 'NotoSansKR-VF.ttf')
W4, H4 = 4096, 2304


def font(size, weight=500):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([weight])
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
    a = np.concatenate([imagecodecs.jpegxl_decode(p.read_bytes()) for p in parts], axis=0)
    if a.ndim == 2:
        a = np.stack([a] * 3, -1)
    return Image.fromarray(a[:, :, :4] if a.shape[2] >= 4 else a[:, :, :3]).convert('RGBA')


def scene(bg, st, face):
    """얼굴 가운데(1배 좌표 face)가 화면 (512, fy) 에 오게 얹는다. fy 는 작은 그림이면 발을 화면 아래에 붙인 자리."""
    o, h = orig(bg), hires(bg)
    assert h.size == (W4, H4)
    so, sh = orig(st), hires(st)
    if sh.size != (so.width * 4, so.height * 4):      # 아주 큰 그림은 고화질본이 폭 4096 으로 잘려 있다(게임도 같은 자리에 늘여 그린다)
        print('  hires', sh.size, '->', (so.width * 4, so.height * 4))
        sh = sh.resize((so.width * 4, so.height * 4), Image.BILINEAR)
    x1 = 512 - face[0]
    y1 = 576 - so.height if so.height <= 700 else 190 - face[1]      # 큰(가까이 찍은) 그림은 얼굴을 화면 위 1/3 쯤에
    o.alpha_composite(so, (x1, y1)); h.alpha_composite(sh, (x1 * 4, y1 * 4))
    return o.convert('RGB').resize((W4, H4), Image.BILINEAR), h.convert('RGB'), (2048, (y1 + face[1]) * 4)


def halves(lo, hi, box=None):
    box = box or (0, 0, W4, H4)
    l, r = lo.crop(box), hi.crop(box)
    out = r.copy(); out.paste(l.crop((0, 0, l.width // 2, l.height)), (0, 0))
    lw = max(1, out.width // 2048)   # 얇게: 코를 가리지 않게(11-23)
    ImageDraw.Draw(out).rectangle((out.width // 2 - lw, 0, out.width // 2 + lw - 1, out.height), fill=(255, 255, 255))
    return out


def label(img, left, right, size):
    d = ImageDraw.Draw(img); f = font(size, 600)
    for text, ax, al in ((left, int(size * 0.6), 'la'), (right, img.width - int(size * 0.6), 'ra')):
        b = d.textbbox((ax, int(size * 0.5)), text, font=f, anchor=al)
        d.rectangle((b[0] - size // 3, b[1] - size // 4, b[2] + size // 3, b[3] + size // 4), fill=(0, 0, 0))
        d.text((ax, int(size * 0.5)), text, font=f, fill=(255, 255, 255), anchor=al)
    return img


ROWS = [
    # (파일 이름, 제목, 배경, 인물 그림, (코끝 x, 얼굴 가운데 y)(1배), 확대 폭(4K 화소))
    # x 는 코끝(사용자 11-23 「화면 중앙이 아니라 인물의 코를 중심으로」; nose_grid.py 12배 눈금으로 잼): 나누는 선이 코를 지난다
    ('0_프레젠트', '프레젠트', 'bg/bg001004_1_けやき坂通り.jpg', 'st/stプレゼント_通常_smile1.png', (171, 75), 720),   # 사용자 11-23 「프레젠트도 만들어」
    ('1_캐럴', '캐럴', 'bg/bg001001_3_六本木街並み1_雪.jpg', 'st/stキャロル_通常_smile1.png', (127, 105), 720),
    ('2_마나', '마나', 'bg/bg002011_2_海辺全景.jpg', 'st/stマナ_通常_smile.png', (172, 140), 720),
    ('3_하루카', '하루카', 'bg/bg003002_1_天王洲大学外観.jpg', 'st/stハルカ_通常_smile2.png', (109, 120), 720),
    ('4_유', '유', 'bg/bg001007_1_六本木公園.jpg', 'st/stユウ_通常_smile1.png', (119, 135), 720),
]
rows = []
for fname, title, bg, st, face, zw in ROWS:
    lo, hi, (cx, cy) = scene(bg, st, face)
    full = label(halves(lo, hi), '원본 (1024×576을 4K로 키움)', '고화질 묶음 (4096×2304)', 64)
    full.save(OUT / f'{fname}_4K.png', optimize=True)
    zh = zw * 9 // 16
    x0 = cx - zw // 2; y0 = max(0, min(H4 - zh, cy - zh // 2))
    zoom = halves(lo, hi, (x0, y0, x0 + zw, y0 + zh))
    zoom.save(OUT / f'{fname}_얼굴.png', optimize=True)
    rows.append((title, full, zoom, (x0, y0, zw, zh)))
    hero = full.crop((cx - 480, max(0, cy - 250), cx + 480, max(0, cy - 250) + 540)).resize((1920, 1080), Image.LANCZOS)
    label(hero, '원본 (1024×576을 4K로 키움)', '고화질 묶음', 44).save(OUT / f'{fname}_대표.png', optimize=True)
    print(fname, 'face at', (cx, cy), 'zoom', (x0, y0, zw, zh))

PW = 1600; PH = PW * H4 // W4; ZW = PH * 16 // 9
M, T = 40, 64
sheet = Image.new('RGB', (M * 3 + PW + ZW, 160 + len(rows) * (PH + T + M) + 80), (24, 24, 28))
d = ImageDraw.Draw(sheet)
fT, fS, fN = font(48, 700), font(30, 600), font(24, 400)
d.text((M, 40), '길티 크라운 로스트 크리스마스 — 원본 그림과 고화질 묶음 비교 (인물 얼굴 — 회상 속 인물)', font=fT, fill=(255, 255, 255))
d.text((M, 106), '얼굴 한가운데를 나눴습니다. 왼쪽 반은 원본(1024×576)을 4K 화면에 키운 모습, 오른쪽 반은 고화질 묶음(4096×2304)입니다.', font=fN, fill=(190, 190, 200))
y = 160
for title, full, zoom, (x0, y0, zw, zh) in rows:
    d.text((M, y + 12), title, font=fS, fill=(255, 255, 255))
    d.text((M * 2 + PW, y + 18), '얼굴 확대 (노란 네모 자리) — 왼쪽 원본 · 오른쪽 고화질', font=fN, fill=(190, 190, 200))
    y += T
    small = full.resize((PW, PH), Image.LANCZOS); s = PW / W4
    ImageDraw.Draw(small).rectangle((x0 * s, y0 * s, (x0 + zw) * s, (y0 + zh) * s), outline=(255, 210, 0), width=3)
    sheet.paste(small, (M, y)); sheet.paste(zoom.resize((ZW, PH), Image.LANCZOS), (M * 2 + PW, y))
    y += PH + M
d.text((M, y + 6), '고화질 묶음이 없으면 대사·메뉴 글자만 4K로 나오고, 그림은 왼쪽 반처럼 원래 해상도를 키워서 보여 줍니다.', font=fN, fill=(190, 190, 200))
sheet.save(OUT / '정리_인물.png', optimize=True)
print('sheet', sheet.size)
