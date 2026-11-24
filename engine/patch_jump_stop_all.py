"""점프 뒤 끌 변수에 메뉴 잠금 사본($LOCAL_sys_skip·$LOCAL_sys_auto)·$LOCAL_skip·초고속 건너뛰기(#SYSTEM_skip_express)를 더함.
시험 스위치 N2HD_TEST_EXPRESS: 점프를 누를 때 초고속 건너뛰기를 쓰다 대사 기록을 연 상태로 만듦. 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\backlog_jump.inc'); s = p.read_text('utf-8')


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:80], s.count(old))
    s = s.replace(old, new)


rep(' // A checkpoint keeps $SYSTEM_skip / $SYSTEM_text_auto as they were when it was taken; a jump restored them and the\n'
    ' // game skipped through the read text back to where the reader had been (user, 10-27). After a jump both are off.\n',
    ' // A checkpoint keeps $SYSTEM_skip / $SYSTEM_text_auto as they were when it was taken, and the menu lock keeps a copy\n'
    ' // ($LOCAL_sys_skip / $LOCAL_sys_auto, put back when the backlog closes: function.nss MenuLock). The express skip\n'
    ' // (#SYSTEM_skip_express, a global the load does not touch) skips to the first unread line. A jump brought them back\n'
    ' // and the game skipped through the read text to where the reader had been (user, 10-27). After a jump all are off.\n')
rep('for(const char* n:{"$SYSTEM_skip","$SYSTEM_text_auto"}){',
    'for(const char* n:{"$SYSTEM_skip","$SYSTEM_text_auto","$LOCAL_sys_skip","$LOCAL_sys_auto","$LOCAL_skip","#SYSTEM_skip_express"}){')
# 시험: 누를 때 초고속 건너뛰기 중이었던 것처럼
rep('{char l[200];sprintf_s(l,"click point=%d of %u start=%u end=%u sealed=%d hist=%u",',
    'if(GetEnvironmentVariableA("N2HD_TEST_EXPRESS",0,0))for(const char* n:{"#SYSTEM_skip_express","$LOCAL_sys_skip"}){auto tv=var(n);if(tv)*(double*)(tv+0x10)=1.0;}\n'
    ' {char l[200];sprintf_s(l,"click point=%d of %u start=%u end=%u sealed=%d hist=%u",')
p.write_text(s, 'utf-8'); print('ok')
