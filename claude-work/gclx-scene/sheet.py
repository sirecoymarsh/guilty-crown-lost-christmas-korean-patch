import sys
from pathlib import Path
from PIL import Image, ImageDraw
d = Path(sys.argv[1]); a, b = int(sys.argv[2]), int(sys.argv[3]); out = sys.argv[4]
ims = []
for i in range(a, b + 1):
    p = d / f'shot-{i:03d}.bmp'
    if not p.exists(): continue
    im = Image.open(p).convert('RGB').resize((480, 270)); ImageDraw.Draw(im).text((6, 4), str(i), fill=(255, 255, 0)); ims.append(im)
cols = 4; rows = (len(ims) + cols - 1) // cols
sh = Image.new('RGB', (480 * cols, 270 * rows))
for k, im in enumerate(ims): sh.paste(im, ((k % cols) * 480, (k // cols) * 270))
sh.save(out); print(len(ims))
