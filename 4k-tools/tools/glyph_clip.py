"""Codex 4K 글자(N2HD_Glyph) 재현: 맑은 고딕 26px 의 1배 글자 칸에 GetGlyphOutline 4배를 넣을 때 잘리는 잉크 비율.
python -X utf8 glyph_clip.py [글자들]  →  F:\\AI\\gclx-4k\\testrun\\glyph_clip.png (원래 4배 | 잘린 4배)"""
import ctypes, ctypes.wintypes as wt, sys
import numpy as np
from PIL import Image, ImageDraw

gdi = ctypes.windll.gdi32
class GLYPHMETRICS(ctypes.Structure):
    _fields_ = [('gmBlackBoxX', wt.UINT), ('gmBlackBoxY', wt.UINT), ('gmptGlyphOrigin', wt.POINT), ('gmCellIncX', ctypes.c_short), ('gmCellIncY', ctypes.c_short)]
class FIXED(ctypes.Structure):
    _fields_ = [('fract', wt.WORD), ('value', ctypes.c_short)]
class MAT2(ctypes.Structure):
    _fields_ = [('eM11', FIXED), ('eM12', FIXED), ('eM21', FIXED), ('eM22', FIXED)]
gdi.CreateFontW.restype = wt.HFONT

def mat(s):
    m = MAT2(); m.eM11.value = s; m.eM22.value = s; return m

def outline(dc, ch, s):
    gm = GLYPHMETRICS(); m = mat(s)
    n = gdi.GetGlyphOutlineW(dc, ord(ch), 6, ctypes.byref(gm), 0, None, ctypes.byref(m))   # GGO_GRAY8_BITMAP
    buf = (ctypes.c_ubyte * max(n, 1))()
    gdi.GetGlyphOutlineW(dc, ord(ch), 6, ctypes.byref(gm), n, buf, ctypes.byref(m))
    pitch = (gm.gmBlackBoxX + 3) & ~3
    a = np.frombuffer(bytes(buf), np.uint8)[:pitch * gm.gmBlackBoxY].reshape(gm.gmBlackBoxY, pitch)[:, :gm.gmBlackBoxX] if n else np.zeros((0, 0), np.uint8)
    return gm, a

text = sys.argv[1] if len(sys.argv) > 1 else '덮었다 넘겼다 뻗어 젖혀 흩어 엎드려 덤벼'
dc = gdi.CreateCompatibleDC(None)
font = gdi.CreateFontW(26, 0, 0, 0, 500, 0, 0, 0, 1, 0, 0, 4, 0, 'Malgun Gothic')   # HANGUL_CHARSET, ANTIALIASED
gdi.SelectObject(dc, font)
rows, report = [], []
for ch in text:
    if ch == ' ': continue
    g1, a1 = outline(dc, ch, 1)
    g4, a4 = outline(dc, ch, 4)
    w, h = g1.gmBlackBoxX, g1.gmBlackBoxY                       # Codex: the 1x cell (engine glyph texture) ~ black box
    dx = g4.gmptGlyphOrigin.x - g1.gmptGlyphOrigin.x * 4; dy = g1.gmptGlyphOrigin.y * 4 - g4.gmptGlyphOrigin.y
    cell = np.zeros((h * 4, w * 4), np.uint8)
    ys, xs = np.nonzero(a4)
    tx, ty = xs + dx, ys + dy
    ok = (tx >= 0) & (tx < w * 4) & (ty >= 0) & (ty < h * 4)
    cell[ty[ok], tx[ok]] = a4[ys[ok], xs[ok]]
    lost = a4[ys[~ok], xs[~ok]].astype(float).sum() / max(1.0, a4.astype(float).sum())
    report.append(f'{ch}: 1배 칸 {w}x{h}, 4배 잉크 {g4.gmBlackBoxX}x{g4.gmBlackBoxY} 위치 {dx},{dy} → 잘린 잉크 {lost * 100:.1f}%')
    full = np.zeros((max(h * 4, a4.shape[0] + max(0, dy)) + 8, max(w * 4, a4.shape[1] + max(0, dx)) + 8), np.uint8)
    full[max(0, dy):max(0, dy) + a4.shape[0], max(0, dx):max(0, dx) + a4.shape[1]] = a4
    rows.append((full, cell))
print('\n'.join(report))
W = sum(max(f.shape[1], c.shape[1]) + 20 for f, c in rows); H = max(f.shape[0] for f, c in rows) * 2 + 30
img = Image.new('L', (W, H), 30); x = 0
for f, c in rows:
    img.paste(Image.fromarray((f * 4).clip(0, 255).astype(np.uint8)), (x, 0)); img.paste(Image.fromarray((c * 4).clip(0, 255).astype(np.uint8)), (x, H // 2 + 10))
    x += max(f.shape[1], c.shape[1]) + 20
img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
img.save(r'F:\AI\gclx-4k\testrun\glyph_clip.png')
