"""1배 그림 캐시: 해독기 갈고리(관찰 단계). 한 번만 돌린다."""
from pathlib import Path
src = Path(r'F:\AI\gclx-4k\engine\src')


def patch(name, pairs):
    p = src / name; s = p.read_text('utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (name, old[:70], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, 'utf-8')


patch('runtime_hooks.cpp', [
    ('static void* origLoadImage;\n', 'static void* origLoadImage;\n#include "img_cache.inc"\n'),
    ('__declspec(naked) static void hookLoadImage(){__asm {\n pushfd\n pushad\n call N2HD_LoadBegin\n popad\n popfd\n',
     '__declspec(naked) static void hookLoadImage(){__asm {\n pushfd\n pushad\n push eax\n call imgBegin\n add esp,4\n popad\n popfd\n'),
    (' call N2HD_ImageLoaded\n add esp,8\n popad\n', ' call N2HD_ImageLoaded\n add esp,8\n call imgEnd\n popad\n'),
    ('#include "native_hook_manifest.h"\n',
     r'''// The engine's PNG and JPEG decoders (see img_cache.inc).
static void* origPng;static void* origJpg;
static int __cdecl hookPng(void* t,void* file){ImgCache::init();int r=((int(__cdecl*)(void*,void*))origPng)(t,file);if(r&&ImgCache::mode==2)ImgCache::observe("png",t);return r;}
static void __cdecl jpgAfter(void* t,int r){ImgCache::init();if(r&&ImgCache::mode==2)ImgCache::observe("jpg",t);}
// 0x404f20: the file in eax (kept for the call), the picture at [esp+4].
__declspec(naked) static void hookJpg(){__asm {
 push dword ptr [esp+4]
 call dword ptr [origJpg]
 add esp,4
 pushad
 push eax
 push dword ptr [esp+40]
 call jpgAfter
 add esp,8
 popad
 ret
}}
#include "native_hook_manifest.h"
'''),
])
patch('native_hook_manifest.h', [
    ('{0x467990,(void*)&hookLoadImage,&origLoadImage,6,{0x55,0x8b,0xec,0x83,0xe4,0xf8},0,0},',
     '{0x467990,(void*)&hookLoadImage,&origLoadImage,6,{0x55,0x8b,0xec,0x83,0xe4,0xf8},0,0},\n'
     '{0x46d670,(void*)&hookPng,&origPng,6,{0x55,0x8b,0xec,0x8b,0x4d,0x0c},0,0},\n'
     '{0x404f20,(void*)&hookJpg,&origJpg,8,{0x83,0xec,0x0c,0x53,0x8b,0x5c,0x24,0x14},0,0},'),
])
print('ok')
