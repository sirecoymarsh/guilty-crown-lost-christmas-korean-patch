"""EXE 가져오기 표에서 DSOUND.dll 항목(이름 또는 순번)과 IAT 칸 주소를 적는다(읽기만). python -X utf8 iat_dsound.py <exe>"""
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


imp_rva = struct.unpack_from('<I', b, opt + 96 + 8)[0]
o = r2o(imp_rva)
while True:
    oft, ts, fc, name_rva, ft = struct.unpack_from('<IIIII', b, o)
    if not name_rva:
        break
    dll = b[r2o(name_rva):].split(b'\0')[0].decode()
    if dll.lower() in ('dsound.dll', 'ddraw.dll'):
        t = r2o(oft or ft); k = 0
        while True:
            v = struct.unpack_from('<I', b, t + 4 * k)[0]
            if not v:
                break
            what = f'ordinal {v & 0xffff}' if v & 0x80000000 else b[r2o(v) + 2:].split(b'\0')[0].decode()
            print(dll, what, 'IAT', hex(base + ft + 4 * k))
            k += 1
    o += 20
