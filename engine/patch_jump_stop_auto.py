"""대사 기록 점프 뒤 자동 진행·건너뛰기 끄기(사용자 결정 10-27). 점프 단계별 시간(시험 기록). 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\backlog_jump.inc'); s = p.read_text('utf-8')


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:80], s.count(old))
    s = s.replace(old, new)


rep('static int load(){drainAll();bool isJump=',
    'static int load(){LARGE_INTEGER lq0,lq1,lq2,lq3,lqf;QueryPerformanceFrequency(&lqf);QueryPerformanceCounter(&lq0);drainAll();QueryPerformanceCounter(&lq1);bool isJump=')
rep('{char l[120];sprintf_s(l,"loaded ok=%d hist_after=%u",ok,historySize());testLog(l);}',
    'QueryPerformanceCounter(&lq2);{char l[120];sprintf_s(l,"loaded ok=%d hist_after=%u",ok,historySize());testLog(l);}')
# 점프로 불러온 뒤: 저장 때의 자동 진행·건너뛰기 상태가 되살아나 읽은 곳을 건너뛰어 원래 자리까지 가 버렸다(사용자 10-27)
rep(' if(ok){if(isJump)++restores;if(init())chain(savedId());}else ++errors;',
    ' // A checkpoint keeps $SYSTEM_skip / $SYSTEM_text_auto as they were when it was taken; a jump restored them and the\n'
    ' // game skipped through the read text back to where the reader had been (user, 10-27). After a jump both are off.\n'
    ' if(ok&&isJump)for(const char* n:{"$SYSTEM_skip","$SYSTEM_text_auto"}){auto v=var(n);if(!v)continue;{char l[120];sprintf_s(l,"jump off %s type=%d value=%g",n,v[0],*(double*)(v+0x10));testLog(l);}*(double*)(v+0x10)=0.0;}\n'
    ' if(ok){if(isJump)++restores;if(init())chain(savedId());}else ++errors;QueryPerformanceCounter(&lq3);\n'
    ' {char l[160];sprintf_s(l,"load ms drain=%.0f engine=%.0f chain=%.0f",(lq1.QuadPart-lq0.QuadPart)*1000.0/lqf.QuadPart,(lq2.QuadPart-lq1.QuadPart)*1000.0/lqf.QuadPart,(lq3.QuadPart-lq2.QuadPart)*1000.0/lqf.QuadPart);testLog(l);}')
p.write_text(s, 'utf-8'); print('ok')
