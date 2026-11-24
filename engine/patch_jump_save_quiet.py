"""지점 저장(nativeSave) 동안 건너뛰기·자동 진행·초고속 건너뛰기·메뉴 잠금 사본을 0 으로 두고, 끝나면 되돌림.
엔진은 저장 순간 건너뛰기 상태를 저장 데이터에 담아, 불러온 뒤 변수를 꺼도 안 읽은 곳까지 넘어갔다(10-27 시험).
점프 뒤 3초 동안 프레임마다 끄던 것은 한 번도 걸리지 않아 뺀다. 한 번만 돌린다."""
from pathlib import Path
src = Path(r'F:\AI\gclx-4k\engine\src')


def patch(name, pairs):
    p = src / name; s = p.read_text('utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (name, old[:80], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, 'utf-8')


patch('backlog_jump.inc', [
    # 저장 동안 0 (시험 스위치가 켠 건너뛰기도 여기서 0 이 됨 = 건너뛰는 중에 저장되는 경우)
    (' int ok=nativeSave(1);if(tsv)*(double*)(tsv+0x10)=tso;',
     ' // Checkpoints are taken with skip, auto and the express skip off (put back right after): the save keeps the skip\n'
     ' // state, and a jump to a point taken while skipping skipped on through the read text to the first unread line\n'
     ' // (user, 10-27; turning the variables off after the load did not stop it).\n'
     ' static const char* const quietVars[]={"$SYSTEM_skip","$SYSTEM_text_auto","#SYSTEM_skip_express","$LOCAL_sys_skip","$LOCAL_sys_auto","$LOCAL_skip"};\n'
     ' double quietOld[6]={};unsigned char* quietPtr[6]={};bool quiet=!GetEnvironmentVariableA("N2HD_TEST_NO_JUMP_FIX",0,0);\n'
     ' if(quiet)for(int i=0;i<6;++i){quietPtr[i]=var(quietVars[i]);if(quietPtr[i]){quietOld[i]=*(double*)(quietPtr[i]+0x10);*(double*)(quietPtr[i]+0x10)=0.0;}}\n'
     ' int ok=nativeSave(1);\n'
     ' if(quiet)for(int i=0;i<6;++i)if(quietPtr[i])*(double*)(quietPtr[i]+0x10)=quietOld[i];\n'
     ' if(tsv)*(double*)(tsv+0x10)=tso;'),
    # 점프 뒤 3초 프레임 감시는 뺌(효과 없음)
    (' if(ok&&isJump&&!GetEnvironmentVariableA("N2HD_TEST_NO_JUMP_FIX",0,0))quietUntil=GetTickCount64()+3000;\n', ''),
])
p = src / 'backlog_jump.inc'; s = p.read_text('utf-8')
a = s.index('// The loaded state is applied again after the load call returns')
b = s.index('static int load(){')
s = s[:a] + 'static void tick(){}\n' + s[b:]
p.write_text(s, 'utf-8')
print('ok')
