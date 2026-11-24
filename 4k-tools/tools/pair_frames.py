"""켬/끔 시험의 같은 장면 짝 찾기. python -X utf8 pair_frames.py t9 t10"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
R = Path(r'F:\AI\gclx-4k\testrun')
def frames(t):
    return {int(p.stem[5:]): np.asarray(Image.open(p).convert('L').resize((128, 72), Image.BILINEAR), dtype=np.float32)
            for p in sorted((R / t / 'profile').glob('shot-*.*'))}
A, B = frames(sys.argv[1]), frames(sys.argv[2])
out = []
for a, fa in A.items():
    b = min(B, key=lambda b: np.abs(fa - B[b]).mean())
    out.append(f'{a}:{b}:{np.abs(fa - B[b]).mean():.1f}')
print(' '.join(out))
