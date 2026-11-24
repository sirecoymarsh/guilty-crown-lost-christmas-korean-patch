#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include <stdint.h>
#include <cstring>
#include <vector>
#include <set>
#include <string>
#include <intrin.h>
#include <tmmintrin.h>
#include <d3d9.h>
#include <cstdio>
#include "media_backend.h"
extern "C" {
int __cdecl N2HD_Init();
void __cdecl N2HD_BacklogBegin();
void __cdecl N2HD_BacklogEnd();
int __cdecl N2HD_BacklogGlyph(void*,int,int,const unsigned short*);
void __cdecl N2HD_PrepareMovie(const char*);
void __cdecl N2HD_Draw(void*,void*,void*);
void __cdecl N2HD_AfterDraw(void*,void*,void*);
void __cdecl N2HD_Clear();
void __cdecl N2HD_End();
int __cdecl N2HD_Present();
void __cdecl N2HD_RecordTexture(void*);
void __cdecl N2HD_Glyph(void*,void*,void*,int,unsigned);
void __cdecl N2HD_CopyGlyph(void*,void*,int,int,unsigned);
void __cdecl N2HD_CopyGlyphMain(void*,void*,int,int,unsigned);
void __cdecl N2HD_Movie(void*);
void __cdecl N2HD_MovieFrame(void*);
void __cdecl N2HD_Capture(void*,int*);
}
static void* origDraw;static void* origFiltered;static void* origGlyph;static void* origCreate;static void* origDestroy;static void* origRuby;static void* origCopy;static void* origClear;static void* origPresent0;static void* origPresent1;static void* origPresent2;static void* origPresent3;static void* origMovie;static void* origSample;static void* origCapture;
static unsigned __cdecl hookDraw(void* o,void* a){N2HD_Draw(o,a,0);unsigned result=((unsigned(__cdecl*)(void*,void*))origDraw)(o,a);N2HD_AfterDraw(o,a,0);return result;}
static unsigned __cdecl hookFiltered(void* o,void* a,void* f){N2HD_Draw(o,a,f);unsigned result=((unsigned(__cdecl*)(void*,void*,void*))origFiltered)(o,a,f);N2HD_AfterDraw(o,a,f);return result;}
static unsigned __cdecl hookGlyph(void* font,void* gm,void* bits,int width,unsigned c){unsigned result=((unsigned(__cdecl*)(void*,void*,void*,int,unsigned))origGlyph)(font,gm,bits,width,c);if(result==1)N2HD_Glyph(font,gm,bits,width,c);return result;}
static unsigned __cdecl hookDestroy(void** p){if(p&&*p)N2HD_RecordTexture(*p);return ((unsigned(__cdecl*)(void**))origDestroy)(p);}
static void __cdecl hookClear(){N2HD_Clear();((void(__cdecl*)())origClear)();}
static void clampPresentationRect(){int* p=(int*)0x62949c;if(p[0]+p[1]+p[2]+p[3]==-4)return;if(p[0]<0)p[0]=0;if(p[1]<0)p[1]=0;if(p[2]>1024)p[2]=1024;if(p[3]>576)p[3]=576;}
static void __cdecl hookPresent0(){clampPresentationRect();N2HD_End();if(!N2HD_Present())((void(__cdecl*)())origPresent0)();}
static void __cdecl hookPresent1(){clampPresentationRect();N2HD_End();if(!N2HD_Present())((void(__cdecl*)())origPresent1)();}
static void __cdecl hookPresent2(){clampPresentationRect();N2HD_End();if(!N2HD_Present())((void(__cdecl*)())origPresent2)();}
static void __cdecl hookPresent3(){clampPresentationRect();N2HD_End();if(!N2HD_Present())((void(__cdecl*)())origPresent3)();}
static const char* __cdecl resolveMovie(const char* name){N2HD_PrepareMovie(name);return name;}
__declspec(naked) static void hookCreate(){__asm {
 push [esp+12]
 push [esp+12]
 push [esp+12]
 call dword ptr [origCreate]
 add esp,12
 pushfd
 pushad
 push eax
 call N2HD_RecordTexture
 add esp,4
 popad
 popfd
 ret
}}
__declspec(naked) static void hookMovie(){__asm {
 pushfd
 pushad
 push dword ptr [esp+28]
 call resolveMovie
 add esp,4
 mov [esp+28],eax
 popad
 popfd
 push [esp+12]
 push [esp+12]
 push [esp+12]
 call dword ptr [origMovie]
 add esp,12
 pushfd
 pushad
 push eax
 call N2HD_Movie
 add esp,4
 popad
 popfd
 ret
}}
__declspec(naked) static void hookRuby(){__asm {
 pushfd
 pushad
 mov eax,esp
 push [eax+52]
 push [eax+28]
 push [eax+48]
 push [eax+44]
 push [eax+40]
 call N2HD_CopyGlyph
 add esp,20
 popad
 popfd
 jmp dword ptr [origRuby]
}}
__declspec(naked) static void hookCopy(){__asm {
 pushfd
 pushad
 mov eax,esp
 push [eax+52]
 push [eax+20]
 push [eax+48]
 push [eax+44]
 push [eax+40]
 call N2HD_CopyGlyphMain
 add esp,20
 popad
 popfd
 jmp dword ptr [origCopy]
}}
static unsigned __cdecl hookCapture(void* o,void* a,void* f,int* p){N2HD_Capture(o,p);return ((unsigned(__cdecl*)(void*,void*,void*,int*))origCapture)(o,a,f,p);}
static uint64_t movieStats[8]={};
static void* lastRenderer;static LONGLONG lastTime=-1;
static bool convertHdFrame(void* renderer,void* sample){
 if(!renderer||!sample||*(int*)((char*)renderer+0x258)!=3840||*(int*)((char*)renderer+0x260)!=0)return false;
 void*** v=(void***)sample;unsigned char* source=0;typedef HRESULT(__stdcall* GetPointer)(void*,unsigned char**);typedef long(__stdcall* GetSize)(void*);if(FAILED(((GetPointer)(*v)[3])(sample,&source))||!source)return false;int h=*(int*)((char*)renderer+0x25c),w=3840;if(h!=2160||((GetSize)(*v)[4])(sample)<w*h*3)return false;auto rows=*(uint32_t***)((char*)renderer+0x26c);if(!rows)return false;
 static const bool ssse3=[](){int cpu[4];__cpuid(cpu,1);return (cpu[2]&(1<<9))!=0;}();const __m128i mask=_mm_setr_epi8(0,1,2,-1,3,4,5,-1,6,7,8,-1,9,10,11,-1),alpha=_mm_set1_epi32(0xff000000);
 for(int y=0;y<h;++y){const unsigned char* src=source+(h-1-y)*w*3;uint32_t* dst=rows[y];int x=0;if(ssse3)for(;x+4<w;x+=4){__m128i packed=_mm_loadu_si128((const __m128i*)(src+x*3));packed=_mm_or_si128(_mm_shuffle_epi8(packed,mask),alpha);_mm_storeu_si128((__m128i*)(dst+x),packed);}for(;x<w;++x)dst[x]=0xff000000|src[x*3]|(src[x*3+1]<<8)|(src[x*3+2]<<16);}
 *(int*)((char*)renderer+0x268)=1;return true;
}
static unsigned __stdcall hookSample(void* renderer,void* sample){
 if(renderer&&sample){int width=*(int*)((char*)renderer+0x258);if(width==3840||N2HD_HasVideo(*(void**)((char*)renderer+0x254))){typedef HRESULT(__stdcall* GetTime)(void*,LONGLONG*,LONGLONG*);LONGLONG start=0,end=0;auto get=(GetTime)(*(void***)sample)[5];if(SUCCEEDED(get(sample,&start,&end))){N2HD_VideoTime(*(void**)((char*)renderer+0x254),start);if(renderer==lastRenderer&&start==lastTime)return 0;if(renderer!=lastRenderer||start<lastTime)memset(movieStats,0,sizeof(movieStats));lastRenderer=renderer;lastTime=start;if(!movieStats[2]||movieStats[4]!=(uint64_t)start){if(!movieStats[2]){movieStats[0]=3840;movieStats[1]=2160;movieStats[3]=start;movieStats[5]=GetTickCount64();}++movieStats[2];movieStats[4]=start;movieStats[6]=GetTickCount64();movieStats[7]=end;}}}}
 unsigned result=0;if(!convertHdFrame(renderer,sample))result=((unsigned(__stdcall*)(void*,void*))origSample)(renderer,sample);if(renderer&&*(int*)((char*)renderer+0x258)==3840)N2HD_MovieFrame(*(void**)((char*)renderer+0x254));return result;
}
extern "C" __declspec(dllexport) void __cdecl N2HD_MovieStats(uint64_t* out){memcpy(out,movieStats,sizeof(movieStats));}
static void* origBacklog;static void* origBacklogGlyph;static void* origBacklogSpace;
static void* backlogSpaceResume=(void*)0x403bed;
static unsigned __cdecl hookBacklog(){N2HD_BacklogBegin();unsigned r=((unsigned(__cdecl*)())origBacklog)();if(r)N2HD_BacklogEnd();return r;}
__declspec(naked) static void hookBacklogSpace(){__asm {
 mov edx,0xa1a1
 jmp dword ptr [backlogSpaceResume]
}}
__declspec(naked) static void hookBacklogGlyph(){__asm {
 cmp dword ptr [esp],0x403e79
 jne original
 pushfd
 pushad
 mov eax,esp
 push [eax+8]
 push [eax+44]
 push [eax+28]
 push [eax+40]
 call N2HD_BacklogGlyph
 add esp,16
 mov [esp+28],eax
 popad
 popfd
original:
 jmp dword ptr [origBacklogGlyph]
}}
static void bgmKeepAfterLoad(bool restart);static void bgmKeepSelect();static void bgmKeepClear();   // bgm_keep.inc (Claude 11-24)
#include "backlog_jump.inc"
struct Hook {uintptr_t address;void* replacement;void** original;unsigned size;unsigned char expected[16];void* trampoline;DWORD oldProtection;};
// Claude 10-26: 4x art and bundled fonts.
extern "C" void __cdecl N2HD_ImageLoaded(const char*,void*);
extern "C" void __cdecl N2HD_LoadBegin();
static void* origLoadImage;
#include "img_cache.inc"
#include "fast_png.inc"
// 0x467990: the picture loader; the file name comes in eax, the picture goes back in eax, no stack arguments.
__declspec(naked) static void hookLoadImage(){__asm {
 pushfd
 pushad
 push eax
 call imgBegin
 add esp,4
 popad
 popfd
 push eax
 call dword ptr [origLoadImage]
 pushfd
 pushad
 push eax
 push dword ptr [esp+40]
 call N2HD_ImageLoaded
 add esp,8
 call imgEnd
 popad
 popfd
 add esp,4
 ret
}}
// The choice hit test (hit_zoom.inc): 0x452715, inside the loop over a button's MouseUsual pictures; edx is the picture,
// [esp+0x20] the list node, [esp+0x24] the event with the pointer at +0x28/+0x2c. A hit goes on at 0x45282f, a miss at 0x4527ad.
extern "C" int __cdecl N2HD_HitTest(void*,int,int,void*);
static void* origHitTest;static void* hitYes=(void*)0x45282f;static void* hitNo=(void*)0x4527ad;
__declspec(naked) static void hookHitTest(){__asm {
 mov eax,dword ptr [esp+0x24]
 mov ecx,dword ptr [esp+0x20]
 push ecx
 push dword ptr [eax+0x2c]
 push dword ptr [eax+0x28]
 push edx
 call N2HD_HitTest
 add esp,16
 test eax,eax
 jnz yes
 jmp dword ptr [hitNo]
yes:
 jmp dword ptr [hitYes]
}}
// The engine's PNG and JPEG decoders (see img_cache.inc).
static void* origPng;static void* origJpg;
static int __cdecl hookPng(void* t,void* file){ImgCache::init();if(ImgCache::fill(t))return 1;
 int r=0;const int fm=FastPng::mode();
 if(fm==2){unsigned char test[0x480]={};double a=ImgCache::now();bool fast=FastPng::decode(test,file);double b=ImgCache::now();r=((int(__cdecl*)(void*,void*))origPng)(t,file);double c=ImgCache::now();
  if(fast){if(r)FastPng::compare(t,test,c-b,b-a);else HeapFree(GetProcessHeap(),0,*(void**)(test+0x28));}}
 else{if(fm==1&&FastPng::decode(t,file))r=1;else r=((int(__cdecl*)(void*,void*))origPng)(t,file);}
 if(r){if(ImgCache::mode==2)ImgCache::observe("png",t);else if(ImgCache::mode==3)ImgCache::verify(t);else ImgCache::store(t);}return r;}
static int __cdecl jpgFill(void* t){ImgCache::init();return ImgCache::fill(t);}
static void __cdecl jpgAfter(void* t,int r){if(r){if(ImgCache::mode==2)ImgCache::observe("jpg",t);else if(ImgCache::mode==3)ImgCache::verify(t);else ImgCache::store(t);}}
// 0x469b20 (the JPEG decoder, tried first): the file in edx (kept for the call), the picture at [esp+4].
__declspec(naked) static void hookJpg(){__asm {
 sub esp,4
 pushad
 push dword ptr [esp+40]
 call jpgFill
 add esp,4
 mov [esp+32],eax
 popad
 cmp dword ptr [esp],0
 lea esp,[esp+4]
 jz miss
 mov eax,1
 ret
miss:
 push dword ptr [esp+4]
 call dword ptr [origJpg]
 add esp,4
 pushad
 push eax
 push dword ptr [esp+40]
 call jpgAfter
 add esp,8
 popad
 ret
}}
// Fonts the scripts name but Windows may not have (Noto Sans KR / Noto Serif KR): <game>\fonts\*.ttf|otf|ttc, private to
// this process. Added before the game's main thread runs (the launcher installs the hooks on a suspended process).
static void loadPrivateFonts(){wchar_t dir[MAX_PATH];if(!GetModuleFileNameW(0,dir,MAX_PATH))return;wchar_t* s=wcsrchr(dir,L'\\');if(!s)return;s[1]=0;
 wchar_t pattern[MAX_PATH];wsprintfW(pattern,L"%sfonts\\*",dir);WIN32_FIND_DATAW fd;HANDLE h=FindFirstFileW(pattern,&fd);if(h==INVALID_HANDLE_VALUE)return;
 do{const wchar_t* e=wcsrchr(fd.cFileName,L'.');if(e&&(!lstrcmpiW(e,L".ttf")||!lstrcmpiW(e,L".otf")||!lstrcmpiW(e,L".ttc"))){wchar_t path[MAX_PATH];wsprintfW(path,L"%sfonts\\%s",dir,fd.cFileName);int added=AddFontResourceExW(path,FR_PRIVATE,0);
  wchar_t logDir[MAX_PATH];if(GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",logDir,MAX_PATH)){wchar_t logPath[MAX_PATH];wsprintfW(logPath,L"%s\\fonts.log",logDir);CreateDirectoryW(logDir,0);
   HANDLE lf=CreateFileW(logPath,FILE_APPEND_DATA,FILE_SHARE_READ,0,OPEN_ALWAYS,0,0);if(lf!=INVALID_HANDLE_VALUE){char line[600];int n=wsprintfA(line,"%ls added=%d\r\n",fd.cFileName,added);DWORD w;WriteFile(lf,line,n,&w,0);CloseHandle(lf);}}}}
 while(FindNextFileW(h,&fd));FindClose(h);}
// Test runs only (Claude): with N2HD_PROFILE_DIR set, the game's SHGetFolderPathA (IAT 0x511264; it puts its saves under
// that folder) answers that directory instead, so a hidden test never writes into the user's own profile.
static char profileDir[MAX_PATH];
static HRESULT WINAPI testFolderPath(HWND,int,HANDLE,DWORD,LPSTR path){if(!path)return E_INVALIDARG;lstrcpynA(path,profileDir,MAX_PATH);CreateDirectoryA(profileDir,0);return S_OK;}
// Also for test runs: the engine pauses its script while GetForegroundWindow is not its window, and takes the
// foreground itself. In test mode it is told its window is in front and never takes the user's foreground.
static HWND WINAPI testForeground(){HWND h=*(HWND*)0x629854;return h?h:GetDesktopWindow();}
static BOOL WINAPI testSetForeground(HWND){return TRUE;}
static HWND WINAPI testSetActive(HWND h){return h;}
// And the face each requested font really gets (CreateFontIndirectA, IAT 0x511048), once per pair, in fonts.log:
// whether a script's "Noto Serif KR" resolves to the bundled file or to a Windows substitute.
static HFONT WINAPI testCreateFont(const LOGFONTA* lf){HFONT f=CreateFontIndirectA(lf);if(!f||!lf)return f;static std::set<std::string> seen;
 HDC dc=CreateCompatibleDC(0);HGDIOBJ old=SelectObject(dc,f);char got[LF_FACESIZE]={};GetTextFaceA(dc,LF_FACESIZE,got);SelectObject(dc,old);DeleteDC(dc);
 std::string key=std::string(lf->lfFaceName)+"\t"+got;if(!seen.insert(key).second)return f;
 char logPath[MAX_PATH];wsprintfA(logPath,"%s\\fonts.log",profileDir);HANDLE h=CreateFileA(logPath,FILE_APPEND_DATA,FILE_SHARE_READ,0,OPEN_ALWAYS,0,0);
 if(h!=INVALID_HANDLE_VALUE){char line[200];int n=wsprintfA(line,"font want=%s got=%s\r\n",lf->lfFaceName,got);DWORD w;WriteFile(h,line,n,&w,0);CloseHandle(h);}return f;}
// And which archives and save files the game opens (CreateFileA, IAT 0x511188), once per path, in files.log.
#include "lyric_save_view.inc"
static HANDLE WINAPI testCreateFile(LPCSTR name,DWORD access,DWORD share,LPSECURITY_ATTRIBUTES sa,DWORD disp,DWORD flags,HANDLE tmpl){HANDLE r=LyricSave::view(name,access,share,sa,disp,flags,tmpl);
 static std::set<std::string> seen;if(name&&seen.insert(name).second){char logPath[MAX_PATH];wsprintfA(logPath,"%s\\files.log",profileDir);HANDLE h=CreateFileA(logPath,FILE_APPEND_DATA,FILE_SHARE_READ,0,OPEN_ALWAYS,0,0);
  if(h!=INVALID_HANDLE_VALUE){char line[600];int n=wsprintfA(line,"%s %s\r\n",r==INVALID_HANDLE_VALUE?"FAIL":"ok",name);DWORD w;WriteFile(h,line,n,&w,0);CloseHandle(h);}}return r;}
// Windows 11 throttles a process none of whose windows is visible (EcoQoS: slower cores; coarse timer resolution, and
// the engine paces frames with winmm timers and waits). Opt out, so a game window behind others or a hidden test window
// runs like a front one.
static void noPowerThrottling(){if(GetEnvironmentVariableA("N2HD_TEST_KEEP_THROTTLE",0,0))return;PROCESS_POWER_THROTTLING_STATE st{PROCESS_POWER_THROTTLING_CURRENT_VERSION,PROCESS_POWER_THROTTLING_EXECUTION_SPEED|PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION,0};
 SetProcessInformation(GetCurrentProcess(),ProcessPowerThrottling,&st,sizeof st);}
// Test runs only: N2HD_TEST_NATIVE=1 leaves the game's own 1024x576 renderer in place (no 4K hooks) and times its
// Present calls into native.log, to compare frame pacing with the 4K mode (Direct3DCreate9 IAT 0x511354, then the
// IDirect3D9::CreateDevice and IDirect3DDevice9::Present vtable slots).
typedef IDirect3D9* (WINAPI* NatCreate9)(UINT);static NatCreate9 natRealCreate9;
typedef HRESULT (WINAPI* NatCreateDev)(IDirect3D9*,UINT,D3DDEVTYPE,HWND,DWORD,D3DPRESENT_PARAMETERS*,IDirect3DDevice9**);static NatCreateDev natRealCreateDev;
typedef HRESULT (WINAPI* NatPresent)(IDirect3DDevice9*,const RECT*,const RECT*,HWND,const RGNDATA*);static NatPresent natRealPresent;
static uint64_t natFrames,natHist[6];static LARGE_INTEGER natLast,natFreq;static DWORD natLastLog;
static void natPatchVtbl(void** vt,int idx,void* fn,void** orig){DWORD old;if(VirtualProtect(&vt[idx],4,PAGE_READWRITE,&old)){*orig=vt[idx];vt[idx]=fn;VirtualProtect(&vt[idx],4,old,&old);}}
static void natFrame();
// Claude 11-21, test only (N2HD_PROFILE_DIR + N2HD_TEST_FRAMES=1): every shown frame's wall time (Unix seconds, double)
// into frames.bin, for both renderers (the original one presents by GDI BitBlt, which PresentMon does not see).
extern "C" void __cdecl N2HD_TestFrameStamp(){static int on=-1;static FILE* f;static unsigned n;
 if(on<0){on=profileDir[0]&&GetEnvironmentVariableA("N2HD_TEST_FRAMES",0,0)?1:0;if(on){char p[MAX_PATH];wsprintfA(p,"%s\\frames.bin",profileDir);f=fopen(p,"ab");if(!f)on=0;}}
 if(!on)return;FILETIME ft;GetSystemTimePreciseAsFileTime(&ft);double t=((((uint64_t)ft.dwHighDateTime<<32)|ft.dwLowDateTime)-116444736000000000ull)/1e7;
 fwrite(&t,8,1,f);if(!(++n&31))fflush(f);}
static HRESULT WINAPI natPresent(IDirect3DDevice9* d,const RECT* a,const RECT* b,HWND w,const RGNDATA* r){HRESULT hr=natRealPresent(d,a,b,w,r);natFrame();return hr;}
extern "C" void __cdecl N2HD_TestTick();extern "C" void __cdecl N2HD_TestNativeFrame(double);
static void natFrame(){N2HD_TestTick();N2HD_TestFrameStamp();LARGE_INTEGER now;QueryPerformanceCounter(&now);
 if(!natFreq.QuadPart)QueryPerformanceFrequency(&natFreq);++natFrames;
 if(natLast.QuadPart){double ms=(now.QuadPart-natLast.QuadPart)*1000.0/natFreq.QuadPart;N2HD_TestNativeFrame(ms);++natHist[ms<12?0:ms<20?1:ms<35?2:ms<50?3:ms<100?4:5];}natLast=now;
 DWORD t=GetTickCount();if(t-natLastLog>=10000){natLastLog=t;char path[MAX_PATH];wsprintfA(path,"%s\\native.log",profileDir);FILE* f=fopen(path,"a");
  if(f){fprintf(f,"stat t=%lu presents=%llu hist<12/20/35/50/100/+=%llu/%llu/%llu/%llu/%llu/%llu\n",t,(unsigned long long)natFrames,(unsigned long long)natHist[0],(unsigned long long)natHist[1],(unsigned long long)natHist[2],(unsigned long long)natHist[3],(unsigned long long)natHist[4],(unsigned long long)natHist[5]);fclose(f);}}}
// The original renderer draws in software and shows each frame with a full-window BitBlt (IAT 0x511030).
static BOOL WINAPI natBitBlt(HDC d,int x,int y,int w,int h,HDC src,int sx,int sy,DWORD rop){BOOL r=BitBlt(d,x,y,w,h,src,sx,sy,rop);if(w>=640&&h>=360)natFrame();else if(w>0&&h>0)N2HD_TestFrameStamp();return r;}   // smaller copies: partial screen updates (the original backlog), stamped for the test only
static HRESULT WINAPI natCreateDev(IDirect3D9* self,UINT a,D3DDEVTYPE t,HWND w,DWORD f,D3DPRESENT_PARAMETERS* pp,IDirect3DDevice9** out){HRESULT hr=natRealCreateDev(self,a,t,w,f,pp,out);
 if(SUCCEEDED(hr)&&out&&*out&&!natRealPresent)natPatchVtbl(*(void***)*out,17,(void*)natPresent,(void**)&natRealPresent);return hr;}
static IDirect3D9* WINAPI natCreate9(UINT v){IDirect3D9* d=natRealCreate9(v);if(d&&!natRealCreateDev)natPatchVtbl(*(void***)d,16,(void*)natCreateDev,(void**)&natRealCreateDev);return d;}
static void patchSlot(uintptr_t at,void* fn){void** slot=(void**)at;DWORD old;if(VirtualProtect(slot,4,PAGE_READWRITE,&old)){*slot=fn;VirtualProtect(slot,4,old,&old);}}
extern "C" void __cdecl N2HD_TestCursorInit();
static void redirectProfileForTests(){if(!GetEnvironmentVariableA("N2HD_PROFILE_DIR",profileDir,MAX_PATH)||!profileDir[0]){patchSlot(0x511188,(void*)&LyricSave::view);return;}
 patchSlot(0x511264,(void*)&testFolderPath);patchSlot(0x51128c,(void*)&testForeground);patchSlot(0x5112a4,(void*)&testSetForeground);patchSlot(0x511320,(void*)&testSetActive);
 patchSlot(0x511048,(void*)&testCreateFont);patchSlot(0x511188,(void*)&testCreateFile);}
// Only the render deadline changes. Preserve the native speed selection, event wait,
// timeGetTime clock, and all script/audio/animation duration calculations.
// [Display] FrameRate=60 in n2hd-options.ini restores the original deadline.
static void* origFramePeriod;
static void* framePeriodResume=(void*)0x490cc9;
static double framePeriodScale=0.5;
static bool idleHalf=true;
static void loadFrameRate(){wchar_t path[MAX_PATH];if(!GetModuleFileNameW(0,path,MAX_PATH))return;
 wchar_t* tail=wcsrchr(path,L'\\');if(!tail||tail-path+19>=MAX_PATH)return;
 lstrcpyW(tail+1,L"n2hd-options.ini");
 framePeriodScale=GetPrivateProfileIntW(L"Display",L"FrameRate",120,path)==60?1.0:0.5;
 // Claude 11-02: the engine's other wait, taken on a tick with nothing to draw (0x44d85e), still slept the native 16 ms,
 // so script-driven effects (embers, falling text) showed on a 16 ms grid and the present rate fell to 17-40 fps there.
 // Halve it with the render deadline. [Display] IdleHalf=0 keeps the native idle wait.
 idleHalf=framePeriodScale<1.0&&GetPrivateProfileIntW(L"Display",L"IdleHalf",1,path)!=0;
 {wchar_t v[8];if(GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",0,0)&&GetEnvironmentVariableW(L"N2HD_TEST_IDLEHALF",v,8))idleHalf=framePeriodScale<1.0&&_wtoi(v)!=0;}
}
// Claude 11-21: config page 3 (sys_config.nss) loads nss/kr_cmd_<q0|q1|q2|f60|f120|get>.png through the picture loader
// (CreateTexture runs it on the script thread); the name is the command. The answer goes into the script's own
// #KR_quality (0 4K, 1 4K text with 1x art, 2 original) and #KR_fps (120 or 60), which the page sets to numbers first.
extern "C" void __cdecl N2HD_SetQuality(int q);
extern "C" int __cdecl N2HD_GetQuality();
static void setFrameRate(int fps){wchar_t path[MAX_PATH];if(!GetModuleFileNameW(0,path,MAX_PATH))return;wchar_t* tail=wcsrchr(path,L'\\');if(!tail||tail-path+19>=MAX_PATH)return;
 lstrcpyW(tail+1,L"n2hd-options.ini");framePeriodScale=fps==60?1.0:0.5;
 idleHalf=framePeriodScale<1.0&&GetPrivateProfileIntW(L"Display",L"IdleHalf",1,path)!=0;
 WritePrivateProfileStringW(L"Display",L"FrameRate",fps==60?L"60":L"120",path);}
static void krConfigCommand(const char* name){if(!name)return;const char* p=strstr(name,"kr_cmd_");if(!p)return;p+=7;
 if(!strncmp(p,"q0.",3))N2HD_SetQuality(0);else if(!strncmp(p,"q1.",3))N2HD_SetQuality(1);else if(!strncmp(p,"q2.",3))N2HD_SetQuality(2);
 else if(!strncmp(p,"f60.",4))setFrameRate(60);else if(!strncmp(p,"f120.",5))setFrameRate(120);
 else if(!strncmp(p,"trace",5)){   // test only (N2HD_PROFILE_DIR): trace.log gets the marker and the script's $GameName
  if(!profileDir[0])return;auto v=Jump::var("$GameName");const char* g=v&&v[0]==1?(const char*)v+0x98:"?";char line[400],path[MAX_PATH];
  wsprintfA(line,"%lu %.40s %.200s\r\n",GetTickCount(),p,g);wsprintfA(path,"%s\\trace.log",profileDir);
  HANDLE h=CreateFileA(path,FILE_APPEND_DATA,FILE_SHARE_READ,0,OPEN_ALWAYS,0,0);if(h!=INVALID_HANDLE_VALUE){DWORD w;WriteFile(h,line,lstrlenA(line),&w,0);CloseHandle(h);}return;}
 else if(strncmp(p,"get.",4))return;
 auto put=[](const char* n,double x){auto v=Jump::var(n);if(v&&v[0]!=1)*(double*)(v+0x10)=x;};
 put("#KR_quality",(double)N2HD_GetQuality());put("#KR_fps",framePeriodScale<1.0?120.0:60.0);}
__declspec(naked) static void hookFramePeriod(){__asm {
 fidivr dword ptr [ecx*4+0x6294b4]
 fmul qword ptr [framePeriodScale]
 jmp dword ptr [framePeriodResume]
}}
static void* origIdlePeriod;
static void* idlePeriodResume=(void*)0x44d866;
__declspec(naked) static void hookIdlePeriod(){__asm {
 mov eax,dword ptr [edx*4+0x6294b4]
 cmp byte ptr [idleHalf],0
 je keep
 shr eax,1
 jnz keep
 inc eax
keep:
 push eax
 jmp dword ptr [idlePeriodResume]
}}
#include "script_locks.inc"
#include "bgm_keep.inc"
#include "native_hook_manifest.h"
#include "window_resize.inc"
#include "dsb_trace.inc"
// The EXE must be the known release (SHA-256). The large-address-aware bit is ignored: with it the game gets 4 GB of
// address space instead of 2 GB, which the 4K text surfaces (38 MB blocks each) and the backlog need (10-27: the
// backlog crashed the game with std::bad_alloc when the biggest free block was 44-48 MB).
static bool validImage(){wchar_t path[32768];if(!GetModuleFileNameW(0,path,32768))return false;HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ,0,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,0);if(file==INVALID_HANDLE_VALUE)return false;BCRYPT_ALG_HANDLE alg=0;BCRYPT_HASH_HANDLE hash=0;unsigned char digest[32];bool ok=BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,0,0)>=0&&BCryptCreateHash(alg,&hash,0,0,0,0,0)>=0;unsigned char buffer[65536];DWORD count=0;bool first=true;while(ok){if(!ReadFile(file,buffer,sizeof(buffer),&count,0)){ok=false;break;}if(!count)break;if(first){first=false;if(count>0x40){DWORD e=*(DWORD*)(buffer+0x3c);if(e+0x18<count&&*(DWORD*)(buffer+e)==0x4550)buffer[e+4+18]&=~0x20;}}if(BCryptHashData(hash,buffer,count,0)<0)ok=false;}if(ok)ok=BCryptFinishHash(hash,digest,32,0)>=0;if(hash)BCryptDestroyHash(hash);if(alg)BCryptCloseAlgorithmProvider(alg,0);CloseHandle(file);static const unsigned char expected[32]={0xf8,0x44,0xac,0x46,0x76,0x01,0x05,0x8a,0x78,0x8f,0x27,0x68,0x3f,0xdb,0x95,0x00,0xc6,0x12,0xe5,0xaa,0x9b,0xdb,0x01,0x32,0x86,0xb8,0x80,0x5f,0x6f,0x67,0x06,0xbd};return ok&&!memcmp(expected,digest,32);}
static void jump(void* at,void* to){unsigned char* p=(unsigned char*)at;p[0]=0xe9;*(uint32_t*)(p+1)=(uint32_t)((uintptr_t)to-(uintptr_t)p-5);}
extern "C" __declspec(dllexport) int __cdecl N2HD_Install(){static LONG state=0;if(InterlockedCompareExchange(&state,1,0))return state==2;if((uintptr_t)GetModuleHandleW(0)!=0x400000||!validImage()){state=-1;return 0;}loadPrivateFonts();redirectProfileForTests();N2HD_TestCursorInit();Win::install();noPowerThrottling();loadFrameRate();
 if(profileDir[0]&&GetEnvironmentVariableA("N2HD_TEST_NATIVE",0,0)){natRealCreate9=*(NatCreate9*)0x511354;patchSlot(0x511354,(void*)&natCreate9);patchSlot(0x511030,(void*)&natBitBlt);
  for(auto &h:hooks)if(h.address==0x467990&&!memcmp((void*)h.address,h.expected,h.size)){h.trampoline=VirtualAlloc(0,h.size+5,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);if(!h.trampoline)break;memcpy(h.trampoline,h.expected,h.size);jump((char*)h.trampoline+h.size,(void*)(h.address+h.size));*h.original=h.trampoline;DWORD old;if(VirtualProtect((void*)h.address,h.size,PAGE_EXECUTE_READWRITE,&old)){jump((void*)h.address,h.replacement);if(h.size>5)memset((char*)h.address+5,0x90,h.size-5);VirtualProtect((void*)h.address,h.size,old,&old);FlushInstructionCache(GetCurrentProcess(),(void*)h.address,h.size);}}state=2;return 1;}
 for(auto &h:hooks){if(memcmp((void*)h.address,h.expected,h.size)){state=-1;return 0;}h.trampoline=VirtualAlloc(0,h.size+5,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);if(!h.trampoline){state=-1;return 0;}memcpy(h.trampoline,h.expected,h.size);jump((char*)h.trampoline+h.size,(void*)(h.address+h.size));*h.original=h.trampoline;}
 for(auto &h:hooks){if(!VirtualProtect((void*)h.address,h.size,PAGE_EXECUTE_READWRITE,&h.oldProtection)){for(int j=(int)(sizeof(hooks)/sizeof(hooks[0]))-1;j>=0;--j){auto &r=hooks[j];if(r.oldProtection){DWORD old;VirtualProtect((void*)r.address,r.size,r.oldProtection,&old);}}state=-1;return 0;}}
 for(auto &h:hooks){jump((void*)h.address,h.replacement);if(h.size>5)memset((char*)h.address+5,0x90,h.size-5);FlushInstructionCache(GetCurrentProcess(),(void*)h.address,h.size);}for(int i=(int)(sizeof(hooks)/sizeof(hooks[0]))-1;i>=0;--i){auto &h=hooks[i];DWORD old;VirtualProtect((void*)h.address,h.size,h.oldProtection,&old);}lockFixInstall();DsbTrace::install();BgmKeep::install();state=2;return N2HD_Init();}
extern "C" __declspec(dllexport) DWORD WINAPI N2HD_RemoteInstall(void*){return N2HD_Install();}
