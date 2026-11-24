"""원래 모드 시험에서도 그림 읽기 시간과 0.08초 넘는 프레임을 4K 모드와 같은 꼴로 남긴다. 한 번만 돌린다.
- native 분기에서 그림 로더 갈고리(0x467990)만 건다(시간만; N2HD_ART_OFF 로 4배는 안 씀).
- natFrame 이 N2HD_TestNativeFrame(ms) 를 불러 art-off.log 에 longframe 줄."""
from pathlib import Path
src = Path(r'F:\AI\gclx-4k\engine\src')


def patch(name, pairs):
    p = src / name; s = p.read_text('utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (name, old[:70], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, 'utf-8')


patch('n2hd_gpu_v8.cpp', [
    ('extern "C" void __cdecl N2HD_TestTick(){',
     'extern "C" void __cdecl N2HD_TestNativeFrame(double ms){Guard guard;if(!artIndexLoaded)artLoadIndex();double load=pfFreq?artLoadFrame*1000.0/pfFreq:0;\n'
     ' if(ms>80&&artLog){fprintf(artLog,"longframe %.0fms our=0 engine_load=%.0f decoding=0 upload=0.0 frame=0\\n",ms,load);fflush(artLog);}artLoadFrame=0;}\n'
     'extern "C" void __cdecl N2HD_TestTick(){'),
])
patch('runtime_hooks.cpp', [
    ('extern "C" void __cdecl N2HD_TestTick();\nstatic void natFrame(){N2HD_TestTick();LARGE_INTEGER now;',
     'extern "C" void __cdecl N2HD_TestTick();extern "C" void __cdecl N2HD_TestNativeFrame(double);\nstatic void natFrame(){N2HD_TestTick();LARGE_INTEGER now;'),
    ('if(natLast.QuadPart){double ms=(now.QuadPart-natLast.QuadPart)*1000.0/natFreq.QuadPart;',
     'if(natLast.QuadPart){double ms=(now.QuadPart-natLast.QuadPart)*1000.0/natFreq.QuadPart;N2HD_TestNativeFrame(ms);'),
    ('natRealCreate9=*(NatCreate9*)0x511354;patchSlot(0x511354,(void*)&natCreate9);patchSlot(0x511030,(void*)&natBitBlt);',
     'natRealCreate9=*(NatCreate9*)0x511354;patchSlot(0x511354,(void*)&natCreate9);patchSlot(0x511030,(void*)&natBitBlt);\n'
     '  for(auto &h:hooks)if(h.address==0x467990&&!memcmp((void*)h.address,h.expected,h.size)){h.trampoline=VirtualAlloc(0,h.size+5,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);if(!h.trampoline)break;'
     'memcpy(h.trampoline,h.expected,h.size);jump((char*)h.trampoline+h.size,(void*)(h.address+h.size));*h.original=h.trampoline;DWORD old;'
     'if(VirtualProtect((void*)h.address,h.size,PAGE_EXECUTE_READWRITE,&old)){jump((void*)h.address,h.replacement);if(h.size>5)memset((char*)h.address+5,0x90,h.size-5);VirtualProtect((void*)h.address,h.size,old,&old);FlushInstructionCache(GetCurrentProcess(),(void*)h.address,h.size);}}'),
])
print('ok')
