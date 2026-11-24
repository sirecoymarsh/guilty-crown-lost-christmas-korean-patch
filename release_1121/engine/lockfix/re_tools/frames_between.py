"""trace 표지 두 개 사이(h0→h1 등)의 걸린 시간과 그 사이 프레임 수를 센다(읽기만).
python -X utf8 frames_between.py <시험 이름> <표지A> <표지B>   예: h0 h1"""
import ctypes, json, struct, sys, time
from pathlib import Path

run = Path(r'F:\AI\gclx-4k\testrun') / sys.argv[1]
ka, kb = sys.argv[2], sys.argv[3]
rep = json.loads((run / 'report.json').read_text('utf-8'))
k32 = ctypes.windll.kernel32; k32.GetTickCount64.restype = ctypes.c_ulonglong
boot = time.time() - k32.GetTickCount64() / 1000.0
ev = []
for line in (run / 'profile' / 'trace.log').read_text(errors='replace').splitlines():
    f = line.split()
    if len(f) >= 2 and f[1].startswith('trace_'):
        ev.append(((boot + int(f[0]) / 1000.0) - rep['t0_epoch'], f[1][6:8]))
raw = (run / 'profile' / 'frames.bin').read_bytes()
ts = [t - rep['t0_epoch'] for t in struct.unpack('<%dd' % (len(raw) // 8), raw[:len(raw) // 8 * 8])]
out = []
for i, (t, k) in enumerate(ev):
    if k == ka:
        nxt = next(((t2, k2) for t2, k2 in ev[i + 1:] if k2 == kb), None)
        if nxt:
            n = sum(1 for x in ts if t <= x < nxt[0])
            out.append((round(t, 2), round((nxt[0] - t) * 1000), n))
print(f'{sys.argv[1]} {ka}->{kb}: (시작초, ms, 프레임 수)')
for o in out:
    print('  ', o, f'{o[1] / max(o[2], 1):.1f} ms/프레임' if o[2] else '')
