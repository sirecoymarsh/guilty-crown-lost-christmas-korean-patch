"""엔진 EXE 의 .text 에서 1000(0x3E8)·2000(0x7D0) 상수를 쓰는 자리를 찾아, 뒤따르는 call(가져오기 이름 포함)과 함께 보여 준다. 읽기만.
python -X utf8 scan_1000.py <exe>"""
import struct, sys
import capstone

path = sys.argv[1]
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
        imp[base + ft + 4 * i] = f'{dll}!{fn}'
        i += 1
    d += 20

text = [s for s in secs if s[0] == '.text'][0]
_, vs, va, rs, raw = text
code = b[raw:raw + min(vs, rs)]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False
want = {0x3E8: '1000', 0x7D0: '2000'}
hits = []
for val in want:
    pat = struct.pack('<I', val)
    p = 0
    while True:
        p = code.find(pat, p)
        if p < 0:
            break
        hits.append((p, val)); p += 1
hits.sort()
print('sections', [(s[0], hex(s[2]), hex(s[1])) for s in secs], 'hits', len(hits))
for p, val in hits:
    # 상수 앞 1~6바이트에서 명령이 시작한다고 보고, 그 명령부터 0x30 바이트를 푼다
    shown = False
    for back in (1, 2, 3, 4, 5, 6, 7):
        st = p - back
        ins = list(md.disasm(code[st:st + 0x40], base + va + st))
        if not ins:
            continue
        first = ins[0]
        if first.size != back + 4 and not (first.size > back and first.size >= back + 4):
            continue
        if hex(val) not in first.op_str:
            continue
        line = []
        for x in ins[:9]:
            s = f'{x.mnemonic} {x.op_str}'
            if x.mnemonic == 'call':
                if x.op_str.startswith('dword ptr [0x'):
                    a = int(x.op_str[11:-1], 16)
                    s += f' ; {imp.get(a, "?")}'
            line.append(s)
            if x.mnemonic in ('ret', 'jmp'):
                break
        print(f'{base + va + st:08x} [{want[val]}]  ' + ' | '.join(line))
        shown = True
        break
    if not shown:
        print(f'{base + va + p:08x} [{want[val]}]  (명령 경계 못 찾음)')
