"""덮어쓰기 배포 시험 사본: 원본 영문판 위에 배포할 파일만 덮어쓴 폴더를 만든다.
- 덮어쓰지 않는 큰 묶음(cg.npa·cg1.npa·sound.npa·voice.npa)은 원본에 하드 링크, 나머지는 복사.
- 덮어쓸 자리는 먼저 지운 뒤 복사(하드 링크 너머 원본에 쓰지 않게).
python -I -X utf8 make_ovtest.py <stage 폴더> <시험 사본 폴더>
"""
import os, shutil, sys
from pathlib import Path
SRC = Path(r'Y:\GAME\Guilty-Crown-Lost-Christmas_Win_EN_Full-rip\GUILTY CROWN LOST XMAS')
LINK = {'cg.npa', 'cg1.npa', 'sound.npa', 'voice.npa'}
stage, T = Path(sys.argv[1]), Path(sys.argv[2])
if T.exists():
    shutil.rmtree(T)
T.mkdir(parents=True)
for p in SRC.rglob('*'):
    rel = p.relative_to(SRC); d = T / rel
    if p.is_dir():
        d.mkdir(parents=True, exist_ok=True); continue
    d.parent.mkdir(parents=True, exist_ok=True)
    if p.name.lower() in LINK and p.parent == SRC:
        os.link(p, d)
    else:
        shutil.copy2(p, d)
n = 0
for p in stage.rglob('*'):
    if p.is_file():
        d = T / p.relative_to(stage)
        d.parent.mkdir(parents=True, exist_ok=True)
        if d.exists():
            d.unlink()
        shutil.copy2(p, d); n += 1
print('test copy', T, 'overlaid', n, 'files')
