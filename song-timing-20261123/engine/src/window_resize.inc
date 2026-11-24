// Claude 11-23: free window size (user: "창 모드 배율이 고정인데 자유롭게 키울 수 없어? 너무 옛날거라 창모드 플레이가 불가능할 정도야").
// Windowed, the engine makes a fixed 1024x576 client: style 0xCA0000 (caption, system menu, minimize; CreateWindowExA,
// SetWindowLongA at 0x491c38), AdjustWindowRect of 1024x576, then SetWindowPos with that size centred (0x4922fc) or only
// moved (0x49234d, SWP_NOSIZE). It reads the mouse 1:1 (0x46b620: GetCursorPos - window rect - SM_CXFIXEDFRAME, and
// - SM_CYCAPTION - SM_CYFIXEDFRAME) and moves it back the same way for keyboard focus (0x46b730 -> SetCursorPos).
// The 4K device already stretches its 4096x2304 canvas to whatever client the window has (Present(0,0,0,0)), so here:
// - the windowed style also gets a sizing frame and a maximize box (import slots of CreateWindowExA, SetWindowLongA,
//   AdjustWindowRect), and the client keeps 16:9 while dragging (WM_SIZING); maximize gives the largest 16:9 client
//   that fits the work area (WM_GETMINMAXINFO), the minimum is 640x360;
// - GetCursorPos answers the point that the engine's 1:1 formula turns into the engine coordinate under the real
//   pointer, and SetCursorPos maps the engine's point back to the real client;
// - the client size and window place are kept in n2hd-options.ini [Window] ClientW/ClientH/X/Y and come back when the
//   engine sizes its window; with nothing saved the first window is the largest 16:9 client of 3/4 of the work-area height.
// Fullscreen (no caption) is left to the engine. [Window] Resizable=0 turns all of this off.
namespace Win {
static const DWORD kBase = 0xCA0000, kExtra = WS_THICKFRAME | WS_MAXIMIZEBOX;
static bool enabled = true;
static int savedW, savedH, savedX, savedY; static bool havePos;
static WNDPROC origProc; static HWND subclassed; static bool applying;
typedef BOOL (WINAPI* GetCursorPosFn)(LPPOINT); typedef BOOL (WINAPI* SetCursorPosFn)(int, int);
typedef HWND (WINAPI* CreateWindowExAFn)(DWORD, LPCSTR, LPCSTR, DWORD, int, int, int, int, HWND, HMENU, HINSTANCE, LPVOID);
typedef LONG (WINAPI* SetWindowLongAFn)(HWND, int, LONG); typedef BOOL (WINAPI* AdjustWindowRectFn)(LPRECT, DWORD, BOOL);
typedef BOOL (WINAPI* SetWindowPosFn)(HWND, HWND, int, int, int, int, UINT);
static GetCursorPosFn prevGetCursorPos; static SetCursorPosFn prevSetCursorPos; static CreateWindowExAFn prevCreate;
static SetWindowLongAFn prevSetLong; static AdjustWindowRectFn prevAdjust; static SetWindowPosFn prevSetPos;

static std::wstring ini() { wchar_t p[MAX_PATH]; if (!GetModuleFileNameW(0, p, MAX_PATH)) return L""; wchar_t* s = wcsrchr(p, L'\\'); if (s) s[1] = 0; return std::wstring(p) + L"n2hd-options.ini"; }
static int readInt(const wchar_t* key, int def, bool* found = 0) { wchar_t v[32]; auto path = ini(); DWORD n = GetPrivateProfileStringW(L"Window", key, L"", v, 32, path.c_str()); if (found) *found = n > 0; return n ? _wtoi(v) : def; }
static void writeInt(const wchar_t* key, int x) { wchar_t v[32]; wsprintfW(v, L"%d", x); WritePrivateProfileStringW(L"Window", key, v, ini().c_str()); }
static void load() {
  enabled = readInt(L"Resizable", 1) != 0;
  savedW = readInt(L"ClientW", 0); savedH = readInt(L"ClientH", 0);
  bool fx = false, fy = false; savedX = readInt(L"X", 0, &fx); savedY = readInt(L"Y", 0, &fy); havePos = fx && fy;
  if (savedW < 640 || savedH < 360 || savedW > 16384 || savedH > 16384) savedW = savedH = 0;
}
static bool windowed(HWND h) { LONG st = GetWindowLongA(h, GWL_STYLE); return (st & WS_CAPTION) == WS_CAPTION; }
static SIZE frame(HWND h) { RECT r = {0, 0, 1000, 1000}; AdjustWindowRectEx(&r, (DWORD)GetWindowLongA(h, GWL_STYLE), FALSE, (DWORD)GetWindowLongA(h, GWL_EXSTYLE)); SIZE s = {r.right - r.left - 1000, r.bottom - r.top - 1000}; return s; }
static RECT workOf(HMONITOR m) { MONITORINFO mi = {sizeof mi}; if (!GetMonitorInfoW(m, &mi)) { RECT r = {0, 0, GetSystemMetrics(SM_CXSCREEN), GetSystemMetrics(SM_CYSCREEN)}; return r; } return mi.rcWork; }
static SIZE fit169(int w, int h) { SIZE s; if (w * 9 >= h * 16) { s.cy = h; s.cx = h * 16 / 9; } else { s.cx = w; s.cy = w * 9 / 16; } return s; }
static void save(HWND h) {
  if (!enabled || !windowed(h) || IsIconic(h)) return;
  RECT c, w; if (!GetClientRect(h, &c) || !GetWindowRect(h, &w) || c.right < 320) return;
  writeInt(L"ClientW", c.right); writeInt(L"ClientH", c.bottom); writeInt(L"X", w.left); writeInt(L"Y", w.top);
  savedW = c.right; savedH = c.bottom; savedX = w.left; savedY = w.top; havePos = true;
}
// Keep the client 16:9 while the user drags an edge or a corner (the opposite edge stays put).
static void lockAspect(HWND h, int edge, RECT* r) {
  SIZE f = frame(h); int cw = r->right - r->left - f.cx, ch = r->bottom - r->top - f.cy;
  if (cw < 640) cw = 640; if (ch < 360) ch = 360;
  if (edge == WMSZ_TOP || edge == WMSZ_BOTTOM) cw = ch * 16 / 9; else ch = cw * 9 / 16;
  int ww = cw + f.cx, wh = ch + f.cy;
  if (edge == WMSZ_LEFT || edge == WMSZ_TOPLEFT || edge == WMSZ_BOTTOMLEFT) r->left = r->right - ww; else r->right = r->left + ww;
  if (edge == WMSZ_TOP || edge == WMSZ_TOPLEFT || edge == WMSZ_TOPRIGHT) r->top = r->bottom - wh; else r->bottom = r->top + wh;
}
static void minMax(HWND h, MINMAXINFO* mm) {
  SIZE f = frame(h); HMONITOR mon = MonitorFromWindow(h, MONITOR_DEFAULTTONEAREST); MONITORINFO mi = {sizeof mi}; GetMonitorInfoW(mon, &mi);
  RECT wk = mi.rcWork; SIZE c = fit169(wk.right - wk.left - f.cx, wk.bottom - wk.top - f.cy);
  mm->ptMinTrackSize.x = 640 + f.cx; mm->ptMinTrackSize.y = 360 + f.cy;
  mm->ptMaxSize.x = c.cx + f.cx; mm->ptMaxSize.y = c.cy + f.cy;
  mm->ptMaxPosition.x = (wk.left - mi.rcMonitor.left) + ((wk.right - wk.left) - mm->ptMaxSize.x) / 2;
  mm->ptMaxPosition.y = (wk.top - mi.rcMonitor.top) + ((wk.bottom - wk.top) - mm->ptMaxSize.y) / 2;
  mm->ptMaxTrackSize.x = mm->ptMaxSize.x > mm->ptMaxTrackSize.x ? mm->ptMaxSize.x : mm->ptMaxTrackSize.x;
  mm->ptMaxTrackSize.y = mm->ptMaxSize.y > mm->ptMaxTrackSize.y ? mm->ptMaxSize.y : mm->ptMaxTrackSize.y;
}
static void testLog(const char* fmt, ...);
static bool testRun();
static LRESULT CALLBACK proc(HWND h, UINT m, WPARAM w, LPARAM l) {
  if (m == WM_WINDOWPOSCHANGED && testRun()) { WINDOWPOS* p = (WINDOWPOS*)l; testLog("WM_WINDOWPOSCHANGED x=%d y=%d cx=%d cy=%d flags=%x", p->x, p->y, p->cx, p->cy, p->flags); }
  if (enabled && windowed(h)) {
    if (m == WM_SIZING) { lockAspect(h, (int)w, (RECT*)l); return TRUE; }
    if (m == WM_GETMINMAXINFO) { LRESULT r = CallWindowProcA(origProc, h, m, w, l); minMax(h, (MINMAXINFO*)l); return r; }
    if (m == WM_EXITSIZEMOVE) save(h);
    if (m == WM_SIZE && (w == SIZE_MAXIMIZED || w == SIZE_RESTORED)) save(h);
  }
  return CallWindowProcA(origProc, h, m, w, l);
}
static void subclass(HWND h) {
  if (!h || subclassed == h) return;
  WNDPROC p = (WNDPROC)GetWindowLongPtrA(h, GWLP_WNDPROC); if (!p || p == proc) return;
  origProc = p; subclassed = h; SetWindowLongPtrA(h, GWLP_WNDPROC, (LONG_PTR)proc);
}
// The client to use when the engine asks for its 1024x576 window: saved, or the largest 16:9 of 3/4 of the work-area height.
static SIZE wantedClient(HMONITOR mon) {
  RECT wk = workOf(mon); int ww = wk.right - wk.left, wh = wk.bottom - wk.top;
  SIZE s; if (savedW && savedH) { s.cx = savedW; s.cy = savedH; } else s = fit169(ww, wh * 3 / 4);
  SIZE cap = fit169(ww, wh); if (s.cx > cap.cx || s.cy > cap.cy) s = cap;   // never larger than the screen (125%/150% displays)
  if (s.cx < 1024 && !(savedW && savedH)) { s.cx = 1024; s.cy = 576; }
  return s;
}

static BOOL WINAPI myGetCursorPos(LPPOINT p) {
  BOOL ok = prevGetCursorPos(p); HWND h = *(HWND*)0x629854;
  if (!ok || !p || !enabled || !h || !windowed(h)) return ok;
  RECT c, w; if (!GetClientRect(h, &c) || c.right <= 0 || c.bottom <= 0 || !GetWindowRect(h, &w)) return ok;
  POINT q = *p; ScreenToClient(h, &q);
  int ex = MulDiv(q.x, 1024, c.right), ey = MulDiv(q.y, 576, c.bottom);
  p->x = w.left + GetSystemMetrics(SM_CXFIXEDFRAME) + ex;
  p->y = w.top + GetSystemMetrics(SM_CYCAPTION) + GetSystemMetrics(SM_CYFIXEDFRAME) + ey;
  return TRUE;
}
static BOOL WINAPI mySetCursorPos(int x, int y) {
  HWND h = *(HWND*)0x629854;
  if (!enabled || !h || !windowed(h)) return prevSetCursorPos(x, y);
  RECT c, w; if (!GetClientRect(h, &c) || !GetWindowRect(h, &w)) return prevSetCursorPos(x, y);
  int ex = x - w.left - GetSystemMetrics(SM_CXFIXEDFRAME), ey = y - w.top - GetSystemMetrics(SM_CYCAPTION) - GetSystemMetrics(SM_CYFIXEDFRAME);
  POINT q = {MulDiv(ex, c.right, 1024), MulDiv(ey, c.bottom, 576)}; ClientToScreen(h, &q);
  return prevSetCursorPos(q.x, q.y);
}
static HWND WINAPI myCreate(DWORD ex, LPCSTR cls, LPCSTR name, DWORD st, int x, int y, int cx, int cy, HWND parent, HMENU menu, HINSTANCE inst, LPVOID param) {
  if (enabled && st == kBase) st |= kExtra;
  return prevCreate(ex, cls, name, st, x, y, cx, cy, parent, menu, inst, param);
}
static LONG WINAPI mySetLong(HWND h, int i, LONG v) {
  if (enabled && i == GWL_STYLE && (DWORD)v == kBase) v |= kExtra;
  return prevSetLong(h, i, v);
}
static BOOL WINAPI myAdjust(LPRECT r, DWORD st, BOOL menu) {
  if (enabled && st == kBase) st |= kExtra;
  return prevAdjust(r, st, menu);
}
// Test runs only (N2HD_PROFILE_DIR): every SetWindowPos the engine makes goes to winpos.log, and the test window is
// never moved by this module (run_test keeps it off every monitor).
static void testLog(const char* fmt, ...) {
  char d[MAX_PATH]; if (!GetEnvironmentVariableA("N2HD_PROFILE_DIR", d, MAX_PATH)) return;
  char line[400]; va_list a; va_start(a, fmt); wvsprintfA(line, fmt, a); va_end(a);
  char path[MAX_PATH]; wsprintfA(path, "%s\\winpos.log", d);
  HANDLE f = CreateFileA(path, FILE_APPEND_DATA, FILE_SHARE_READ, 0, OPEN_ALWAYS, 0, 0); if (f == INVALID_HANDLE_VALUE) return;
  char t[32]; wsprintfA(t, "%lu ", GetTickCount()); DWORD w; WriteFile(f, t, lstrlenA(t), &w, 0); WriteFile(f, line, lstrlenA(line), &w, 0); WriteFile(f, "\r\n", 2, &w, 0); CloseHandle(f);
}
static bool testRun() { static int v = -1; if (v < 0) v = GetEnvironmentVariableA("N2HD_PROFILE_DIR", 0, 0) ? 1 : 0; return v == 1; }
static BOOL WINAPI mySetPos(HWND h, HWND after, int x, int y, int cx, int cy, UINT flags) {
  if (testRun()) { RECT cur = {}; GetWindowRect(h, &cur); testLog("SetWindowPos hwnd=%p after=%p x=%d y=%d cx=%d cy=%d flags=%x cur=%d,%d,%d,%d ret=%p", h, after, x, y, cx, cy, flags, cur.left, cur.top, cur.right, cur.bottom, _ReturnAddress()); }
  if (!enabled || applying || !h || !windowed(h) || !(GetWindowLongA(h, GWL_STYLE) & WS_THICKFRAME)) return prevSetPos(h, after, x, y, cx, cy, flags);
  subclass(h);
  SIZE f = frame(h); bool engineSize = !(flags & SWP_NOSIZE) && cx == 1024 + f.cx && cy == 576 + f.cy;
  bool engineMove = (flags & SWP_NOSIZE) && !(flags & SWP_NOMOVE);
  if (!engineSize && !engineMove) return prevSetPos(h, after, x, y, cx, cy, flags);
  // The monitor the engine meant (it centres on the work area of its own monitor).
  RECT want = {x, y, x + (engineSize ? cx : 1024 + f.cx), y + (engineSize ? cy : 576 + f.cy)};
  HMONITOR mon = MonitorFromRect(&want, MONITOR_DEFAULTTONEAREST);
  SIZE c = engineSize ? wantedClient(mon) : SIZE{0, 0};
  RECT cur; GetWindowRect(h, &cur);
  int ww = engineSize ? c.cx + f.cx : cur.right - cur.left, wh = engineSize ? c.cy + f.cy : cur.bottom - cur.top;
  int nx, ny; bool placed = false;
  if (havePos) { RECT r = {savedX, savedY, savedX + ww, savedY + wh}; HMONITOR m2 = MonitorFromRect(&r, MONITOR_DEFAULTTONULL); if (m2) { RECT wk = workOf(m2); if (r.top >= wk.top - 8 && r.top < wk.bottom - 40) { nx = savedX; ny = savedY; placed = true; } } }
  if (!placed) { RECT wk = workOf(mon); nx = wk.left + ((wk.right - wk.left) - ww) / 2; ny = wk.top + ((wk.bottom - wk.top) - wh) / 2; }
  if (testRun()) { nx = cur.left; ny = cur.top; testLog("  -> keep test window at %d,%d size %d,%d", nx, ny, ww, wh); }
  applying = true;
  BOOL r = prevSetPos(h, after, nx, ny, engineSize ? ww : cx, engineSize ? wh : cy, flags);
  applying = false;
  return r;
}
static void patch(uintptr_t at, void* fn, void** prev) { void** slot = (void**)at; *prev = *slot; DWORD old; if (VirtualProtect(slot, 4, PAGE_READWRITE, &old)) { *slot = fn; VirtualProtect(slot, 4, old, &old); } }
static void install() {
  load(); if (!enabled) return;
  patch(0x511318, (void*)&myGetCursorPos, (void**)&prevGetCursorPos);   // after N2HD_TestCursorInit: chains to the test cursor
  patch(0x511314, (void*)&mySetCursorPos, (void**)&prevSetCursorPos);
  patch(0x5112b4, (void*)&myCreate, (void**)&prevCreate);
  patch(0x5112b0, (void*)&mySetLong, (void**)&prevSetLong);
  patch(0x5112c0, (void*)&myAdjust, (void**)&prevAdjust);
  patch(0x5112bc, (void*)&mySetPos, (void**)&prevSetPos);
}
}  // namespace Win
