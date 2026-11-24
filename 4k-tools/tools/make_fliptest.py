"""숨긴 시험용 게임 사본 P:\\AI\\gclx-fliptest\\game: 큰 읽기 전용 묶음(cg·cg1·sound·voice.npa, dx·dx4k·hires·fonts 안의 파일)은 하드 링크,
엔진·실행기·대본·작은 파일은 진짜 사본. hires\\art.log 는 링크하지 않는다(DLL 이 덧쓰는 기록이 원본으로 새지 않게).
그 뒤 시험할 DLL 을 넣는다. python -X utf8 make_fliptest.py <시험 DLL>"""
import os, shutil, sys
from pathlib import Path

SRC = Path(r'P:\AI\gclx-codexrun\game')
DST = Path(r'P:\AI\gclx-fliptest\game')
LINK = {'cg.npa', 'cg1.npa', 'sound.npa', 'voice.npa'}
LINK_DIRS = {'dx', 'dx4k', 'hires', 'fonts'}
SKIP = {'art.log', 'launcher-test.log'}
DST.mkdir(parents=True, exist_ok=True)
n_link = n_copy = 0
for p in SRC.rglob('*'):
    rel = p.relative_to(SRC)
    d = DST / rel
    if p.is_dir():
        d.mkdir(parents=True, exist_ok=True); continue
    if p.name in SKIP:
        continue
    if d.exists():
        if d.stat().st_size == p.stat().st_size and (rel.parts[0] in LINK_DIRS or p.name in LINK):
            continue
        d.unlink()
    d.parent.mkdir(parents=True, exist_ok=True)
    if p.name in LINK or rel.parts[0] in LINK_DIRS:
        os.link(p, d); n_link += 1
    else:
        shutil.copy2(p, d); n_copy += 1
shutil.copy2(sys.argv[1], DST / 'n2hd_runtime.dll')
print('links', n_link, 'copies', n_copy, '->', DST)
