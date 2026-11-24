"""곡 바꾸기 시험(lk_mc_*)에서 누름마다 가장 긴 프레임 간격이 표지 s8(곡 누름·KuFade 시작)·s9(SoundPlay 뒤) 사이 어디에 있는지 본다.
python -X utf8 gap_at_click.py <시험 이름> [...]"""
import ctypes, json, struct, sys, time
from pathlib import Path

RUNS = Path(r'F:\AI\gclx-4k\testrun')
k32 = ctypes.windll.kernel32; k32.GetTickCount64.restype = ctypes.c_ulonglong
for name in sys.argv[1:]:
    run = RUNS / name
    rep = json.loads((run / 'report.json').read_text('utf-8'))
    raw = (run / 'profile' / 'frames.bin').read_bytes()
    ts = [t - rep['t0_epoch'] for t in struct.unpack('<%dd' % (len(raw) // 8), raw[:len(raw) // 8 * 8])]
    boot = time.time() - k32.GetTickCount64() / 1000.0
    ev = []
    for line in (run / 'profile' / 'trace.log').read_text(errors='replace').splitlines():
        p = line.split()
        if len(p) >= 2 and p[1].startswith('trace_s'):
            ev.append(((boot + (int(p[0]) & 0xffffffff) / 1000.0) - rep['t0_epoch'], p[1][6:8]))
    print(name)
    clicks = [(c[0], c[1]) for c in rep.get('clicks_xy', [])][1:]
    for i, (spec, sent) in enumerate(clicks):
        nxt = clicks[i + 1][1] if i + 1 < len(clicks) else 1e9
        seg = [(t, k) for t, k in ev if sent - 1.2 <= t < nxt - 1.2]
        tt = {}
        for t, k in seg:
            tt.setdefault(k, t)
        a = tt.get('s8', tt.get('s3'))
        if a is None:
            continue
        b = tt.get('s9', a)
        gaps = [(x, y - x) for x, y in zip(ts, ts[1:]) if x < b + 0.4 and y > a - 0.2]
        gx, g = max(gaps, key=lambda q: q[1]) if gaps else (0, 0)
        print(f'  {spec:<12} s8→s9 {(b - a) * 1000:5.0f}ms | 가장 긴 간격 {g * 1000:4.0f}ms, s8 뒤 {(gx - a) * 1000:+5.0f}ms 에서 시작, s9 {"앞" if gx + g <= b + 0.02 else "뒤"} {abs((gx + g - b)) * 1000:4.0f}ms 에 끝')
