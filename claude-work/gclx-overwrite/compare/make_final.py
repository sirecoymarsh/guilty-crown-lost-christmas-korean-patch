"""최종 비교 그림(사용자 11-23 「여자의 얼굴 반이 효과가 좋겠어, 스크루지는 별로」): 스크루지는 빼고 프레젠트 얼굴을 앞에.
make_compare.py·make_faces.py 가 만든 4K 반반 그림과 확대 조각을 다시 엮기만 한다(그림을 새로 풀지 않음).
- 정리_최종.png: 프레젠트 웃는 장면 → 프레젠트 서 있는 그림 → 롯폰기 거리 → 무너진 고속도로
- 대표_프레젠트.png: 프레젠트 웃는 얼굴 반반 한 장(1920x1080)
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
C = Path(r'Y:\AI\claude-work\gclx-overwrite\compare')
FONT = r'P:\AI\gclx-codexrun\game\fonts\NotoSansKR-VF.ttf'
W4, H4 = 4096, 2304


def font(size, weight=500):
    f = ImageFont.truetype(FONT, size); f.set_variation_by_axes([weight]); return f


def label(img, left, right, size):
    d = ImageDraw.Draw(img); f = font(size, 600)
    for text, ax, al in ((left, int(size * 0.6), 'la'), (right, img.width - int(size * 0.6), 'ra')):
        b = d.textbbox((ax, int(size * 0.5)), text, font=f, anchor=al)
        d.rectangle((b[0] - size // 3, b[1] - size // 4, b[2] + size // 3, b[3] + size // 4), fill=(0, 0, 0))
        d.text((ax, int(size * 0.5)), text, font=f, fill=(255, 255, 255), anchor=al)
    return img


ROWS = [  # 제목, 4K 반반, 확대 조각(라벨 없는 것), 확대 자리(4K 좌표)
    ('프레젠트 — 서 있는 그림', C / 'out_faces/1_프레젠트_4K.png', C / 'out_faces/1_프레젠트_얼굴.png', (1688, 178, 720, 405)),
    ('프레젠트 — 웃는 장면', C / 'out_faces/2_프레젠트_웃음_4K.png', C / 'out_faces/2_프레젠트_웃음_얼굴.png', (1088, 220, 1920, 1080)),
    ('배경 — 롯폰기 거리', C / 'out/1_롯폰기거리_4K.png', C / 'out/1_롯폰기거리_확대.png', (1448, 563, 1200, 675)),
    ('배경 — 무너진 고속도로', C / 'out/2_고속도로_4K.png', C / 'out/2_고속도로_확대.png', (1448, 663, 1200, 675)),
]
PW = 1600; PH = PW * H4 // W4; ZW = PH * 16 // 9
M, T = 40, 64
sheet = Image.new('RGB', (M * 3 + PW + ZW, 160 + len(ROWS) * (PH + T + M) + 80), (24, 24, 28))
d = ImageDraw.Draw(sheet)
fT, fS, fN = font(48, 700), font(30, 600), font(24, 400)
d.text((M, 40), '길티 크라운 로스트 크리스마스 — 원본 그림과 고화질 묶음 비교', font=fT, fill=(255, 255, 255))
d.text((M, 106), '그림마다 가운데를 나눴습니다. 왼쪽 반은 원본(1024×576)을 4K 화면에 키운 모습, 오른쪽 반은 고화질 묶음(4096×2304)입니다.', font=fN, fill=(190, 190, 200))
y = 160
for title, full_p, zoom_p, (x0, y0, zw, zh) in ROWS:
    full, zoom = Image.open(full_p).convert('RGB'), Image.open(zoom_p).convert('RGB')
    if zoom_p.parent.name == 'out':                    # 첫 판 확대 조각에는 작은 라벨이 이미 있다 → 그대로 두고 크기만
        pass
    d.text((M, y + 12), title, font=fS, fill=(255, 255, 255))
    d.text((M * 2 + PW, y + 18), '확대 (노란 네모 자리) — 왼쪽 원본 · 오른쪽 고화질', font=fN, fill=(190, 190, 200))
    y += T
    small = full.resize((PW, PH), Image.LANCZOS); s = PW / W4
    ImageDraw.Draw(small).rectangle((x0 * s, y0 * s, (x0 + zw) * s, (y0 + zh) * s), outline=(255, 210, 0), width=3)
    sheet.paste(small, (M, y))
    z = zoom.resize((ZW, PH), Image.LANCZOS)
    if zoom_p.parent.name == 'out_faces':
        z = label(z, '원본', '고화질', 34)
    sheet.paste(z, (M * 2 + PW, y))
    y += PH + M
d.text((M, y + 6), '고화질 묶음이 없으면 대사·메뉴 글자만 4K로 나오고, 그림은 왼쪽 반처럼 원래 해상도를 키워서 보여 줍니다.', font=fN, fill=(190, 190, 200))
sheet.save(C / 'final' / '정리_최종.png', optimize=True)

# 대표 한 장: 사용자가 고른 서 있는 그림의 얼굴 — 4K 반반 그림에서 얼굴 둘레 960x540 을 2배로(1920x1080)
hero = Image.open(C / 'out_faces/1_프레젠트_4K.png').convert('RGB').crop((2048 - 480, 380 - 250, 2048 + 480, 380 + 290)).resize((1920, 1080), Image.LANCZOS)
hero = label(hero, '원본 (1024×576을 4K로 키움)', '고화질 묶음', 44)
dd = ImageDraw.Draw(hero); f = font(30, 500)
dd.text((hero.width // 2, hero.height - 34), '길티 크라운 로스트 크리스마스 한국어 패치 — 고화질 묶음', font=f, fill=(255, 255, 255), anchor='ms', stroke_width=3, stroke_fill=(0, 0, 0))
hero.save(C / 'final' / '대표_프레젠트_얼굴.png', optimize=True)
print('ok', sheet.size, hero.size)
