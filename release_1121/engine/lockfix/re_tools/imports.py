"""EXE 가 가져오는 DLL 과 소리·스레드·대기 관련 함수의 IAT 주소를 적는다(읽기만).  python -X utf8 imports.py <exe>"""
import struct, sys
b = open(sys.argv[1], 'rb').read()
pe = struct.unpack_from('<I', b, 0x3c)[0]; opt = pe + 24
base = struct.unpack_from('<I', b, opt + 28)[0]
nsec = struct.unpack_from('<H', b, pe + 6)[0]; so = opt + struct.unpack_from('<H', b, pe + 20)[0]
secs = [(b[so + i * 40:so + i * 40 + 8].rstrip(b'\0').decode(), *struct.unpack_from('<IIII', b, so + i * 40 + 8)) for i in range(nsec)]


def r2o(r):
    for n, vs, va, rs, raw in secs:
        if va <= r < va + max(vs, rs):
            return r - va + raw


print('sections', [(s[0], hex(base + s[2]), hex(s[1])) for s in secs])
irva = struct.unpack_from('<I', b, opt + 104)[0]
d = r2o(irva)
want = ('Sound', 'wave', 'mci', 'time', 'Thread', 'Event', 'Mutex', 'WaitFor', 'Sleep', 'CoCreate', 'DirectSound', 'ov_', 'ogg')
while d and struct.unpack_from('<I', b, d + 12)[0]:
    oft, _, _, nm, ft = struct.unpack_from('<IIIII', b, d)
    dll = b[r2o(nm):b.index(b'\0', r2o(nm))].decode()
    names = []
    i = 0
    while True:
        th = struct.unpack_from('<I', b, r2o(oft or ft) + 4 * i)[0]
        if not th:
            break
        fn = f'#{th & 0xffff}' if th & 0x80000000 else b[r2o(th) + 2:b.index(b'\0', r2o(th) + 2)].decode()
        names.append((base + ft + 4 * i, fn))
        i += 1
    keep = [f'{a:06x}:{n}' for a, n in names if any(w.lower() in n.lower() for w in want)]
    print(f'{dll} ({len(names)})', ' '.join(keep) if dll.lower() not in ('kernel32.dll', 'user32.dll') or True else '')
    d += 20
