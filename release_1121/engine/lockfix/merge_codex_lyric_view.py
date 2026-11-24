"""lockfix\\src 에 코덱스의 「옛 세이브 가사 보기」(awakening\\lyric_save_view.inc, 11-24 07:04 놀이 사본 DLL 54196c77)를 얹는다.
코덱스 build_compat.py 의 build_sources() 가 runtime_hooks.cpp 에 하는 세 군데 바꿈을 그대로 한다(코덱스 폴더는 읽기만).
python -I -X utf8 merge_codex_lyric_view.py
"""
import hashlib, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / 'src'
CODEX = Path(r'P:\AI\Codex\projects\gclx-song-20261123\awakening')

r = SRC / 'runtime_hooks.cpp'
text = r.read_bytes()
if b'lyric_save_view.inc' in text:
    print('already merged')
else:
    def replace(a, b):
        global text
        assert text.count(a) == 1, a
        text = text.replace(a, b)
    replace(b'static HANDLE WINAPI testCreateFile(', b'#include "lyric_save_view.inc"\r\nstatic HANDLE WINAPI testCreateFile(')
    replace(b'HANDLE r=CreateFileA(name,access,share,sa,disp,flags,tmpl);', b'HANDLE r=LyricSave::view(name,access,share,sa,disp,flags,tmpl);')
    replace(b'profileDir,MAX_PATH)||!profileDir[0])return;', b'profileDir,MAX_PATH)||!profileDir[0]){patchSlot(0x511188,(void*)&LyricSave::view);return;}')
    r.write_bytes(text)
    shutil.copyfile(CODEX / 'lyric_save_view.inc', SRC / 'lyric_save_view.inc')
    print('merged')
# 코덱스가 실제로 빌드한 소스와 같은지: 코덱스 runtime\src 의 파일들과 대조(내가 더한 것만 달라야 한다)
cs = CODEX / 'runtime' / 'src'
diff = []
for p in sorted(cs.iterdir()):
    if p.suffix in ('.cpp', '.inc', '.h'):
        q = SRC / p.name
        if not q.exists():
            diff.append(f'missing here: {p.name}')
        elif hashlib.sha256(p.read_bytes()).digest() != hashlib.sha256(q.read_bytes()).digest():
            diff.append(f'differs: {p.name}')
for q in sorted(SRC.iterdir()):
    if q.suffix in ('.cpp', '.inc', '.h') and not (cs / q.name).exists():
        diff.append(f'only here: {q.name}')
print('\n'.join(diff) if diff else 'identical')
