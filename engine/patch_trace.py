"""시험 계측: 0.15초 넘는 프레임 안의 렌더러 호출(들어감/나옴·스레드·시각)을 art.log 에 'trace' 줄로. 한 번만 돌린다."""
from pathlib import Path
src = Path(r'F:\AI\gclx-4k\engine\src')


def patch(name, pairs):
    p = src / name; s = p.read_text('utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (name, old[:70], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, 'utf-8')


patch('n2hd_gpu_v8.cpp', [
    ('enum {PF_DRAW,PF_GLYPH,PF_COPY,PF_CAPTURE,PF_CLEAR,PF_END,PF_PRESENT,PF_MOVIE,PF_LOAD,PF_N};',
     'enum {PF_DRAW,PF_GLYPH,PF_COPY,PF_CAPTURE,PF_CLEAR,PF_END,PF_PRESENT,PF_MOVIE,PF_LOAD,PF_BACKLOG,PF_N};\n'
     '// Event ring for the long-frame trace: (time, slot*2 + 0 enter / 1 leave, thread).\n'
     'struct TraceEv{LONGLONG t;int id;DWORD tid;};static TraceEv traceRing[8192];static volatile LONG traceN;\n'
     'static void traceEv(int id){LONG i=InterlockedIncrement(&traceN)-1;LARGE_INTEGER q;QueryPerformanceCounter(&q);TraceEv& e=traceRing[i&8191];e.t=q.QuadPart;e.id=id;e.tid=GetCurrentThreadId();}'),
    ('struct PerfScope{int s;LARGE_INTEGER a;PerfScope(int x):s(x){QueryPerformanceCounter(&a);}~PerfScope(){LARGE_INTEGER b;QueryPerformanceCounter(&b);',
     'struct PerfScope{int s;LARGE_INTEGER a;PerfScope(int x):s(x){traceEv(x*2);QueryPerformanceCounter(&a);}~PerfScope(){traceEv(s*2+1);LARGE_INTEGER b;QueryPerformanceCounter(&b);'),
])
patch('backlog_renderer.inc', [
    ('N2HD_BacklogBegin(){Guard guard;', 'N2HD_BacklogBegin(){Guard guard;PerfScope perf(PF_BACKLOG);'),
    ('N2HD_BacklogGlyph(void* font,int x,int y,const unsigned short* record){Guard guard;', 'N2HD_BacklogGlyph(void* font,int x,int y,const unsigned short* record){Guard guard;PerfScope perf(PF_BACKLOG);'),
    ('N2HD_BacklogEnd(){Guard guard;', 'N2HD_BacklogEnd(){Guard guard;PerfScope perf(PF_BACKLOG);'),
    ('N2HD_BacklogLayout(Backlog::Ink* out,int capacity){Guard guard;', 'N2HD_BacklogLayout(Backlog::Ink* out,int capacity){Guard guard;PerfScope perf(PF_BACKLOG);'),
    ('N2HD_BacklogPlacement(int* out,int capacity){Guard guard;', 'N2HD_BacklogPlacement(int* out,int capacity){Guard guard;PerfScope perf(PF_BACKLOG);'),
])
patch('hires_art.inc', [
    ('extern "C" __declspec(dllexport) void __cdecl N2HD_LoadBegin(){QueryPerformanceCounter(&artLoadT0);}',
     'extern "C" __declspec(dllexport) void __cdecl N2HD_LoadBegin(){traceEv(100);QueryPerformanceCounter(&artLoadT0);}'),
    # 0.15초 넘는 프레임: 앞 프레임 끝 이후의 사건을 모두 적는다
    ('static void artFrameTiming(){static LARGE_INTEGER f,last;LARGE_INTEGER now;',
     'static void artTraceDump(LONGLONG from,LONGLONG to,double freq){if(!artLog)return;LONG n=traceN;LONG start=n>8192?n-8192:0;int shown=0;\n'
     ' static const char* names[]={"draw","glyph","copy","capture","clear","end","present","movie","load","backlog"};\n'
     ' for(LONG i=start;i<n&&shown<400;++i){TraceEv& e=traceRing[i&8191];if(e.t<from||e.t>to)continue;const char* nm=e.id==100?"loadbegin":e.id/2<10?names[e.id/2]:"?";\n'
     '  fprintf(artLog,"trace +%.1fms %s %s t%lu\\n",(e.t-from)*1000.0/freq,nm,e.id==100?"":e.id&1?"out":"in",e.tid);++shown;}fflush(artLog);}\n'
     'static void artFrameTiming(){static LARGE_INTEGER f,last;LARGE_INTEGER now;'),
    ('if(ms>80&&artLog){fprintf(artLog,"longframe ',
     'if(ms>150)artTraceDump(last.QuadPart,now.QuadPart,(double)f.QuadPart);if(ms>80&&artLog){fprintf(artLog,"longframe '),
])
print('ok')
