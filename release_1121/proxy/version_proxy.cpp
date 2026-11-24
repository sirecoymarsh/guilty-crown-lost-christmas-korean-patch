// Claude 11-21: version.dll next to "GUILTY CROWN LOST XMAS.exe" so that every way of starting the game (the game's own
// icon, a shortcut, a store launcher) gets the Korean runtime (n2hd_runtime.dll), not only Korean4K.exe.
// The game imports version.dll, so Windows loads this file from the game folder first. All 17 exports jump to the
// real system version.dll. At process attach the game's entry point gets a 5-byte jump to start(); start() puts the
// bytes back, loads n2hd_runtime.dll from the game folder and calls its N2HD_Install (the same call Korean4K.exe makes
// before the game runs), then continues at the real entry point. If Korean4K.exe already put the runtime in, nothing
// is done again (N2HD_Install is also guarded). If the runtime is missing or refuses this EXE, the game simply runs.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

static const char* const names[17] = {"GetFileVersionInfoA", "GetFileVersionInfoByHandle", "GetFileVersionInfoExA", "GetFileVersionInfoExW",
    "GetFileVersionInfoSizeA", "GetFileVersionInfoSizeExA", "GetFileVersionInfoSizeExW", "GetFileVersionInfoSizeW", "GetFileVersionInfoW",
    "VerFindFileA", "VerFindFileW", "VerInstallFileA", "VerInstallFileW", "VerLanguageNameA", "VerLanguageNameW", "VerQueryValueA", "VerQueryValueW"};
extern "C" FARPROC real[17] = {};

static void loadReal() {
    wchar_t path[MAX_PATH];
    UINT n = GetSystemDirectoryW(path, MAX_PATH);   // a 32-bit process reads System32 through SysWOW64
    if (!n || n + 13 >= MAX_PATH) return;
    lstrcpyW(path + n, L"\\version.dll");
    HMODULE m = LoadLibraryW(path);
    if (!m) return;
    for (int i = 0; i < 17; ++i) real[i] = GetProcAddress(m, names[i]);
}

#define THUNK(i, n) extern "C" __declspec(naked) void p_##n() { __asm { jmp dword ptr [real + i * 4] } }
THUNK(0, GetFileVersionInfoA) THUNK(1, GetFileVersionInfoByHandle) THUNK(2, GetFileVersionInfoExA) THUNK(3, GetFileVersionInfoExW)
THUNK(4, GetFileVersionInfoSizeA) THUNK(5, GetFileVersionInfoSizeExA) THUNK(6, GetFileVersionInfoSizeExW) THUNK(7, GetFileVersionInfoSizeW)
THUNK(8, GetFileVersionInfoW) THUNK(9, VerFindFileA) THUNK(10, VerFindFileW) THUNK(11, VerInstallFileA) THUNK(12, VerInstallFileW)
THUNK(13, VerLanguageNameA) THUNK(14, VerLanguageNameW) THUNK(15, VerQueryValueA) THUNK(16, VerQueryValueW)

static unsigned char* entry;
static unsigned char saved[5];
extern "C" void* realEntry = 0;

static void install() {
    DWORD old;
    if (VirtualProtect(entry, 5, PAGE_EXECUTE_READWRITE, &old)) {
        memcpy(entry, saved, 5);
        VirtualProtect(entry, 5, old, &old);
        FlushInstructionCache(GetCurrentProcess(), entry, 5);
    }
    if (GetModuleHandleW(L"n2hd_runtime.dll")) return;          // Korean4K.exe put it in already
    wchar_t path[32768];
    DWORD n = GetModuleFileNameW(0, path, 32768);
    if (!n || n >= 32768 - 32) return;
    wchar_t* slash = wcsrchr(path, L'\\');
    if (!slash) return;
    lstrcpyW(slash + 1, L"n2hd_runtime.dll");
    if (GetFileAttributesW(path) == INVALID_FILE_ATTRIBUTES) return;
    HMODULE m = LoadLibraryW(path);
    if (!m) return;
    typedef int(__cdecl * Install)();
    Install f = (Install)GetProcAddress(m, "N2HD_Install");
    if (f) f();
}

extern "C" __declspec(naked) void start() {
    __asm {
        pushad
        pushfd
        call install
        popfd
        popad
        jmp dword ptr [realEntry]
    }
}

static void hookEntry() {
    unsigned char* base = (unsigned char*)GetModuleHandleW(0);
    if (!base) return;
    IMAGE_DOS_HEADER* dos = (IMAGE_DOS_HEADER*)base;
    IMAGE_NT_HEADERS32* nt = (IMAGE_NT_HEADERS32*)(base + dos->e_lfanew);
    if (dos->e_magic != IMAGE_DOS_SIGNATURE || nt->Signature != IMAGE_NT_SIGNATURE || !nt->OptionalHeader.AddressOfEntryPoint) return;
    wchar_t exe[32768];
    DWORD n = GetModuleFileNameW(0, exe, 32768);
    if (!n || n >= 32768) return;
    const wchar_t* name = wcsrchr(exe, L'\\');
    if (!name || lstrcmpiW(name + 1, L"GUILTY CROWN LOST XMAS.exe")) return;   // only the game itself
    entry = base + nt->OptionalHeader.AddressOfEntryPoint;
    realEntry = entry;
    DWORD old;
    if (!VirtualProtect(entry, 5, PAGE_EXECUTE_READWRITE, &old)) return;
    memcpy(saved, entry, 5);
    entry[0] = 0xe9;
    *(DWORD*)(entry + 1) = (DWORD)((unsigned char*)&start - entry - 5);
    VirtualProtect(entry, 5, old, &old);
    FlushInstructionCache(GetCurrentProcess(), entry, 5);
}

BOOL WINAPI DllMain(HINSTANCE h, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(h);
        loadReal();
        hookEntry();
    }
    return TRUE;
}
