"""손 모양 지도(hand.txt)들을 타이틀 화면 위에 겹쳐 한 장으로: 빨간 점 = 엔진이 손 모양(단추 위)으로 정한 곳, 초록 상자 = 대본의 판정 그림 자리.
python -X utf8 hand_maps_png.py <출력.png> <제목=run 이름> ..."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

RUNS = Path(r'F:\AI\gclx-4k\testrun')
base = Image.open(r'F:\AI\gclx-4k\testrun\fg\back_title.png').crop((128, 0, 3968, 2160)).resize((1024, 576))
font = ImageFont.truetype('malgun.ttf', 26)
boxes = [(416, 326, 94, 36), (416, 362, 95, 36), (416, 398, 137, 36), (416, 434, 76, 38)]   # start, load, config, exit (hit pictures, CG hidden)
panels = []
for arg in sys.argv[2:]:
    title, run = arg.split('=')
    lines = (RUNS / run / 'hand.txt').read_text('utf-8').splitlines()[1:]
    im = base.copy().convert('RGB'); d = ImageDraw.Draw(im)
    for x, y, w, h in boxes:
        d.rectangle([x, y, x + w, y + h], outline=(0, 170, 0), width=2)
    for ln in lines:
        y = int(ln[:3]); cells = ln[4:]
        for i, c in enumerate(cells):
            x = 380 + 24 * i
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(220, 0, 0) if c == '#' else (170, 170, 170))
    im = im.crop((300, 250, 1024, 576))
    canvas = Image.new('RGB', (im.width, im.height + 40), 'white'); canvas.paste(im, (0, 40))
    ImageDraw.Draw(canvas).text((8, 4), title, fill='black', font=font)
    panels.append(canvas)
out = Image.new('RGB', (sum(p.width for p in panels) + 10 * (len(panels) - 1), panels[0].height), 'white')
x = 0
for p in panels:
    out.paste(p, (x, 0)); x += p.width + 10
out.save(sys.argv[1]); print(sys.argv[1])
