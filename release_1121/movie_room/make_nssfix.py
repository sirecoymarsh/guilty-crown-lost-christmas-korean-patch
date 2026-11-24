"""영상 감상 덧씌우기 묶음 nss.fix.npa (11-24 오후, 1장 전투 영상 칸 추가).
엔진은 폴더의 .npa 를 이름순으로 다 읽고 같은 이름은 먼저 읽은 것이 이긴다 → nss.fix.npa 가 nss.npa 보다 앞(cg.fix.npa 와 같은 방식).
nss.npa 는 그대로 둔다: 코덱스 세이브 호환(story_resume.inc)이 nss.npa 의 SHA-256 을 확인하므로(sameFile(..\\nss.npa)),
nss.npa 를 바꾸면 코덱스가 krresume.npa·story-resume.n2r 를 다시 만들어야 한다. 영상 감상은 타이틀 화면이라 세이브와 무관.
배포 때 한 번에 nss.npa 로 합치고(그때 코덱스 자료도 다시) 이 파일은 뺀다.
python -I -X utf8 make_nssfix.py <새 nss_play.npa> <출력 nss.fix.npa> [<기준 nss.npa>]
기준(놀이 사본에 깔린 nss.npa, 코덱스 세이브 호환이 묶인 판)을 주면 그와 다른·새 항목을 모두 담는다(11-24 오후: 사운드 문안·연출 다시 보기까지).
"""
import sys, struct, hashlib
from pathlib import Path
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_assets import NPA, KEYS
import patch_seek as ps
INV = bytes(KEYS.index(x) for x in range(256))
TPL = NPA(r'Y:\GAME\Guilty-Crown-Lost-Christmas_Win_EN_Full-rip\GUILTY CROWN LOST XMAS\cg1.npa')
NAMES = ['kr_movie.nss', 'kr_mov_bg2.png', 'kr_mov_cur.png'] + [f'kr_mth{k:02d}.jpg' for k in range(1, 6)]

src = NPA(Path(sys.argv[1])); ent = {e['name']: e for e in src.entries}
out = Path(sys.argv[2])
if len(sys.argv) > 3:
    base = NPA(Path(sys.argv[3])); bent = {e['name']: e for e in base.entries if e['type'] == 2}
    NAMES = [n for n, e in ent.items() if e['type'] == 2 and (n not in bent or ps.rd(base, bent[n]) != ps.rd(src, e))]
    print('entries', len(NAMES), sorted(NAMES)[:12], '...')
files = {n.encode('cp932'): ps.rd(src, ent[n]) for n in NAMES}

prod = TPL.k1 * TPL.k2
table, payload = bytearray(), bytearray()
order = sorted(files)
for idx, nb in enumerate(order):
    key = -sum(prod >> s for s in (24, 16, 8, 0)) - sum(idx >> s for s in (24, 16, 8, 0))
    raw_name = bytes((b - 0xfc * j - key) & 255 for j, b in enumerate(nb))
    data = files[nb]; size = len(data)
    raw = bytearray(data)
    k = (((0x20101118 - sum(nb)) * len(nb) + prod) * size) & 255
    for j in range(min(len(raw), 0x1000 + len(nb))):
        raw[j] = INV[(raw[j] + k + j) & 255]
    meta = struct.pack('<BIIII', 2, 0, len(payload), len(raw), size)
    payload += raw
    table += struct.pack('<I', len(raw_name)) + raw_name + meta
head = bytearray(TPL.header)
struct.pack_into('<ii??III8xI', head, 7, TPL.k1, TPL.k2, False, True, len(order), 0, len(order), len(table))
out.write_bytes(bytes(head) + bytes(table) + bytes(payload))

chk = NPA(out)
got = {bytes.fromhex(e['name_hex']): chk.read(e) for e in chk.entries if e['type'] == 2}
assert got == files, 'read-back mismatch'
print(out.name, out.stat().st_size, 'bytes', 'files', len(order), 'sha256', hashlib.sha256(out.read_bytes()).hexdigest()[:8])
