"""frames.bin(DLL 시험 기록) 으로 입력마다 반응 시간: 입력 뒤 첫 화면까지, 그 뒤 이어진 프레임 묶음 길이."""
import json, struct, sys, statistics
from pathlib import Path
RUNS = Path(r'F:/AI/gclx-4k/testrun')
def load(run):
    r = json.load(open(RUNS / run / 'report.json', encoding='utf-8')); raw = (RUNS / run / 'profile' / 'frames.bin').read_bytes()
    return r, sorted(struct.unpack('<%dd' % (len(raw) // 8), raw[:len(raw) // 8 * 8]))
summary = {}
for run in sys.argv[1:]:
    r, ts = load(run); t0 = r['t0_epoch']; ev = r['events']
    rd = [t for t in ts if t0 + 95 <= t <= t0 + 105]
    print(run, 'frames', len(ts), 'reading fps', round(len(rd) / 10))
    rows = []
    for i, (n, t) in enumerate(ev):
        nxt = ev[i + 1][1] if i + 1 < len(ev) else t + 6
        seg = [x for x in ts if t <= x < min(nxt, t + 6)]
        first = (seg[0] - t) * 1000 if seg else None
        rows.append((n, round(t - t0, 1), None if first is None else round(first), len(seg)))
        print('   %-10s %6.1fs  first %s  frames %d' % (n, t - t0, '-' if first is None else '%5.0fms' % first, len(seg)))
    def med(kind, sel):
        v = [f for (n, s, f, c), (n2, t) in zip(rows, ev) if n == kind and f is not None and sel(s)]
        return (round(statistics.median(v)), max(v), len(v)) if v else None
    summary[run] = {'open': rows[0][2], 'scroll_up_med_max_n': med('wheel_up', lambda s: 115.5 < s < 130), 'scroll_down_med_max_n': med('wheel_down', lambda s: True),
                    'reopen': next((f for n, s, f, c in rows if n == 'wheel_up' and s >= 130), None), 'click': next((f for n, s, f, c in rows if n == 'click'), None)}
print(json.dumps(summary, ensure_ascii=False, indent=1))
