"""시험 기록: 4K 그리기마다 화면 꼭짓점·원본 좌표·자르기·바뀐 영역(N2HD_GLYPH_LOG → draw.log, 원본이 글자 층 크기일 때만). 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\n2hd_gpu_v8.cpp'); s = p.read_text('utf-8')
old = ' V v[4];int minU=*std::min_element(sx,sx+4),minV=*std::min_element(sy,sy+4);\n'
assert s.count(old) == 1
new = r''' {static int dlog=-1;static FILE* df;if(dlog<0){wchar_t d[MAX_PATH];dlog=GetEnvironmentVariableW(L"N2HD_GLYPH_LOG",0,0)&&GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",d,MAX_PATH)?1:0;if(dlog)df=_wfopen((std::wstring(d)+L"\\draw.log").c_str(),L"a");}
  if(df&&sw==544){fprintf(df,"%llu tex=%p %dx%d mode=%d op=%d x=%d,%d,%d,%d y=%d,%d,%d,%d sx=%d,%d,%d,%d sy=%d,%d,%d,%d clip=%d,%d,%d,%d dirty=%d,%d,%d,%d sc=%ld,%ld,%ld,%ld\n",(unsigned long long)GetTickCount64(),pv(t,0x28),sw,sh,mode,opacity,x[0],x[1],x[2],x[3],y[0],y[1],y[2],y[3],sx[0],sx[1],sx[2],sx[3],sy[0],sy[1],sy[2],sy[3],clip[0],clip[1],clip[2],clip[3],dirty[0],dirty[1],dirty[2],dirty[3],rc.left,rc.top,rc.right,rc.bottom);fflush(df);}}
''' + old
s = s.replace(old, new)
p.write_text(s, 'utf-8'); print('ok')
