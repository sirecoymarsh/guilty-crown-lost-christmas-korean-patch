@echo off
rem Claude 11-21: proxy version.dll for GUILTY CROWN LOST XMAS.exe (loads n2hd_runtime.dll at the game entry point).
set TEMP=F:\AI\gclx-4k\release_1121\proxy\temp
set TMP=%TEMP%
if not exist "%TEMP%" mkdir "%TEMP%"
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul
cd /d F:\AI\gclx-4k\release_1121\proxy
cl /nologo /LD /O2 /MT /W3 /GS- version_proxy.cpp kernel32.lib /Fo"F:\AI\gclx-4k\release_1121\proxy\temp\\" /link /DEF:version.def /OUT:F:\AI\gclx-4k\release_1121\proxy\version.dll /INCREMENTAL:NO
