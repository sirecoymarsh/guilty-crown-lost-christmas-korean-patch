"""EXE .text 에서 주어진 주소를 읽거나 쓰는 명령을 모두 찾는다(쓰기만 따로 표시). python -X utf8 xref.py <exe> <주소16진,…>"""
import struct, sys
import capstone

path = sys.argv[1]
targets = [int(x, 16) for x in sys.argv[2].split(',')]
b = open(path, 'rb').read()
pe = struct.unpack_from('<I', b, 0x3c)[0]; opt = pe + 24
base = struct.unpack_from('<I', b, opt + 28)[0]
nsec = struct.unpack_from('<H', b, pe + 6)[0]; so = opt + struct.unpack_from('<H', b, pe + 20)[0]
text = None
for i in range(nsec):
    nm = b[so + i * 40:so + i * 40 + 8].rstrip(b'\0')
    vs, va, rs, raw = struct.unpack_from('<IIII', b, so + i * 40 + 8)
    if nm == b'.text':
        text = (va, raw, rs)
va, raw, rs = text
code = b[raw:raw + rs]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = False
hits = {t: [] for t in targets}
# 선형 역어셈블은 자료 섞임에서 어긋나므로, 대상 주소 바이트가 나오는 자리 앞쪽 몇 바이트부터 해석해 그 명령을 찾는다
for t in targets:
    pat = struct.pack('<I', t)
    i = code.find(pat)
    while i >= 0:
        for back in range(1, 9):
            s = i - back
            if s < 0:
                continue
            ins = next(md.disasm(code[s:s + 16], base + va + s), None)
            if ins and ins.address + ins.size >= base + va + i + 4 and ins.address <= base + va + i and f'[{hex(t)}' in ins.op_str:
                txt = f'{ins.mnemonic} {ins.op_str}'
                write = txt.split(',')[0].count(hex(t)) > 0 and ins.mnemonic not in ('cmp', 'test', 'push', 'fld', 'fild', 'fidivr', 'movzx', 'movsx')
                hits[t].append((ins.address - base, txt, write))
                break
        i = code.find(pat, i + 1)
for t in targets:
    print(f'== 0x{t:x}: {len(hits[t])} 곳')
    for a, txt, w in hits[t]:
        print(f'   {"쓰기" if w else "읽기"}  {a:06x}  {txt}')
