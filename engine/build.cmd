@echo off
rem Codex n2hd 4K runtime (final-language-qa-20261026 engine) + Claude hires_art.inc (4x art) + bundled fonts.
rem libjxl 0.11.2 32-bit static decoder from the Reconquista build (tools\build_libjxl.cmd there).
set TEMP=F:\AI\gclx-4k\engine\temp
set TMP=%TEMP%
if not exist "%TEMP%" mkdir "%TEMP%"
if not exist "F:\AI\gclx-4k\engine\build" mkdir "F:\AI\gclx-4k\engine\build"
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul
set JXL=P:\AI\Codex\projects\reconquista_flowchart_20261024\build\libjxl-x86
cd /d F:\AI\gclx-4k\engine\src
cl /nologo /LD /O2 /MT /EHsc /W3 /arch:SSE2 /std:c++17 /utf-8 /I "%JXL%\lib\include" /Fo"F:\AI\gclx-4k\engine\temp\\" n2hd_gpu_v8.cpp runtime_hooks.cpp media_backend.cpp d3d9.lib gdi32.lib user32.lib d3dcompiler.lib bcrypt.lib cabinet.lib mfplat.lib mfreadwrite.lib mfuuid.lib ole32.lib dxva2.lib "%JXL%\lib\jxl_dec.lib" "%JXL%\lib\jxl_threads.lib" "%JXL%\third_party\highway\hwy.lib" "%JXL%\third_party\brotli\brotlidec.lib" "%JXL%\third_party\brotli\brotlicommon.lib" /link /OUT:F:\AI\gclx-4k\engine\build\n2hd_runtime.dll /INCREMENTAL:NO
