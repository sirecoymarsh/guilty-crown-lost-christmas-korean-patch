"""시험 기록 2: 글자 층(544 폭) 그리기를 함수 들머리에서(일찍 끝나는 것도) 기록하고, 마스크(filter)가 있으면 「덮」 세로획 자리
(화면 1배 x 152~168, y 425)의 마스크 값도 남김(N2HD_GLYPH_LOG → draw2.log). 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\n2hd_gpu_v8.cpp'); s = p.read_text('utf-8')
old = ' int mode=iv(object,0xc)&0xfff;\n'
assert s.count(old) == 1
new = old + r''' {static int dlog=-1;static FILE* df;if(dlog<0){wchar_t d[MAX_PATH];dlog=GetEnvironmentVariableW(L"N2HD_GLYPH_LOG",0,0)&&GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",d,MAX_PATH)?1:0;if(dlog)df=_wfopen((std::wstring(d)+L"\\draw2.log").c_str(),L"a");}
  if(df&&sw==544){fprintf(df,"%llu tex=%p mode=%d op=%d filter=%p x=%d,%d y=%d,%d clip=%d,%d,%d,%d",(unsigned long long)GetTickCount64(),pv(t,0x28),mode,opacity,filter,x[0],x[1],y[0],y[2],clip[0],clip[1],clip[2],clip[3]);
   if(filter){int stride=iv(filter,0x20);unsigned char* fd=(unsigned char*)pv(filter,0x28);unsigned char* lut=(unsigned char*)filter+0x2c;fprintf(df," stride=%d mask",stride);if(fd&&stride>=1024&&stride<=16384)for(int xx=152;xx<=168;++xx)fprintf(df," %d",lut[fd[425*stride+xx]]);}
   fprintf(df,"\n");fflush(df);}}
'''
s = s.replace(old, new)
p.write_text(s, 'utf-8'); print('ok')
