"""시험 계측: 렌더러 진입점별 시간과 프레임마다 렌더러가 쓴 시간(10초마다 stat 줄). 한 번만 돌린다."""
from pathlib import Path
src = Path(r'F:\AI\gclx-4k\engine\src')
p = src / 'n2hd_gpu_v8.cpp'; s = p.read_text('utf-8')


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:70], s.count(old))
    s = s.replace(old, new)


GUARD = 'static CRITICAL_SECTION rendererLock;struct Guard{Guard(){EnterCriticalSection(&rendererLock);}~Guard(){LeaveCriticalSection(&rendererLock);}};'
rep(GUARD, GUARD + '''
// Claude 10-27: time spent inside the renderer, by entry point and per frame (written to the test log as "stat" lines).
enum {PF_DRAW,PF_GLYPH,PF_COPY,PF_CAPTURE,PF_CLEAR,PF_END,PF_PRESENT,PF_MOVIE,PF_LOAD,PF_N};static LONGLONG pfTotal[PF_N],pfFrame,pfFrameMax,pfFreq;static uint64_t pfOver16,pfOver50;
struct PerfScope{int s;LARGE_INTEGER a;PerfScope(int x):s(x){QueryPerformanceCounter(&a);}~PerfScope(){LARGE_INTEGER b;QueryPerformanceCounter(&b);pfTotal[s]+=b.QuadPart-a.QuadPart;pfFrame+=b.QuadPart-a.QuadPart;}};''')
for sig, slot in (('N2HD_RecordTexture(void* t){Guard guard;', 'PF_LOAD'),
                  ('N2HD_Glyph(void* font,GLYPHMETRICS* gm,void* native,int width,unsigned code){Guard guard;', 'PF_GLYPH'),
                  ('N2HD_CopyGlyph(void* dst,void* src,int x,int y,uint32_t c){Guard guard;', 'PF_COPY'),
                  ('N2HD_CopyGlyphMain(void* dst,void* src,int x,int y,uint32_t c){Guard guard;', 'PF_COPY'),
                  ('N2HD_Movie(void* movie){Guard guard;', 'PF_MOVIE'),
                  ('N2HD_Clear(){Guard guard;', 'PF_CLEAR'),
                  ('N2HD_MovieFrame(void* data){Guard guard;', 'PF_MOVIE'),
                  ('N2HD_Capture(void* object,int* parameters){Guard guard;', 'PF_CAPTURE'),
                  ('N2HD_AfterDraw(void* object,void* arg,void* filter){Guard guard;', 'PF_DRAW'),
                  ('N2HD_Draw(void* object,void* arg2,void* filter){Guard guard;', 'PF_DRAW'),
                  ('N2HD_End(){Guard guard;', 'PF_END'),
                  ('N2HD_Present(){Guard guard;', 'PF_PRESENT')):
    rep(sig, sig + f'PerfScope perf({slot});')
old_shot_head = 'static void testShot(){static int every=-1,shots=0;static DWORD last=0;static wchar_t dir[MAX_PATH];if(every<0){wchar_t v[32];every=GetEnvironmentVariableW(L"N2HD_TEST_SHOT_MS",v,32)?_wtoi(v):0;if(!GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",dir,MAX_PATH))every=0;}if(every<=0||shots>=60)return;DWORD now=GetTickCount();'
new_shot_head = ('static void testStat(DWORD now){static DWORD lastStat=0;if(!artLog||(lastStat&&now-lastStat<10000))return;lastStat=now;double f=pfFreq?1000.0/pfFreq:0;'
                 'fprintf(artLog,"stat t=%lu presents=%llu draw=%.0f glyph=%.0f copy=%.0f capture=%.0f clear=%.0f end=%.0f present=%.0f movie=%.0f load=%.0f our_over16=%llu our_over50=%llu our_max=%.0f long50=%llu long100=%llu uploads=%llu late=%llu decode_ms_max=%llu upload_ms_max=%llu cache_mb=%llu\\n",now,(unsigned long long)presents,'
                 'pfTotal[PF_DRAW]*f,pfTotal[PF_GLYPH]*f,pfTotal[PF_COPY]*f,pfTotal[PF_CAPTURE]*f,pfTotal[PF_CLEAR]*f,pfTotal[PF_END]*f,pfTotal[PF_PRESENT]*f,pfTotal[PF_MOVIE]*f,pfTotal[PF_LOAD]*f,'
                 '(unsigned long long)pfOver16,(unsigned long long)pfOver50,pfFrameMax*f,(unsigned long long)artLongFrames50,(unsigned long long)artLongFrames100,(unsigned long long)artUploads,(unsigned long long)artLate,(unsigned long long)artDecodeMsMax,(unsigned long long)artUploadMsMax,(unsigned long long)(artCacheBytes>>20));fflush(artLog);}\n'
                 'static void testShot(){static int every=-1,shots=0;static DWORD last=0;static bool test=false;static wchar_t dir[MAX_PATH];if(every<0){wchar_t v[32];every=GetEnvironmentVariableW(L"N2HD_TEST_SHOT_MS",v,32)?_wtoi(v):0;test=GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",dir,MAX_PATH)!=0;if(!test)every=0;}'
                 'DWORD now=GetTickCount();if(test)testStat(now);if(every<=0||shots>=60)return;')
rep(old_shot_head, new_shot_head)
p.write_text(s, 'utf-8')

q = src / 'hires_art.inc'; t = q.read_text('utf-8')
old = 'N2HD_ImageLoaded(const char* name,void* t){Guard guard;'
assert t.count(old) == 1
t = t.replace(old, old + 'PerfScope perf(PF_LOAD);')
old2 = 'static void artFrameTiming(){static LARGE_INTEGER f,last;LARGE_INTEGER now;if(!f.QuadPart)QueryPerformanceFrequency(&f);QueryPerformanceCounter(&now);'
assert t.count(old2) == 1
t = t.replace(old2, old2 + 'pfFreq=f.QuadPart;{double our=pfFrame*1000.0/f.QuadPart;if(our>16)++pfOver16;if(our>50)++pfOver50;if(pfFrame>pfFrameMax)pfFrameMax=pfFrame;pfFrame=0;}')
q.write_text(t, 'utf-8')
print('ok')
