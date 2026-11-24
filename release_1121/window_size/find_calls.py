"""게임 실행 파일에서 창·마우스 API 를 부르는 곳(call dword ptr [IAT])을 찾아 앞뒤를 디스어셈블한다.
python -I -X utf8 find_calls.py"""
import struct, capstone
p = r'P:\AI\gclx-codexrun\game\GUILTY CROWN LOST XMAS.exe'
b = open(p, 'rb').read()
BASE, TEXT_RVA, TEXT_RAW, TEXT_SIZE = 0x400000, 0x1000, 0x400, 0x10fe00
SLOTS = {0x511278: 'GetClientRect', 0x511288: 'GetWindowRect', 0x5112b0: 'SetWindowLongA', 0x5112b4: 'CreateWindowExA',
         0x5112bc: 'SetWindowPos', 0x5112c0: 'AdjustWindowRect', 0x511314: 'SetCursorPos', 0x511318: 'GetCursorPos', 0x511304: 'ShowWindow'}
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for slot, name in SLOTS.items():
    pat = b'\xff\x15' + struct.pack('<I', slot)
    i = 0; hits = []
    while True:
        i = text.find(pat, i)
        if i < 0: break
        hits.append(BASE + TEXT_RVA + i); i += 6
    print(f'== {name} [{hex(slot)}] calls: {[hex(h) for h in hits]}')
    for h in hits[:4]:
        start = h - 0x50; o = start - BASE - TEXT_RVA
        code = text[o:o + 0x60]
        for ins in md.disasm(code, start):
            if ins.address >= h - 0x40:
                print(f'   {ins.address:08x} {ins.mnemonic} {ins.op_str}')
            if ins.address > h: break
        print('   ---')
