"""타이틀이 밝아지기 시작하는 순간 불러오기 자리를 한 번 누르고, 그 뒤 화면을 찍는다(앞 창, 사용자가 조작을 맡겼을 때만).
python -X utf8 fg_fade_click.py <이름> [밝기 문턱=150]"""
import sys, time
import numpy as np
sys.path.insert(0, r'F:\AI\gclx-4k\tools')
import fg_probe as F
from PIL import ImageGrab, Image

name = sys.argv[1]; thr = float(sys.argv[2]) if len(sys.argv) > 2 else 150
U = F.U
t0 = time.time()
while time.time() - t0 < 90:
    im = ImageGrab.grab(bbox=(2400, 1000, 3400, 1800)).convert('L')   # right half of the title art (white when the title is up)
    m = float(np.asarray(im).mean())
    if m > thr:
        break
    time.sleep(0.25)
print('title bright', round(m, 1), 'after', round(time.time() - t0, 1), 's')
F.click_at(1800, 1418)
shots = []
for i in range(4):
    time.sleep(1.5); shots.append(F.shot(f'{name}_{i}'))
o = Image.new('RGB', (1024 * len(shots), 540))
for i, p in enumerate(shots):
    o.paste(Image.open(p).resize((1024, 540)), (i * 1024, 0))
o.save(F.OUT / f'{name}_seq.png'); print(F.OUT / f'{name}_seq.png')
