"""JPEG 해독기 갈고리를 0x404f20 → 0x469b20(파일은 edx, 그림은 [esp+4], 앞 9바이트)으로. 한 번만 돌린다."""
from pathlib import Path
src = Path(r'F:\AI\gclx-4k\engine\src')


def patch(name, pairs):
    p = src / name; s = p.read_text('utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (name, old[:70], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, 'utf-8')


patch('runtime_hooks.cpp', [
    ('// 0x404f20: the file in eax (kept for the call), the picture at [esp+4].', '// 0x469b20 (the JPEG decoder, tried first): the file in edx (kept for the call), the picture at [esp+4].'),
])
patch('native_hook_manifest.h', [
    ('{0x404f20,(void*)&hookJpg,&origJpg,8,{0x83,0xec,0x0c,0x53,0x8b,0x5c,0x24,0x14},0,0},',
     '{0x469b20,(void*)&hookJpg,&origJpg,9,{0x55,0x8b,0xec,0x81,0xec,0x64,0x02,0x00,0x00},0,0},'),
])
print('ok')
