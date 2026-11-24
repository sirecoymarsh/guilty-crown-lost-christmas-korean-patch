"""인물마다 서 있는 그림 한 장(1배)을 회색 바탕에 모아 본다. python cast_sheet.py out.png 이름..."""
import sys, io
from PIL import Image, ImageDraw
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from npa_assets import NPA
cg = NPA(r'P:\AI\gclx-codexrun\game\cg.npa')
ent = {bytes.fromhex(e['name_hex']).replace(b'\\', b'/').lower(): e for e in cg.entries if e['type'] == 2}
tiles = []
for i, n in enumerate(sys.argv[2:]):
    im = Image.open(io.BytesIO(cg.read(ent[n.encode('cp932').lower()]))).convert('RGBA')
    bg = Image.new('RGBA', im.size, (70, 70, 80, 255)); bg.alpha_composite(im)
    bg = bg.convert('RGB'); bg = bg.resize((bg.width * 640 // bg.height, 640))
    ImageDraw.Draw(bg).text((6, 6), str(i + 1), fill=(255, 255, 0))
    tiles.append(bg)
sheet = Image.new('RGB', (sum(t.width + 8 for t in tiles), 640), 'black')
x = 0
for t in tiles:
    sheet.paste(t, (x, 0)); x += t.width + 8
sheet.save(sys.argv[1]); print(sheet.size)
