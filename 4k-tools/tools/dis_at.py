"""모듈 파일의 RVA 앞뒤를 역어셈블하고, 부르는 import·참조하는 문자열을 이름으로 보여 준다.
python -X utf8 dis_at.py <파일> <rva(16진)> [앞바이트=0x60] [뒤바이트=0x20]"""
import struct, sys
import capstone

path, rva = sys.argv[1], int(sys.argv[2], 16)
before = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x60
after = int(sys.argv[4], 16) if len(sys.argv) > 4 else 0x20
b = open(path, 'rb').read()
pe = struct.unpack_from('<I', b, 0x3c)[0]; opt = pe + 24
base = struct.unpack_from('<I', b, opt + 28)[0]
nsec = struct.unpack_from('<H', b, pe + 6)[0]; so = opt + struct.unpack_from('<H', b, pe + 20)[0]
secs = [(b[so + i * 40:so + i * 40 + 8].rstrip(b'\0').decode(), *struct.unpack_from('<IIII', b, so + i * 40 + 8)) for i in range(nsec)]


def r2o(r):
    for n, vs, va, rs, raw in secs:
        if va <= r < va + max(vs, rs):
            return r - va + raw


# import 표: IAT 주소 → 이름
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
        imp[base + ft + 4 * i] = f'{dll}!{fn}'
        i += 1
    d += 20


def string_at(va):
    o = r2o(va - base) if va >= base else None
    if o is None or o >= len(b):
        return None
    s = b[o:o + 80]
    if s[:2].isascii() and b'\0' in s:
        t = s[:s.index(b'\0')]
        if len(t) >= 4 and all(32 <= c < 127 for c in t):
            return t.decode()
    w = b[o:o + 120]
    try:
        t = w.decode('utf-16-le').split('\0')[0]
        if len(t) >= 4 and t.isprintable():
            return 'L"' + t + '"'
    except Exception:
        pass
    return None


md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
start = rva - before
code = b[r2o(start):r2o(start) + before + after]
for ins in md.disasm(code, base + start):
    note = ''
    for tok in ins.op_str.replace('[', ' ').replace(']', ' ').replace(',', ' ').split():
        if tok.startswith('0x'):
            v = int(tok, 16)
            if v in imp:
                note += ' ; ' + imp[v]
            s = string_at(v)
            if s:
                note += ' ; ' + repr(s)
    mark = '>>' if ins.address - base == rva else '  '
    print(f'{mark} {ins.address - base:06x}  {ins.mnemonic:6} {ins.op_str}{note}')
