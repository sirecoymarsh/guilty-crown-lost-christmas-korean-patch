// Claude 11-24: keep the music playing through a J/K restart load (user: "언어 전환할때 음악 멈추는거 해결 가능? 안멈추는척",
// "그래도 해줘"). Addresses and plan: engine\lockfix\bgmkeep_주소.md (session 「길티 크라운 사운드 모드 성능」, static) + dsb trace.
//
// A J/K switch reloads this line's checkpoint: Jump::restart() → script Load(-947002) → state 0x201 → main thread native load
// 0x4727a0 (state 0x202) → objects deleted (0x455a00 calls the stream's destroy [s+0x3f0]=0x479770 when [s+0x104]==obj) and
// rebuilt from frames.npf (new stream s2, thread created suspended) → Sleep(300) → 0x44baf0 wakes the streams → state 0x100.
// The music stops earlier than the delete: the stream thread 0x479d50 ends itself as soon as ([0x620540]&0xffffff00)!=0x100
// (checks at 0x47a09f, 0x47a2b9, 0x47a566), i.e. within 0.5 s of the script's Load.
//
// What this does, only for a restart load:
//  1 restart(): under M, pick playing BGM streams ([s+0x104]==obj, [s+0x108]==0x11, [s+0x110]==BGM, no effect, no fades).
//  2 the three state checks (and the "loading?" check 0x47a9b6 in the decoder rewind) report 0x100 for a kept s (esi).
//  3 0x479770 during the restart load: a kept, still playing s is detached ([s+0x104]=0, *ps=0) instead of destroyed.
//  4 right after origJumpLoad: under M find the rebuilt sound object of the same name; if its new s2 matches (file, type,
//    state 0x11 or 0x02 = rebuilt, thread still suspended (seen 11-24: a playing BGM comes back as 0x02 here), loop, volume, pan, frequency, flags, no fades/effects) swap the old s in and destroy s2; else destroy s.
//  The kept list is cleared at the next checkpoint capture (state is 0x100 again by then).
// v2 (Claude 11-24 night, J/K sweep jks_*): (a) a finished fade leaves its thread handle in the block ([s+0x334] etc. stay != -1 after the
//  fade thread ends) - music started with a fade-in (lx0506 lx007a, SoundPlay_Loop(..,2000,..)) was never kept: 10 J/K in a row cut 0.8-1.6 s.
//  Idle = no thread or the thread has ended. The rebuilt s2 gets the saved fade re-armed (thread waiting) - accept it when it is a no-op
//  (its target equals the kept value). (b) looping SE streams (music played as SE: seBGM_*, ambient loops *_L) are kept too. Up to 8.
// N2HD_BGMKEEP_OFF=1 turns it off (A/B). N2HD_TEST_BGMKEEP_TRACE=1 + N2HD_PROFILE_DIR writes bgmkeep.log.
#include <cstdarg>
extern "C" { void* volatile gBgmKeep[8]; }   // read by the naked stubs: kept streams (0 = empty)
namespace BgmKeep {
static void* origSndDestroy; static void* origSt1; static void* origSt2; static void* origSt3; static void* origSt4;   // manifest trampolines (unused)
static FILE* lf; static bool trace=false; static int off=-1;
struct Kept {void* s; bool detached; char name[0x100];};
static Kept kept[8]; static int nk=0;
struct Caps{DWORD dwSize,dwFlags,dwBufferBytes,dwUnlockTransferRate,dwPlayCpuOverhead;};   // DSBCAPS (dsound.h needs mmsystem here)
static DWORD U(void* s,int o){return *(DWORD*)((char*)s+o);}
static unsigned char B8(void* s,int o){return *((unsigned char*)s+o);}
static DWORD freq(void* s){DWORD f=U(s,0x124);return f==1000?U(s,0x3cc):f;}   // 1000 = own speed; once played the field may hold the rate ([s+0x3cc])
static void lockM(){((void(__cdecl*)())0x44abc0)();}
static void unlockM(){((void(__cdecl*)())0x44ac00)();}
static bool disabled(){if(off<0)off=GetEnvironmentVariableA("N2HD_BGMKEEP_OFF",0,0)?1:0;return off==1;}
static void logf_(const char* fmt,...){if(!trace)return;va_list a;va_start(a,fmt);fprintf(lf,"%lu ",GetTickCount());vfprintf(lf,fmt,a);fputc('\n',lf);fflush(lf);va_end(a);}
static void install(){char dir[MAX_PATH];if(!GetEnvironmentVariableA("N2HD_TEST_BGMKEEP_TRACE",0,0)||!GetEnvironmentVariableA("N2HD_PROFILE_DIR",dir,MAX_PATH))return;
 char p[MAX_PATH];wsprintfA(p,"%s\\bgmkeep.log",dir);lf=fopen(p,"a");trace=lf!=0;logf_("start off=%d",disabled()?1:0);}
static bool blockIdle(void* s,int h){HANDLE t=(HANDLE)(size_t)U(s,h);return t==INVALID_HANDLE_VALUE||WaitForSingleObject(t,0)==WAIT_OBJECT_0;}
static bool noFades(void* s){return blockIdle(s,0x334)&&blockIdle(s,0x370)&&blockIdle(s,0x3ac);}
// rebuilt s2: a re-armed fade (volume block +0x314: target +0x324; pan +0x350: target +0x360; frequency +0x38c: target +0x39c) is fine when it
// only lands where the kept s already is.
static bool fadeNoop(void* s,void* s2,int h,int target,int value){return (int)U(s2,h)==-1||blockIdle(s2,h)||U(s2,target)==U(s,value);}
static bool s2FadesNoop(void* s,void* s2){return fadeNoop(s,s2,0x334,0x324,0x11c)&&fadeNoop(s,s2,0x370,0x360,0x120)&&fadeNoop(s,s2,0x3ac,0x39c,0x124);}
static void clear(){for(int i=0;i<8;++i)gBgmKeep[i]=0;nk=0;}
static int find(void* s){for(int i=0;i<nk;++i)if(kept[i].s==s)return i;return -1;}
// 1. restart(): pick playing BGM streams (script thread; M is recursive).
static void select(){clear();if(disabled())return;lockM();
 for(char* node=*(char**)0x5aa7ac;node&&nk<8;node=*(char**)(node+0x18)){char* obj=*(char**)(node+0xc);if(!obj)break;void* s=*(void**)(obj+0x1388);if(!s)continue;
  if(*(char**)((char*)s+0x104)!=obj||B8(s,0x108)!=0x11||(U(s,0x110)!=0x10000000&&(int)U(s,0x114)!=-1)||U(s,0x3f4)!=0)continue;
  if(!noFades(s)){logf_("skip fading obj=%s h=%lx/%lx/%lx",obj,U(s,0x334),U(s,0x370),U(s,0x3ac));continue;}
  kept[nk].s=s;kept[nk].detached=false;memcpy(kept[nk].name,obj,0xff);kept[nk].name[0xff]=0;gBgmKeep[nk]=s;++nk;
  logf_("keep s=%p obj=%s file=%s type=%lx pos=%lu vol=%lu loop=%ld",s,obj,(char*)s,U(s,0x110),U(s,0x10c),U(s,0x11c),(long)U(s,0x114));}
 unlockM();if(nk==0)logf_("keep none");}
// 3. destroy during the restart load (main thread, M held by the delete).
static bool detach(void** pp,void* s){int k=find(s);if(k<0||kept[k].detached||!Jump::loading||!Jump::restartLoad||B8(s,0x108)!=0x11)return false;
 char* owner=*(char**)((char*)s+0x104);if(owner){memcpy(kept[k].name,owner,0xff);kept[k].name[0xff]=0;}
 *(void**)((char*)s+0x104)=0;*pp=0;kept[k].detached=true;logf_("detach s=%p name=%s pos=%lu",s,kept[k].name,U(s,0x10c));return true;}
static void destroyStream(void* s){void* t=s;((int(__cdecl*)(void**))*(void**)((char*)s+0x3f0))(&t);}
// 4. after the native load (main thread, before the script thread resumes; new streams are still suspended).
static void afterLoad(bool ok){void* drop[16];int nd=0;
 if(nk)lockM();
 for(int i=0;i<nk;++i){Kept& k=kept[i];if(!k.detached)continue;void* s=k.s;void* s2=0;char* obj2=0;
  // several objects can carry the same name (rebuilt sound + others): take the one whose stream matches best
  int best=-1;if(ok)for(char* node=*(char**)0x5aa7ac;node;node=*(char**)(node+0x18)){char* obj=*(char**)(node+0xc);if(!obj)break;
   if(strcmp(obj,k.name)!=0)continue;void* c=*(void**)(obj+0x1388);if(!c||*(char**)((char*)c+0x104)!=obj)continue;
   int sc=(strcmp((char*)s,(char*)c)==0)+(U(s,0x114)==U(c,0x114))+(U(s,0x11c)==U(c,0x11c))+(U(s,0x124)==U(c,0x124))+(B8(c,0x108)==0x11)*2;
   logf_("  cand obj=%p s2=%p st=%02x loop=%ld vol=%lu freq=%lu score=%d",obj,c,B8(c,0x108),(long)U(c,0x114),U(c,0x11c),U(c,0x124),sc);
   if(sc>best){best=sc;obj2=obj;s2=c;}}
  bool same=s2&&strcmp((char*)s,(char*)s2)==0&&U(s,0x110)==U(s2,0x110)&&(B8(s2,0x108)==0x11||B8(s2,0x108)==0x02)&&U(s,0x114)==U(s2,0x114)&&U(s,0x11c)==U(s2,0x11c)
           &&U(s,0x120)==U(s2,0x120)&&freq(s)==freq(s2)&&U(s,0x140)==U(s2,0x140)&&s2FadesNoop(s,s2)&&U(s2,0x3f4)==0&&B8(s,0x108)==0x11;
  logf_("after name=%s s=%p s2=%p same=%d st=%02x st2=%02x pos=%lu",k.name,s,s2,same?1:0,B8(s,0x108),s2?B8(s2,0x108):0,U(s,0x10c));
  if(s2&&!same)logf_("  diff file=%d type=%lx/%lx loop=%ld/%ld vol=%lu/%lu pan=%ld/%ld freq=%lu/%lu flag=%lx/%lx fade=%ld,%ld,%ld tgt=%lu,%lu,%lu fx=%lx",strcmp((char*)s,(char*)s2),U(s,0x110),U(s2,0x110),(long)U(s,0x114),(long)U(s2,0x114),U(s,0x11c),U(s2,0x11c),(long)U(s,0x120),(long)U(s2,0x120),U(s,0x124),U(s2,0x124),U(s,0x140),U(s2,0x140),(long)U(s2,0x334),(long)U(s2,0x370),(long)U(s2,0x3ac),U(s2,0x324),U(s2,0x360),U(s2,0x39c),U(s2,0x3f4));
  if(same&&(int)U(s2,0x334)!=-1)logf_("  s2 fade re-armed tgt=%lu vol=%lu (accepted)",U(s2,0x324),U(s,0x11c));
  if(same){*(void**)(obj2+0x1388)=s;*(void**)((char*)s+0x104)=obj2;drop[nd++]=s2;}
  else drop[nd++]=s;
  k.detached=false;}
 if(nk)unlockM();
 for(int i=0;i<nd;++i)destroyStream(drop[i]);
 if(!ok)clear();}
}  // namespace BgmKeep
static int __cdecl hookSndDestroy(void** pp){void* s=pp?*pp:0;if(s&&BgmKeep::nk&&BgmKeep::detach(pp,s))return 1;return ((int(__cdecl*)(void**))BgmKeep::origSndDestroy)(pp);}
static void bgmKeepSelect(){BgmKeep::select();}
static void bgmKeepClear(){if(BgmKeep::nk){BgmKeep::logf_("clear");BgmKeep::clear();}}
static void bgmKeepAfterLoad(bool restart){if(BgmKeep::nk&&restart)BgmKeep::afterLoad(true);else if(BgmKeep::nk){for(int i=0;i<BgmKeep::nk;++i)if(BgmKeep::kept[i].detached)BgmKeep::afterLoad(false);}}
// 2. state checks in the stream thread (esi = s): report 0x100 for a kept s while the engine is in 0x2xx. Integer only (FPU holds values here).
#define BGMKEEP_TEST_ESI(hit) __asm cmp esi,dword ptr [gBgmKeep] __asm je hit __asm cmp esi,dword ptr [gBgmKeep+4] __asm je hit __asm cmp esi,dword ptr [gBgmKeep+8] __asm je hit __asm cmp esi,dword ptr [gBgmKeep+12] __asm je hit __asm cmp esi,dword ptr [gBgmKeep+16] __asm je hit __asm cmp esi,dword ptr [gBgmKeep+20] __asm je hit __asm cmp esi,dword ptr [gBgmKeep+24] __asm je hit __asm cmp esi,dword ptr [gBgmKeep+28] __asm je hit
__declspec(naked) static void stubState1(){__asm{        // 0x47a09f: mov eax,[0x620540] → 0x47a0a4
 mov eax,dword ptr ds:[0x620540]
 test esi,esi
 jz done
 push ecx
 mov ecx,eax
 and ecx,0xffffff00
 cmp ecx,0x200
 pop ecx
 jne done}
 BGMKEEP_TEST_ESI(hit1)
 __asm{jmp done
hit1:
 mov eax,0x100
done:
 push 0x47a0a4
 ret}}
__declspec(naked) static void stubState2(){__asm{        // 0x47a2b9: mov edx,[0x620540] → 0x47a2bf
 mov edx,dword ptr ds:[0x620540]
 test esi,esi
 jz done
 push ecx
 mov ecx,edx
 and ecx,0xffffff00
 cmp ecx,0x200
 pop ecx
 jne done}
 BGMKEEP_TEST_ESI(hit2)
 __asm{jmp done
hit2:
 mov edx,0x100
done:
 push 0x47a2bf
 ret}}
__declspec(naked) static void stubState3(){__asm{        // 0x47a566: mov eax,[0x620540] → 0x47a56b
 mov eax,dword ptr ds:[0x620540]
 test esi,esi
 jz done
 push ecx
 mov ecx,eax
 and ecx,0xffffff00
 cmp ecx,0x200
 pop ecx
 jne done}
 BGMKEEP_TEST_ESI(hit3)
 __asm{jmp done
hit3:
 mov eax,0x100
done:
 push 0x47a56b
 ret}}
__declspec(naked) static void stubLoading(){__asm{       // 0x47a9b6: cmp dword ptr [0x620540],0x202 → 0x47a9c0 (je): a kept s is "not loading"
 test esi,esi
 jz normal}
 BGMKEEP_TEST_ESI(hit4)
 __asm{
normal:
 cmp dword ptr ds:[0x620540],0x202
 push 0x47a9c0
 ret
hit4:
 cmp esp,1
 push 0x47a9c0
 ret}}
