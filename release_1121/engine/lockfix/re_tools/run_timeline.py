"""시험 폴더의 trace.log·locks.log·누름을 한 줄기 시험 시계로 섞어 보여 준다(읽기만).
python -X utf8 run_timeline.py <시험 이름> [시작초 끝초]"""
import ctypes, json, sys, time
from pathlib import Path

run = Path(r'F:\AI\gclx-4k\testrun') / sys.argv[1]
a = float(sys.argv[2]) if len(sys.argv) > 2 else 0
b = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9
rep = json.loads((run / 'report.json').read_text('utf-8'))
k32 = ctypes.windll.kernel32; k32.GetTickCount64.restype = ctypes.c_ulonglong
boot = time.time() - k32.GetTickCount64() / 1000.0
ev = []
for name in ('trace.log', 'locks.log'):
    p = run / 'profile' / name
    if p.exists():
        for line in p.read_text(errors='replace').splitlines():
            f = line.split(' ', 1)
            if f[0].isdigit():
                ev.append(((boot + int(f[0]) / 1000.0) - rep['t0_epoch'], name[:5], f[1] if len(f) > 1 else ''))
for c in rep.get('clicks_xy', []):
    ev.append((c[1], 'CLICK', c[0] + ' (단추 뗀 뒤 적은 시각)'))
for h in rep.get('hovers_xy', []):
    ev.append((h[1], 'hover', h[0]))
shots = sorted((run / 'profile').glob('shot-*'))
for t, kind, text in sorted(ev):
    if a <= t <= b:
        print(f'{t:8.2f}  {kind:<5} {text}')
