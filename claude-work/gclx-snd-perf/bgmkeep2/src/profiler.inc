// Test runs only (Claude 10-27): sampling profiler of every thread in the game. Every ~1 ms a helper thread suspends
// each one in turn, reads EIP and the first return address into the game EXE found on its stack, and counts them per
// thread; profile.log in N2HD_PROFILE_DIR gets the totals every 30 s. Shows where frame time goes outside the renderer
// (10-27: the presenting thread spends 93% waiting in win32u, so the work is on other threads).
#include <map>
#include <timeapi.h>
#include <tlhelp32.h>
static DWORD profRender;static volatile LONG profSamples;
struct ProfThread {HANDLE h;uint32_t samples=0;std::map<HMODULE,uint32_t> module;std::map<uint32_t,uint32_t> eip,caller;};
static CRITICAL_SECTION profLock;static std::map<DWORD,ProfThread> prof;
static bool profInExe(uint32_t a){return a>=0x401000&&a<0x511000;}
static void profScanThreads(){DWORD me=GetCurrentThreadId(),pid=GetCurrentProcessId();HANDLE s=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);if(s==INVALID_HANDLE_VALUE)return;
 THREADENTRY32 te{sizeof te};for(BOOL ok=Thread32First(s,&te);ok;ok=Thread32Next(s,&te)){if(te.th32OwnerProcessID!=pid||te.th32ThreadID==me)continue;
  EnterCriticalSection(&profLock);if(!prof.count(te.th32ThreadID)){HANDLE h=OpenThread(THREAD_SUSPEND_RESUME|THREAD_GET_CONTEXT|THREAD_QUERY_INFORMATION,FALSE,te.th32ThreadID);if(h)prof[te.th32ThreadID].h=h;}LeaveCriticalSection(&profLock);}
 CloseHandle(s);}
// First value on the stack that points into the EXE code (no objects here: __try).
static uint32_t profFindCaller(const uint32_t* sp){for(int i=0;i<256;++i){uint32_t v;__try{v=sp[i];}__except(1){return 0;}if(profInExe(v))return v;}return 0;}
static DWORD WINAPI profRun(void*){timeBeginPeriod(1);DWORD lastScan=0;std::vector<std::pair<DWORD,HANDLE>> list;
 for(;;){Sleep(1);DWORD now=GetTickCount();if(now-lastScan>2000){lastScan=now;profScanThreads();list.clear();EnterCriticalSection(&profLock);for(auto& t:prof)list.push_back({t.first,t.second.h});LeaveCriticalSection(&profLock);}
  for(auto& t:list){if(SuspendThread(t.second)==(DWORD)-1)continue;CONTEXT c{};c.ContextFlags=CONTEXT_CONTROL;bool ok=GetThreadContext(t.second,&c)!=0;uint32_t eip=c.Eip,caller=0;
   if(ok&&!profInExe(eip))caller=profFindCaller((const uint32_t*)c.Esp);
   ResumeThread(t.second);if(!ok)continue;
   HMODULE m=0;GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,(LPCWSTR)(uintptr_t)eip,&m);
   EnterCriticalSection(&profLock);ProfThread& p=prof[t.first];++p.samples;++p.module[m];if(profInExe(eip))++p.eip[eip&~0xfu];else if(caller)++p.caller[caller];LeaveCriticalSection(&profLock);}
  InterlockedIncrement(&profSamples);}
 return 0;}
static void profDump(const wchar_t* dir){wchar_t path[MAX_PATH];wsprintfW(path,L"%s\\profile.log",dir);FILE* f=_wfopen(path,L"w");if(!f)return;
 EnterCriticalSection(&profLock);fprintf(f,"rounds %ld, render thread %lu\n",profSamples,profRender);
 for(auto& t:prof){ProfThread& p=t.second;if(!p.samples)continue;
  uint32_t exe=0;for(auto& e:p.eip)exe+=e.second;
  fprintf(f,"\n== thread %lu%s samples %u, in exe %u\n",t.first,t.first==profRender?" (render)":"",p.samples,exe);
  std::vector<std::pair<uint32_t,HMODULE>> mods;for(auto& m:p.module)mods.push_back({m.second,m.first});std::sort(mods.rbegin(),mods.rend());
  for(size_t i=0;i<mods.size()&&i<6;++i){wchar_t n[MAX_PATH]=L"?";if(mods[i].second)GetModuleFileNameW(mods[i].second,n,MAX_PATH);const wchar_t* b=wcsrchr(n,L'\\');fprintf(f,"  %7u %ls\n",mods[i].first,b?b+1:n);}
  std::vector<std::pair<uint32_t,uint32_t>> v;for(auto& e:p.eip)v.push_back({e.second,e.first});std::sort(v.rbegin(),v.rend());
  fprintf(f,"  -- exe eip\n");for(size_t i=0;i<v.size()&&i<25;++i)fprintf(f,"  %7u %08x\n",v[i].first,v[i].second);
  v.clear();for(auto& e:p.caller)v.push_back({e.second,e.first});std::sort(v.rbegin(),v.rend());
  fprintf(f,"  -- exe return address when outside the exe\n");for(size_t i=0;i<v.size()&&i<15;++i)fprintf(f,"  %7u %08x\n",v[i].first,v[i].second);}
 LeaveCriticalSection(&profLock);fclose(f);}
// Called from testShot (render thread) in test runs with N2HD_TEST_PROFILE set.
static void profTick(const wchar_t* dir,DWORD now){static int on=-1;static DWORD last;if(on<0){on=GetEnvironmentVariableW(L"N2HD_TEST_PROFILE",0,0)?1:0;
  if(on){InitializeCriticalSection(&profLock);profRender=GetCurrentThreadId();HANDLE h=CreateThread(0,0,profRun,0,0,0);if(h){SetThreadPriority(h,THREAD_PRIORITY_TIME_CRITICAL);CloseHandle(h);}last=now;}}
 if(on&&now-last>=30000){last=now;profDump(dir);}}
