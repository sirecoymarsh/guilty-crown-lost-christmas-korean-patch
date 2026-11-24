"""점프 뒤 3초 동안 프레임마다(그리기 스레드 = 대본 스레드의 hookClear) 건너뛰기·자동 진행을 끔.
불러오기 직후 한 번 끄기는 엔진이 그 뒤에 저장 상태를 다시 적용해 소용없었다(10-27 시험). 한 번만 돌린다."""
from pathlib import Path
src = Path(r'F:\AI\gclx-4k\engine\src')


def patch(name, pairs):
    p = src / name; s = p.read_text('utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (name, old[:80], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, 'utf-8')


patch('backlog_jump.inc', [
    (' if(ok&&isJump&&!GetEnvironmentVariableA("N2HD_TEST_NO_JUMP_FIX",0,0))for(const char* n:{"$SYSTEM_skip","$SYSTEM_text_auto","$LOCAL_sys_skip","$LOCAL_sys_auto","$LOCAL_skip","#SYSTEM_skip_express"}){',
     ' if(ok&&isJump&&!GetEnvironmentVariableA("N2HD_TEST_NO_JUMP_FIX",0,0))quietUntil=GetTickCount64()+3000;\n'
     ' if(ok&&isJump&&!GetEnvironmentVariableA("N2HD_TEST_NO_JUMP_FIX",0,0))for(const char* n:{"$SYSTEM_skip","$SYSTEM_text_auto","$LOCAL_sys_skip","$LOCAL_sys_auto","$LOCAL_skip","#SYSTEM_skip_express"}){'),
    ('static int load(){', r'''// The loaded state is applied again after the load call returns (10-27: skip turned off right after the load came back
// on and skipped ahead). So for 3 s after a jump every frame turns them off again (tick, from the frame-start hook on
// the script thread).
static volatile ULONGLONG quietUntil;
static void tick(){if(!quietUntil)return;if(GetTickCount64()>quietUntil){quietUntil=0;return;}
 for(const char* n:{"$SYSTEM_skip","$SYSTEM_text_auto","$LOCAL_sys_skip","$LOCAL_sys_auto","$LOCAL_skip","#SYSTEM_skip_express"}){auto v=var(n);if(v&&*(double*)(v+0x10)!=0.0){char l[100];sprintf_s(l,"quiet %s was %g",n,*(double*)(v+0x10));testLog(l);*(double*)(v+0x10)=0.0;}}}
static int load(){'''),
])
patch('runtime_hooks.cpp', [
    ('static void __cdecl hookClear(){N2HD_Clear();', 'static void jumpTick();   // backlog_jump.inc, below\nstatic void __cdecl hookClear(){jumpTick();N2HD_Clear();'),
    ('#include "backlog_jump.inc"\n', '#include "backlog_jump.inc"\nstatic void jumpTick(){Jump::tick();}\n'),
])
print('ok')
