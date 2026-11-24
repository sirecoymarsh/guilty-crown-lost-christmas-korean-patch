// Claude 11-24: H (key list at the bottom) and J (story text Japanese <-> Korean), and the Japanese glyphs J needs.
// User: "화면 최하단에 키보드 단축키 메뉴를 표시하게 해줘" + "H키를 배정해 그것만 키 리스트 숨기기로",
//       "J키를 누르면 인게임에서 일본어와 한국어를 교체 가능하게 해줘" (story text).
// - Keys come from the window's own WM_KEYDOWN (a subclass on the main window; real keys and test-posted keys alike).
//   SetShortcut("H") was never called by the engine (no free slot past the original eight) and a script process
//   polling $SYSTEM_keydown_h never ran (hidden tests kb3..kb6), so the keys are taken here.
// - H: the picture nss/kr_keybar.png (made in function.nss LoadBox, faded in with the text box) is simply not drawn
//   while off. Kept in n2hd-options.ini [Display] KeyBar (1 shown, 0 hidden).
// - J: flips the global #KR_JP (a double at +0x10, created by 0_boot) on the render thread, only while a line is waiting
//   ($TypeBeginIn) and the backlog and the menu are closed (J inside the backlog stays the game's "back to the last
//   choice"). Every story block has a Japanese twin right after it, if(#KR_JP){ <PRE ...>[jtextNNNN] ... </PRE> }
//   (sound_seek/jp_twin.py), so the next line comes up in the other language. A notice says which.
//   11-24: standard lines now load both languages and swap on the spot (sound_seek/jp_swap.py, KrJSwapTick), and J/K
//   cycle four states (Korean, Japanese, Japanese over Korean, Korean over Japanese) — see krKeysEngine.
// - Glyphs: Japanese characters cp949 does not have (222, e.g. ー 気 体) sit on UHC codes the Korean scripts never use
//   (jp_map.h); kana and kanji, mapped or not, are drawn with a Japanese font (Noto Sans CJK JP from <game>\fonts, else
//   Yu Gothic / Meiryo / MS Gothic). The engine's own GetGlyphOutlineA (import slot 0x511054) and the 4K glyphs
//   (N2HD_Glyph) both go through ggoA; the backlog decodes through jpMapped.
#include "jp_map.h"
static volatile LONG gKeyBarOff=0,gPendingJ=0,gPendingK=0,gPendingSL=0;static std::unordered_set<void*> keyBarData;static WNDPROC kkPrev;static HWND kkWnd;

static wchar_t jpMapped(unsigned code){if(code<0x8141||code>0xa0fe)return 0;int lo=0,hi=kJpMapN-1;while(lo<=hi){int m=(lo+hi)/2;unsigned c=kJpMap[m].code;if(c==code)return kJpMap[m].ch;if(c<code)lo=m+1;else hi=m-1;}return 0;}
static bool jpRange(wchar_t w){return (w>=0x3040&&w<=0x30ff)||(w>=0x4e00&&w<=0x9fff)||w==0x3005||w==0x3006;}
static wchar_t jpWide(unsigned code){if(code<0x8000)return 0;wchar_t w=jpMapped(code);if(w)return w;char s[2]={(char)(code>>8),(char)code};wchar_t u=0;
 if(MultiByteToWideChar(949,MB_ERR_INVALID_CHARS,s,2,&u,1)!=1)return 0;return jpRange(u)?u:0;}
static const wchar_t* jpFace(){static wchar_t face[LF_FACESIZE];static bool done=false;if(done)return face[0]?face:0;done=true;
 const wchar_t* tries[]={L"Noto Sans CJK JP Medium",L"Noto Sans CJK JP",L"Yu Gothic UI",L"Yu Gothic",L"Meiryo",L"MS Gothic"};HDC dc=CreateCompatibleDC(0);
 for(auto t:tries){LOGFONTW lf={};lf.lfHeight=-24;lf.lfCharSet=DEFAULT_CHARSET;lstrcpynW(lf.lfFaceName,t,LF_FACESIZE);HFONT f=CreateFontIndirectW(&lf);if(!f)continue;HGDIOBJ o=SelectObject(dc,f);wchar_t got[LF_FACESIZE]={};GetTextFaceW(dc,LF_FACESIZE,got);SelectObject(dc,o);DeleteObject(f);
  if(!lstrcmpiW(got,t)){lstrcpynW(face,t,LF_FACESIZE);break;}}
 DeleteDC(dc);return face[0]?face:0;}
struct JpFontKey{LONG h,w,wt;BYTE it;bool operator==(const JpFontKey& o)const{return h==o.h&&w==o.w&&wt==o.wt&&it==o.it;}};
static HFONT jpFontFor(HDC dc){const wchar_t* face=jpFace();if(!face)return 0;HFONT cur=(HFONT)GetCurrentObject(dc,OBJ_FONT);LOGFONTW lf={};if(!cur||!GetObjectW(cur,sizeof lf,&lf))return 0;
 static std::vector<std::pair<JpFontKey,HFONT>> cache;static SRWLOCK lk=SRWLOCK_INIT;JpFontKey k{lf.lfHeight,lf.lfWidth,lf.lfWeight,lf.lfItalic};
 AcquireSRWLockExclusive(&lk);for(auto& c:cache)if(c.first==k){HFONT f=c.second;ReleaseSRWLockExclusive(&lk);return f;}
 lf.lfCharSet=DEFAULT_CHARSET;lstrcpynW(lf.lfFaceName,face,LF_FACESIZE);HFONT f=CreateFontIndirectW(&lf);if(f&&cache.size()<64)cache.push_back({k,f});ReleaseSRWLockExclusive(&lk);return f;}
typedef DWORD (WINAPI* GgoAFn)(HDC,UINT,UINT,LPGLYPHMETRICS,DWORD,LPVOID,const MAT2*);static GgoAFn ggoPrev=GetGlyphOutlineA;
static DWORD WINAPI ggoA(HDC dc,UINT code,UINT fmt,LPGLYPHMETRICS gm,DWORD cb,LPVOID buf,const MAT2* mat){wchar_t w=jpWide(code);if(!w)return ggoPrev(dc,code,fmt,gm,cb,buf,mat);
 HFONT f=jpFontFor(dc);if(!f)return ggoPrev(dc,code,fmt,gm,cb,buf,mat);HGDIOBJ o=SelectObject(dc,f);DWORD r=GetGlyphOutlineW(dc,w,fmt,gm,cb,buf,mat);SelectObject(dc,o);return r;}

static void kkLog(const char* fmt,...){static int on=-1;static char path[MAX_PATH];if(on<0){char d[MAX_PATH];on=GetEnvironmentVariableA("N2HD_PROFILE_DIR",d,MAX_PATH)?1:0;if(on)wsprintfA(path,"%s\\keys.log",d);}if(!on)return;char line[300];va_list a;va_start(a,fmt);wvsprintfA(line,fmt,a);va_end(a);HANDLE f=CreateFileA(path,FILE_APPEND_DATA,FILE_SHARE_READ,0,OPEN_ALWAYS,0,0);if(f==INVALID_HANDLE_VALUE)return;char t[24];wsprintfA(t,"%lu ",GetTickCount());DWORD w;WriteFile(f,t,lstrlenA(t),&w,0);WriteFile(f,line,lstrlenA(line),&w,0);WriteFile(f,"\r\n",2,&w,0);CloseHandle(f);}
static void keyBarNote(const char* name,void* t){if(!t)return;void* d=pv(t,0x28);if(!d)return;
 // 11-24: the recall (replay) key list kr_keybar_rp.png hides with H too
 if(name&&(!_stricmp(name,"nss/kr_keybar.png")||!_stricmp(name,"nss\\kr_keybar.png")||!_stricmp(name,"nss/kr_keybar_rp.png")||!_stricmp(name,"nss\\kr_keybar_rp.png")))keyBarData.insert(d);else if(!keyBarData.empty())keyBarData.erase(d);}
static bool keyBarHidden(void* t){return gKeyBarOff&&!keyBarData.empty()&&keyBarData.count(pv(t,0x28))!=0;}
static void keyBarSave(){WritePrivateProfileStringW(L"Display",L"KeyBar",gKeyBarOff?L"0":L"1",qualityFile().c_str());}
static LRESULT CALLBACK kkProc(HWND h,UINT m,WPARAM w,LPARAM l){
 if(m==WM_KEYDOWN)kkLog("keydown vk=%x l=%x",(unsigned)w,(unsigned)l);
 if(m==WM_KEYDOWN&&!(l&0x40000000)){
  if(w=='H'){InterlockedExchange(&gKeyBarOff,gKeyBarOff?0:1);keyBarSave();InterlockedExchange(&gRepaint,2);}
  else if(w=='J'){InterlockedExchange(&gPendingJ,1);InterlockedExchange(&gRepaint,2);}
  else if(w=='K'){InterlockedExchange(&gPendingK,1);InterlockedExchange(&gRepaint,2);}
  else if(w=='S'||w=='L'){InterlockedExchange(&gPendingSL,(LONG)w);InterlockedExchange(&gRepaint,2);}}
 return CallWindowProcA(kkPrev,h,m,w,l);}
static double dv(const char* name){auto v=((unsigned char*(__cdecl*)(const char*))0x465130)(name);return v?*(double*)(v+0x10):0.0;}
// The render thread, at the start of each engine render (qualityInit): set up once, then apply a pending J.
static void krKeysEngine(){static bool once=false;
 if(!once){once=true;kkLog("keys engine start face=%ls",jpFace()?jpFace():L"(none)");InterlockedExchange(&gKeyBarOff,GetPrivateProfileIntW(L"Display",L"KeyBar",1,qualityFile().c_str())?0:1);
  void** slot=(void**)0x511054;DWORD old;if(*slot&&VirtualProtect(slot,4,PAGE_READWRITE,&old)){ggoPrev=(GgoAFn)*slot;*slot=(void*)&ggoA;VirtualProtect(slot,4,old,&old);}}
 HWND hwnd=*(HWND*)0x629854;if(hwnd&&hwnd!=kkWnd&&IsWindow(hwnd)){WNDPROC p=(WNDPROC)GetWindowLongPtrA(hwnd,GWLP_WNDPROC);if(p&&p!=kkProc){kkPrev=p;kkWnd=hwnd;SetWindowLongPtrA(hwnd,GWLP_WNDPROC,(LONG_PTR)kkProc);kkLog("subclass hwnd=%p prev=%p",hwnd,p);}}
 // 11-24 user "회상 모드에선 작동하지 않는 S 키 … 키를 누르면 회상 모드에선 저장을 할 수 없습니다 같은 경고": recall replay
 // (kr_scenario KsPlay sets $KR_REPLAY and locks save/load) - say so above the text window.
 LONG psl=InterlockedExchange(&gPendingSL,0);
 if(psl&&dv("$KR_REPLAY")!=0.0)noticeShowBox(psl=='S'?L"회상에서는 저장할 수 없습니다":L"회상에서는 불러올 수 없습니다");
 LONG pj=InterlockedExchange(&gPendingJ,0),pk=InterlockedExchange(&gPendingK,0);
 if(pj||pk){
  bool waiting=dv("$TypeBeginIn")!=0.0,backlog=dv("$SYSTEM_backlog_enable")!=0.0,menu=dv("$SYSTEM_menu_enable")!=0.0;
  auto v=((unsigned char*(__cdecl*)(const char*))0x465130)("#KR_JP");
  kkLog("%s pending: var=%p waiting=%d backlog=%d menu=%d kr_jp=%d",pj?"J":"K",v,(int)waiting,(int)backlog,(int)menu,v?(int)(*(double*)(v+0x10)*10):-1);
  // 11-24 「해당 구역 로딩된건 바뀌지 않네」 + 「K를 누르면 한국어, JJ를 누르면 일한 병기, KK를 누르면 한일 병기 … K도 마찬가지」:
  // #KR_JP 0 Korean, 1 Japanese, 2 Japanese over Korean, 3 Korean over Japanese.
  // J: Japanese -> Japanese+Korean -> Korean (from anything else, Japanese). K: Korean -> Korean+Japanese -> Japanese.
  // Standard lines carry both languages (jp_swap.py); the script's KrJSwapTick sees #KR_JP change and re-lays the line on
  // screen. Other lines ($KR_PASSON off) switch from the next one.
  if(v&&waiting&&!backlog&&!menu){double& d=*(double*)(v+0x10);int m=(int)(d+0.5);if(m<0||m>3)m=0;
   if(pj)m=m==1?2:m==2?0:1;
   if(pk)m=m==0?3:m==3?1:0;
   // recall replay has no checkpoints (backlog_jump replaying()), so the line can't restart there: next line
   d=(double)m;bool now=dv("$KR_PASSON")!=0.0&&dv("$KR_REPLAY")==0.0;
   static const wchar_t* const name[4]={L"본문  한국어",L"본문  일본어",L"본문  일본어 + 한국어",L"본문  한국어 + 일본어"};
   static const wchar_t* const hint[4]={L"K 한 번 더 → 한국어 + 일본어",L"J 한 번 더 → 일본어 + 한국어",L"J 한 번 더 → 한국어",L"K 한 번 더 → 일본어"};
   wchar_t msg[96];if(now)wsprintfW(msg,L"%s      %s",name[m],hint[m]);else wsprintfW(msg,L"%s  (다음 대사부터)",name[m]);
   noticeShowBox(msg);}}}

static bool jpRangeB(wchar_t w){return jpRange(w);}
static HFONT jpFontForB(HDC dc){return jpFontFor(dc);}
