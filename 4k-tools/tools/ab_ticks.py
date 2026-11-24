"""PresentMon CSV 여러 개를 같은 구간으로 나란히: 5초 칸 fps 와, 지정 구간의 평균 fps·간격(8.33ms 칸) 분포.
python -X utf8 ab_ticks.py <구간시작초> <구간끝초> <csv> [<csv> …]"""
import collections, csv, sys

lo, hi = float(sys.argv[1]), float(sys.argv[2])
for path in sys.argv[3:]:
    rows = [r for r in csv.DictReader(open(path, encoding='utf-8-sig')) if (r.get('TimeInMs') or '').replace('.', '', 1).isdigit()]
    t0 = float(rows[0]['TimeInMs'])
    bins = collections.Counter(int((float(r['TimeInMs']) - t0) / 5000) for r in rows)
    win = [r for r in rows if lo <= (float(r['TimeInMs']) - t0) / 1000 < hi]
    ticks = collections.Counter(min(9, round(float(r['MsBetweenPresents']) / 8.33)) for r in win)
    print(f'{path}\n  5초칸 fps: {" ".join(f"{bins[b] / 5:.0f}" for b in range(max(bins) + 1))}')
    print(f'  {lo:.0f}~{hi:.0f}초 평균 {len(win) / (hi - lo):.1f}fps  간격(칸) {dict(sorted(ticks.items()))}')
