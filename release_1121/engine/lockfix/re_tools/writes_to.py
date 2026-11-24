"""엔진 EXE .text 에서 전역 주소에 값을 쓰는 명령(mov [addr], imm / mov [addr], reg)과 그 주소를 읽는 명령을 갈라 적는다. 읽기만.
python -X utf8 writes_to.py <exe> <va(16진)> [w|r|all]"""
import struct, sys
import capstone

path, target = sys.argv[1], int(sys.argv[2], 16)
mode = sys.argv[3] if len(sys.argv) > 3 else 'w'
b = open(path, 'rb').read()
pe = struct.unpack_from('<I', b, 0x3c)[0]; opt = pe + 24
base = struct.unpack_from('<I', b, opt + 28)[0]
nsec = struct.unpack_from('<H', b, pe + 6)[0]; so = opt + struct.unpack_from('<H', b, pe + 20)[0]
secs = [(b[so + i * 40:so + i * 40 + 8].rstrip(b'\0').decode(), *struct.unpack_from('<IIII', b, so + i * 40 + 8)) for i in range(nsec)]
_, tvs, tva, trs, traw = [s for s in secs if s[0] == '.text'][0]
tb = b[traw:traw + trs]; tbase = base + tva
pat = struct.pack('<I', target)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
k = 0; seen = set()
while True:
    k = tb.find(pat, k)
    if k < 0:
        break
    # 명령 시작을 뒤로 1~6바이트 더듬어 맞는 길이를 찾는다
    for back in range(1, 7):
        s = k - back
        if s < 0:
            continue
        ins = next(md.disasm(tb[s:s + 16], tbase + s), None)
        if ins is None or ins.address + ins.size < tbase + k + 4 or ins.address + ins.size > tbase + k + 8:
            continue
        if f'[0x{target:x}]' not in ins.op_str:   # 메모리 피연산자일 때만(즉치값으로 잘못 읽힌 풀이는 버림)
            continue
        ops = ins.op_str.split(',')
        is_write = ins.mnemonic in ('mov', 'and', 'or', 'add', 'sub', 'inc', 'dec', 'xor', 'xchg') and f'[0x{target:x}]' in ops[0]
        if ins.address in seen:
            break
        seen.add(ins.address)
        if mode == 'all' or (mode == 'w' and is_write) or (mode == 'r' and not is_write):
            print(f'{ins.address:08x}  {"W" if is_write else "r"}  {ins.mnemonic} {ins.op_str}')
        break
    k += 1
