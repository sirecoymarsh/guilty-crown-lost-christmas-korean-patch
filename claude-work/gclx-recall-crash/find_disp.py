import struct, sys, capstone
path = sys.argv[1]; disps = [int(x, 16) for x in sys.argv[2].split(',')]
b = open(path, 'rb').read()
pe = struct.unpack_from('<I', b, 0x3c)[0]; opt = pe + 24
base = struct.unpack_from('<I', b, opt + 28)[0]
nsec = struct.unpack_from('<H', b, pe + 6)[0]; so = opt + struct.unpack_from('<H', b, pe + 20)[0]
for i in range(nsec):
    nm = b[so + i * 40:so + i * 40 + 8].rstrip(b'\0')
    vs, va, rs, raw = struct.unpack_from('<IIII', b, so + i * 40 + 8)
    if nm == b'.text':
        code = b[raw:raw + rs]; cva = base + va
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True
off = 0
while off < len(code):
    hit = False
    for ins in md.disasm(code[off:off + 0x10000], cva + off):
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.disp in disps:
                print(hex(ins.address), ins.mnemonic, ins.op_str)
        last = ins.address + ins.size
    nxt = last - cva
    off = nxt if nxt > off else off + 1
