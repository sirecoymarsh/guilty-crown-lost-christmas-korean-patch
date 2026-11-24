"""기다리는 표본이 32비트 ntdll 의 어느 함수(시스템 호출 꼴)에 있는지: 느린 칸/빠른 칸, 스레드별.
python -X utf8 eip_waits.py <이름> <스레드,…> [느림fps=60] [빠름fps=90]"""
import collections, csv, struct, sys
from pathlib import Path

OUT = Path(r'F:\AI\gclx-4k\perf')
name, tids = sys.argv[1], [int(x) for x in sys.argv[2].split(',')]
slow_th = float(sys.argv[3]) if len(sys.argv) > 3 else 60
fast_th = float(sys.argv[4]) if len(sys.argv) > 4 else 90


def exports(path):
    b = open(path, 'rb').read()
    pe = struct.unpack_from('<I', b, 0x3c)[0]; opt = pe + 24
    nsec = struct.unpack_from('<H', b, pe + 6)[0]; so = opt + struct.unpack_from('<H', b, pe + 20)[0]
    secs = [struct.unpack_from('<IIII', b, so + i * 40 + 8) for i in range(nsec)]   # vsize, va, rawsize, raw
    off = lambda rva: next(rva - va + raw for vs, va, rs, raw in secs if va <= rva < va + max(vs, rs))
    erva = struct.unpack_from('<I', b, opt + 96)[0]; e = off(erva)
    nfun, nname, afun, aname, aord = struct.unpack_from('<IIIII', b, e + 20)
    funs = [struct.unpack_from('<I', b, off(afun) + 4 * i)[0] for i in range(nfun)]
    res = []
    for i in range(nname):
        nr = struct.unpack_from('<I', b, off(aname) + 4 * i)[0]; o = struct.unpack_from('<H', b, off(aord) + 2 * i)[0]
        n = b[off(nr):b.index(b'\0', off(nr))].decode()
        res.append((funs[o], n))
    return sorted(res)


EX = {'ntdll.dll': exports(r'C:\Windows\SysWOW64\ntdll.dll'), 'win32u.dll': exports(r'C:\Windows\SysWOW64\win32u.dll'),
      'KERNELBASE.dll': exports(r'C:\Windows\SysWOW64\KernelBase.dll')}


def fn(mod, off):
    ex = EX.get(mod)
    if not ex:
        return f'{mod}+{off:x}'
    best = None
    for a, n in ex:
        if a <= off:
            best = n
        else:
            break
    return f'{mod}!{best}'


t0 = float((OUT / f'{name}_t0.txt').read_text()) * 1000
fps = collections.Counter(int(float(r['TimeInMs']) // 5000) for r in csv.DictReader(open(OUT / f'{name}_pm.csv', encoding='utf-8-sig')))
slow = {b for b, c in fps.items() if c / 5 < slow_th}; fast = {b for b, c in fps.items() if c / 5 >= fast_th}
acc = collections.defaultdict(collections.Counter); tot = collections.Counter()
for line in open(OUT / f'{name}_eip.tsv', encoding='utf-8'):
    parts = line.rstrip('\n').split('\t'); t, th, mod, off = parts[:4]; th = int(th)
    callers = parts[4] if len(parts) > 4 else ''
    if th not in tids:
        continue
    b = int((float(t) - t0) // 5000)
    lab = '느림' if b in slow else '빠름' if b in fast else None
    if not lab:
        continue
    tot[(th, lab)] += 1
    if mod in EX:   # 기다림이면 누가 불렀는지(스택에서 찾은 게임 EXE e… / 4K DLL d… 주소 첫 둘)
        acc[(th, lab)][fn(mod, int(off, 16)) + ('  <- ' + ','.join(callers.split(',')[:2]) if callers else '')] += 1
for k in sorted(acc):
    print(k, '표본', tot[k])
    for f, c in acc[k].most_common(6):
        print(f'   {100 * c / tot[k]:5.1f}%  {f}')
