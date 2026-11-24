"""인물 그림 후보를 1배로 꺼내 50px 눈금을 그려 한 장에 모은다(얼굴 가운데 좌표를 눈으로 잡으려고)."""
import sys, io
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from npa_assets import NPA
cg = NPA(r'P:\AI\gclx-codexrun\game\cg.npa')
ent = {bytes.fromhex(e['name_hex']).replace(b'\\', b'/').lower(): e for e in cg.entries if e['type'] == 2}
names = sys.argv[2:]
tiles = []
for n in names:
    im = Image.open(io.BytesIO(cg.read(ent[n.encode('cp932').lower()]))).convert('RGBA')
    bg = Image.new('RGBA', im.size, (60, 60, 70, 255)); bg.alpha_composite(im)
    d = ImageDraw.Draw(bg)
    for x in range(0, im.width, 50):
        d.line((x, 0, x, im.height), fill=(255, 0, 0, 255) if x % 100 == 0 else (255, 160, 160, 255), width=1)
        if x % 100 == 0: d.text((x + 2, 2), str(x), fill=(255, 255, 0, 255))
    for y in range(0, im.height, 50):
        d.line((0, y, im.width, y), fill=(255, 0, 0, 255) if y % 100 == 0 else (255, 160, 160, 255), width=1)
        if y % 100 == 0: d.text((2, y + 2), str(y), fill=(255, 255, 0, 255))
    tiles.append(bg.convert('RGB'))
H = 900
tiles = [t.resize((t.width * H // t.height, H)) if t.height > H else t for t in tiles]
sheet = Image.new('RGB', (sum(t.width for t in tiles) + 10 * len(tiles), max(t.height for t in tiles)), 'black')
x = 0
for t in tiles:
    sheet.paste(t, (x, 0)); x += t.width + 10
sheet.save(sys.argv[1])
print([(n, t.size) for n, t in zip(names, tiles)])
