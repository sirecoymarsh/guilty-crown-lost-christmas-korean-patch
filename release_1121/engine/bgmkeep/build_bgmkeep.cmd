@echo off
rem Claude 11-24: J/K music continuity work copy (bgmkeep\src = engine\src + dsb_trace.inc / bgm_keep.inc). Output bgmkeep\out only.
set TEMP=F:\AI\gclx-4k\release_1121\engine\bgmkeep\temp
set TMP=%TEMP%
if not exist "%TEMP%" mkdir "%TEMP%"
if not exist "F:\AI\gclx-4k\release_1121\engine\bgmkeep\out" mkdir "F:\AI\gclx-4k\release_1121\engine\bgmkeep\out"
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul
set JXL=P:\AI\Codex\projects\reconquista_flowchart_20261024\build\libjxl-x86
cd /d F:\AI\gclx-4k\release_1121\engine\bgmkeep\src
cl /nologo /LD /O2 /MT /EHsc /W3 /arch:SSE2 /std:c++17 /utf-8 /I "%JXL%\lib\include" /Fo"F:\AI\gclx-4k\release_1121\engine\bgmkeep\temp\\" n2hd_gpu_v8.cpp runtime_hooks.cpp media_backend.cpp d3d9.lib gdi32.lib user32.lib d3dcompiler.lib bcrypt.lib cabinet.lib mfplat.lib mfreadwrite.lib mfuuid.lib ole32.lib dxva2.lib winmm.lib "%JXL%\lib\jxl_dec.lib" "%JXL%\lib\jxl_threads.lib" "%JXL%\third_party\highway\hwy.lib" "%JXL%\third_party\brotli\brotlidec.lib" "%JXL%\third_party\brotli\brotlicommon.lib" /link /OUT:F:\AI\gclx-4k\release_1121\engine\bgmkeep\out\n2hd_runtime.dll /INCREMENTAL:NO
