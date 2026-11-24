"""인물 얼굴 둘레를 6배로 키워 5px 눈금(10px 마다 숫자)을 그린다 — 코끝 x 좌표를 1배 화소 단위로 읽으려고.
python nose_grid.py out.png 이름:x0:y0 ... (각 60x60 1배 구역)"""
import sys, io
from PIL import Image, ImageDraw
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from npa_assets import NPA
cg = NPA(r'P:\AI\gclx-codexrun\game\cg.npa')
ent = {bytes.fromhex(e['name_hex']).replace(b'\\', b'/').lower(): e for e in cg.entries if e['type'] == 2}
import os; S, R = int(os.environ.get("NG_S", 6)), int(os.environ.get("NG_R", 60))
tiles = []
for arg in sys.argv[2:]:
    n, x0, y0 = arg.rsplit(':', 2); x0, y0 = int(x0), int(y0)
    im = Image.open(io.BytesIO(cg.read(ent[n.encode('cp932').lower()]))).convert('RGBA').crop((x0, y0, x0 + R, y0 + R))
    bg = Image.new('RGBA', im.size, (70, 70, 80, 255)); bg.alpha_composite(im)
    bg = bg.convert('RGB').resize((R * S, R * S), Image.NEAREST); d = ImageDraw.Draw(bg)
    for k in range(0, R + 1, 5):
        c = (255, 0, 0) if (x0 + k) % 10 == 0 else (255, 160, 160)
        d.line((k * S, 0, k * S, R * S), fill=c)
        if (x0 + k) % 10 == 0: d.text((k * S + 2, 2), str(x0 + k), fill=(255, 255, 0))
    for k in range(0, R + 1, 5):
        c = (255, 0, 0) if (y0 + k) % 10 == 0 else (255, 160, 160)
        d.line((0, k * S, R * S, k * S), fill=c)
        if (y0 + k) % 10 == 0: d.text((2, k * S + 2), str(y0 + k), fill=(255, 255, 0))
    tiles.append(bg)
sheet = Image.new('RGB', (len(tiles) * (R * S + 10), R * S), 'black')
for i, t in enumerate(tiles): sheet.paste(t, (i * (R * S + 10), 0))
sheet.save(sys.argv[1]); print(sheet.size)
