"""시험 전용 N2HD_TEST_NATIVE: 4K 갈고리 없이 게임 원래 1024x576 렌더러로 돌리고 프레임 간격만 잰다(4K 모드와 견주기). 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\runtime_hooks.cpp'); s = p.read_text('utf-8')


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:70], s.count(old))
    s = s.replace(old, new)


rep('#include <tmmintrin.h>\n', '#include <tmmintrin.h>\n#include <d3d9.h>\n#include <cstdio>\n')
rep('static void patchSlot(uintptr_t at,void* fn){', r'''// Test runs only: N2HD_TEST_NATIVE=1 leaves the game's own 1024x576 renderer in place (no 4K hooks) and times its
// Present calls into native.log, to compare frame pacing with the 4K mode (Direct3DCreate9 IAT 0x511354, then the
// IDirect3D9::CreateDevice and IDirect3DDevice9::Present vtable slots).
typedef IDirect3D9* (WINAPI* NatCreate9)(UINT);static NatCreate9 natRealCreate9;
typedef HRESULT (WINAPI* NatCreateDev)(IDirect3D9*,UINT,D3DDEVTYPE,HWND,DWORD,D3DPRESENT_PARAMETERS*,IDirect3DDevice9**);static NatCreateDev natRealCreateDev;
typedef HRESULT (WINAPI* NatPresent)(IDirect3DDevice9*,const RECT*,const RECT*,HWND,const RGNDATA*);static NatPresent natRealPresent;
static uint64_t natFrames,natHist[6];static LARGE_INTEGER natLast,natFreq;static DWORD natLastLog;
static void natPatchVtbl(void** vt,int idx,void* fn,void** orig){DWORD old;if(VirtualProtect(&vt[idx],4,PAGE_READWRITE,&old)){*orig=vt[idx];vt[idx]=fn;VirtualProtect(&vt[idx],4,old,&old);}}
static HRESULT WINAPI natPresent(IDirect3DDevice9* d,const RECT* a,const RECT* b,HWND w,const RGNDATA* r){HRESULT hr=natRealPresent(d,a,b,w,r);LARGE_INTEGER now;QueryPerformanceCounter(&now);
 if(!natFreq.QuadPart)QueryPerformanceFrequency(&natFreq);++natFrames;
 if(natLast.QuadPart){double ms=(now.QuadPart-natLast.QuadPart)*1000.0/natFreq.QuadPart;++natHist[ms<12?0:ms<20?1:ms<35?2:ms<50?3:ms<100?4:5];}natLast=now;
 DWORD t=GetTickCount();if(t-natLastLog>=10000){natLastLog=t;char path[MAX_PATH];wsprintfA(path,"%s\\native.log",profileDir);FILE* f=fopen(path,"a");
  if(f){fprintf(f,"stat t=%lu presents=%llu hist<12/20/35/50/100/+=%llu/%llu/%llu/%llu/%llu/%llu\n",t,(unsigned long long)natFrames,(unsigned long long)natHist[0],(unsigned long long)natHist[1],(unsigned long long)natHist[2],(unsigned long long)natHist[3],(unsigned long long)natHist[4],(unsigned long long)natHist[5]);fclose(f);}}
 return hr;}
static HRESULT WINAPI natCreateDev(IDirect3D9* self,UINT a,D3DDEVTYPE t,HWND w,DWORD f,D3DPRESENT_PARAMETERS* pp,IDirect3DDevice9** out){HRESULT hr=natRealCreateDev(self,a,t,w,f,pp,out);
 if(SUCCEEDED(hr)&&out&&*out&&!natRealPresent)natPatchVtbl(*(void***)*out,17,(void*)natPresent,(void**)&natRealPresent);return hr;}
static IDirect3D9* WINAPI natCreate9(UINT v){IDirect3D9* d=natRealCreate9(v);if(d&&!natRealCreateDev)natPatchVtbl(*(void***)d,16,(void*)natCreateDev,(void**)&natRealCreateDev);return d;}
static void patchSlot(uintptr_t at,void* fn){''')
rep('loadPrivateFonts();redirectProfileForTests();noPowerThrottling();\n',
    'loadPrivateFonts();redirectProfileForTests();noPowerThrottling();\n'
    ' if(profileDir[0]&&GetEnvironmentVariableA("N2HD_TEST_NATIVE",0,0)){natRealCreate9=*(NatCreate9*)0x511354;patchSlot(0x511354,(void*)&natCreate9);state=2;return 1;}\n')
p.write_text(s, 'utf-8')
r = Path(r'F:\AI\gclx-4k\tools\run_test.py'); t = r.read_text('utf-8')
t = t.replace("    ap.add_argument('--keep-throttle',", "    ap.add_argument('--native', action='store_true', help='4K 없이 원래 1024x576 렌더러(프레임 간격만 native.log)')\n    ap.add_argument('--keep-throttle',", 1)
t = t.replace("    if a.keep_throttle:\n", "    if a.native:\n        lines.append('set N2HD_TEST_NATIVE=1')\n    if a.keep_throttle:\n", 1)
r.write_text(t, 'utf-8')
print('ok', 'N2HD_TEST_NATIVE' in t)
