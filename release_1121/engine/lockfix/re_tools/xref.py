"""엔진 EXE .text 에서 주소(가져오기 칸·함수·전역)를 참조하는 자리를 찾는다. 읽기만.
python -X utf8 xref.py <exe> <va(16진)> [call|any]
call = E8 상대 호출만, any = 4바이트 절대 주소가 나오는 모든 자리(+ E8 호출)"""
import struct, sys

path, target = sys.argv[1], int(sys.argv[2], 16)
mode = sys.argv[3] if len(sys.argv) > 3 else 'any'
b = open(path, 'rb').read()
pe = struct.unpack_from('<I', b, 0x3c)[0]; opt = pe + 24
base = struct.unpack_from('<I', b, opt + 28)[0]
nsec = struct.unpack_from('<H', b, pe + 6)[0]; so = opt + struct.unpack_from('<H', b, pe + 20)[0]
secs = [(b[so + i * 40:so + i * 40 + 8].rstrip(b'\0').decode(), *struct.unpack_from('<IIII', b, so + i * 40 + 8)) for i in range(nsec)]
out = []
for n, vs, va, rs, raw in secs:
    data = b[raw:raw + min(vs, rs)]
    if n == '.text':
        p = 0
        while True:
            p = data.find(b'\xe8', p)
            if p < 0:
                break
            if p + 5 <= len(data):
                rel = struct.unpack_from('<i', data, p + 1)[0]
                if base + va + p + 5 + rel == target:
                    out.append((base + va + p, 'call'))
            p += 1
        p = 0
        while True:
            p = data.find(b'\xe9', p)
            if p < 0:
                break
            if p + 5 <= len(data):
                rel = struct.unpack_from('<i', data, p + 1)[0]
                if base + va + p + 5 + rel == target:
                    out.append((base + va + p, 'jmp'))
            p += 1
    if mode == 'any':
        pat = struct.pack('<I', target)
        p = 0
        while True:
            p = data.find(pat, p)
            if p < 0:
                break
            out.append((base + va + p, f'abs in {n}'))
            p += 1
for a, k in sorted(out):
    print(f'{a:08x} {k}')
print(len(out), 'refs')
