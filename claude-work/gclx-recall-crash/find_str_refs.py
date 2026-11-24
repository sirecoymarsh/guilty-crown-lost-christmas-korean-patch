import struct, sys, capstone
path = sys.argv[1]; needle = sys.argv[2].encode()
b = open(path, 'rb').read()
pe = struct.unpack_from('<I', b, 0x3c)[0]; opt = pe + 24
base = struct.unpack_from('<I', b, opt + 28)[0]
nsec = struct.unpack_from('<H', b, pe + 6)[0]; so = opt + struct.unpack_from('<H', b, pe + 20)[0]
secs = []
for i in range(nsec):
    nm = b[so + i * 40:so + i * 40 + 8].rstrip(b'\0')
    vs, va, rs, raw = struct.unpack_from('<IIII', b, so + i * 40 + 8)
    secs.append((nm, vs, va, rs, raw))
def o2va(o):
    for nm, vs, va, rs, raw in secs:
        if raw <= o < raw + rs: return base + va + o - raw
addrs = []
i = -1
while True:
    i = b.find(needle + b'\0', i + 1)
    if i < 0: break
    if i > 0 and b[i-1] != 0: continue
    addrs.append(o2va(i))
print('string at', [hex(a) for a in addrs])
for a in addrs:
    pat = struct.pack('<I', a)
    j = -1
    while True:
        j = b.find(pat, j + 1)
        if j < 0: break
        print('  ref at', hex(o2va(j)), 'file', hex(j))
