"""원작 UI 그림을 꺼내 한 장 훑어보기(검은 바탕·체크 바탕 위, 이름·크기 붙임). python -X utf8 ui_survey.py <게임 폴더> <출력 폴더>"""
import io, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

game, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
arc = NPA(game / 'cg.npa'); ent = {e['name'].replace('\\', '/'): e for e in arc.entries}
want = [k for k in ent if k.startswith(('sys/extra/cglib/', 'sys/save/', 'sys/config/', 'sys/phase/', 'sys/backlog/', 'sys/dialog/', 'sys/title/', 'sys/menu/', 'sys/adv/'))
        and k.lower().endswith(('.png', '.jpg', '.bmp')) and '/info/' not in k and 'ボイス選択' not in k]
font = ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf', 14)
tiles = []
for k in sorted(want):
    try:
        im = Image.open(io.BytesIO(arc.read(ent[k]))).convert('RGBA')
    except Exception:
        continue
    (out / k.replace('/', '__')).with_suffix('.png').write_bytes(b'')
    im.save((out / k.replace('/', '__')).with_suffix('.png'))
    t = im.copy(); t.thumbnail((300, 170))
    bg = Image.new('RGBA', (310, 200), (40, 40, 48, 255))
    chk = Image.new('RGBA', t.size, (90, 90, 90, 255))
    d = ImageDraw.Draw(chk)
    for y in range(0, t.size[1], 10):
        for x in range(0, t.size[0], 10):
            if (x // 10 + y // 10) % 2:
                d.rectangle([x, y, x + 9, y + 9], fill=(130, 130, 130, 255))
    chk.alpha_composite(t)
    bg.alpha_composite(chk, (5, 5))
    ImageDraw.Draw(bg).text((5, 178), f'{k[4:]} {im.size[0]}x{im.size[1]}', font=font, fill=(255, 255, 255, 255))
    tiles.append(bg)
cols = 6
for page in range(0, len(tiles), 48):
    part = tiles[page:page + 48]
    rows = (len(part) + cols - 1) // cols
    sheet = Image.new('RGBA', (cols * 310, rows * 200), (20, 20, 24, 255))
    for i, t in enumerate(part):
        sheet.alpha_composite(t, ((i % cols) * 310, (i // cols) * 200))
    sheet.convert('RGB').save(out / f'_sheet_{page // 48}.jpg', quality=85)
print(len(tiles), 'images')
