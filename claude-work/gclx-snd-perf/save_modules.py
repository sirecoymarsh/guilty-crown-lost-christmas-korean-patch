"""사용자 세이브 script.npf 안의 대본 모듈(이름·크기)과 function.nss 판(새 기능 표시)을 읽기만 한다."""
import sys, os, re, struct
sys.path.insert(0, r'P:\AI\Codex\projects\gclx-song-20261123\awakening')
sys.path.insert(0, r'P:\AI\Codex\projects\gclx-song-20261123\tools')
from save_lyrics import decode_program

D = sys.argv[1]
BS = b'\x5c'
REC = re.compile(b'nss' + re.escape(BS) + rb'([^\x00]{1,60}?\.nss)\x00\x00\x00\x00(....)', re.S | re.I)
FEATS = ['KrJBegin', 'KrBoxAdd', 'krKeyBar', 'KrLyPlay', '$KR_TALL', 'KrPassText', 'KrJSwapTick']
for slot in sys.argv[2:]:
    p = os.path.join(D, slot, 'script.npf')
    if not os.path.exists(p):
        continue
    plain, key = decode_program(open(p, 'rb').read())
    mods = []
    for m in REC.finditer(plain):
        n = struct.unpack('<I', m.group(2))[0]
        if 0 < n < 8_000_000:
            mods.append((m.group(1).decode('cp932', 'replace'), n, plain[m.end():m.end() + n]))
    fns = [src for nm, n, src in mods if nm.lower() == 'function.nss']
    names = [nm for nm, n, src in mods]
    print(slot, 'modules', len(mods), names[:12], '...')
    for s in fns:
        print('    function.nss', len(s), sorted(w for w in FEATS if w.encode() in s))
    for nm, n, src in mods:
        if nm.lower().startswith('lx'):
            print('    scene', nm, n, 'mtext' if b'[mtext' in src else '-', 'KrAltIJ' if b'KrAltIJ' in src else '-')
