@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul
cl /nologo /LD /O2 /MT /EHsc /W3 /arch:SSE2 n2hd_gpu_v8.cpp runtime_hooks.cpp media_backend.cpp d3d9.lib gdi32.lib d3dcompiler.lib bcrypt.lib cabinet.lib mfplat.lib mfreadwrite.lib mfuuid.lib ole32.lib dxva2.lib /link /OUT:n2hd_runtime.dll /INCREMENTAL:NO
