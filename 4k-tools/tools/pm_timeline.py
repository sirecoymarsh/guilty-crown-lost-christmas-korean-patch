"""PresentMon CSV 를 5초 칸으로: fps, 프레임 CPU 바쁨, Present 안에서 보낸 시간(합성 복사 대기), CPU 기다림.
python -X utf8 pm_timeline.py <csv> [칸초=5]"""
import csv, statistics, sys

rows = [r for r in csv.DictReader(open(sys.argv[1], encoding='utf-8-sig')) if (r.get('TimeInMs') or '').replace('.', '', 1).isdigit()]   # 끊긴 마지막 줄 빼기
step = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0


def f(r, k):
    try:
        return float(r[k])
    except Exception:
        return None


t0 = f(rows[0], 'TimeInMs')
buckets = {}
for r in rows:
    b = int((f(r, 'TimeInMs') - t0) / 1000 // step)
    buckets.setdefault(b, []).append(r)
print('초      fps  CPU바쁨중앙 p90  Present안중앙 p90  CPU기다림중앙  사이간격p90')
allp, allc = [], []
for b in sorted(buckets):
    rs = buckets[b]
    cpu = [x for x in (f(r, 'MsCPUBusy') for r in rs) if x is not None]
    inp = [x for x in (f(r, 'MsInPresentAPI') for r in rs) if x is not None]
    wait = [x for x in (f(r, 'MsCPUWait') for r in rs) if x is not None]
    bp = [x for x in (f(r, 'MsBetweenPresents') for r in rs) if x]
    q = lambda a, p: sorted(a)[min(len(a) - 1, int(len(a) * p))] if a else 0
    print(f'{b*step:5.0f} {len(rs)/step:6.1f}  {statistics.median(cpu):6.1f} {q(cpu,.9):6.1f}   {statistics.median(inp):6.2f} {q(inp,.9):6.2f}   {statistics.median(wait):6.2f}   {q(bp,.9):6.1f}')
    allp += inp; allc += cpu
print('전체: Present 안 중앙', round(statistics.median(allp), 2), 'ms, CPU 바쁨 중앙', round(statistics.median(allc), 2), 'ms')
