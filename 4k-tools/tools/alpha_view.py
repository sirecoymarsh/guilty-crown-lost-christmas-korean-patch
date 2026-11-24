"""옛/새 투명도 4배를 나란히(색은 Lanczos). python -X utf8 alpha_view.py out.png name1 name2 ..."""
import sys
from pathlib import Path
import cv2, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r'F:\AI\gclx-4k\tools')
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA
from alpha_scan import old_alpha4, new_alpha4, CG
arc = NPA(CG)
ent = {e['name'].replace(chr(92), '/'): e for e in arc.entries if e['type'] == 2}
def comp(rgb, a, dark):
    h, w = a.shape; yy, xx = np.mgrid[:h, :w]
    bg = np.full((h, w, 1), 20.0) if dark else np.where(((yy // 32 + xx // 32) % 2)[..., None] == 0, 90.0, 150.0)
    al = a[..., None].astype(np.float32) / 255
    return (rgb * al + bg * (1 - al)).clip(0, 255).astype(np.uint8)
rows = []
for name in sys.argv[2:]:
    img = cv2.imdecode(np.frombuffer(arc.read(ent[name]), np.uint8), cv2.IMREAD_UNCHANGED)
    h, w = img.shape[:2]
    rgb4 = cv2.resize(img[:, :, :3], (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    src4 = cv2.resize(img, (w * 4, h * 4), interpolation=cv2.INTER_NEAREST)
    panels = [comp(src4[:, :, :3].astype(np.float32), src4[:, :, 3], True), comp(rgb4, old_alpha4(img[:, :, 3]), True), comp(rgb4, new_alpha4(img[:, :, 3]), True)]
    # 가장 옅은 픽셀이 많은 곳 중심으로 900x600 잘라 보기
    a = img[:, :, 3]; soft = ((a > 0) & (a < 128)).astype(np.float32)
    s = cv2.boxFilter(soft, -1, (min(w, 225), min(h, 150)))
    cy, cx = np.unravel_index(np.argmax(s), s.shape)
    y0 = int(np.clip(cy * 4 - 300, 0, max(0, h * 4 - 600))); x0 = int(np.clip(cx * 4 - 450, 0, max(0, w * 4 - 900)))
    crops = [p[y0:y0 + 600, x0:x0 + 900] for p in panels]
    ch, cw = crops[0].shape[:2]
    row = np.full((ch + 22, cw * 3 + 20, 3), 40, np.uint8)
    for i, c in enumerate(crops): row[22:, i * (cw + 10):i * (cw + 10) + cw] = c
    im = Image.fromarray(row[:, :, ::-1].copy()); ImageDraw.Draw(im).text((4, 4), f'{name[:40]} | 1x nearest | old alpha4 | new alpha4', fill=(255, 255, 0))
    rows.append(im)
W = max(r.width for r in rows); out = Image.new('RGB', (W, sum(r.height for r in rows)), (40, 40, 40)); y = 0
for r in rows: out.paste(r, (0, y)); y += r.height
out.save(sys.argv[1]); print(sys.argv[1])
