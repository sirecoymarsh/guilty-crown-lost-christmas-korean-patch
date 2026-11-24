"""멈춤 앞뒤의 프레임 시각을 ms 로 찍는다(읽기만).  python -X utf8 frames_around.py <시험> <시작초> <끝초>"""
import json, struct, sys
from pathlib import Path
RUNS = Path(r'F:\AI\gclx-4k\testrun')
name, a, b = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
run = RUNS / name
rep = json.loads((run / 'report.json').read_text('utf-8'))
raw = (run / 'profile' / 'frames.bin').read_bytes()
ts = [t - rep['t0_epoch'] for t in struct.unpack('<%dd' % (len(raw) // 8), raw[:len(raw) // 8 * 8])]
ev = sorted([(h[1], 'hover ' + h[0]) for h in rep.get('hovers_xy', [])] + [(c[1], 'CLICK ' + c[0]) for c in rep.get('clicks_xy', [])])
seg = [t for t in ts if a <= t <= b]
out = []
prev = None
i = 0
for t in seg:
    while i < len(ev) and ev[i][0] < t:
        if ev[i][0] >= a:
            out.append(f'   -- {ev[i][0]:.1f} {ev[i][1]} (도구 기록 시각, 보낸 뒤)')
        i += 1
    d = (t - prev) * 1000 if prev is not None else 0
    mark = '  <<<<' if d > 600 else ('  <' if d > 250 else '')
    out.append(f'{t:8.3f}  +{d:7.1f}ms{mark}')
    prev = t
# 긴 60fps 구간은 접는다
res = []
run_ = 0
for line in out:
    if line.startswith('   --') or '<' in line:
        if run_ > 6:
            res.append(f'      ... ({run_ - 6}프레임 생략)')
        res.append(line); run_ = 0
    else:
        run_ += 1
        if run_ <= 6:
            res.append(line)
if run_ > 6:
    res.append(f'      ... ({run_ - 6}프레임 생략)')
print('\n'.join(res))
