"""비교 시안 시트: 줄 = 문제 나기 쉬운 자리(1:1, 4배 화소), 열 = 방식. 투명 그림은 어두운 회색 위에 얹어 테두리를 보인다.
python -X utf8 sample_sheet.py -> F:\\AI\\gclx-4k\\sample1\\sheet_a.png, sheet_b.png
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

Q = Path(r'F:\AI\gclx-4k\sample1')
COLS = [('bilinear', '지금 4K 화면(원본 늘림)'), ('lanczos', 'AI 없이 부드럽게'), ('ai', 'AI 그대로(high-fidelity)'), ('blend', '섞기(레콘키스타 방식)')]
# (그림, 1배 x, 1배 y, 설명) — 자르는 크기 1배 120×75 = 4배 480×300
SHEETS = {
    'sheet_a': [('st_present', 100, 28, '스탠딩 얼굴·머리카락'), ('st_present', 85, 140, '털 깃·리본'), ('st_present', 70, 330, '치마 질감(거친 결)'),
                ('bu_scrooge', 290, 150, '흉상 얼굴'), ('bu_scrooge', 150, 450, '옷 질감')],
    'sheet_b': [('ev_present', 420, 22, '이벤트 CG 얼굴'), ('ev_present', 250, 40, '불길·흐린 곳'), ('ev_present', 60, 120, '결정 모서리'),
                ('bg_street', 110, 90, '배경 현수막 글자'), ('bg_street', 560, 250, '배경 불빛·나무(흐린 곳)'), ('bg_street', 570, 420, '배경 자동차')],
}
CW, CH, GAP, HEAD, LABEL = 480, 300, 8, 34, 28
font = Image.open  # placeholder to keep names short below
F = ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf', 18)
BG = (40, 48, 60)
cache = {}


def pic(key, tag):
    if (key, tag) not in cache:
        im = Image.open(Q / 'out' / f'{key}.{tag}.png')
        if im.mode == 'RGBA':
            base = Image.new('RGBA', im.size, BG + (255,))
            im = Image.alpha_composite(base, im)
        cache[(key, tag)] = im.convert('RGB')
    return cache[(key, tag)]


for name, rows in SHEETS.items():
    W = len(COLS) * (CW + GAP) + GAP
    H = HEAD + len(rows) * (CH + LABEL + GAP) + GAP
    sheet = Image.new('RGB', (W, H), (18, 20, 24))
    d = ImageDraw.Draw(sheet)
    for c, (_, title) in enumerate(COLS):
        d.text((GAP + c * (CW + GAP) + 6, 6), title, font=F, fill=(235, 235, 235))
    for r, (key, x, y, label) in enumerate(rows):
        top = HEAD + r * (CH + LABEL + GAP)
        d.text((GAP + 6, top + 2), label, font=F, fill=(200, 210, 120))
        for c, (tag, _) in enumerate(COLS):
            crop = pic(key, tag).crop((x * 4, y * 4, x * 4 + CW, y * 4 + CH))
            sheet.paste(crop, (GAP + c * (CW + GAP), top + LABEL))
    sheet.save(Q / f'{name}.png')
    print(name, sheet.size)
