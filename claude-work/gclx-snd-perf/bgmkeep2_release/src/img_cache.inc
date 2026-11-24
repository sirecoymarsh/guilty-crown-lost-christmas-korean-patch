// Claude 10-27: the engine's own (1x) pictures, decoded once. The engine decodes every picture it loads with its own
// 2012 libpng / JPEG code, again and again: a smoke effect 27 times in 150 s, and ~200 pictures, ~2 of the ~3 s, when a
// backlog jump restores a scene. The PNG (0x46d670, cdecl (picture, file)) and JPEG (0x404f20, file in eax, picture on
// the stack) decoders are wrapped. After a decode, the picture fields it set and its pixel buffer (process heap, the
// engine allocator 0x46a280 is HeapAlloc) are kept, keyed by the name the loader (0x467990) is loading. The next decode
// of that name gets a heap copy of the buffer and the same fields; the loader's 0x469060 then builds the row pointers as
// after a real decode. The picture struct is 0x480 bytes, zeroed by 0x469010 apart from +0x30 (its destroy function).
#include <unordered_map>
namespace ImgCache {
static thread_local const char* cur;                 // name the loader on this thread is loading
static SRWLOCK lock=SRWLOCK_INIT;
struct Entry {std::vector<std::pair<int,uint32_t>> fields;std::vector<uint8_t> pixels;uint64_t last=0;};
static std::unordered_map<std::string,Entry> map;static size_t bytes;static uint64_t tick;
static size_t budget=(size_t)512<<20;
static uint64_t hits,misses,stores,hitBytes;static double hitMs,missMs;
static int mode=-1;                                   // 0 off, 1 cache, 2 observe (test log of the fields a decoder sets)
static char logDir[MAX_PATH];
// Only with a 4 GB address space (large-address-aware EXE): in 2 GB the 4K text surfaces already run out (see validImage).
static void init(){if(mode>=0)return;char v[16];mode=GetEnvironmentVariableA("N2HD_IMGCACHE",v,16)?atoi(v):1;GetEnvironmentVariableA("N2HD_PROFILE_DIR",logDir,MAX_PATH);
 MEMORYSTATUSEX ms{sizeof ms};if(!GlobalMemoryStatusEx(&ms)||ms.ullTotalVirtual<(3ull<<30)){if(mode==1)mode=0;}}
static void log(const char* line){if(!logDir[0])return;char path[MAX_PATH];wsprintfA(path,"%s\\imgcache.log",logDir);HANDLE h=CreateFileA(path,FILE_APPEND_DATA,FILE_SHARE_READ,0,OPEN_ALWAYS,0,0);
 if(h!=INVALID_HANDLE_VALUE){DWORD w;WriteFile(h,line,lstrlenA(line),&w,0);WriteFile(h,"\r\n",2,&w,0);CloseHandle(h);}}
static double now(){static LARGE_INTEGER f;LARGE_INTEGER c;if(!f.QuadPart)QueryPerformanceFrequency(&f);QueryPerformanceCounter(&c);return c.QuadPart*1000.0/f.QuadPart;}
// Observe: every nonzero dword of a freshly decoded picture apart from the buffer, row pointers and destroy function.
static void observe(const char* kind,void* t){static int np=0,nj=0;if(++(kind[0]==0x6a?nj:np)>40)return;const uint32_t* d=(const uint32_t*)t;char line[1600];int k=wsprintfA(line,"%s %s:",kind,cur?cur:"?");
 for(int o=0;o<0x480/4&&k<1500;++o){if(o==0x28/4||o==0x2c/4||o==0x30/4||!d[o])continue;k+=wsprintfA(line+k," +%x=%x",o*4,d[o]);}
 void* p=*(void**)((char*)t+0x28);k+=wsprintfA(line+k," | buf %u",p?(unsigned)HeapSize(GetProcessHeap(),0,p):0);log(line);}
static thread_local double missStart;
static const int FIELDS[]={4,8,0xc,0x10,0x14};   // what both decoders set besides the buffer (+0x28), observed 10-27
static void stats(){static uint64_t n=0;if(!logDir[0]||(++n)%200)return;char l[200];
 sprintf_s(l,"hits %llu misses %llu stores %llu cache_mb %u hit_ms_avg %.2f miss_ms_avg %.2f",hits,misses,stores,(unsigned)(bytes>>20),hits?hitMs/hits:0,misses?missMs/misses:0);log(l);}
// A copy of the kept decode into the fresh picture t, or 0.
static int fill(void* t){if(mode!=1||!cur||!t)return 0;double t0=now();AcquireSRWLockShared(&lock);auto it=map.find(cur);
 if(it==map.end()){ReleaseSRWLockShared(&lock);missStart=now();return 0;}
 const Entry& e=it->second;size_t sz=e.pixels.size();void* buf=HeapAlloc(GetProcessHeap(),0,sz);
 if(buf){memcpy(buf,e.pixels.data(),e.pixels.size());for(auto& f:e.fields)*(uint32_t*)((char*)t+f.first)=f.second;*(void**)((char*)t+0x28)=buf;}
 ReleaseSRWLockShared(&lock);if(!buf){missStart=now();return 0;}
 AcquireSRWLockExclusive(&lock);auto j=map.find(cur);if(j!=map.end())j->second.last=++tick;++hits;hitMs+=now()-t0;hitBytes+=sz;ReleaseSRWLockExclusive(&lock);stats();return 1;}
static void store(void* t);
// Test mode 3: decode for real every time and compare with the kept copy (fields and the whole buffer).
static uint64_t verified,diffs;
static void verify(void* t){if(mode!=3||!cur||!t)return;void* p=*(void**)((char*)t+0x28);if(!p)return;SIZE_T n=HeapSize(GetProcessHeap(),0,p);
 AcquireSRWLockShared(&lock);auto it=map.find(cur);bool have=it!=map.end(),same=false;
 if(have){const Entry& e=it->second;same=e.pixels.size()==n&&!memcmp(e.pixels.data(),p,n);for(auto& f:e.fields)if(*(uint32_t*)((char*)t+f.first)!=f.second)same=false;}
 ReleaseSRWLockShared(&lock);
 if(have){++verified;if(!same){++diffs;char l[400];sprintf_s(l,"verify DIFF %s size %u",cur,(unsigned)n);log(l);}if(verified%100==0){char l[100];sprintf_s(l,"verify %llu same, %llu different",verified-diffs,diffs);log(l);}return;}
 int m=mode;mode=1;store(t);mode=m;}
// After a real decode of cur into t: keep its fields and buffer.
static void store(void* t){if(mode!=1||!cur||!t)return;double ms=missStart?now()-missStart:0;missStart=0;void* p=*(void**)((char*)t+0x28);if(!p)return;
 SIZE_T n=HeapSize(GetProcessHeap(),0,p);if(n==(SIZE_T)-1||n>(64u<<20))return;
 Entry e;for(int f:FIELDS)e.fields.push_back({f,*(uint32_t*)((char*)t+f)});try{e.pixels.assign((uint8_t*)p,(uint8_t*)p+n);}catch(...){return;}
 AcquireSRWLockExclusive(&lock);++misses;missMs+=ms;auto old=map.find(cur);if(old!=map.end()){bytes-=old->second.pixels.size();map.erase(old);}
 e.last=++tick;bytes+=e.pixels.size();map.emplace(cur,std::move(e));++stores;
 while(bytes>budget&&!map.empty()){auto lru=map.begin();for(auto i=map.begin();i!=map.end();++i)if(i->second.last<lru->second.last)lru=i;bytes-=lru->second.pixels.size();map.erase(lru);}
 ReleaseSRWLockExclusive(&lock);stats();}
}
extern "C" void __cdecl N2HD_LoadBegin();
static void krConfigCommand(const char* name);   // runtime_hooks.cpp: config page 3 commands (kr_cmd_*)
static void __cdecl imgBegin(const char* name){krConfigCommand(name);ImgCache::cur=name;N2HD_LoadBegin();}
static void __cdecl imgEnd(){ImgCache::cur=0;}
