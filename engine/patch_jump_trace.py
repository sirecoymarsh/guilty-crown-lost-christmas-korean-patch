"""긴 프레임 추적에 지점 저장 단계(시작·엔진 저장 뒤·보관 뒤·끝)를 넣는다. 한 번만 돌린다."""
from pathlib import Path
src = Path(r'F:\AI\gclx-4k\engine\src')


def patch(name, pairs):
    p = src / name; s = p.read_text('utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (name, old[:70], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, 'utf-8')


patch('n2hd_gpu_v8.cpp', [
    ('static void traceEv(int id){LONG i=InterlockedIncrement(&traceN)-1;LARGE_INTEGER q;QueryPerformanceCounter(&q);TraceEv& e=traceRing[i&8191];e.t=q.QuadPart;e.id=id;e.tid=GetCurrentThreadId();}',
     'static void traceEv(int id){LONG i=InterlockedIncrement(&traceN)-1;LARGE_INTEGER q;QueryPerformanceCounter(&q);TraceEv& e=traceRing[i&8191];e.t=q.QuadPart;e.id=id;e.tid=GetCurrentThreadId();}\n'
     'extern "C" void __cdecl N2HD_Trace(int id){traceEv(id);}'),
])
patch('hires_art.inc', [
    ('const char* nm=e.id==100?"loadbegin":e.id/2<10?names[e.id/2]:"?";',
     'static const char* jn[]={"jump-begin","jump-saved","jump-archived","jump-end"};const char* nm=e.id==100?"loadbegin":e.id>=110&&e.id<114?jn[e.id-110]:e.id/2<10?names[e.id/2]:"?";'),
    ('nm,e.id==100?"":e.id&1?"out":"in",e.tid);', 'nm,e.id>=100?"":e.id&1?"out":"in",e.tid);'),
])
patch('backlog_jump.inc', [
    ('static int capture(){Lock guard;', 'extern "C" void __cdecl N2HD_Trace(int);\nstatic int capture(){N2HD_Trace(110);struct TraceEnd{~TraceEnd(){N2HD_Trace(113);}}traceEnd;Lock guard;'),
    ('int ok=nativeSave(1);strcpy_s((char*)0x5a54b4,260,old);', 'int ok=nativeSave(1);N2HD_Trace(111);strcpy_s((char*)0x5a54b4,260,old);'),
    ('if(ok&&archive(cp)){points.push_back(cp);', 'if(ok&&archive(cp)){N2HD_Trace(112);points.push_back(cp);'),
])
print('ok')
