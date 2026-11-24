#include "inject_renderer.h"
int WINAPI wWinMain(HINSTANCE,HINSTANCE,PWSTR,int){
 wchar_t own[32768];if(!GetModuleFileNameW(0,own,32768))return 1;wchar_t* slash=wcsrchr(own,L'\\');if(!slash)return 2;*slash=0;std::wstring directory=own,game=directory+L"\\GUILTY CROWN LOST XMAS.exe",dll=directory+L"\\n2hd_runtime.dll";
 // Claude test launcher: the game window never takes the foreground, failures go to launcher-test.log (no message boxes).
 STARTUPINFOW si={sizeof(si)};si.dwFlags=STARTF_USESHOWWINDOW;si.wShowWindow=SW_SHOWNOACTIVATE;PROCESS_INFORMATION pi={};std::wstring command=L"\""+game+L"\"";
 std::wstring logPath=directory+L"\\launcher-test.log";auto note=[&](const char* s,DWORD v){HANDLE f=CreateFileW(logPath.c_str(),FILE_APPEND_DATA,FILE_SHARE_READ,0,OPEN_ALWAYS,0,0);if(f!=INVALID_HANDLE_VALUE){char b[200];int n=wsprintfA(b,"%s %lu\r\n",s,v);DWORD w;WriteFile(f,b,n,&w,0);CloseHandle(f);}};
 if(!CreateProcessW(game.c_str(),&command[0],0,0,FALSE,CREATE_SUSPENDED,0,directory.c_str(),&si,&pi)){note("create_failed",GetLastError());return 3;}
 DWORD code=0;bool ok=installRenderer(pi.hProcess,pi.dwProcessId,dll.c_str(),code);if(ok)ok=ResumeThread(pi.hThread)!=(DWORD)-1;if(!ok){TerminateProcess(pi.hProcess,7);WaitForSingleObject(pi.hProcess,5000);note("install_failed",code);}else note("started_pid",pi.dwProcessId);CloseHandle(pi.hThread);CloseHandle(pi.hProcess);return ok?0:7;
}
