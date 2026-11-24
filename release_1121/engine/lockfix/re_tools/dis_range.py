"""엔진 EXE 를 VA 범위로 역어셈블(가져오기 이름·문자열 주석). 읽기만.
python -X utf8 dis_range.py <exe> <시작 va> <끝 va> [grep 낱말...]
grep 낱말을 주면 그 낱말이 든 줄만(앞뒤 문맥 없이)"""
import struct, sys
import capstone

path, a, z = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
words = sys.argv[4:]
b = open(path, 'rb').read()
pe = struct.unpack_from('<I', b, 0x3c)[0]; opt = pe + 24
base = struct.unpack_from('<I', b, opt + 28)[0]
nsec = struct.unpack_from('<H', b, pe + 6)[0]; so = opt + struct.unpack_from('<H', b, pe + 20)[0]
secs = [(b[so + i * 40:so + i * 40 + 8].rstrip(b'\0').decode(), *struct.unpack_from('<IIII', b, so + i * 40 + 8)) for i in range(nsec)]


def r2o(r):
    for n, vs, va, rs, raw in secs:
        if va <= r < va + max(vs, rs):
            return r - va + raw


imp = {}
irva = struct.unpack_from('<I', b, opt + 104)[0]
d = r2o(irva)
while d and struct.unpack_from('<I', b, d + 12)[0]:
    oft, _, _, nm, ft = struct.unpack_from('<IIIII', b, d)
    dll = b[r2o(nm):b.index(b'\0', r2o(nm))].decode()
    i = 0
    while True:
        th = struct.unpack_from('<I', b, r2o(oft or ft) + 4 * i)[0]
        if not th:
            break
        fn = f'#{th & 0xffff}' if th & 0x80000000 else b[r2o(th) + 2:b.index(b'\0', r2o(th) + 2)].decode()
        imp[base + ft + 4 * i] = fn
        i += 1
    d += 20


def cstr(va):
    o = r2o(va - base)
    if o is None or o >= len(b):
        return None
    e = b.find(b'\0', o, o + 80)
    s = b[o:e] if e > o else b''
    if len(s) >= 3:
        for enc in ('cp932', 'cp949'):
            try:
                t = s.decode(enc)
                if all(ch.isprintable() for ch in t):
                    return t
            except UnicodeDecodeError:
                pass
    return None


md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
o = r2o(a - base)
import re
for x in md.disasm(b[o:o + (z - a)], a):
    s = f'{x.address:08x}  {x.mnemonic:6} {x.op_str}'
    note = []
    for m in re.finditer(r'0x([0-9a-f]{6,8})', x.op_str):
        v = int(m.group(1), 16)
        if v in imp:
            note.append(imp[v])
        elif base + 0x111000 <= v < base + 0x22b000:
            t = cstr(v)
            if t:
                note.append(repr(t))
    if note:
        s += '   ; ' + ' '.join(note)
    if not words or any(w in s for w in words):
        print(s)
