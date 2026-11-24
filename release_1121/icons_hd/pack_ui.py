"""코덱스가 4배로 다시 그린 문장 끝 아이콘(icons_hd/codex_out)을 본 패치용 hires_ui 로 묶는다(11-24).
- hires_ui\\index.tsv: 이름(cp932, ASCII 소문자, 'cg/' 없음)\t1배 w\t1배 h\t4배 w\t4배 h\t알파\tkey\t0 — hires\\index.tsv 와 같은 꼴(DLL hires_art.inc 가 둘 다 읽음).
- 그림: <key>.jxl 무손실(고화질 묶음과 같은 imagecodecs JPEG XL; reconquista build/pylib 의 것).
python -X utf8 pack_ui.py <출력 hires_ui 폴더>
"""
import sys, hashlib, json
from pathlib import Path
sys.path.insert(0, r'P:\AI\Codex\projects\reconquista_flowchart_20261024\build\pylib')
import numpy as np
import imagecodecs
from PIL import Image

SRC = Path(__file__).resolve().parent / 'codex_out'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
sets = [('通常', 34, 'icon_n'), ('auto', 16, 'icon_a')]
lines = []; man = {}
for folder, n, kp in sets:
    for i in range(n):
        src = SRC / folder / f'{folder}-{i:03d}.png'
        arr = np.asarray(Image.open(src).convert('RGBA'))
        assert arr.shape == (104, 104, 4), (src, arr.shape)
        data = imagecodecs.jpegxl_encode(np.ascontiguousarray(arr), lossless=True)
        back = imagecodecs.jpegxl_decode(data)
        assert back.shape == arr.shape and np.array_equal(back, arr), src
        key = f'{kp}_{i:03d}'
        (out / f'{key}.jxl').write_bytes(data)
        name = f'sys/icon/{folder}/{folder}-{i:03d}.png'
        lines.append(f'{name}\t26\t26\t104\t104\t1\t{key}\t0\n')
        man[key] = {'name': name, 'png_sha256': hashlib.sha256(src.read_bytes()).hexdigest(), 'jxl_bytes': len(data)}
(out / 'index.tsv').write_bytes(''.join(lines).encode('cp932'))
(Path(__file__).resolve().parent / 'hires_ui_manifest.json').write_text(json.dumps(man, ensure_ascii=False, indent=1), 'utf-8')
print(len(lines), 'icons', sum(m['jxl_bytes'] for m in man.values()) // 1024, 'KB ->', out)
