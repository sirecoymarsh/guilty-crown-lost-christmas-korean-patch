// Claude 11-24: the engine's lock-order inversion between script threads (user "사운드 모드 반응이 굉장히 느린데?").
// Script processes (CreateProcess) are real OS threads (0x48d380, thread function 0x473650); they and the render thread
// (0x44ce90) take turns through the object mutex M ([0x6212b4]; lock 0x44abc0, unlock 0x44ac00).
//  - PassageTime()/RemainTime(): the VM (0x43b2bb, 0x43af10) locks M and calls 0x44c4c0, which - when the delete lock E
//    (manual-reset event [0x54ed04]) is taken - waits for E up to 1000 ms with M still held, then answers 0.
//  - Delete() (0x40e310 -> 0x449e50) comes in without M, takes E first (ResetEvent at 0x449ef3) and only then locks M
//    (0x449f37); it gives both back at its end. Every object kind goes this way (colors, pictures, texts).
// So when one script thread deletes while another asks a sound for its time, each holds what the other needs until the
// 1000 ms time-out. The render thread needs M for every frame: the screen stands still for 1.02 s (2.02 s when two
// threads were asking), and the time function's answer 0 makes PassageTime jump to the full length for that tick.
// The sound screen made it common: the bar process asks every 16 ms, the lyrics process every 100 ms, and the title
// hint process deletes on every row the cursor crosses (hidden runs pf_/pp_/pr_*: every gap over 0.6 s was 1.02 s or
// 2.02 s). The story scenes with song lyrics have the same pair (lyrics process against the main script's Delete).
// Here: before the engine's function, while E is taken, give M back, wait for E and lock M again - the order Delete
// uses. The engine's own wait is cut to 0 ms, so nothing blocks on E with M held; if it bailed out because E was taken
// in between (its Delete cannot finish without M, so E still shows taken), go round again. After a second in all,
// answer as the engine did (0).
// The second ring (runs lk_tr_open_074642, lk_mc_*: 1-4 s on nearly every song change while one plays): deleting a
// process object whose thread is running. The destructor (0x45ad80) sets the thread's state [ctx+4] to 0, wakes it and
// waits for the thread to end - 100 ms; then it marks every called function's frame stopped too and waits 1500 ms, and
// 1500 ms more with M held; then TerminateThread - all while the Delete that reached it still holds [0x54ed08] and E.
// The VM (0x4737f0) looks at the frame's [ctx+4] between statements, so the thread ends once its current engine
// function returns. But that function can be waiting for the deleter's locks: PassageTime for E (a second), the
// thread's own Delete (0x449e50) for [0x54ed08] and E (1500 ms twice each) - which is the 1 s and the 3.1 s.
// Here: a thread that has been asked to stop and still finds those locks taken 30 ms later stops there - its frames
// are marked as the destructor's second step would mark them at 100 ms, and the function returns without doing its
// work (as the engine's own time-out or TerminateThread would leave it). For that, Delete's wait for the two locks is
// done here in short slices before the engine's function runs (which then finds them free). The 30 ms keep the
// original meaning of Request(process, Stop) - the thread runs on until its called functions have returned - when an
// unrelated Delete merely holds the locks for a moment; only a Delete that waits for this thread holds them that long.
// Nothing changes for a thread that is not being stopped, other than that it waits here instead of inside the engine.
// The thread's own record comes from the script thread function 0x473650 (stdcall, its one argument), kept per thread.
// Test runs (N2HD_PROFILE_DIR): N2HD_TEST_LOCKFIX_OFF=1 keeps the engine's behaviour for A/B runs,
// N2HD_TEST_LOCKFIX_NOSTOP=1 leaves out only the stop-request part; locks.log gets a line for each time a function
// had to step aside or stopped.
static void* origRemainTime;static void* origDelete;
static bool lockFixOn=true,lockFixLog=false,lockFixStopAware=true;
static DWORD scriptTls=TlsAlloc();static void* origScriptThread;
static void __stdcall scriptThreadNote(void* ctx){if(scriptTls!=TLS_OUT_OF_INDEXES)TlsSetValue(scriptTls,ctx);}
__declspec(naked) static void hookScriptThread(){__asm{
 push dword ptr [esp+4]
 call scriptThreadNote
 jmp dword ptr [origScriptThread]
}}
static bool scriptStopAsked(){if(!lockFixStopAware||scriptTls==TLS_OUT_OF_INDEXES)return false;const volatile LONG* c=(const volatile LONG*)TlsGetValue(scriptTls);return c&&c[1]==0;}
// The destructor's second step (0x45ae79), for this thread's own frames: [ctx+0x1f34] is the called function's frame,
// [ctx+0x1f38] its caller's. With them marked the VM ends the thread when the current engine function returns.
static void scriptStopNow(){if(scriptTls==TLS_OUT_OF_INDEXES)return;char* root=(char*)TlsGetValue(scriptTls);if(!root)return;
 for(char* c=*(char**)(root+0x1f34);c;c=*(char**)(c+0x1f34)){*(volatile LONG*)(c+4)=0;*(char**)(c+0x1f38)=0;}}
static void lockFixNote(const char* what,const char* name,DWORD ms){if(!lockFixLog)return;char line[200],path[MAX_PATH];
 wsprintfA(line,"%lu %s %lu ms %.60s\r\n",GetTickCount(),what,ms,name?name:"");wsprintfA(path,"%s\\locks.log",profileDir);
 HANDLE h=CreateFileA(path,FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,0,OPEN_ALWAYS,0,0);if(h!=INVALID_HANDLE_VALUE){DWORD w;WriteFile(h,line,lstrlenA(line),&w,0);CloseHandle(h);}}
static int __cdecl hookRemainTime(const char* name){typedef int(__cdecl* Fn)(const char*);typedef void(__cdecl* Lock)();
 Fn engine=(Fn)origRemainTime;
 if(!lockFixOn){if(!lockFixLog)return engine(name);DWORD t=GetTickCount();int r=engine(name);DWORD d=GetTickCount()-t;if(d>=100)lockFixNote("engine-waited",name,d);return r;}   // A/B runs: how long the engine's own function sat in its wait
 DWORD t0=GetTickCount(),stopAt=0;bool stepped=false,stopSeen=false;
 for(;;){HANDLE e=*(HANDLE*)0x54ed04;if(e==INVALID_HANDLE_VALUE||!e)return engine(name);
  if(WaitForSingleObject(e,0)==WAIT_TIMEOUT){   // a Delete holds E and needs M: step aside
   if(scriptStopAsked()){DWORD now=GetTickCount();if(!stopSeen){stopSeen=true;stopAt=now;}
    else if(now-stopAt>=30){scriptStopNow();lockFixNote("stop-asked",name,now-t0);return engine(name);}}   // that Delete is waiting for this very thread to end
   if(GetTickCount()-t0>=1000){lockFixNote("gave-up",name,GetTickCount()-t0);return engine(name);}   // the engine's answer after a second (0)
   stepped=true;((Lock)0x44ac00)();WaitForSingleObject(e,10);((Lock)0x44abc0)();continue;}
  int r=engine(name);
  if(r==0&&WaitForSingleObject(e,0)==WAIT_TIMEOUT&&GetTickCount()-t0<1000){stepped=true;continue;}   // E was taken between the look above and the engine's own: it answered without reading
  if(stepped)lockFixNote("stepped-aside",name,GetTickCount()-t0);
  return r;}}
// Delete (0x449e50, cdecl, two stack arguments; also called by the Create functions to clear a failed object): wait
// here for its two locks, so a stop request is seen. After 1500 ms the engine's own waits take over.
static int __cdecl hookDelete(void* a,void* b){typedef int(__cdecl* Fn)(void*,void*);Fn engine=(Fn)origDelete;
 if(!lockFixOn||!lockFixStopAware||!b||!*(const char*)b)return engine(a,b);   // (no name: the engine returns at once)
 DWORD t0=GetTickCount(),stopAt=0;bool waited=false,stopSeen=false;
 for(;;){HANDLE hb=*(HANDLE*)0x54ed08,he=*(HANDLE*)0x54ed04;HANDLE busy=0;
  if(hb&&hb!=INVALID_HANDLE_VALUE&&WaitForSingleObject(hb,0)==WAIT_TIMEOUT)busy=hb;
  else if(he&&he!=INVALID_HANDLE_VALUE&&WaitForSingleObject(he,0)==WAIT_TIMEOUT)busy=he;
  if(!busy)break;
  if(scriptStopAsked()){DWORD now=GetTickCount();if(!stopSeen){stopSeen=true;stopAt=now;}
   else if(now-stopAt>=30){scriptStopNow();lockFixNote("delete-stopped",(const char*)b,now-t0);return 0;}}   // the Delete that holds them is waiting for this thread
  if(GetTickCount()-t0>=1500)break;
  waited=true;WaitForSingleObject(busy,5);}
 if(waited)lockFixNote("delete-waited","",GetTickCount()-t0);
 return engine(a,b);}
// After the hooks are in: the switch, and the engine's own wait (0x44c4ff push 1000) down to 0 ms.
static void lockFixInstall(){lockFixLog=profileDir[0]!=0;
 if(profileDir[0]&&GetEnvironmentVariableA("N2HD_TEST_LOCKFIX_NOSTOP",0,0))lockFixStopAware=false;
 if(profileDir[0]&&GetEnvironmentVariableA("N2HD_TEST_LOCKFIX_OFF",0,0)){lockFixOn=false;return;}
 unsigned char* p=(unsigned char*)0x44c4ff;static const unsigned char expected[5]={0x68,0xe8,0x03,0x00,0x00};
 if(memcmp(p,expected,5)){lockFixOn=false;return;}   // not the code this was read from: leave the engine alone
 DWORD old;if(VirtualProtect(p,5,PAGE_EXECUTE_READWRITE,&old)){*(uint32_t*)(p+1)=0;VirtualProtect(p,5,old,&old);FlushInstructionCache(GetCurrentProcess(),p,5);}else lockFixOn=false;}
