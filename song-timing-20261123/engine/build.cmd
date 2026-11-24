@echo off
rem Claude 11-21: flip_1102 (d6d5974a) + new ruby map (11-17 translation) + config page 3 commands (kr_cmd_*).
set TEMP=P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\revisions\song-subtitles-20261123\engine\temp
set TMP=%TEMP%
if not exist "%TEMP%" mkdir "%TEMP%"
if not exist "P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\revisions\song-subtitles-20261123\engine\payload" mkdir "P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\revisions\song-subtitles-20261123\engine\payload"
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul
set JXL=P:\AI\Codex\projects\reconquista_flowchart_20261024\build\libjxl-x86
cd /d P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\revisions\song-subtitles-20261123\engine\src
cl /nologo /LD /O2 /MT /EHsc /W3 /arch:SSE2 /std:c++17 /utf-8 /I "%JXL%\lib\include" /Fo"P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\revisions\song-subtitles-20261123\engine\temp\\" n2hd_gpu_v8.cpp runtime_hooks.cpp media_backend.cpp d3d9.lib gdi32.lib user32.lib d3dcompiler.lib bcrypt.lib cabinet.lib mfplat.lib mfreadwrite.lib mfuuid.lib ole32.lib dxva2.lib winmm.lib "%JXL%\lib\jxl_dec.lib" "%JXL%\lib\jxl_threads.lib" "%JXL%\third_party\highway\hwy.lib" "%JXL%\third_party\brotli\brotlidec.lib" "%JXL%\third_party\brotli\brotlicommon.lib" /link /OUT:P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\revisions\song-subtitles-20261123\engine\payload\n2hd_runtime.dll /INCREMENTAL:NO
