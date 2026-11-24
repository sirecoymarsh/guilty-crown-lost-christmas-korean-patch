"""EXE 에서 ASCII 문자열의 VA 와 그 주소를 참조하는 자리를 찾는다(읽기만).  python -X utf8 find_str.py <exe> <문자열> [...]"""
import struct, sys
path = sys.argv[1]
b = open(path, 'rb').read()
pe = struct.unpack_from('<I', b, 0x3c)[0]; opt = pe + 24
base = struct.unpack_from('<I', b, opt + 28)[0]
nsec = struct.unpack_from('<H', b, pe + 6)[0]; so = opt + struct.unpack_from('<H', b, pe + 20)[0]
secs = [(b[so + i * 40:so + i * 40 + 8].rstrip(b'\0').decode(), *struct.unpack_from('<IIII', b, so + i * 40 + 8)) for i in range(nsec)]


def o2va(o):
    for n, vs, va, rs, raw in secs:
        if raw <= o < raw + rs:
            return base + va + o - raw


for s in sys.argv[2:]:
    pat = s.encode('ascii') + b'\0'
    p = 0
    while True:
        p = b.find(pat, p)
        if p < 0:
            break
        if p == 0 or b[p - 1] == 0:
            va = o2va(p)
            refs = []
            q = 0
            k = struct.pack('<I', va)
            while True:
                q = b.find(k, q)
                if q < 0:
                    break
                refs.append(o2va(q)); q += 1
            print(f'{s!r} at {va:08x} refs {[hex(r) for r in refs if r]}')
        p += 1
