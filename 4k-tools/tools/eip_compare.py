"""느린 칸과 빠른 칸에서 스레드별로 「바쁨(어느 코드)」과 「기다림(누가 불렀나)」을 나란히: 주 스레드(d3d9·4K DLL 표본이 가장 많은 스레드)와 바쁜 일꾼 스레드.
python -X utf8 eip_compare.py <이름> [느림fps=60] [빠름fps=100]"""
import collections, csv, sys
from pathlib import Path

OUT = Path(r'F:\AI\gclx-4k\perf')
name = sys.argv[1]
slow_th = float(sys.argv[2]) if len(sys.argv) > 2 else 60
fast_th = float(sys.argv[3]) if len(sys.argv) > 3 else 100
t0 = float((OUT / f'{name}_t0.txt').read_text()) * 1000
fps = collections.Counter()
for r in csv.DictReader(open(OUT / f'{name}_pm.csv', encoding='utf-8-sig')):
    try:
        fps[int(float(r['TimeInMs']) // 5000)] += 1
    except Exception:
        pass
slow = {b for b, c in fps.items() if c / 5 < slow_th and b > 3}
fast = {b for b, c in fps.items() if c / 5 >= fast_th}
WAIT = {'ntdll.dll', 'win32u.dll', 'KERNELBASE.dll', 'wow64cpu.dll', 'KERNEL32.DLL', 'kernel32.dll'}
rows = []
gpu_thr = collections.Counter(); busy_thr = collections.Counter()
for line in open(OUT / f'{name}_eip.tsv', encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    b = int((float(p[0]) - t0) // 5000)
    lab = 'S' if b in slow else 'F' if b in fast else None
    if not lab:
        continue
    th, mod, off = p[1], p[2], int(p[3], 16)
    callers = p[4].split(',') if len(p) > 4 and p[4] else []
    rows.append((lab, th, mod, off, callers))
    if mod in ('d3d9.dll', 'nvd3dum.dll', 'n2hd_runtime.dll'):
        gpu_thr[th] += 1
    if mod not in WAIT:
        busy_thr[th] += 1
main = gpu_thr.most_common(1)[0][0]
workers = [t for t, _ in busy_thr.most_common(5) if t != main][:3]
print(f'느린 칸 {len(slow)}개, 빠른 칸 {len(fast)}개, 주 스레드 {main}, 일꾼 {workers}')
for th in [main] + workers:
    for lab in ('S', 'F'):
        rs = [r for r in rows if r[1] == th and r[0] == lab]
        if not rs:
            continue
        busy = [r for r in rs if r[2] not in WAIT]
        print(f'\n[{"주" if th == main else "일꾼"} {th}] {"느림" if lab == "S" else "빠름"}: 표본 {len(rs)}, 바쁨 {100 * len(busy) / len(rs):.0f}%')
        code = collections.Counter((r[2], r[3] & ~0xff) for r in busy)
        for (m, o), c in code.most_common(6):
            print(f'   바쁨 {100 * c / len(rs):5.1f}%  {m}+0x{o:x}')
        waits = collections.Counter(','.join(r[4][:3]) for r in rs if r[2] in WAIT)
        for k, c in waits.most_common(5):
            print(f'   기다림 {100 * c / len(rs):5.1f}%  <- {k or "?"}')
