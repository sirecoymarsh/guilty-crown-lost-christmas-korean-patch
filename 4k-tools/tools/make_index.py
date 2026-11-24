"""hires\\index.tsv (DLL 이 읽는 표): manifest.json 에서 끝난 그림만.
줄: 이름(cp932, "bg/....jpg", ASCII 소문자)\t1배 w\t1배 h\t4배 w\t4배 h\t알파 0/1\tkey\t타일 줄 수(0 = 파일 하나)
타일로 나눈 그림(tile_alpha.py)은 <key>_0.jxl, <key>_1.jxl ... 이 다 있어야 타일로 넣고, 아니면 <key>.jxl 로.
python -X utf8 make_index.py
"""
import json, sys
from pathlib import Path

H = Path(r'F:\AI\gclx-4k\hires')
m = json.loads((H / 'manifest.json').read_text('utf-8'))
lines, tiled = [], 0
for key, r in sorted(m.items(), key=lambda kv: kv[1]['name']):
    tile = r.get('tile', 0)
    if tile and not all((H / f'{key}_{i}.jxl').exists() for i in range(-(-r['out'][1] // tile))):
        tile = 0
    if not tile and not (H / f'{key}.jxl').exists():
        continue
    tiled += bool(tile)
    name = ''.join(c.lower() if c < '\x80' else c for c in r['name'].replace('\\', '/'))
    lines.append(f"{name}\t{r['w']}\t{r['h']}\t{r['out'][0]}\t{r['out'][1]}\t{1 if r['alpha'] else 0}\t{key}\t{tile}\n")
tmp = H / 'index.tsv.tmp'
tmp.write_bytes(''.join(lines).encode('cp932'))
tmp.replace(H / 'index.tsv')
print(len(lines), '줄 (타일', tiled, ') →', H / 'index.tsv')
