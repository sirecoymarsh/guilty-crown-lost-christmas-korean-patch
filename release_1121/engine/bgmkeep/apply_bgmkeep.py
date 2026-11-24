"""J/K 다시 시작에서 음악 잇기(bgm_keep.inc)를 엔진 소스 폴더에 넣는다 — 여러 번 돌려도 같은 결과(이미 들어 있으면 건너뜀).
python -I -X utf8 apply_bgmkeep.py <src 폴더>
- bgm_keep.inc 복사(이 폴더의 src\\bgm_keep.inc)
- runtime_hooks.cpp: 앞 선언 한 줄, #include "bgm_keep.inc"(native_hook_manifest.h 앞), N2HD_Install 끝에 BgmKeep::install()
- native_hook_manifest.h: 갈고리 다섯(0x479770 스트림 없애기, 0x47a09f·0x47a2b9·0x47a566 상태 검사, 0x47a9b6 로드 중 검사)
- backlog_jump.inc: restart() 의 bgmKeepSelect(), load() 의 bgmKeepAfterLoad(), jumpCapture 의 bgmKeepClear()
dsb_trace.inc(시험용 DirectSound 기록)는 넣지 않는다.
"""
import sys, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = Path(sys.argv[1])


def edit(name, a, b):
    p = src / name
    s = p.read_text('utf-8', errors='surrogateescape')
    if b in s:
        print('skip', name, b[:40].replace('\n', ' '))
        return
    assert s.count(a) == 1, (name, a[:60], s.count(a))
    p.write_text(s.replace(a, b), 'utf-8', errors='surrogateescape')
    print('edit', name)


shutil.copyfile(HERE / 'src/bgm_keep.inc', src / 'bgm_keep.inc')
edit('runtime_hooks.cpp', '#include "backlog_jump.inc"\n',
     'static void bgmKeepAfterLoad(bool restart);static void bgmKeepSelect();static void bgmKeepClear();   // bgm_keep.inc (Claude 11-24)\n#include "backlog_jump.inc"\n')
edit('runtime_hooks.cpp', '#include "native_hook_manifest.h"\n', '#include "bgm_keep.inc"\n#include "native_hook_manifest.h"\n')
edit('runtime_hooks.cpp', 'lockFixInstall();state=2;', 'lockFixInstall();BgmKeep::install();state=2;')
edit('native_hook_manifest.h', 'static Hook hooks[]={\n', 'static Hook hooks[]={\n'
     '{0x479770,(void*)&hookSndDestroy,&BgmKeep::origSndDestroy,5,{0x56,0x8b,0x74,0x24,0x08},0,0},   // Claude 11-24 sound stream destroy (bgm_keep.inc)\n'
     '{0x47a09f,(void*)&stubState1,&BgmKeep::origSt1,5,{0xa1,0x40,0x05,0x62,0x00},0,0},   // Claude 11-24 stream thread state checks (bgm_keep.inc)\n'
     '{0x47a2b9,(void*)&stubState2,&BgmKeep::origSt2,6,{0x8b,0x15,0x40,0x05,0x62,0x00},0,0},\n'
     '{0x47a566,(void*)&stubState3,&BgmKeep::origSt3,5,{0xa1,0x40,0x05,0x62,0x00},0,0},\n'
     '{0x47a9b6,(void*)&stubLoading,&BgmKeep::origSt4,10,{0x81,0x3d,0x40,0x05,0x62,0x00,0x02,0x02,0x00,0x00},0,0},\n')
edit('backlog_jump.inc', 'if(stage(points[h])){pending=h;restartLoad=true;return 1;}',
     'if(stage(points[h])){pending=h;restartLoad=true;bgmKeepSelect();return 1;}')
edit('backlog_jump.inc', ' bool wasRestart=restartLoad;restartLoad=false;\n',
     ' bool wasRestart=restartLoad;restartLoad=false;\n bgmKeepAfterLoad(ok&&wasRestart);   // Claude 11-24: J/K restart keeps the music (bgm_keep.inc)\n')
edit('backlog_jump.inc', 'static int __cdecl jumpCapture(){', 'static int __cdecl jumpCapture(){bgmKeepClear();')
print('done')
