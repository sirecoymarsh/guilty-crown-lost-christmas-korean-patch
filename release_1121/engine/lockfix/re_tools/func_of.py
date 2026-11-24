"""주소가 든 함수의 시작(앞쪽 int3 채움 뒤 첫 명령)을 어림잡고, 그 함수를 부르는 자리(E8/E9)와 표에 적힌 자리(절대 주소)를 찾는다. 읽기만.
python -X utf8 func_of.py <exe> <va> [...]"""
import struct, sys

path = sys.argv[1]
b = open(path, 'rb').read()
pe = struct.unpack_from('<I', b, 0x3c)[0]; opt = pe + 24
base = struct.unpack_from('<I', b, opt + 28)[0]
nsec = struct.unpack_from('<H', b, pe + 6)[0]; so = opt + struct.unpack_from('<H', b, pe + 20)[0]
secs = [(b[so + i * 40:so + i * 40 + 8].rstrip(b'\0').decode(), *struct.unpack_from('<IIII', b, so + i * 40 + 8)) for i in range(nsec)]
text = [s for s in secs if s[0] == '.text'][0]
_, vs, va, rs, raw = text
code = b[raw:raw + min(vs, rs)]
tb = base + va


def start_of(addr):
    p = addr - tb
    while p > 0:
        # 함수 사이는 0xCC 채움(2개 이상) 또는 ret 뒤 채움
        if code[p - 1] == 0xCC and code[p] != 0xCC:
            return tb + p
        p -= 1
    return None


def refs(target):
    out = []
    for op, name in ((0xE8, 'call'), (0xE9, 'jmp')):
        p = 0
        while True:
            p = code.find(bytes([op]), p)
            if p < 0:
                break
            if p + 5 <= len(code) and tb + p + 5 + struct.unpack_from('<i', code, p + 1)[0] == target:
                out.append((tb + p, name))
            p += 1
    pat = struct.pack('<I', target)
    for n, vs_, va_, rs_, raw_ in secs:
        data = b[raw_:raw_ + min(vs_, rs_)]
        p = 0
        while True:
            p = data.find(pat, p)
            if p < 0:
                break
            out.append((base + va_ + p, 'abs:' + n))
            p += 1
    return sorted(out)


for a in sys.argv[2:]:
    addr = int(a, 16)
    s = start_of(addr)
    print(f'{addr:08x} -> func {s:08x}' if s else f'{addr:08x} -> ?')
    if s:
        for r, k in refs(s):
            print(f'    {r:08x} {k}   (in func {start_of(r):08x})' if k in ('call', 'jmp') else f'    {r:08x} {k}')
