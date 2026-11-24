"""놀이 사본 cg.npa 에서 단계(フェイズ) 표지 그림을 꺼내 본다(읽기만)."""
import sys
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
import patch_seek as ps
from npa_assets import NPA

BS = chr(92)
out = Path(r'Y:\AI\claude-work\gclx-phase')
src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r'P:\AI\gclx-codexrun\game\cg.npa')
arc = NPA(src)
ent = {e['name']: e for e in arc.entries}
names = [n for n in ent if n.lower().startswith('sys' + BS + 'phase') and n.lower().endswith('.png')]
print(len(names))
print([n.split(BS, 2)[-1] for n in names][:60])
for n in names:
    leaf = n.split(BS, 2)[-1]
    if 'フェイズ' in leaf or leaf in ('1' + BS + 'タイトル.png', '1' + BS + '英字.png', '1' + BS + '数字.png'):
        b = ps.rd(arc, ent[n])
        fn = src.stem + '_' + leaf.replace(BS, '_')
        (out / fn).write_bytes(b)
        print('saved', fn, len(b))
