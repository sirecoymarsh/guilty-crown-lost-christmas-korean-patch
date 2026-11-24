"""시험 4K 캡처를 훑어보기 판으로. python -X utf8 shot_sheet.py <run 이름> [한 판 장수=12]
판은 run\\sheets\\sheet-NN.jpg (3열, 장마다 960x540, 왼쪽 위에 번호)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

run = Path(r'F:\AI\gclx-4k\testrun') / sys.argv[1]
per = int(sys.argv[2]) if len(sys.argv) > 2 else 12
shots = sorted((run / 'profile').glob('shot-*.bmp'))
out = run / 'sheets'
out.mkdir(exist_ok=True)
W, H, C = 960, 540, 3
for k in range(0, len(shots), per):
    group = shots[k:k + per]
    rows = (len(group) + C - 1) // C
    sheet = Image.new('RGB', (W * C, H * rows), 'gray')
    d = ImageDraw.Draw(sheet)
    for i, p in enumerate(group):
        im = Image.open(p).convert('RGB').resize((W, H), Image.LANCZOS)
        x, y = (i % C) * W, (i // C) * H
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + 70, y + 30], fill='black')
        d.text((x + 6, y + 6), p.stem[5:], fill='yellow')
    sheet.save(out / f'sheet-{k // per:02d}.jpg', quality=85)
print(len(shots), '장 →', out)
