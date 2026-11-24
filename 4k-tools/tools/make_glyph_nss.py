"""글자 시험 대본: nss.test.npa(타이틀 없이 시작·자동 진행)에서 첫 대사 「화려한 일루미네이션.」을 시험 글자 줄로 바꾼
nss_variants\\nss.test_glyph.npa. 게임 폴더에는 안 둔다(run_test.py --nss nss.test_glyph.npa 가 넣고 되돌림).
python -X utf8 make_glyph_nss.py ["시험 줄"]"""
import sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

NSS_DIR = Path(r'F:\AI\gclx-4k\nss_variants')
SRC = Path(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\outputs\korean-game-candidate\game\nss.npa')
test = NPA(NSS_DIR / 'nss.test.npa'); src = NPA(SRC)
line = sys.argv[1] if len(sys.argv) > 1 else '뒤덮여 덮친다 엎드려 뻗는 넘겼다 썼다 펼쳐 벗어 떨어져 섰다'
files = {e['name']: test.read(e) for e in test.entries if e['name'] == 'lx0010.nss'}
lx = next(src.read(e) for e in src.entries if e['name'] == 'lx0010.nss')
old = '화려한 일루미네이션&.'.encode('cp949')
assert lx.count(old) == 1, lx.count(old)
assert files['lx0010.nss'] == lx
files['lx0010.nss'] = lx.replace(old, (line + '&.').encode('cp949'))
dst = NSS_DIR / 'nss.test_glyph.npa'
dst.write_bytes(test.pack({'lx0010.nss': files['lx0010.nss']}))
chk = NPA(dst)
assert {e['name']: chk.read(e) for e in chk.entries if e['name'] == 'lx0010.nss'} == files
print('글자 시험 대본 →', dst)
