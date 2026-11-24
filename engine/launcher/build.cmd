@echo off
rem Test-only launcher (Codex Korean4K.exe source + SW_SHOWNOACTIVATE for the game window). Not for the shipped patch.
set TEMP=F:\AI\gclx-4k\engine\temp
set TMP=%TEMP%
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul
cd /d F:\AI\gclx-4k\engine\launcher
cl /nologo /O2 /MT /EHsc /W3 /utf-8 launcher.cpp user32.lib psapi.lib /link /SUBSYSTEM:WINDOWS /OUT:Korean4K_test.exe /INCREMENTAL:NO
