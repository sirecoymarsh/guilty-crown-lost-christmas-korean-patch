"""인물 그림 한 장의 일부(1배)를 2배로 키워 25px 눈금과 함께 저장. python head_grid.py out.png 이름 x0 y0 x1 y1"""
import sys, io
from PIL import Image, ImageDraw
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from npa_assets import NPA
cg = NPA(r'P:\AI\gclx-codexrun\game\cg.npa')
ent = {bytes.fromhex(e['name_hex']).replace(b'\\', b'/').lower(): e for e in cg.entries if e['type'] == 2}
out, name = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = map(int, sys.argv[3:7])
im = Image.open(io.BytesIO(cg.read(ent[name.encode('cp932').lower()]))).convert('RGBA').crop((x0, y0, x1, y1))
bg = Image.new('RGBA', im.size, (60, 60, 70, 255)); bg.alpha_composite(im)
bg = bg.resize((im.width * 2, im.height * 2)); d = ImageDraw.Draw(bg)
for x in range(0, x1 - x0, 25):
    d.line((x * 2, 0, x * 2, bg.height), fill=(255, 0, 0, 255) if (x0 + x) % 50 == 0 else (255, 170, 170, 160))
    if (x0 + x) % 50 == 0: d.text((x * 2 + 3, 3), str(x0 + x), fill=(255, 255, 0, 255))
for y in range(0, y1 - y0, 25):
    d.line((0, y * 2, bg.width, y * 2), fill=(255, 0, 0, 255) if (y0 + y) % 50 == 0 else (255, 170, 170, 160))
    if (y0 + y) % 50 == 0: d.text((3, y * 2 + 3), str(y0 + y), fill=(255, 255, 0, 255))
bg.convert('RGB').save(out)
