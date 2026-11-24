"""nss 묶음의 kr_hint_*.png 를 한 장에 모아 번호와 함께 본다(읽기만).  python -I -X utf8 hint_sheet.py <npa> <out.png>"""
import io, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
import npa_adapter as A
from PIL import Image, ImageDraw

arc = A.NPA(Path(sys.argv[1]))
ents = sorted((e for e in arc.entries if e['name'].startswith('kr_hint_')), key=lambda e: e['name'])
ims = []
for e in ents:
    im = Image.open(io.BytesIO(arc.read(e))).convert('RGBA')
    bg = Image.new('RGBA', im.size, (230, 230, 230, 255)); bg.alpha_composite(im)
    ims.append((e['name'], bg.convert('RGB')))
print([(n, im.size) for n, im in ims][:3], len(ims))
w = 900
rows = []
for n, im in ims:
    im = im.resize((w, max(1, round(im.height * w / im.width))), Image.LANCZOS)
    row = Image.new('RGB', (w + 170, im.height), (60, 60, 60)); row.paste(im, (170, 0))
    ImageDraw.Draw(row).text((6, 4), n, fill=(255, 255, 0)); rows.append(row)
sheet = Image.new('RGB', (w + 170, sum(r.height for r in rows)), (0, 0, 0))
y = 0
for r in rows:
    sheet.paste(r, (0, y)); y += r.height
sheet.save(sys.argv[2]); print(sys.argv[2], sheet.size)
