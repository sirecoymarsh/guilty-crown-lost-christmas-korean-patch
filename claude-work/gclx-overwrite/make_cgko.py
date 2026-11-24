"""한국어판 cg.npa 에서 원본과 다른 그림(바뀐 160 + 더한 385)만 뽑아 따로 묶음(.npa)을 만든다.
원본 cg.npa 는 건드리지 않고 이 묶음을 게임 폴더에 더하면 되게 하려는 것(덮어쓰기 꼴 배포).
묶음 꼴은 cg1.npa 를 본뜬다: 폴더 항목(형 1, fid = 부모 폴더 번호) 뒤에 그 안 파일(형 2, fid = 그 폴더 번호), 압축 없음, 암호 있음.
python -I -X utf8 make_cgko.py <출력.npa>
"""
import sys, json, struct, hashlib
from pathlib import Path
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from npa_assets import NPA, KEYS
INV = bytes(KEYS.index(x) for x in range(256))
W = Path(r'Y:\AI\claude-work\gclx-overwrite')
KR = NPA(r'P:\AI\gclx-codexrun\game\cg.npa')
TPL = NPA(r'Y:\GAME\Guilty-Crown-Lost-Christmas_Win_EN_Full-rip\GUILTY CROWN LOST XMAS\cg1.npa')
out = Path(sys.argv[1])

refs = json.loads((W / 'refs.json').read_text('utf-8'))
want = {r['hex'] for r in refs}
files = {}                                   # 이름 바이트(cp932, 역슬래시) -> 내용
for e in KR.entries:
    if e['type'] == 2 and e['name_hex'] in want:
        files[bytes.fromhex(e['name_hex'])] = KR.read(e)
assert len(files) == len(want) == 545, len(files)

# 항목 차례: 이름순으로 훑으며 처음 보는 폴더를 그 안 파일보다 먼저
order, folder_id, seen = [], {b'': 0}, set()
for nb in sorted(files):
    parts = nb.decode('cp932').split('\\')     # cp932 둘째 바이트가 0x5c 인 글자(表 등)가 있어 바이트로 자르면 안 된다
    for i in range(1, len(parts)):
        d = '\\'.join(parts[:i]).encode('cp932')
        if d not in seen:
            seen.add(d); folder_id[d] = len(folder_id); order.append(('d', d))
    order.append(('f', nb))

prod = TPL.k1 * TPL.k2
table, payload = bytearray(), bytearray()
for idx, (kind, nb) in enumerate(order):
    key = -sum(prod >> s for s in (24, 16, 8, 0)) - sum(idx >> s for s in (24, 16, 8, 0))
    raw_name = bytes((b - 0xfc * j - key) & 255 for j, b in enumerate(nb))
    u = nb.decode('cp932'); parent = u.rsplit('\\', 1)[0].encode('cp932') if '\\' in u else b''
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
