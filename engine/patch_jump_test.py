"""시험 전용: N2HD_TEST_JUMP_BACK=k 면 대사 기록에서 누를 때 커서 대신 「k 개 앞 지점」으로 점프. 점프·지점 저장 때 기록 줄.
backlog_jump.inc 경로를 인자로(지금 판·바꾸기 전 판 둘 다에 쓰려고). python patch_jump_test.py <파일>"""
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text('utf-8')


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:70], s.count(old))
    s = s.replace(old, new)


rep('static int poll(){++polls;if(!init())return 0;',
    'static int testJumpBack(){static int v=-2;if(v==-2){char b[16];v=GetEnvironmentVariableA("N2HD_TEST_JUMP_BACK",b,16)?atoi(b):-1;}return v;}\n'
    'static void testLog(const char* line){char d[MAX_PATH];if(!GetEnvironmentVariableA("N2HD_PROFILE_DIR",d,MAX_PATH))return;char path[MAX_PATH];sprintf_s(path,"%s\\\\jumptest.log",d);FILE* f=0;if(!fopen_s(&f,path,"a")&&f){fprintf(f,"%llu %s\\n",(unsigned long long)GetTickCount64(),line);fclose(f);}}\n'
    'static int poll(){++polls;if(!init())return 0;')
rep('if(!down){held=false;return 0;}++downs;if(held||h<0)return 0;held=true;',
    'if(!down){held=false;return 0;}++downs;if(testJumpBack()>0&&!held&&(int)points.size()>testJumpBack())h=(int)points.size()-1-testJumpBack();if(held||h<0)return 0;held=true;'
    '{char l[200];sprintf_s(l,"click point=%d of %u start=%u end=%u sealed=%d hist=%u",h,(unsigned)points.size(),points[h].start,points[h].end,points[h].sealed?1:0,historySize());testLog(l);}')
rep('int ok=((int(__cdecl*)())origJumpLoad)();',
    '{char l[120];sprintf_s(l,"load jump=%d selected=%d hist_before=%u",isJump?1:0,selected,historySize());testLog(l);}int ok=((int(__cdecl*)())origJumpLoad)();{char l[120];sprintf_s(l,"loaded ok=%d hist_after=%u",ok,historySize());testLog(l);}')
rep('static int capture(){', 'static int captureImpl();\nstatic int capture(){int r=captureImpl();char l[80];sprintf_s(l,"capture hist=%u points=%u",historySize(),(unsigned)points.size());testLog(l);return r;}\nstatic int captureImpl(){')
p.write_text(s, 'utf-8'); print('ok', p.name)
