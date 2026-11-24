"""시험 사본 P:\\AI\\gclx-4k-test\\game — Codex 실행 후보에서 큰 아카이브·영상만 하드링크(읽기만 함),
나머지는 복사(게임이 고쳐 쓸 수 있는 파일이 Codex 폴더로 새지 않게). 내 DLL·글꼴·hires(F: 로 이어진 연결점).
python -X utf8 make_testgame.py
"""
import os, shutil, subprocess
from pathlib import Path

SRC = Path(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\outputs\korean-game-candidate\game')
DST = Path(r'P:\AI\gclx-4k-test\game')
LINK = {'.npa', '.mp4', '.ngs'}
DST.mkdir(parents=True, exist_ok=True)
for f in SRC.rglob('*'):
    rel = f.relative_to(SRC)
    t = DST / rel
    if f.is_dir():
        t.mkdir(parents=True, exist_ok=True); continue
    if t.exists():
        t.unlink()
    t.parent.mkdir(parents=True, exist_ok=True)
    if f.suffix.lower() in LINK and f.stat().st_size > 1 << 20:
        os.link(f, t)
    else:
        shutil.copy2(f, t)
shutil.copy2(r'F:\AI\gclx-4k\engine\build\n2hd_runtime.dll', DST / 'n2hd_runtime.dll')
(DST / 'fonts').mkdir(exist_ok=True)
for name in ('NotoSansKR-VF.ttf', 'NotoSerifKR-VF.ttf'):
    shutil.copy2(Path(r'C:\Windows\Fonts') / name, DST / 'fonts' / name)
if not (DST / 'hires').exists():
    subprocess.run(['cmd', '/c', 'mklink', '/J', str(DST / 'hires'), r'F:\AI\gclx-4k\hires'], check=True, capture_output=True)
print('시험 사본 준비:', DST)
