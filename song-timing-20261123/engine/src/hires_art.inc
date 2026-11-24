// 4x remastered art (Claude, 10-26; F:\AI\gclx-4k\tools\remaster_batch.py, vn-art-4k-remaster skill).
// The engine still loads, lays out and animates its 1x pictures. The image loader (0x467990: name in eax, returns the
// picture) is wrapped so each loaded picture remembers its file; when that picture is drawn the 4K target samples the
// 4x copy <game>\hires\<key>.jxl instead (same normalised UVs, so position and zoom are unchanged).
// - index.tsv: name(cp932, "bg/....jpg", ASCII lower case)\t1x w\t1x h\t4x w\t4x h\talpha 0/1\tkey\ttile rows (0 or missing = one file)
// - a picture whose size differs from the index, whose pixels the engine later changes (sparse signature), or whose
//   file fails to decode is drawn from its 1x pixels as before.
// - Decoding runs on one worker thread, started when the engine loads the picture. The draw path only uploads finished
//   bands (a few ms) and draws the 1x pixels until then: decoding on the draw path stalled the game 0.05-0.2 s at every
//   picture change (10-27: 18.6 s in 6 minutes).
// - 4x textures are POOL_DEFAULT filled band by band through a strip-sized SYSTEMMEM surface (the game is 32-bit and not
//   large address aware: no dynamic textures, no lasting CPU copy, no picture-sized block). They are cached per file, not
//   per engine picture, up to ART_CACHE_MAX of video memory (least recently drawn go first): the engine frees and loads
//   the same files again and again, and the general cache drops anything unused for 300 frames (10-27: 195 of 320
//   uploads were pictures already decoded once).
#define JXL_STATIC_DEFINE
#define JXL_THREADS_STATIC_DEFINE
#include <jxl/decode.h>
#include <jxl/thread_parallel_runner.h>
#include <string>
#include <thread>
#include <cstdio>
#include <deque>
#include <memory>
#include <algorithm>
#include <unordered_set>
// path: <game>\hires\<key>; the art is <key>.jxl, or with tile>0 <key>_0.jxl, <key>_1.jxl ... each tile rows tall
// (transparent pictures: libjxl decodes their alpha into one 4-byte-per-pixel block, 60 MB for a 15 MP picture).
struct ArtEntry {int w,h,ow,oh;bool alpha;std::wstring path;int tile;};
struct ArtRef {const ArtEntry* e;uint32_t sig;int pw,ph;};   // pw,ph: the engine surface size (width padded, 619 -> 620)
static std::unordered_map<std::string,ArtEntry> artIndex;static bool artIndexLoaded;static std::unordered_map<void*,ArtRef> art;
static uint64_t artLoads,artMatched,artUploads,artFails,artStale,artDecodeMsTotal,artDecodeMsMax,artUploadMsMax,artLate,artLongFrames50,artLongFrames100;
static void* jxlRunner;static FILE* artLog;
// Engine side, for the test log: time inside the engine's own picture loader, and frame intervals by bucket.
static LARGE_INTEGER artLoadT0;static LONGLONG artLoadFrame,artLoadTotal,artLoadMax;static uint64_t artFrameHist[6],artLongWithLoad;

static std::wstring artGameDir(){wchar_t p[MAX_PATH];if(!GetModuleFileNameW(0,p,MAX_PATH))return L"";wchar_t* s=wcsrchr(p,L'\\');if(s)s[1]=0;return p;}
static std::string artNorm(const char* n){std::string o;const unsigned char* p=(const unsigned char*)n;
 while(*p){unsigned c=*p;if((c>=0x81&&c<=0x9f)||(c>=0xe0&&c<=0xfc)){o+=(char)c;if(p[1]){o+=(char)p[1];p+=2;}else ++p;continue;}
  if(c=='\\')c='/';if(c>='A'&&c<='Z')c+=32;o+=(char)c;++p;}
 if(o.compare(0,3,"cg/")==0)o.erase(0,3);return o;}
static void artLoadIndex(){artIndexLoaded=true;std::wstring dir=artGameDir()+L"hires\\";
 if(GetEnvironmentVariableW(L"N2HD_ART_OFF",0,0)){if(GetEnvironmentVariableW(L"N2HD_ART_LOG",0,0))artLog=_wfopen((dir+L"art-off.log").c_str(),L"a");return;}
 if(GetEnvironmentVariableW(L"N2HD_ART_LOG",0,0))artLog=_wfopen((dir+L"art.log").c_str(),L"a");
 FILE* f=_wfopen((dir+L"index.tsv").c_str(),L"rb");if(!f)return;char line[1024];
 while(fgets(line,sizeof line,f)){char* t[8];int n=0;char* s=line;t[n++]=s;while(*s&&n<8){if(*s=='\t'){*s=0;t[n++]=s+1;}++s;}if(n<7)continue;
  char* k=t[6];k[strcspn(k,"\r\n")]=0;ArtEntry a{atoi(t[1]),atoi(t[2]),atoi(t[3]),atoi(t[4]),t[5][0]=='1',dir+std::wstring(k,k+strlen(k)),n>=8?atoi(t[7]):0};
  if(a.w>0&&a.h>0&&a.ow>0&&a.oh>0)artIndex[artNorm(t[0])]=a;}
 fclose(f);if(artLog){fprintf(artLog,"index %u entries\n",(unsigned)artIndex.size());fflush(artLog);}}
static uint32_t artSig(void* t){int w=iv(t,8),h=iv(t,12);uint32_t** rows=(uint32_t**)pv(t,0x2c);if(!rows||w<1||h<1)return 0;uint32_t s=2166136261u;
 for(unsigned i=0;i<64;++i){int y=(int)((i*37u+3)%(unsigned)h),x=(int)((i*101u+7)%(unsigned)w);s=(s^rows[y][x])*16777619u;}return s|1;}
// The texture covers the engine surface (pw x ph, padded) at the art's scale: the art in the top left, the padding
// filled from its last column and row so bilinear sampling at the edge never reaches empty texels.
static void artSize(const ArtEntry& e,int pw,int ph,int& tw,int& th){tw=(int)((double)pw*e.ow/e.w+0.5);th=(int)((double)ph*e.oh/e.h+0.5);if(tw<e.ow)tw=e.ow;if(th<e.oh)th=e.oh;}

// Decoded rows go to bands of ART_BAND rows (4 MB at 4096 wide): the game has no picture-sized hole left after a few
// minutes (10-27: 15 MP pictures failed every time, 13 MP ones still went up).
static const int ART_BAND=256;
typedef std::vector<std::vector<uint8_t>> ArtBands;
struct JxlRowOut {ArtBands* bands;int pitch;int ch;int y0;};
static void artRow(void* opaque,size_t x,size_t y,size_t n,const void* pixels){auto o=(JxlRowOut*)opaque;y+=o->y0;uint8_t* d=(*o->bands)[y/ART_BAND].data()+(y%ART_BAND)*o->pitch+x*4;const uint8_t* s=(const uint8_t*)pixels;
 if(o->ch==4)for(size_t i=0;i<n;++i,d+=4,s+=4){d[0]=s[2];d[1]=s[1];d[2]=s[0];d[3]=s[3];}
 else for(size_t i=0;i<n;++i,d+=4,s+=3){d[0]=s[2];d[1]=s[1];d[2]=s[0];d[3]=255;}}
// libjxl's allocations, to log the biggest request and the one that failed.
struct ArtMem {size_t largest,failed;};
static void* artAlloc(void* op,size_t n){auto m=(ArtMem*)op;if(n>m->largest)m->largest=n;void* p=malloc(n);if(!p&&n>m->failed)m->failed=n;return p;}
static void artFree(void*,void* p){free(p);}
static size_t artLargestFree(){MEMORY_BASIC_INFORMATION mi;size_t best=0;for(uint64_t p=0x10000;p<0xfffe0000ull;p+=mi.RegionSize){if(!VirtualQuery((void*)(uintptr_t)p,&mi,sizeof mi)||!mi.RegionSize)break;if(mi.State==MEM_FREE&&mi.RegionSize>best)best=mi.RegionSize;}return best;}
// One file (the whole art, or one tile): its rows land at y0.. in the bands.
static bool artDecode(const std::vector<uint8_t>& buf,const ArtEntry& e,int y0,int rows,ArtBands& bands,int pitch,ArtMem& mem){
 if(!jxlRunner)jxlRunner=JxlThreadParallelRunnerCreate(nullptr,(size_t)std::max(1,std::min(8,(int)std::thread::hardware_concurrency()-1)));
 JxlMemoryManager mm{&mem,artAlloc,artFree};
 JxlDecoder* dec=JxlDecoderCreate(&mm);if(!dec)return false;bool full=false,ok=false;JxlRowOut out{&bands,pitch,e.alpha?4:3,y0};JxlPixelFormat fmt{(uint32_t)out.ch,JXL_TYPE_UINT8,JXL_NATIVE_ENDIAN,0};
 if((!jxlRunner||JxlDecoderSetParallelRunner(dec,JxlThreadParallelRunner,jxlRunner)==JXL_DEC_SUCCESS)&&JxlDecoderSubscribeEvents(dec,JXL_DEC_BASIC_INFO|JXL_DEC_FULL_IMAGE)==JXL_DEC_SUCCESS&&JxlDecoderSetInput(dec,buf.data(),buf.size())==JXL_DEC_SUCCESS){
  JxlDecoderCloseInput(dec);
  for(;;){JxlDecoderStatus st=JxlDecoderProcessInput(dec);
   if(st==JXL_DEC_BASIC_INFO){JxlBasicInfo bi;if(JxlDecoderGetBasicInfo(dec,&bi)!=JXL_DEC_SUCCESS||(int)bi.xsize!=e.ow||(int)bi.ysize!=rows)break;}
   else if(st==JXL_DEC_NEED_IMAGE_OUT_BUFFER){if(JxlDecoderSetImageOutCallback(dec,&fmt,artRow,&out)!=JXL_DEC_SUCCESS)break;}
   else if(st==JXL_DEC_FULL_IMAGE)full=true;
   else{ok=st==JXL_DEC_SUCCESS&&full;break;}}}
 JxlDecoderDestroy(dec);return ok;}

// ---- worker thread: file -> bands. Decoded but not yet uploaded bands are held to ART_PENDING_MAX (32-bit address space).
static volatile LONG artDecoding;static double artUpFrameMs;
static volatile LONG64 artPendingBytes;static const LONG64 ART_PENDING_MAX=256ll<<20;
struct ArtJob {const ArtEntry* e;int tw,th;ArtBands bands;ArtMem mem{0,0};const char* why=0;uint64_t decodeMs=0;volatile LONG state=0;LONG64 counted=0;bool wanted=false;   // state 0 queued 1 decoding 2 ready 3 failed
 ~ArtJob(){if(counted)InterlockedAdd64(&artPendingBytes,-counted);}};
static CRITICAL_SECTION artQLock;static CONDITION_VARIABLE artQCv;static std::deque<std::shared_ptr<ArtJob>> artQueue;static bool artWorkerStarted;
static void artDecodeJob(ArtJob& j){const ArtEntry& e=*j.e;LARGE_INTEGER f,a,b;QueryPerformanceFrequency(&f);QueryPerformanceCounter(&a);const int pitch=j.tw*4;const char* why=0;
 try{j.bands.resize((j.th+ART_BAND-1)/ART_BAND);for(size_t i=0;i<j.bands.size();++i)j.bands[i].resize((size_t)std::min(ART_BAND,j.th-(int)i*ART_BAND)*pitch);}catch(...){why="bands";}
 const int step=e.tile>0?e.tile:e.oh;
 for(int y0=0,i=0;!why&&y0<e.oh;y0+=step,++i){std::wstring file=e.tile>0?e.path+L"_"+std::to_wstring(i)+L".jxl":e.path+L".jxl";std::vector<uint8_t> buf;
  HANDLE h=CreateFileW(file.c_str(),GENERIC_READ,FILE_SHARE_READ,0,OPEN_EXISTING,FILE_FLAG_SEQUENTIAL_SCAN,0);
  if(h==INVALID_HANDLE_VALUE){why="open";break;}
  DWORD size=GetFileSize(h,0),got=0;try{buf.resize(size);}catch(...){why="file buffer";}if(!why&&(!size||!ReadFile(h,buf.data(),size,&got,0)||got!=size))why="read";CloseHandle(h);
  if(!why&&!artDecode(buf,e,y0,std::min(step,e.oh-y0),j.bands,pitch,j.mem))why="decode";}
 auto row=[&](int y){return j.bands[y/ART_BAND].data()+(size_t)(y%ART_BAND)*pitch;};
 if(!why){for(int y=0;y<e.oh;++y){uint32_t* r=(uint32_t*)row(y);for(int x=e.ow;x<j.tw;++x)r[x]=r[e.ow-1];}for(int y=e.oh;y<j.th;++y)memcpy(row(y),row(e.oh-1),pitch);}
 if(why)ArtBands().swap(j.bands);else{j.counted=(LONG64)j.tw*j.th*4;InterlockedAdd64(&artPendingBytes,j.counted);}
 QueryPerformanceCounter(&b);j.decodeMs=(uint64_t)((b.QuadPart-a.QuadPart)*1000/f.QuadPart);j.why=why;artDecodeMsTotal+=j.decodeMs;if(j.decodeMs>artDecodeMsMax)artDecodeMsMax=j.decodeMs;
 if(artLog){if(!why)fprintf(artLog,"decode %ls.jxl %dx%d %llums ok jxl_max_alloc %uKB tile %d\n",e.path.c_str(),j.tw,j.th,(unsigned long long)j.decodeMs,(unsigned)(j.mem.largest>>10),e.tile);
  else fprintf(artLog,"decode %ls.jxl %dx%d %llums FAIL %s jxl_max_alloc %uKB jxl_failed_alloc %uKB largest_free %uKB\n",e.path.c_str(),j.tw,j.th,(unsigned long long)j.decodeMs,why,(unsigned)(j.mem.largest>>10),(unsigned)(j.mem.failed>>10),(unsigned)(artLargestFree()>>10));fflush(artLog);}}
static DWORD WINAPI artWorker(void*){for(;;){std::shared_ptr<ArtJob> j;EnterCriticalSection(&artQLock);while(artQueue.empty())SleepConditionVariableCS(&artQCv,&artQLock,INFINITE);j=artQueue.front();artQueue.pop_front();LeaveCriticalSection(&artQLock);
 if(j.use_count()==1)continue;   // dropped while queued
 while(artPendingBytes>ART_PENDING_MAX)Sleep(4);
 InterlockedExchange(&j->state,1);InterlockedIncrement(&artDecoding);artDecodeJob(*j);InterlockedDecrement(&artDecoding);InterlockedExchange(&j->state,j->why?3:2);}}

// ---- render thread (rendererLock): jobs by file, the video memory cache by file.
struct ArtTex {IDirect3DTexture9* tex;int tw,th;uint64_t lastFrame;size_t bytes;};
static std::unordered_map<const ArtEntry*,std::shared_ptr<ArtJob>> artJobs;static std::unordered_map<const ArtEntry*,ArtTex> artCache;static std::unordered_set<const ArtEntry*> artBad;
static size_t artCacheBytes;static const size_t ART_CACHE_MAX=(size_t)2048<<20;
// The one upload in progress (see artUpStep).
struct ArtUp {std::shared_ptr<ArtJob> job;IDirect3DTexture9* tx=0;IDirect3DSurface9* dst=0;IDirect3DSurface9* strip=0;int y=0;double ms=0;};
static std::unique_ptr<ArtUp> artUp;
static void artRequest(const ArtEntry* e,int tw,int th,bool urgent){
 if(!artWorkerStarted){InitializeCriticalSection(&artQLock);InitializeConditionVariable(&artQCv);HANDLE h=CreateThread(0,0,artWorker,0,0,0);if(h){SetThreadPriority(h,THREAD_PRIORITY_BELOW_NORMAL);CloseHandle(h);}artWorkerStarted=true;}
 if(artUp&&artUp->job->e==e&&artUp->job->tw==tw&&artUp->job->th==th)return;
 auto it=artJobs.find(e);
 if(it!=artJobs.end()&&it->second->tw==tw&&it->second->th==th){if(urgent)it->second->wanted=true;
  if(urgent&&it->second->state==0){EnterCriticalSection(&artQLock);auto q=std::find(artQueue.begin(),artQueue.end(),it->second);if(q!=artQueue.end()&&q!=artQueue.begin()){auto j=*q;artQueue.erase(q);artQueue.push_front(j);}LeaveCriticalSection(&artQLock);}
  return;}
 auto j=std::make_shared<ArtJob>();j->e=e;j->tw=tw;j->th=th;j->wanted=urgent;artJobs[e]=j;
 EnterCriticalSection(&artQLock);if(urgent)artQueue.push_front(j);else artQueue.push_back(j);LeaveCriticalSection(&artQLock);WakeConditionVariable(&artQCv);}
static void artEvict(){while(artCacheBytes>ART_CACHE_MAX){auto lru=artCache.end();for(auto it=artCache.begin();it!=artCache.end();++it)if(it->second.lastFrame<frames&&(lru==artCache.end()||it->second.lastFrame<lru->second.lastFrame))lru=it;
 if(lru==artCache.end())break;lru->second.tex->Release();artCacheBytes-=lru->second.bytes;artCache.erase(lru);}}
static void artCacheRemove(const ArtEntry* e){auto c=artCache.find(e);if(c!=artCache.end()){c->second.tex->Release();artCacheBytes-=c->second.bytes;artCache.erase(c);}}
// Finished bands -> POOL_DEFAULT texture, a few bands per frame end (ART_UPLOAD_MS): one 60 MB picture in one go held
// the frame 80-90 ms (10-27). One upload at a time; the picture is drawn from its 1x pixels until it is in the cache.
static const double ART_UPLOAD_MS=4.0;
static void artUpEnd(const char* why){ArtUp& u=*artUp;ArtJob& j=*u.job;if(u.strip)u.strip->Release();if(u.dst)u.dst->Release();
 if(why&&u.tx){u.tx->Release();u.tx=0;}
 ArtBands().swap(j.bands);if(j.counted){InterlockedAdd64(&artPendingBytes,-j.counted);j.counted=0;}
 if(u.ms>artUploadMsMax)artUploadMsMax=(uint64_t)u.ms;
 if(u.tx){artCacheRemove(j.e);size_t bytes=(size_t)j.tw*j.th*4;artCache[j.e]={u.tx,j.tw,j.th,frames,bytes};artCacheBytes+=bytes;++artUploads;artEvict();}else{++artFails;artBad.insert(j.e);}
 if(artLog){fprintf(artLog,"upload %ls.jxl %dx%d %.0fms %s decode %llums cache %uMB\n",j.e->path.c_str(),j.tw,j.th,u.ms,u.tx?"ok":why,(unsigned long long)j.decodeMs,(unsigned)(artCacheBytes>>20));fflush(artLog);}
 artUp.reset();}
static void artUpStep(){LARGE_INTEGER f,a,b;QueryPerformanceFrequency(&f);QueryPerformanceCounter(&a);ArtUp& u=*artUp;ArtJob& j=*u.job;const int pitch=j.tw*4;
 if(!u.tx){if(FAILED(dev->CreateTexture(j.tw,j.th,1,0,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&u.tx,0))){u.tx=0;artUpEnd("texture");return;}
  if(FAILED(u.tx->GetSurfaceLevel(0,&u.dst))||FAILED(dev->CreateOffscreenPlainSurface(j.tw,ART_BAND,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&u.strip,0))){artUpEnd("strip");return;}}
 for(;;){int n=std::min(ART_BAND,j.th-u.y);D3DLOCKED_RECT l;if(FAILED(u.strip->LockRect(&l,0,0))){artUpEnd("lock");return;}
  const uint8_t* band=j.bands[u.y/ART_BAND].data();for(int y=0;y<n;++y)memcpy((uint8_t*)l.pBits+(size_t)y*l.Pitch,band+(size_t)y*pitch,pitch);u.strip->UnlockRect();
  RECT r{0,0,j.tw,n};POINT p{0,u.y};if(FAILED(dev->UpdateSurface(u.strip,&r,u.dst,&p))){artUpEnd("update");return;}
  std::vector<uint8_t>().swap(j.bands[u.y/ART_BAND]);u.y+=n;
  QueryPerformanceCounter(&b);double ms=(b.QuadPart-a.QuadPart)*1000.0/f.QuadPart;
  if(u.y>=j.th){u.ms+=ms;artUpFrameMs+=ms;artUpEnd(0);return;}
  if(ms>=ART_UPLOAD_MS){u.ms+=ms;artUpFrameMs+=ms;return;}}}
// Each frame end: go on with the upload in progress, or start the next finished job (pictures being drawn first).
static void artFrameEnd(){if(!dev)return;if(!artUp&&artJobs.empty())return;if(dev->TestCooperativeLevel()!=D3D_OK)return;
 if(!artUp){auto pick=artJobs.end();
  for(auto it=artJobs.begin();it!=artJobs.end();){LONG s=it->second->state;
   if(s==3){artBad.insert(it->first);++artFails;it=artJobs.erase(it);continue;}
   if(s==2&&(pick==artJobs.end()||(it->second->wanted&&!pick->second->wanted)))pick=it;++it;}
  if(pick==artJobs.end())return;
  artUp.reset(new ArtUp);artUp->job=pick->second;artJobs.erase(pick);}
 artUpStep();}
static void artRelease(){for(auto &c:artCache)c.second.tex->Release();artCache.clear();artCacheBytes=0;
 if(artUp){if(artUp->strip)artUp->strip->Release();if(artUp->dst)artUp->dst->Release();if(artUp->tx)artUp->tx->Release();artUp.reset();}}
// Frame pacing for the test log: presents more than 50 / 100 ms apart.
static void artTraceDump(LONGLONG from,LONGLONG to,double freq){if(!artLog)return;LONG n=traceN;LONG start=n>8192?n-8192:0;int shown=0;
 static const char* names[]={"draw","glyph","copy","capture","clear","end","present","movie","load","backlog"};
 for(LONG i=start;i<n&&shown<8000;++i){TraceEv& e=traceRing[i&8191];if(e.t<from||e.t>to)continue;static const char* jn[]={"jump-begin","jump-saved","jump-archived","jump-end","normal-save-in","normal-save-out","drain-in","drain-out"};const char* nm=e.id==100?"loadbegin":e.id>=110&&e.id<118?jn[e.id-110]:e.id/2<10?names[e.id/2]:"?";
  fprintf(artLog,"trace +%.1fms %s %s t%lu\n",(e.t-from)*1000.0/freq,nm,e.id>=100?"":e.id&1?"out":"in",e.tid);++shown;}fflush(artLog);}
static void artFrameTiming(){static LARGE_INTEGER f,last;LARGE_INTEGER now;if(!f.QuadPart)QueryPerformanceFrequency(&f);QueryPerformanceCounter(&now);pfFreq=f.QuadPart;double ourMs=pfFrame*1000.0/f.QuadPart;{double our=ourMs;if(our>16)++pfOver16;if(our>50)++pfOver50;if(pfFrame>pfFrameMax)pfFrameMax=pfFrame;pfFrame=0;}
 if(last.QuadPart){double ms=(now.QuadPart-last.QuadPart)*1000.0/f.QuadPart;if(ms>50)++artLongFrames50;if(ms>100)++artLongFrames100;++artFrameHist[ms<12?0:ms<20?1:ms<35?2:ms<50?3:ms<100?4:5];if(ms>150)artTraceDump(last.QuadPart,now.QuadPart,(double)f.QuadPart);if(ms>80&&artLog){fprintf(artLog,"longframe %.0fms our=%.0f engine_load=%.0f decoding=%ld upload=%.1f frame=%llu at=%.0f\n",ms,ourMs,artLoadFrame*1000.0/f.QuadPart,artDecoding,artUpFrameMs,(unsigned long long)frames,now.QuadPart*1000.0/f.QuadPart);fflush(artLog);}if(ms>50&&artLoadFrame*1000.0/f.QuadPart>25)++artLongWithLoad;}artLoadFrame=0;artUpFrameMs=0;last=now;}

extern "C" __declspec(dllexport) void __cdecl N2HD_LoadBegin(){traceEv(100);QueryPerformanceCounter(&artLoadT0);}
extern "C" __declspec(dllexport) void __cdecl N2HD_ImageLoaded(const char* name,void* t){Guard guard;PerfScope perf(PF_LOAD);{LARGE_INTEGER b,f;QueryPerformanceCounter(&b);QueryPerformanceFrequency(&f);LONGLONG d=b.QuadPart-artLoadT0.QuadPart;if(artLoadT0.QuadPart&&d>0){artLoadFrame+=d;artLoadTotal+=d;if(d>artLoadMax)artLoadMax=d;double ms=d*1000.0/f.QuadPart;if(artLog&&ms>=20&&name&&t){fprintf(artLog,"slowload %.0fms %s %dx%d fmt %x\n",ms,name,iv(t,8),iv(t,12),(unsigned)*(unsigned short*)((char*)t+4));fflush(artLog);}}}
 if(name&&t&&(!_stricmp(name,"SCREEN")||!_stricmp(name,"VIDEO")))screenPending(t);   // menu backdrops: S-key save, load, backlog, close… use VIDEO; the right-click path SCREEN
 if(!name||!t)return;if(!artIndexLoaded)artLoadIndex();if(artIndex.empty())return;void* data=pv(t,0x28);if(!data)return;++artLoads;
 auto it=artIndex.find(artNorm(name));
 int pw=iv(t,8),ph=iv(t,12);bool fits=it!=artIndex.end()&&pw>=it->second.w&&pw<=it->second.w+7&&ph>=it->second.h&&ph<=it->second.h+7;
 if(artLog&&artLoads<=400){fprintf(artLog,"load %s %dx%d%s\n",name,pw,ph,it==artIndex.end()?" (not in index)":fits?" MATCH":" (size differs)");fflush(artLog);}
 if(!fits){art.erase(data);return;}
 art[data]={&it->second,artSig(t),pw,ph};++artMatched;
 const ArtEntry* e=&it->second;if(artBad.count(e))return;int tw,th;artSize(*e,pw,ph,tw,th);   // start decoding now, before the picture is drawn
 auto c=artCache.find(e);if(c!=artCache.end()&&c->second.tw==tw&&c->second.th==th){c->second.lastFrame=frames;return;}
 artRequest(e,tw,th,false);}
// The 4x texture of an engine picture, or 0 to draw its 1x pixels (also while the 4x copy is still decoding).
static IDirect3DTexture9* artTexture(void* t){if(gQuality>=1)return 0;void* data=pv(t,0x28);auto ar=art.find(data);if(ar==art.end())return 0;
 if(high.count(data)||movieVersions.count(data)||VideoFrame(data))return 0;
 if(iv(t,8)!=ar->second.pw||iv(t,12)!=ar->second.ph||artSig(t)!=ar->second.sig){if(artLog){fprintf(artLog,"stale %ls.jxl engine %dx%d (was %dx%d) sig %08x (was %08x)\n",ar->second.e->path.c_str(),iv(t,8),iv(t,12),ar->second.pw,ar->second.ph,artSig(t),ar->second.sig);fflush(artLog);}art.erase(ar);++artStale;return 0;}
 const ArtEntry* e=ar->second.e;int tw,th;artSize(*e,ar->second.pw,ar->second.ph,tw,th);
 auto c=artCache.find(e);if(c!=artCache.end()&&c->second.tw==tw&&c->second.th==th){c->second.lastFrame=frames;boundUV=0;return c->second.tex;}
 if(artBad.count(e))return 0;
 artRequest(e,tw,th,true);++artLate;return 0;}
