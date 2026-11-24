"""VA 범위 안의 함수 시작(int3 채움 뒤 첫 명령)을 어림으로 나열하고, 함수마다 길이·부르는 자리 수·안에서 쓰는 가져오기/문자열을 한 줄로 적는다. 읽기만.
python -X utf8 funcs_in.py <exe> <시작 va> <끝 va> [--calls]   (--calls: 안에서 부르는 엔진 함수 주소도)"""
import struct, sys
import capstone

path, a, z = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
show_calls = '--calls' in sys.argv
b = open(path, 'rb').read()
pe = struct.unpack_from('<I', b, 0x3c)[0]; opt = pe + 24
base = struct.unpack_from('<I', b, opt + 28)[0]
nsec = struct.unpack_from('<H', b, pe + 6)[0]; so = opt + struct.unpack_from('<H', b, pe + 20)[0]
secs = [(b[so + i * 40:so + i * 40 + 8].rstrip(b'\0').decode(), *struct.unpack_from('<IIII', b, so + i * 40 + 8)) for i in range(nsec)]


def v2o(v):
    r = v - base
    for n, vs, va, rs, raw in secs:
        if va <= r < va + max(vs, rs):
            return raw + r - va
    return None


# 가져오기 이름
imp = {}
idir = struct.unpack_from('<I', b, opt + 104)[0]
o = v2o(base + idir)
while o is not None:
    oft, _, _, nrva, ft = struct.unpack_from('<IIIII', b, o)
    if not nrva:
        break
    t = v2o(base + (oft or ft)); i = 0
    while True:
        v = struct.unpack_from('<I', b, t + i * 4)[0]
        if not v:
            break
        if not v & 0x80000000:
            no = v2o(base + v) + 2
            imp[base + ft + i * 4] = b[no:b.index(b'\0', no)].decode('latin1')
        else:
            dn = v2o(base + nrva)
            imp[base + ft + i * 4] = b[dn:b.index(b'\0', dn)].decode('latin1') + '#%d' % (v & 0xffff)
        i += 1
    o += 20

text = [s for s in secs if s[0] == '.text'][0]
_, tvs, tva, trs, traw = text
tb = b[traw:traw + trs]; tbase = base + tva


def string_at(v):
    o = v2o(v)
    if o is None or o >= len(b):
        return None
    e = o
    while e < len(b) and 32 <= b[e] < 127 and e - o < 48:
        e += 1
    if e - o >= 4 and e < len(b) and b[e] == 0:
        return b[o:e].decode('latin1')
    return None


# 함수 시작: 범위 안에서 int3(0xCC) 연속 뒤 첫 바이트, 그리고 범위 첫 주소
starts = []
i = a - tbase
end = z - tbase
if tb[i - 1] == 0xcc or True:
    starts.append(a)
while i < end:
    if tb[i] == 0xcc:
        j = i
        while j < end and tb[j] == 0xcc:
            j += 1
        if j < end and j - i >= 1:
            starts.append(tbase + j)
        i = j
    else:
        i += 1
starts = sorted(set(starts))
# 호출 수: .text 전체에서 E8 상대 호출 대상 세기
calls = {}
k = 0
while True:
    k = tb.find(b'\xe8', k)
    if k < 0 or k + 5 > len(tb):
        break
    t = tbase + k + 5 + struct.unpack_from('<i', tb, k + 1)[0]
    calls[t] = calls.get(t, 0) + 1
    k += 1
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for n, s in enumerate(starts):
    e = starts[n + 1] if n + 1 < len(starts) else z
    code = tb[s - tbase:e - tbase]
    notes = []; inner = []
    last = s
    for ins in md.disasm(code, s):
        last = ins.address + ins.size
        op = ins.op_str
        if ins.mnemonic == 'call' and op.startswith('0x'):
            inner.append(op[2:])
        for tok in op.replace('[', ' ').replace(']', ' ').replace(',', ' ').split():
            if tok.startswith('0x'):
                try:
                    v = int(tok, 16)
                except ValueError:
                    continue
                if v in imp and imp[v] not in notes:
                    notes.append(imp[v])
                elif 0x511000 <= v < 0x534000:
                    st = string_at(v)
                    if st and repr(st) not in notes:
                        notes.append(repr(st))
    line = f'{s:08x} len {last - s:5d} callers {calls.get(s, 0):3d}  ' + ' '.join(notes[:14])
    if show_calls and inner:
        seen = []
        for c in inner:
            if c not in seen:
                seen.append(c)
        line += '  | calls ' + ' '.join(seen[:24])
    print(line)
