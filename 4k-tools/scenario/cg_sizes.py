"""장면 CG 의 원래 크기 → cg_sizes.json (상세 화면에서 틀 안에 맞추려고). python -X utf8 cg_sizes.py <게임 폴더>"""
import io, json, sys
from collections import Counter
from pathlib import Path
from PIL import Image
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

game = Path(sys.argv[1])
here = Path(__file__).parent
scenes = json.load(open(here / 'scenes.json', encoding='utf-8'))
want = {s['cg'] for s in scenes}
found = {}
for name in ('cg.npa', 'cg1.npa'):
    arc = NPA(game / name)
    for e in arc.entries:
        n = 'cg/' + e['name'].replace('\\', '/')
        if n in want and n not in found:
            found[n] = list(Image.open(io.BytesIO(arc.read(e))).size)
missing = sorted(want - set(found))
print(len(want), 'wanted', len(found), 'found', 'missing:', missing[:5])
print(Counter(tuple(v) for v in found.values()))
json.dump(found, open(here / 'cg_sizes.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
