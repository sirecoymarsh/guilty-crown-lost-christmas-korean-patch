"""11-21 출고 시험 사본 P:\\AI\\gclx-reltest\\game: 놀이 사본에서 큰 읽기 전용 묶음은 하드 링크(make_fliptest 와 같은 규칙),
작은 파일은 진짜 사본. 그다음 바꿀 파일을 넣는다 — 하드 링크인 자리는 먼저 링크를 끊고(unlink) 새 파일을 복사한다
(링크 자리에 그대로 쓰면 놀이 사본 파일까지 바뀐다).
python -I -X utf8 make_reltest.py
"""
import os, shutil, hashlib
from pathlib import Path
W = Path(__file__).resolve().parent
SRC = Path(r'P:\AI\gclx-codexrun\game')
DST = Path(r'P:\AI\gclx-reltest\game')
LINK = {'cg.npa', 'cg1.npa', 'sound.npa', 'voice.npa'}
LINK_DIRS = {'dx', 'dx4k', 'hires', 'fonts'}
SKIP = {'art.log', 'launcher-test.log', 'n2hd-options.ini'}
INSTALL = {
    'nss.npa': W / 'staging/nss_final.npa',
    'n2hd_runtime.dll': W / 'engine/payload/n2hd_runtime.dll',
    'version.dll': W / 'proxy/version.dll',
    'Korean4K_test.exe': W / 'launcher_test/Korean4K_test.exe',
    'dx/mv_lx0201.ngs': W / 'movie/out/mv_lx0201.ngs',
    'dx4k/mv_lx0201.mp4': W / 'movie/out/mv_lx0201.mp4',
}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

DST.mkdir(parents=True, exist_ok=True)
n_link = n_copy = 0
for p in SRC.rglob('*'):
    rel = p.relative_to(SRC); d = DST / rel
    if p.is_dir():
        d.mkdir(parents=True, exist_ok=True); continue
    if p.name in SKIP or rel.as_posix() in INSTALL:
        continue
    if d.exists():
        continue
    d.parent.mkdir(parents=True, exist_ok=True)
    if p.name in LINK or rel.parts[0] in LINK_DIRS:
        os.link(p, d); n_link += 1
    else:
        shutil.copy2(p, d); n_copy += 1
for rel, f in INSTALL.items():
    d = DST / rel
    if d.exists():
        d.unlink()                       # 하드 링크였으면 여기서 끊긴다
    shutil.copyfile(f, d)
    assert sha(d) == sha(f)
src_sha = {rel: sha(SRC / rel)[:8] for rel in INSTALL if (SRC / rel).exists()}
print('links', n_link, 'copies', n_copy, '->', DST)
print('play copy untouched:', src_sha)
