"""시험 기록 3: N2HD_Draw 들머리에서 글자 층(544 폭) 그리기마다 일찍 끝나는 까닭(불투명도·+0x30·arg2·변환+0xf0·filter)을 남김
(N2HD_GLYPH_LOG → draw3.log). 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\n2hd_gpu_v8.cpp'); s = p.read_text('utf-8')
old = 'extern "C" __declspec(dllexport) void __cdecl N2HD_Draw(void* object,void* arg2,void* filter){Guard guard;PerfScope perf(PF_DRAW);++calls;if(!object)return;'
assert s.count(old) == 1
new = old + r''' {static int dlog=-1;static FILE* df;if(dlog<0){wchar_t d[MAX_PATH];dlog=GetEnvironmentVariableW(L"N2HD_GLYPH_LOG",0,0)&&GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",d,MAX_PATH)?1:0;if(dlog)df=_wfopen((std::wstring(d)+L"\\draw3.log").c_str(),L"a");}
  void* tt=pv(object,0x2c);void* mm=pv(object,0x28);if(df&&tt&&iv(tt,8)==544){fprintf(df,"%llu tex=%p op=%d o30=%p arg2=%p filter=%p mf0=%p mode=%d\n",(unsigned long long)GetTickCount64(),pv(tt,0x28),*((unsigned char*)object+0x1c),pv(object,0x30),arg2,filter,mm?pv(mm,0xf0):0,iv(object,0xc)&0xfff);fflush(df);}}
'''
s = s.replace(old, new)
p.write_text(s, 'utf-8'); print('ok')
