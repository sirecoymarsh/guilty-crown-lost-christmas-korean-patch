"""받는 사람처럼: 원본 영문판 사본에 ZIP 을 풀어 덮어쓴 뒤, 놀이 사본(손 확인하는 판)과 같은지 본다.
- 파일: 놀이 사본에 있는 게임 파일은 모두 같아야 한다(cg.npa 는 원본 그대로이므로 빼고, 대신 아래 그림 대조).
- 그림: 놀이 사본 cg.npa 의 모든 항목이, 「cg.kor.npa 에 있으면 그것, 없으면 원본 cg.npa」로 바이트까지 같아야 한다.
python -I -X utf8 verify_zip.py <zip> <풀 폴더>
"""
import sys, os, shutil, zipfile, hashlib
from pathlib import Path
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from npa_assets import NPA
SRC = Path(r'Y:\GAME\Guilty-Crown-Lost-Christmas_Win_EN_Full-rip\GUILTY CROWN LOST XMAS')
PLAY = Path(r'P:\AI\gclx-codexrun\game')
zp, T = Path(sys.argv[1]), Path(sys.argv[2])
LINK = {'cg.npa', 'cg1.npa', 'sound.npa', 'voice.npa'}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


if T.exists():
    shutil.rmtree(T)
for p in SRC.rglob('*'):
    d = T / p.relative_to(SRC)
    if p.is_dir():
        d.mkdir(parents=True, exist_ok=True); continue
    d.parent.mkdir(parents=True, exist_ok=True)
    os.link(p, d) if (p.name.lower() in LINK and p.parent == SRC) else shutil.copy2(p, d)
with zipfile.ZipFile(zp) as z:
    names = [n for n in z.namelist() if not n.endswith('/')]
    for n in names:
        d = T / n
        assert d.name.lower() not in LINK, n          # 하드 링크 너머 원본에 쓰지 않는다
        if d.exists():
            d.unlink()
    z.extractall(T)
print('extracted', len(names))
skip = {'cg.npa', 'korean4k_test.exe', 'launcher-test.log', 'n2hd-options.ini'}
bad, n = [], 0
for p in PLAY.rglob('*'):
    rel = p.relative_to(PLAY)
    top = rel.parts[0].lower()
    if not p.is_file() or top in ('hires', 'dx4k') or rel.name.lower() in skip:
        continue
    n += 1
    q = T / rel
    if not q.exists() or sha(p) != sha(q):
        bad.append(str(rel))
extra = sorted(str(p.relative_to(T)) for p in T.rglob('*') if p.is_file() and not (PLAY / p.relative_to(T)).exists())
print('files compared', n, 'different', bad, 'only in release copy', extra)
ko, orig, play = NPA(T / 'cg.kor.npa'), NPA(T / 'cg.npa'), NPA(PLAY / 'cg.npa')
kmap = {e['name_hex']: e for e in ko.entries if e['type'] == 2}
omap = {e['name_hex']: e for e in orig.entries if e['type'] == 2}
mism, cnt = [], 0
for e in play.entries:
    if e['type'] != 2:
        continue
    cnt += 1
    src = (ko, kmap[e['name_hex']]) if e['name_hex'] in kmap else (orig, omap.get(e['name_hex']))
    if src[1] is None or src[0].read(src[1]) != play.read(e):
        mism.append(e['name'])
print('cg entries compared', cnt, 'mismatch', len(mism), mism[:5])
print('RESULT', 'PASS' if not bad and not mism and extra == ['cg.kor.npa', '패치_사용방법.txt'] else 'FAIL')
