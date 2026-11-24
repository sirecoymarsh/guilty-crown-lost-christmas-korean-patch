"""cg.npa 에서 이름에 주어진 글이 든 그림을 뽑는다(큰 묶음은 mmap). python -X utf8 dump_cg.py <cg.npa> <출력 폴더> <이름 조각>..."""
import io, sys
from pathlib import Path
sys.path.insert(0, r'F:\AI\gclx-4k\tools')
from title_hits import MNPA

a = MNPA(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
keys = [k.lower() for k in sys.argv[3:]]
for e in a.entries:
    n = e['name'].lower().replace(chr(92), '/')
    if any(k in n for k in keys):
        p = out / n.replace('/', '__'); p.write_bytes(a.read(e)); print(p.name, e['size'])
