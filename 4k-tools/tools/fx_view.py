"""효과·겹침 그림: 원본(4배 nearest)과 결과(4배 그대로)를 어두운 바탕에 얹어 같은 곳을 잘라 나란히. python -X utf8 fx_view.py out.png key..."""
import json, sys
from pathlib import Path
import cv2, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\reconquista_flowchart_20261024\build\pylib')
import imagecodecs
from npa_adapter import NPA
H = Path(r'F:\AI\gclx-4k\hires')
m = json.loads((H / 'manifest.json').read_text('utf-8'))
arc = NPA(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\outputs\korean-game-candidate\game\cg.npa')
ent = {e['name'].replace(chr(92), '/'): e for e in arc.entries if e['type'] == 2}
def over(rgba, bg=24.0):
    a = rgba[:, :, 3:4].astype(np.float32) / 255
    return (rgba[:, :, :3].astype(np.float32) * a + bg * (1 - a)).clip(0, 255).astype(np.uint8)
rows = []
for key in sys.argv[2:]:
    v = m[key]
    src = cv2.imdecode(np.frombuffer(arc.read(ent[v['name']]), np.uint8), cv2.IMREAD_UNCHANGED)
    out = imagecodecs.jpegxl_decode((H / f'{key}.jxl').read_bytes())[:, :, [2, 1, 0, 3]]
    ow, oh = out.shape[1], out.shape[0]
    big = cv2.resize(src, (ow, oh), interpolation=cv2.INTER_NEAREST)
    A, B = over(big), over(out)
    s = cv2.boxFilter((src[:, :, 3] > 0).astype(np.float32), -1, (max(1, src.shape[1] // 5), max(1, src.shape[0] // 5)))
    cy, cx = np.unravel_index(np.argmax(s), s.shape)
    fy, fx = oh / src.shape[0], ow / src.shape[1]
    y0 = int(np.clip(cy * fy - 260, 0, max(0, oh - 520))); x0 = int(np.clip(cx * fx - 400, 0, max(0, ow - 800)))
    a, b = A[y0:y0 + 520, x0:x0 + 800], B[y0:y0 + 520, x0:x0 + 800]
    row = np.full((a.shape[0] + 22, a.shape[1] * 2 + 10, 3), 50, np.uint8); row[22:, :a.shape[1]] = a; row[22:, a.shape[1] + 10:] = b
    im = Image.fromarray(row[:, :, ::-1].copy()); ImageDraw.Draw(im).text((4, 4), f'{key} | source (nearest) | result', fill=(255, 255, 0)); rows.append(im)
W = max(r.width for r in rows); o = Image.new('RGB', (W, sum(r.height for r in rows)), (50, 50, 50)); y = 0
for r in rows: o.paste(r, (0, y)); y += r.height
o.save(sys.argv[1]); print(sys.argv[1])
