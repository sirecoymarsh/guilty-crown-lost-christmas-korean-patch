"""1배 그림 캐시 구현(채우기·보관·지우기·통계). 한 번만 돌린다."""
from pathlib import Path
src = Path(r'F:\AI\gclx-4k\engine\src')


def patch(name, pairs):
    p = src / name; s = p.read_text('utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (name, old[:70], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, 'utf-8')


patch('img_cache.inc', [
    ('static void init(){if(mode>=0)return;char v[16];mode=GetEnvironmentVariableA("N2HD_IMGCACHE",v,16)?atoi(v):1;GetEnvironmentVariableA("N2HD_PROFILE_DIR",logDir,MAX_PATH);}',
     '// Only with a 4 GB address space (large-address-aware EXE): in 2 GB the 4K text surfaces already run out (see validImage).\n'
     'static void init(){if(mode>=0)return;char v[16];mode=GetEnvironmentVariableA("N2HD_IMGCACHE",v,16)?atoi(v):1;GetEnvironmentVariableA("N2HD_PROFILE_DIR",logDir,MAX_PATH);\n'
     ' MEMORYSTATUSEX ms{sizeof ms};if(!GlobalMemoryStatusEx(&ms)||ms.ullTotalVirtual<(3ull<<30)){if(mode==1)mode=0;}}'),
    ('extern "C" void __cdecl N2HD_LoadBegin();',
     r'''static thread_local double missStart;
static const int FIELDS[]={4,8,0xc,0x10,0x14};   // what both decoders set besides the buffer (+0x28), observed 10-27
static void stats(){static uint64_t n=0;if(!logDir[0]||(++n)%200)return;char l[200];
 sprintf_s(l,"hits %llu misses %llu stores %llu cache_mb %u hit_ms_avg %.2f miss_ms_avg %.2f",hits,misses,stores,(unsigned)(bytes>>20),hits?hitMs/hits:0,misses?missMs/misses:0);log(l);}
// A copy of the kept decode into the fresh picture t, or 0.
static int fill(void* t){if(mode!=1||!cur||!t)return 0;double t0=now();AcquireSRWLockShared(&lock);auto it=map.find(cur);
 if(it==map.end()){ReleaseSRWLockShared(&lock);missStart=now();return 0;}
 const Entry& e=it->second;void* buf=HeapAlloc(GetProcessHeap(),0,e.pixels.size());
 if(buf){memcpy(buf,e.pixels.data(),e.pixels.size());for(auto& f:e.fields)*(uint32_t*)((char*)t+f.first)=f.second;*(void**)((char*)t+0x28)=buf;}
 ReleaseSRWLockShared(&lock);if(!buf){missStart=now();return 0;}
 AcquireSRWLockExclusive(&lock);auto j=map.find(cur);if(j!=map.end())j->second.last=++tick;++hits;hitMs+=now()-t0;hitBytes+=e.pixels.size();ReleaseSRWLockExclusive(&lock);stats();return 1;}
// After a real decode of cur into t: keep its fields and buffer.
static void store(void* t){if(mode!=1||!cur||!t)return;double ms=missStart?now()-missStart:0;missStart=0;void* p=*(void**)((char*)t+0x28);if(!p)return;
 SIZE_T n=HeapSize(GetProcessHeap(),0,p);if(n==(SIZE_T)-1||n>(64u<<20))return;
 Entry e;for(int f:FIELDS)e.fields.push_back({f,*(uint32_t*)((char*)t+f)});try{e.pixels.assign((uint8_t*)p,(uint8_t*)p+n);}catch(...){return;}
 AcquireSRWLockExclusive(&lock);++misses;missMs+=ms;auto old=map.find(cur);if(old!=map.end()){bytes-=old->second.pixels.size();map.erase(old);}
 e.last=++tick;bytes+=e.pixels.size();map.emplace(cur,std::move(e));++stores;
 while(bytes>budget&&!map.empty()){auto lru=map.begin();for(auto i=map.begin();i!=map.end();++i)if(i->second.last<lru->second.last)lru=i;bytes-=lru->second.pixels.size();map.erase(lru);}
 ReleaseSRWLockExclusive(&lock);stats();}
}
extern "C" void __cdecl N2HD_LoadBegin();'''),
])
patch('runtime_hooks.cpp', [
    ('static int __cdecl hookPng(void* t,void* file){ImgCache::init();int r=((int(__cdecl*)(void*,void*))origPng)(t,file);if(r&&ImgCache::mode==2)ImgCache::observe("png",t);return r;}\n'
     'static void __cdecl jpgAfter(void* t,int r){ImgCache::init();if(r&&ImgCache::mode==2)ImgCache::observe("jpg",t);}',
     'static int __cdecl hookPng(void* t,void* file){ImgCache::init();if(ImgCache::fill(t))return 1;int r=((int(__cdecl*)(void*,void*))origPng)(t,file);\n'
     ' if(r){if(ImgCache::mode==2)ImgCache::observe("png",t);else ImgCache::store(t);}return r;}\n'
     'static int __cdecl jpgFill(void* t){ImgCache::init();return ImgCache::fill(t);}\n'
     'static void __cdecl jpgAfter(void* t,int r){if(r){if(ImgCache::mode==2)ImgCache::observe("jpg",t);else ImgCache::store(t);}}'),
    ('__declspec(naked) static void hookJpg(){__asm {\n push dword ptr [esp+4]\n call dword ptr [origJpg]\n',
     '__declspec(naked) static void hookJpg(){__asm {\n sub esp,4\n pushad\n push dword ptr [esp+40]\n call jpgFill\n add esp,4\n mov [esp+32],eax\n popad\n'
     ' cmp dword ptr [esp],0\n lea esp,[esp+4]\n jz miss\n mov eax,1\n ret\nmiss:\n push dword ptr [esp+4]\n call dword ptr [origJpg]\n'),
])
print('ok')
