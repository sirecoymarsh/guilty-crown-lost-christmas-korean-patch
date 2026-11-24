"""타이틀 단추 본보기 그림(원래 「불러오기」 load-001.png)을 cg.npa 에서 꺼낸다. python -X utf8 get_title_ref.py <게임 폴더> <출력 png>"""
import sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

arc = NPA(Path(sys.argv[1]) / 'cg.npa')
cands = [e for e in arc.entries if e['name'].replace('\\', '/').startswith('sys/title/') and 'load' in e['name'].lower()]
print([e['name'] for e in cands])
pick = next(e for e in cands if e['name'].lower().endswith('load-001.png'))
Path(sys.argv[2]).write_bytes(arc.read(pick))
print('->', sys.argv[2])
