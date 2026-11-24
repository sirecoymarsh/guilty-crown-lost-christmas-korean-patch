"""eip_record.py 결과 분석: PresentMon 5초 칸의 fps 로 느린 칸·빠른 칸을 가르고, 스레드별로 어디(모듈+4KB)에 있었는지 비교.
python -X utf8 eip_analyze.py <이름> [느림fps=60] [빠름fps=90]"""
import collections, csv, sys
from pathlib import Path

OUT = Path(r'F:\AI\gclx-4k\perf')
name = sys.argv[1]
slow_th = float(sys.argv[2]) if len(sys.argv) > 2 else 60
fast_th = float(sys.argv[3]) if len(sys.argv) > 3 else 90
t0 = float((OUT / f'{name}_t0.txt').read_text()) * 1000
rows = list(csv.DictReader(open(OUT / f'{name}_pm.csv', encoding='utf-8-sig')))
STEP = 5000
fps = collections.Counter()
for r in rows:
    fps[int(float(r['TimeInMs']) // STEP)] += 1
fpsb = {b: c / (STEP / 1000) for b, c in fps.items()}
samples = []
for line in open(OUT / f'{name}_eip.tsv', encoding='utf-8'):
    t, th, mod, off = line.rstrip('\n').split('\t')
    samples.append((int((float(t) - t0) // STEP), int(th), mod, int(off, 16)))
WAIT = {'ntdll.dll', 'win32u.dll', 'KERNELBASE.dll', 'wow64cpu.dll', 'kernel32.dll', 'KERNEL32.DLL', 'user32.dll', 'USER32.dll'}
by_thread = collections.Counter(s[1] for s in samples)
busy_thread = collections.Counter(s[1] for s in samples if s[2] not in WAIT)
print('칸 fps:', ' '.join(f'{b*5}s:{fpsb.get(b,0):.0f}' for b in sorted(fpsb)))
print('스레드(전체 표본, 바쁜 표본):', [(t, by_thread[t], busy_thread[t]) for t, _ in busy_thread.most_common(6)])
slow = {b for b, f in fpsb.items() if f < slow_th}
fast = {b for b, f in fpsb.items() if f >= fast_th}
print(f'느린 칸 {len(slow)}개(<{slow_th}fps), 빠른 칸 {len(fast)}개(>={fast_th}fps)')
for t, _ in busy_thread.most_common(4):
    for label, sel in (('느림', slow), ('빠름', fast)):
        ss = [s for s in samples if s[1] == t and s[0] in sel]
        if not ss:
            continue
        mods = collections.Counter(s[2] for s in ss)
        addr = collections.Counter((s[2], s[3] & ~0xfff) for s in ss if s[2] not in WAIT)
        print(f'\n스레드 {t} [{label}] 표본 {len(ss)}: ' + ', '.join(f'{m} {100*c/len(ss):.0f}%' for m, c in mods.most_common(6)))
        for (m, o), c in addr.most_common(8):
            print(f'    {100*c/len(ss):5.1f}%  {m}+0x{o:x}')
