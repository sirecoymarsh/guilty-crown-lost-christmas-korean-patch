// Claude 11-24, test only (N2HD_TEST_DSB_TRACE=1 + N2HD_PROFILE_DIR): log every DirectSound buffer call the engine makes
// (create / duplicate / play / stop / set position / set volume / release) with the first two calling EXE addresses and
// whether a backlog-jump load is running, into dsb.log. Purpose: find where a J/K restart load stops the music and where it
// creates and starts it again (user: "언어 전환할때 음악 멈추는거 해결 가능? 안멈추는척").
namespace DsbTrace {
static FILE* logf; static CRITICAL_SECTION cs; static bool on=false;
typedef HRESULT (WINAPI* CreateFn)(LPCGUID,void**,void*);
typedef HRESULT (STDMETHODCALLTYPE* CsbFn)(void*,const void*,void**,void*);
typedef HRESULT (STDMETHODCALLTYPE* DupFn)(void*,void*,void**);
typedef ULONG (STDMETHODCALLTYPE* RelFn)(void*);
typedef HRESULT (STDMETHODCALLTYPE* PlayFn)(void*,DWORD,DWORD,DWORD);
typedef HRESULT (STDMETHODCALLTYPE* StopFn)(void*);
typedef HRESULT (STDMETHODCALLTYPE* PosFn)(void*,DWORD);
typedef HRESULT (STDMETHODCALLTYPE* VolFn)(void*,LONG);
static CreateFn realCreate; static CsbFn realCsb; static DupFn realDup;
static RelFn realRel; static PlayFn realPlay; static StopFn realStop; static PosFn realPos; static VolFn realVol;
static void callers(uint32_t* c){c[0]=c[1]=0;int k=0;const uint32_t* sp=(const uint32_t*)_AddressOfReturnAddress();
 for(int i=0;i<160&&k<2;++i){uint32_t v;__try{v=sp[i];}__except(1){break;}if(v>=0x401000&&v<0x511000)c[k++]=v;}}
static void put(const char* op,void* buf,long a,long b){if(!on||!logf)return;uint32_t c[2];callers(c);
 EnterCriticalSection(&cs);fprintf(logf,"%lu %s buf=%p a=%ld b=%ld c=%08x,%08x ld=%d tid=%lu\n",GetTickCount(),op,buf,a,b,c[0],c[1],Jump::loading?1:0,GetCurrentThreadId());fflush(logf);LeaveCriticalSection(&cs);}
static ULONG STDMETHODCALLTYPE myRel(void* s){ULONG r=realRel(s);put("release",s,(long)r,0);return r;}
static HRESULT STDMETHODCALLTYPE myPlay(void* s,DWORD r1,DWORD pr,DWORD fl){HRESULT r=realPlay(s,r1,pr,fl);put("play",s,(long)fl,(long)r);return r;}
static HRESULT STDMETHODCALLTYPE myStop(void* s){HRESULT r=realStop(s);put("stop",s,0,(long)r);return r;}
static HRESULT STDMETHODCALLTYPE myPos(void* s,DWORD p){HRESULT r=realPos(s,p);put("setpos",s,(long)p,(long)r);return r;}
static HRESULT STDMETHODCALLTYPE myVol(void* s,LONG v){HRESULT r=realVol(s,v);put("volume",s,v,(long)r);return r;}
static void patchBuffer(void* buf){void** vt=*(void***)buf;if(realRel&&vt[2]==(void*)&myRel)return;DWORD old;
 if(!VirtualProtect(vt,20*sizeof(void*),PAGE_READWRITE,&old))return;
 if(!realRel){realRel=(RelFn)vt[2];realPlay=(PlayFn)vt[12];realPos=(PosFn)vt[13];realVol=(VolFn)vt[15];realStop=(StopFn)vt[18];}
 if(vt[2]==(void*)realRel)vt[2]=(void*)&myRel;if(vt[12]==(void*)realPlay)vt[12]=(void*)&myPlay;if(vt[13]==(void*)realPos)vt[13]=(void*)&myPos;
 if(vt[15]==(void*)realVol)vt[15]=(void*)&myVol;if(vt[18]==(void*)realStop)vt[18]=(void*)&myStop;
 VirtualProtect(vt,20*sizeof(void*),old,&old);put("vtable",buf,(long)(uintptr_t)vt,0);}
static HRESULT STDMETHODCALLTYPE myCsb(void* self,const void* desc,void** out,void* unk){HRESULT r=realCsb(self,desc,out,unk);
 const DWORD* d=(const DWORD*)desc;if(SUCCEEDED(r)&&out&&*out){if(!(d[1]&1))patchBuffer(*out);put("create",*out,(long)d[2],(long)d[1]);}return r;}   // d[1] flags (1 = primary), d[2] bytes
static HRESULT STDMETHODCALLTYPE myDup(void* self,void* src,void** out){HRESULT r=realDup(self,src,out);if(SUCCEEDED(r)&&out&&*out){patchBuffer(*out);put("dup",*out,(long)(uintptr_t)src,0);}return r;}
static HRESULT WINAPI myCreate(LPCGUID g,void** ds,void* unk){HRESULT r=realCreate(g,ds,unk);
 if(SUCCEEDED(r)&&ds&&*ds){void** vt=*(void***)*ds;DWORD old;if(VirtualProtect(vt,12*sizeof(void*),PAGE_READWRITE,&old)){
   if(!realCsb){realCsb=(CsbFn)vt[3];realDup=(DupFn)vt[5];}vt[3]=(void*)&myCsb;vt[5]=(void*)&myDup;VirtualProtect(vt,12*sizeof(void*),old,&old);}}
 put("dscreate",ds?*ds:0,(long)r,0);return r;}
static void install(){char dir[MAX_PATH];if(!GetEnvironmentVariableA("N2HD_TEST_DSB_TRACE",0,0)||!GetEnvironmentVariableA("N2HD_PROFILE_DIR",dir,MAX_PATH))return;
 InitializeCriticalSection(&cs);char p[MAX_PATH];wsprintfA(p,"%s\\dsb.log",dir);logf=fopen(p,"a");if(!logf)return;on=true;
 void** slot=(void**)0x511028;DWORD old;if(VirtualProtect(slot,4,PAGE_READWRITE,&old)){realCreate=(CreateFn)*slot;*slot=(void*)&myCreate;VirtualProtect(slot,4,old,&old);}
 fprintf(logf,"start\n");fflush(logf);}
}  // namespace DsbTrace
