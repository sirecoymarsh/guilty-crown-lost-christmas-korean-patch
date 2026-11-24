"""시험: 프레임 시작(hookClear)에서 엔진의 바뀐 영역(0x62949c)을 기록하고(N2HD_GLYPH_LOG → dirty.log),
N2HD_TEST_DIRTY_PAD=n 이면 엔진이 지우고 그리기 전에 그 영역을 사방 n 픽셀(1배) 넓힌다. 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\runtime_hooks.cpp'); s = p.read_text('utf-8')
old = 'static void __cdecl hookClear(){jumpTick();N2HD_Clear();((void(__cdecl*)())origClear)();}'
assert s.count(old) == 1
new = r'''static void dirtyTest(){static int pad=-1;static FILE* f;if(pad<0){char v[16]={};pad=GetEnvironmentVariableA("N2HD_TEST_DIRTY_PAD",v,16)?atoi(v):0;
  char d[MAX_PATH];if(GetEnvironmentVariableA("N2HD_GLYPH_LOG",0,0)&&GetEnvironmentVariableA("N2HD_PROFILE_DIR",d,MAX_PATH)){char path[MAX_PATH];sprintf_s(path,"%s\\dirty.log",d);fopen_s(&f,path,"a");}}
 int* r=(int*)0x62949c;if(f){fprintf(f,"%llu %d %d %d %d\n",(unsigned long long)GetTickCount64(),r[0],r[1],r[2],r[3]);fflush(f);}
 if(pad&&r[2]>=r[0]&&r[3]>=r[1]){r[0]=std::max(0,r[0]-pad);r[1]=std::max(0,r[1]-pad);r[2]=std::min(1023,r[2]+pad);r[3]=std::min(575,r[3]+pad);}}
static void __cdecl hookClear(){jumpTick();dirtyTest();N2HD_Clear();((void(__cdecl*)())origClear)();}'''
s = s.replace(old, new)
p.write_text(s, 'utf-8'); print('ok')
