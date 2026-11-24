"""단계 표지 「phase」 덧씌우기 묶음 cg.fix.npa — sys\\phase\\フェイズ.png 하나만(make_cgko.py 꼴: 폴더 항목 + 파일, 압축 없음, 암호 있음).
엔진은 폴더의 .npa 를 이름순으로 다 읽고 같은 이름은 먼저 읽은 것이 이긴다 → cg.fix.npa 가 cg.kor.npa·cg.npa 보다 앞.
대본(function_lc_toho.nss)은 세이브에 담기므로 건드리지 않고, 같은 경로의 그림만 바꾼다(옛 세이브에도 바로 보임).
python -I -X utf8 make_cgfix.py <출력.npa>
"""
import sys, struct, hashlib
from pathlib import Path
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from npa_assets import NPA, KEYS
INV = bytes(KEYS.index(x) for x in range(256))
HERE = Path(__file__).resolve().parent
TPL = NPA(r'Y:\GAME\Guilty-Crown-Lost-Christmas_Win_EN_Full-rip\GUILTY CROWN LOST XMAS\cg1.npa')
out = Path(sys.argv[1])
BS = chr(92)
files = {('sys' + BS + 'phase' + BS + 'フェイズ.png').encode('cp932'): (HERE / 'phase_4x.png').read_bytes()}

order, folder_id, seen = [], {b'': 0}, set()
for nb in sorted(files):
    parts = nb.decode('cp932').split(BS)
    for i in range(1, len(parts)):
        d = BS.join(parts[:i]).encode('cp932')
        if d not in seen:
            seen.add(d); folder_id[d] = len(folder_id); order.append(('d', d))
    order.append(('f', nb))

prod = TPL.k1 * TPL.k2
table, payload = bytearray(), bytearray()
for idx, (kind, nb) in enumerate(order):
    key = -sum(prod >> s for s in (24, 16, 8, 0)) - sum(idx >> s for s in (24, 16, 8, 0))
    raw_name = bytes((b - 0xfc * j - key) & 255 for j, b in enumerate(nb))
    u = nb.decode('cp932'); parent = u.rsplit(BS, 1)[0].encode('cp932') if BS in u else b''
    if kind == 'd':
        meta = struct.pack('<BIIII', 1, folder_id[parent], len(payload), 0, 0)
    else:
        data = files[nb]; size = len(data)
        raw = bytearray(data)
        k = (((0x20101118 - sum(nb)) * len(nb) + prod) * size) & 255
        for j in range(min(len(raw), 0x1000 + len(nb))):
            raw[j] = INV[(raw[j] + k + j) & 255]
        meta = struct.pack('<BIIII', 2, folder_id[parent], len(payload), len(raw), size)
        payload += raw
    table += struct.pack('<I', len(raw_name)) + raw_name + meta
head = bytearray(TPL.header)
nd = sum(1 for k, _ in order if k == 'd'); nf = len(order) - nd
struct.pack_into('<ii??III8xI', head, 7, TPL.k1, TPL.k2, False, True, len(order), nd, nf, len(table))
out.write_bytes(bytes(head) + bytes(table) + bytes(payload))

chk = NPA(out)
got = {bytes.fromhex(e['name_hex']): chk.read(e) for e in chk.entries if e['type'] == 2}
assert got == files, 'read-back mismatch'
print(out.name, out.stat().st_size, 'bytes', 'dirs', nd, 'files', nf, 'sha256', hashlib.sha256(out.read_bytes()).hexdigest()[:8])
