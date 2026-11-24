"""PresentMon CSV 요약: 게임이 내보낸 프레임(MsBetweenPresents)과 화면에 실제로 바뀐 프레임(MsBetweenDisplayChange)을 나눠 본다.
python -X utf8 pm_summary.py <csv> [<csv> …]"""
import csv, statistics, sys
from collections import Counter


def num(v):
    try:
        return float(v)
    except Exception:
        return None


for path in sys.argv[1:]:
    rows = [r for r in csv.DictReader(open(path, encoding='utf-8-sig')) if num(r.get('TimeInMs') or '') is not None]   # 끊긴 마지막 줄 빼기
    if not rows:
        print(path, 'no rows'); continue
    t = [num(r['TimeInMs']) for r in rows]
    span = (t[-1] - t[0]) / 1000 if len(t) > 1 else 0
    bp = [x for x in (num(r['MsBetweenPresents']) for r in rows) if x]
    bd = [x for x in (num(r['MsBetweenDisplayChange']) for r in rows) if x]
    gpu = [x for x in (num(r['MsGPUBusy']) for r in rows) if x is not None]
    cpu = [x for x in (num(r['MsCPUBusy']) for r in rows) if x is not None]
    lat = [x for x in (num(r['MsUntilDisplayed']) for r in rows) if x]

    def pct(a, p):
        a = sorted(a); return a[min(len(a) - 1, int(len(a) * p / 100))] if a else None

    def fps(a):
        return round(1000 / statistics.mean(a), 1) if a else None
    disp_hist = Counter(min(5, round(x / 8.333)) for x in bd)   # 120Hz 몇 칸마다 바뀌었나(1=120fps, 2=60, 3=40, 4=30)
    print(f'{path}\n  {span:.1f}초  모드 {Counter(r["PresentMode"] for r in rows).most_common(2)}')
    print(f'  내보낸 프레임 {fps(bp)}fps (p95 {pct(bp,95):.1f}ms)  화면에 바뀐 프레임 {fps(bd)}fps (p95 {pct(bd,95):.1f}ms)' if bd else f'  내보낸 프레임 {fps(bp)}fps')
    print(f'  화면 바뀜 간격(120Hz 칸): {dict(sorted(disp_hist.items()))}  표시 지연 중앙 {pct(lat,50):.1f}ms p95 {pct(lat,95):.1f}ms' if lat else '')
    print(f'  CPU 바쁨 중앙 {pct(cpu,50):.2f}ms p95 {pct(cpu,95):.2f}ms  GPU 바쁨 중앙 {pct(gpu,50):.2f}ms p95 {pct(gpu,95):.2f}ms')
