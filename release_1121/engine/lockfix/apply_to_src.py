"""검증이 끝난 잠금 고침(script_locks.inc)과 코덱스의 옛 세이브 가사 보기(lyric_save_view.inc)를 공용 소스 engine\\src 에 들인다.
- lockfix\\src 는 「engine\\src(ac07b4a7 시점) + 코덱스 세 군데 치환 + 내 두 군데 + 갈고리 표 한 줄」이다. 여기서는 engine\\src 가
  그 바탕과 같은지(바뀐 세 파일 말고는 바이트가 같아야 한다) 먼저 확인하고, 바뀐 파일을 옮긴다. 원래 파일은 src_before_lockfix\\ 에 둔다.
python -I -X utf8 apply_to_src.py [--check]
"""
import hashlib, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NEW = HERE / 'src'
DST = HERE.parent / 'src'
BAK = HERE.parent / 'src_before_lockfix'
CHANGED = {'runtime_hooks.cpp', 'native_hook_manifest.h'}
ADDED = {'script_locks.inc', 'lyric_save_view.inc'}
BUILT = {'n2hd_gpu_v8.lib', 'n2hd_gpu_v8.exp'}      # 빌드가 쓰는 파일(소스 아님)


def h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:8]


problems = []
for p in sorted(NEW.iterdir()):
    if p.name in BUILT:
        continue
    q = DST / p.name
    if p.name in ADDED:
        if q.exists() and h(q) != h(p):
            problems.append(f'{p.name}: engine\\src 에 다른 내용으로 이미 있음')
        continue
    if not q.exists():
        problems.append(f'{p.name}: engine\\src 에 없음')
    elif p.name not in CHANGED and h(p) != h(q):
        problems.append(f'{p.name}: engine\\src 가 고침 바탕과 다름(누가 고쳤다) {h(q)} != {h(p)}')
for q in sorted(DST.iterdir()):
    if q.name not in BUILT and not (NEW / q.name).exists():
        problems.append(f'{q.name}: engine\\src 에만 있음')
# 바뀐 두 파일은 engine\src 쪽이 「고치기 전」 그대로여야 한다: 내 치환을 거꾸로 해서 대조
rh = (NEW / 'runtime_hooks.cpp').read_bytes()
back = rh.replace(b'#include "script_locks.inc"\r\n', b'').replace(b'#include "script_locks.inc"\n', b'')
back = back.replace(b'lockFixInstall();state=2;return N2HD_Init();}', b'state=2;return N2HD_Init();}')
back = back.replace(b'#include "lyric_save_view.inc"\r\nstatic HANDLE WINAPI testCreateFile(', b'static HANDLE WINAPI testCreateFile(')
back = back.replace(b'HANDLE r=LyricSave::view(name,access,share,sa,disp,flags,tmpl);', b'HANDLE r=CreateFileA(name,access,share,sa,disp,flags,tmpl);')
back = back.replace(b'profileDir,MAX_PATH)||!profileDir[0]){patchSlot(0x511188,(void*)&LyricSave::view);return;}', b'profileDir,MAX_PATH)||!profileDir[0])return;')
cur = (DST / 'runtime_hooks.cpp').read_bytes()
if cur != back and cur != rh:
    problems.append('runtime_hooks.cpp: engine\\src 쪽이 고치기 전 바탕과 다름')
mf = (NEW / 'native_hook_manifest.h').read_bytes()
line = b'{0x44c4c0,(void*)&hookRemainTime,&origRemainTime,5,{0x55,0x8b,0x6c,0x24,0x08},0,0},'
assert mf.count(line) == 1
mback = mf.replace(line + b'\r\n', b'').replace(line + b'\n', b'')
mcur = (DST / 'native_hook_manifest.h').read_bytes()
if mcur != mback and mcur != mf:
    problems.append('native_hook_manifest.h: engine\\src 쪽이 고치기 전 바탕과 다름')
if problems:
    print('\n'.join(problems)); raise SystemExit('멈춤: 손으로 합칠 것')
print('engine\\src 는 고침 바탕과 같다')
if '--check' in sys.argv:
    raise SystemExit(0)
BAK.mkdir(exist_ok=True)
for n in sorted(CHANGED | ADDED):
    if (DST / n).exists() and not (BAK / n).exists():
        shutil.copyfile(DST / n, BAK / n)
    shutil.copyfile(NEW / n, DST / n)
    print('->', n, h(DST / n))
