"""매니페스트 키 몇 개를 원본(1배)·결과(4배를 줄임)·결과 1:1 일부로 나란히. python -X utf8 audit_view.py out.png key1 key2 ..."""
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
arcs = {}
def source(name):
    for p in [Path(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\outputs\korean-game-candidate\game\cg.npa')]:
        if p not in arcs:
            a = NPA(p); arcs[p] = (a, {e['name'].replace(chr(92), '/').lower(): e for e in a.entries if e['type'] == 2})
        a, ent = arcs[p]
        for cand in (name.lower(), ('cg/' + name).lower()):
            if cand in ent:
                return cv2.imdecode(np.frombuffer(a.read(ent[cand]), np.uint8), cv2.IMREAD_UNCHANGED)
    raise KeyError(name)
def on_check(rgba):
    if rgba.shape[2] == 3: return rgba
    h, w = rgba.shape[:2]; yy, xx = np.mgrid[:h, :w]
    bg = np.where(((yy // 16 + xx // 16) % 2)[..., None] == 0, 90, 150).astype(np.float32)
    a = rgba[:, :, 3:4].astype(np.float32) / 255
    return (rgba[:, :, :3] * a + bg * (1 - a)).astype(np.uint8)
rows = []
for key in sys.argv[2:]:
    v = m[key]
    src = source(v['name']); out = imagecodecs.jpegxl_decode((H / f'{key}.jxl').read_bytes())
    if out.shape[2] == 4: out = out[:, :, [2, 1, 0, 3]]
    else: out = out[:, :, ::-1]
    if src.ndim == 2: src = cv2.cvtColor(src, cv2.COLOR_GRAY2BGR)
    small = cv2.resize(out, (src.shape[1], src.shape[0]), interpolation=cv2.INTER_AREA)
    tw = 600; th = int(src.shape[0] * tw / src.shape[1])
    a = cv2.resize(on_check(src), (tw, th), interpolation=cv2.INTER_AREA)
    b = cv2.resize(on_check(small), (tw, th), interpolation=cv2.INTER_AREA)
    oy, ox = out.shape[0] // 2 - 200, out.shape[1] // 2 - 300
    c = on_check(out[max(0, oy):oy + 400, max(0, ox):ox + 600])
    row = np.full((max(th, c.shape[0]) + 24, tw * 2 + c.shape[1] + 20, 3), 30, np.uint8)
    row[24:24 + th, :tw] = a; row[24:24 + th, tw + 10:tw * 2 + 10] = b; row[24:24 + c.shape[0], tw * 2 + 20:tw * 2 + 20 + c.shape[1]] = c
    im = Image.fromarray(row[:, :, ::-1].copy()); d = ImageDraw.Draw(im)
    d.text((4, 4), f"{key} {v['method']} src_mad {v['source_mad']} {v['w']}x{v['h']}  | left: 1x source | mid: result shrunk | right: result 1:1 centre", fill=(255, 255, 0))
    rows.append(im)
W = max(r.width for r in rows); out_im = Image.new('RGB', (W, sum(r.height for r in rows)), (30, 30, 30)); y = 0
for r in rows: out_im.paste(r, (0, y)); y += r.height
out_im.save(sys.argv[1]); print(sys.argv[1])
