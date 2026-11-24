"""진단(한 번만): 메뉴를 열 때 화면이 잠깐 1배가 되는 원인. 합본 소스 사본에 기록을 넣는다(N2HD_GLYPH_LOG + N2HD_PROFILE_DIR).
- menu.log: N2HD_Capture 호출(매개변수·면 플래그·스냅샷 여부), 1배 호환 길(AfterDraw) 그리기의 이유와 범위, 1024x576 면을 1배로 올리는 일.
결과: merge_1101\\diag_build\\n2hd_runtime.dll"""
import shutil
from pathlib import Path

SRC = Path(r'F:\AI\gclx-4k\engine\merge_1101\src')
DIAG = Path(r'F:\AI\gclx-4k\engine\merge_1101\diag_src')
if DIAG.exists():
    shutil.rmtree(DIAG)
shutil.copytree(SRC, DIAG)
p = DIAG / 'n2hd_gpu_v8.cpp'
s = p.read_text('utf-8')


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:70], s.count(old))
    s = s.replace(old, new)


rep('static IDirect3DTexture9* upload(void* t){',
    'static FILE* menuLog(){static FILE* f=(FILE*)1;if(f==(FILE*)1){wchar_t d[MAX_PATH];f=0;if(GetEnvironmentVariableW(L"N2HD_GLYPH_LOG",0,0)&&GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",d,MAX_PATH))f=_wfopen((std::wstring(d)+L"\\\\menu.log").c_str(),L"a");}return f;}\n'
    'static IDirect3DTexture9* upload(void* t){')
rep(' if(!object||!parameters||!*((unsigned char*)object+0x1c)||!ensure())return;void* t=pv(object,0x2c);if(!t)return;\n',
    ' if(FILE* f=menuLog()){void* tt=object?pv(object,0x2c):0;fprintf(f,"f=%llu capture obj=%p op=%d t=%p %dx%d tflags=%04x p=%d,%d,%d,%d pos=%d,%d\\n",(unsigned long long)frames,object,object?*((unsigned char*)object+0x1c):-1,tt,tt?iv(tt,8):0,tt?iv(tt,12):0,tt?*(unsigned short*)((char*)tt+4):0,parameters?parameters[0]:0,parameters?parameters[1]:0,parameters?parameters[2]:0,parameters?parameters[3]:0,object?iv(object,0x10):0,object?iv(object,0x14):0);fflush(f);}\n'
    ' if(!object||!parameters||!*((unsigned char*)object+0x1c)||!ensure())return;void* t=pv(object,0x2c);if(!t)return;\n')
rep(' if(!object||pv(object,0x30)||!*((unsigned char*)object+0x1c)||!needsCompatibility(object,arg,filter)||!ensure())return;',
    ' if(object&&!pv(object,0x30)&&*((unsigned char*)object+0x1c)&&needsCompatibility(object,arg,filter))if(FILE* f=menuLog()){void* tt=pv(object,0x2c);void* m=pv(object,0x28);int* dd=(int*)0x62949c;fprintf(f,"f=%llu compat obj=%p t=%p %dx%d arg=%p filter=%p spans=%d high=%d snap=%d dirty=%d,%d,%d,%d\\n",(unsigned long long)frames,object,tt,tt?iv(tt,8):0,tt?iv(tt,12):0,arg,filter,m&&pv(m,0xf0)?1:0,tt&&high.count(pv(tt,0x28))?1:0,tt&&snapshots.count(tt)?1:0,dd[0],dd[1],dd[2],dd[3]);fflush(f);}\n'
    ' if(!object||pv(object,0x30)||!*((unsigned char*)object+0x1c)||!needsCompatibility(object,arg,filter)||!ensure())return;')
# 화면 크기 면을 1배로 올릴 때(스냅샷도 4배 그림도 아닌 길)
rep(' Tex* found=0;for(auto &x:textures)',
    ' if(w==1024&&h==576&&!video)if(FILE* f=menuLog()){static uint64_t lastF=~0ULL;static void* lastT=0;if(lastF!=frames||lastT!=t){lastF=frames;lastT=t;fprintf(f,"f=%llu upload1x t=%p %dx%d fmt=%04x hi=%d\\n",(unsigned long long)frames,t,w,h,fmt,hsrc?1:0);fflush(f);}}\n'
    ' Tex* found=0;for(auto &x:textures)')
p.write_text(s, 'utf-8')
b = Path(r'F:\AI\gclx-4k\engine\merge_1101\build.cmd').read_text('utf-8')
Path(r'F:\AI\gclx-4k\engine\merge_1101\build_diag.cmd').write_text(b.replace(r'merge_1101\src', r'merge_1101\diag_src').replace(r'merge_1101\build', r'merge_1101\diag_build'), 'utf-8')
print('ok')
