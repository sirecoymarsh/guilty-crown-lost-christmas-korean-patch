"""(1) 윈도 11 절전 제한 끄기(EcoQoS·타이머 정밀도), (2) 엔진 1배 그림 읽기 시간, (3) 프레임 간격 분포를 stat 줄에. 한 번만 돌린다."""
from pathlib import Path
src = Path(r'F:\AI\gclx-4k\engine\src')


def patch(name, pairs):
    p = src / name; s = p.read_text('utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (name, old[:70], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, 'utf-8')


patch('runtime_hooks.cpp', [
    ('extern "C" void __cdecl N2HD_ImageLoaded(const char*,void*);',
     'extern "C" void __cdecl N2HD_ImageLoaded(const char*,void*);\nextern "C" void __cdecl N2HD_LoadBegin();'),
    ('__declspec(naked) static void hookLoadImage(){__asm {\n push eax\n call dword ptr [origLoadImage]',
     '__declspec(naked) static void hookLoadImage(){__asm {\n pushfd\n pushad\n call N2HD_LoadBegin\n popad\n popfd\n push eax\n call dword ptr [origLoadImage]'),
    ('static void patchSlot(uintptr_t at,void* fn){',
     '''// Windows 11 throttles a process none of whose windows is visible (EcoQoS: slower cores; coarse timer resolution, and
// the engine paces frames with winmm timers and waits). Opt out, so a game window behind others or a hidden test window
// runs like a front one.
static void noPowerThrottling(){PROCESS_POWER_THROTTLING_STATE st{PROCESS_POWER_THROTTLING_CURRENT_VERSION,PROCESS_POWER_THROTTLING_EXECUTION_SPEED|PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION,0};
 SetProcessInformation(GetCurrentProcess(),ProcessPowerThrottling,&st,sizeof st);}
static void patchSlot(uintptr_t at,void* fn){'''),
    ('loadPrivateFonts();redirectProfileForTests();', 'loadPrivateFonts();redirectProfileForTests();noPowerThrottling();'),
])
patch('hires_art.inc', [
    ('static void* jxlRunner;static FILE* artLog;',
     'static void* jxlRunner;static FILE* artLog;\n// Engine side, for the test log: time inside the engine\'s own picture loader, and frame intervals by bucket.\nstatic LARGE_INTEGER artLoadT0;static LONGLONG artLoadFrame,artLoadTotal,artLoadMax;static uint64_t artFrameHist[6],artLongWithLoad;'),
    ('extern "C" __declspec(dllexport) void __cdecl N2HD_ImageLoaded(const char* name,void* t){Guard guard;PerfScope perf(PF_LOAD);',
     'extern "C" __declspec(dllexport) void __cdecl N2HD_LoadBegin(){QueryPerformanceCounter(&artLoadT0);}\n'
     'extern "C" __declspec(dllexport) void __cdecl N2HD_ImageLoaded(const char* name,void* t){Guard guard;PerfScope perf(PF_LOAD);'
     '{LARGE_INTEGER b;QueryPerformanceCounter(&b);LONGLONG d=b.QuadPart-artLoadT0.QuadPart;if(artLoadT0.QuadPart&&d>0){artLoadFrame+=d;artLoadTotal+=d;if(d>artLoadMax)artLoadMax=d;}}'),
    ('if(last.QuadPart){double ms=(now.QuadPart-last.QuadPart)*1000.0/f.QuadPart;if(ms>50)++artLongFrames50;if(ms>100)++artLongFrames100;}last=now;}',
     'if(last.QuadPart){double ms=(now.QuadPart-last.QuadPart)*1000.0/f.QuadPart;if(ms>50)++artLongFrames50;if(ms>100)++artLongFrames100;'
     '++artFrameHist[ms<12?0:ms<20?1:ms<35?2:ms<50?3:ms<100?4:5];if(ms>50&&artLoadFrame*1000.0/f.QuadPart>25)++artLongWithLoad;}artLoadFrame=0;last=now;}'),
])
patch('n2hd_gpu_v8.cpp', [
    ('upload_ms_max=%llu cache_mb=%llu\\n",now,',
     'upload_ms_max=%llu cache_mb=%llu hist<12/20/35/50/100/+=%llu/%llu/%llu/%llu/%llu/%llu engine_load=%.0f engine_load_max=%.0f long_with_load=%llu\\n",now,'),
    ('(unsigned long long)artUploadMsMax,(unsigned long long)(artCacheBytes>>20));fflush(artLog);}\nstatic void testShot()',
     '(unsigned long long)artUploadMsMax,(unsigned long long)(artCacheBytes>>20),(unsigned long long)artFrameHist[0],(unsigned long long)artFrameHist[1],(unsigned long long)artFrameHist[2],(unsigned long long)artFrameHist[3],(unsigned long long)artFrameHist[4],(unsigned long long)artFrameHist[5],artLoadTotal*f,artLoadMax*f,(unsigned long long)artLongWithLoad);fflush(artLog);}\nstatic void testShot()'),
])
print('ok')
