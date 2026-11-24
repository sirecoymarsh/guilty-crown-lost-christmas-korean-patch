// F8: picture quality [4K | 4K text with 1x art | original] (user 11-01 "is there no way to switch between 4K and the
// original?"; vn-qol hd-art-switch). 0 = 4x art and 4K text, 1 = 1x art and 4K text, 2 = 1x art and the engine's own 1x
// text (text surfaces go down the compatibility path). Kept in n2hd-options.ini [Display] Quality next to the game.
// A change redraws the whole screen at once (the engine renders only when 0x629488 is set, over the rectangle at
// 0x62949c; the full screen is 0,0,0x400,0x240 as its capture code sets it) and shows the setting at the top right for 1.6 s.
// N2HD_TEST_QUALITY_MS (with N2HD_PROFILE_DIR) steps the setting on a timer for hidden test runs.
static volatile LONG gRepaint=0,gRendering=0;static volatile DWORD gNoticeUntil=0;static volatile LONG gNoticeOn=0;
static IDirect3DTexture9* noticeTex;static LONG noticeTexQuality=-1;static int noticeW,noticeH;
// 11-24: the notice shows any short message (F8 quality, and kr_keys.inc: J story language); a new serial rebuilds it.
static wchar_t gNoticeMsg[96];static volatile LONG gNoticeSerial=0,gNoticeBox=0;static volatile DWORD gNoticeLastFrame=0;
static void noticeShow(const wchar_t* s){lstrcpynW(gNoticeMsg,s,96);InterlockedExchange(&gNoticeBox,0);InterlockedIncrement(&gNoticeSerial);gNoticeUntil=GetTickCount()+1600;gNoticeLastFrame=GetTickCount();InterlockedExchange(&gNoticeOn,1);InterlockedExchange(&gRepaint,2);}
static void noticeShowBox(const wchar_t* s){noticeShow(s);InterlockedExchange(&gNoticeBox,1);}   // 11-24 J/K: above the text window
static const wchar_t* qualityText(LONG q){return q==0?L"화질  4K":q==1?L"화질  그림 원본 · 글자 4K":L"화질  원본";}
static std::wstring qualityFile(){return artGameDir()+L"n2hd-options.ini";}
static void qualitySave(LONG q){wchar_t b[8];wsprintfW(b,L"%d",(int)q);WritePrivateProfileStringW(L"Display",L"Quality",b,qualityFile().c_str());}
static DWORD WINAPI qualityThread(void*){bool down=false;DWORD testEvery=0,testLast=GetTickCount(),keepEvery=0,keepLast=testLast;
 {wchar_t v[16],d[MAX_PATH];if(GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",d,MAX_PATH)){if(GetEnvironmentVariableW(L"N2HD_TEST_QUALITY_MS",v,16))testEvery=(DWORD)_wtoi(v);
  if(GetEnvironmentVariableW(L"N2HD_TEST_KEEPALIVE_MS",v,16))keepEvery=(DWORD)_wtoi(v);}}   // test only: a still screen presents no frames, so no test shots
 for(;;){Sleep(15);DWORD now=GetTickCount();HWND hwnd=*(HWND*)0x629854;bool fg=false;
  if(keepEvery&&now-keepLast>=keepEvery){keepLast=now;if(gRepaint<1)InterlockedExchange(&gRepaint,1);}
  if(hwnd){DWORD pid=0;GetWindowThreadProcessId(GetForegroundWindow(),&pid);fg=pid==GetCurrentProcessId();}
  bool key=fg&&(GetAsyncKeyState(VK_F8)&0x8000);bool press=key&&!down;down=key;
  if(testEvery&&now-testLast>=testEvery){testLast=now;press=true;}
  if(press){LONG q=(gQuality+1)%3;InterlockedExchange(&gQuality,q);qualitySave(q);noticeShow(qualityText(q));}
  // 11-24: a J/K press reloads the line (~1.2 s with no frames), which used to eat the notice's 1.6 s - while no frame has
  // drawn the notice for a while, hold its deadline back (the 15 ms loop adds its own step).
  {static DWORD prevLoop=0;DWORD dt=prevLoop?now-prevLoop:0;prevLoop=now;
   if(gNoticeOn&&gNoticeLastFrame&&now-gNoticeLastFrame>200&&dt<1000)gNoticeUntil+=dt;}
  if(gNoticeOn&&(LONG)(now-gNoticeUntil)>=0){InterlockedExchange(&gNoticeOn,0);InterlockedExchange(&gRepaint,2);gNoticeLastFrame=0;}
  if((gRepaint>0||gNoticeOn)&&!gRendering){int* d=(int*)0x62949c;d[0]=0;d[1]=0;d[2]=0x400;d[3]=0x240;*(int*)0x629488=1;}
 }}
// Test only (N2HD_PROFILE_DIR + N2HD_TEST_CURSOR="x,y" in engine 1024x576 coordinates, or the file cursor.txt in the
// profile folder, re-read on every call so a test can move it): the engine reads the mouse only with GetCursorPos
// (0x46b644, through the import slot 0x511318) minus the window rectangle and frame, and a hidden test window never has
// the real cursor; the slot then answers with the screen point of that engine coordinate (windowed: frame and caption).
static int testCursorX,testCursorY;static wchar_t testCursorFile[MAX_PATH];
static BOOL WINAPI testGetCursorPos(POINT* p){HWND hwnd=*(HWND*)0x629854;RECT r;if(!p||!hwnd||!GetWindowRect(hwnd,&r))return GetCursorPos(p);
 if(testCursorFile[0]){FILE* f=_wfopen(testCursorFile,L"rb");if(f){int x,y;if(fscanf_s(f,"%d,%d",&x,&y)==2){testCursorX=x;testCursorY=y;}fclose(f);}}
 // 11-23: windowed, answer the real screen point over the (possibly resized) client, so window_resize.inc maps it back
 // like a real pointer; fullscreen keeps the engine's formula as before.
 RECT c;if((GetWindowLongA(hwnd,GWL_STYLE)&WS_CAPTION)==WS_CAPTION&&GetClientRect(hwnd,&c)&&c.right>0&&c.bottom>0){POINT q={MulDiv(testCursorX,c.right,1024),MulDiv(testCursorY,c.bottom,576)};ClientToScreen(hwnd,&q);*p=q;return TRUE;}
 p->x=r.left+GetSystemMetrics(SM_CXFIXEDFRAME)+testCursorX;p->y=r.top+GetSystemMetrics(SM_CYCAPTION)+GetSystemMetrics(SM_CYFIXEDFRAME)+testCursorY;return TRUE;}
static void testCursorInit(){wchar_t d[MAX_PATH],v[32];if(!GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",d,MAX_PATH))return;
 bool fixed=GetEnvironmentVariableW(L"N2HD_TEST_CURSOR",v,32)&&swscanf_s(v,L"%d,%d",&testCursorX,&testCursorY)==2;
 if(GetEnvironmentVariableW(L"N2HD_TEST_CURSOR_FILE",0,0)){wsprintfW(testCursorFile,L"%s\\cursor.txt",d);fixed=true;}
 if(!fixed)return;void** slot=(void**)0x511318;DWORD old;if(VirtualProtect(slot,4,PAGE_READWRITE,&old)){*slot=(void*)&testGetCursorPos;VirtualProtect(slot,4,old,&old);}}
extern "C" void __cdecl N2HD_TestCursorInit(){static bool done=false;if(!done){done=true;testCursorInit();}}   // from N2HD_Install, also in native test runs
// Called at the start of each engine render (N2HD_Clear): the saved setting and the key thread, once; a full-screen
// render pays off a pending repaint.
static void qualityInit(){static bool done=false;InterlockedExchange(&gRendering,1);
 if(!done){done=true;N2HD_TestCursorInit();LONG q=(LONG)GetPrivateProfileIntW(L"Display",L"Quality",0,qualityFile().c_str());if(q<0||q>2)q=0;InterlockedExchange(&gQuality,q);
  HANDLE h=CreateThread(0,0,qualityThread,0,0,0);if(h){SetThreadPriority(h,THREAD_PRIORITY_BELOW_NORMAL);CloseHandle(h);}}
 int* d=(int*)0x62949c;if(gRepaint>0&&d[0]<=0&&d[1]<=0&&d[2]>=0x400&&d[3]>=0x240)InterlockedDecrement(&gRepaint);krKeysEngine();}
static void qualityRelease(){if(noticeTex){noticeTex->Release();noticeTex=0;}noticeTexQuality=-1;}
static void noticeBuild(LONG q){qualityRelease();const wchar_t* s=gNoticeMsg;
 HDC dc=CreateCompatibleDC(0);HFONT f=CreateFontW(-46,0,0,0,FW_BOLD,0,0,0,DEFAULT_CHARSET,0,0,ANTIALIASED_QUALITY,0,L"Malgun Gothic");HGDIOBJ of=SelectObject(dc,f);
 // 11-24 user "게임에 어울리는 UI로": the settings screen's cell look - gray rim, a gray strip on the left (like its number
 // boxes), near-black inside, light-gray text.
 const int strip=14;SIZE sz={};GetTextExtentPoint32W(dc,s,lstrlenW(s),&sz);int px=34,py=20,w=sz.cx+px*2+strip,h=sz.cy+py*2;
 BITMAPINFO bi={};bi.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);bi.bmiHeader.biWidth=w;bi.bmiHeader.biHeight=-h;bi.bmiHeader.biPlanes=1;bi.bmiHeader.biBitCount=32;void* bits=0;
 HBITMAP bm=CreateDIBSection(dc,&bi,DIB_RGB_COLORS,&bits,0,0);if(bm&&bits){HGDIOBJ ob=SelectObject(dc,bm);memset(bits,0,(size_t)w*h*4);SetBkMode(dc,TRANSPARENT);SetTextColor(dc,RGB(255,255,255));TextOutW(dc,px+strip,py,s,lstrlenW(s));GdiFlush();
  IDirect3DTexture9* tx=0;if(SUCCEEDED(dev->CreateTexture(w,h,1,D3DUSAGE_DYNAMIC,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&tx,0))){D3DLOCKED_RECT l;if(SUCCEEDED(tx->LockRect(0,&l,0,D3DLOCK_DISCARD))){
   for(int y=0;y<h;++y){const uint32_t* src=(const uint32_t*)bits+(size_t)y*w;uint32_t* dst=(uint32_t*)((char*)l.pBits+y*l.Pitch);
    for(int x=0;x<w;++x){unsigned t=(src[x]>>8)&255;bool edge=x<2||y<2||x>=w-2||y>=h-2,band=x<2+strip;
     unsigned a,c;if(edge){a=255;c=56;}else if(band){a=255;c=60;}else{a=t+(255-t)*235/255;c=t*220/255+(255-t)*11*235/(255*255);}
     dst[x]=(a<<24)|(c<<16)|(c<<8)|c;}}   // premultiplied: light-gray text on a near-black cell, gray rim and left strip
   tx->UnlockRect(0);noticeTex=tx;noticeTexQuality=q;noticeW=w;noticeH=h;}else tx->Release();}
  SelectObject(dc,ob);}
 if(bm)DeleteObject(bm);SelectObject(dc,of);DeleteObject(f);DeleteDC(dc);}
// Before Present: the notice on top of the frame (every frame during it is a full repaint, so nothing builds up).
static void qualityOverlay(){if(gNoticeOn)gNoticeLastFrame=GetTickCount();
 if(!gNoticeOn||(LONG)(GetTickCount()-gNoticeUntil)>=0)return;LONG q=gNoticeSerial;if(!noticeTex||noticeTexQuality!=q)noticeBuild(q);if(!noticeTex)return;begin();if(!begun)return;
 // 11-24 J/K notices (gNoticeBox): centred just above the text window (engine y 388 of 576) — user "대사창 상단에서 … 지금은 … 보기 힘들다"
 float x0=(float)(W-noticeW-56),y0=48.f;if(gNoticeBox){x0=(float)((W-noticeW)/2);y0=(float)(H*388/576-noticeH-H*10/576);if(y0<0)y0=0;}
 float x1=x0+noticeW,y1=y0+noticeH;V v[4]={{x0-.5f,y0-.5f,0,1,0xffffffff,0,0,0,0},{x1-.5f,y0-.5f,0,1,0xffffffff,1,0,0,0},{x1-.5f,y1-.5f,0,1,0xffffffff,1,1,0,0},{x0-.5f,y1-.5f,0,1,0xffffffff,0,1,0,0}};
 RECT rc={0,0,W,H};dev->SetPixelShader(pixelShader);float flags[4]={};dev->SetPixelShaderConstantF(0,flags,1);dev->SetTexture(0,noticeTex);dev->SetTexture(1,0);dev->SetTexture(2,0);dev->SetTexture(3,0);dev->SetScissorRect(&rc);
 dev->SetRenderState(D3DRS_BLENDOP,D3DBLENDOP_ADD);dev->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);dev->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);dev->DrawPrimitiveUP(D3DPT_TRIANGLEFAN,2,v,sizeof(V));
 dev->EndScene();begun=false;}
// Claude 11-21: the third config page (화질 row) sets the same setting as F8, without the notice (the page shows it).
extern "C" void __cdecl N2HD_SetQuality(int q){if(q<0||q>2)return;InterlockedExchange(&gQuality,(LONG)q);qualitySave(q);InterlockedExchange(&gRepaint,2);}
extern "C" int __cdecl N2HD_GetQuality(){return (int)gQuality;}
