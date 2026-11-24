"""숨긴 시험용 대본: 첫 실행 질문 건너뛰기·창 모드, 검수용 모두 열기, 타이틀이 뜨면 곧바로 시나리오 열람으로(한 번).
python -X utf8 make_test_variant.py <nss.scenario.npa> <출력 nss.test_scenario.npa> [title]   (title: 열람으로 자동 진입하지 않고 타이틀에서 멈춤)"""
import sys
from pathlib import Path
sys.path.insert(0, r'F:\AI\gclx-4k\tools')
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA
from npa_build import build

src, out = sys.argv[1], sys.argv[2]
mode = sys.argv[3] if len(sys.argv) > 3 else 'auto'
title_only = mode in ('title', 'partial-title')   # partial-title: 몇 장면만 읽음 + 타이틀에서 멈춤(사운드 모드 시험)
arc = NPA(Path(src)); ent = {e['name']: e for e in arc.entries}
boot = arc.read(ent['0_boot.nss'])
a = '\tif(!#N2Start){'.encode('cp932')
assert boot.count(a) == 1
allopen = 'false' if mode in ('locked', 'partial', 'partial-title') else 'true'
# partial: 몇 장면만 읽은 것으로(원작 GameMainSet2 처럼 Conquest(...,true)) - 단계 01 첫 장면, 단계 02 첫·셋째 장면
mark = ''.join(f'Conquest("nss/{n}.nss","{n}.nss",true);' for n in ('lx0010', 'lx0101', 'lx0101_02')) if mode.startswith('partial') else ''
if mode == 'partial-title-end':   # 결말 하나 본 상태(타이틀에 CG 감상 단추) - 원작 감상·불러오기 화면 비교용
    title_only, allopen = True, 'false'
    mark += '#ENDING_OF_XMAS=true;'
boot = boot.replace(a, ('\t#N2Start=true;#SYSTEM_window_full=false;#KS_ALLOPEN=' + allopen + ';' + mark + '\r\n').encode('cp932') + a, 1)
if not title_only:
    b = b'function TitleSelect()\r\n{\r\n'
    assert boot.count(b) == 1
    boot = boot.replace(b, b + b'\tif(!#KS_TEST_DONE){#KS_TEST_DONE=true;$TitleSelect=3;return;}\r\n', 1)
build(src, out, replace={'0_boot.nss': boot})
print('test variant ->', out, 'title only' if title_only else 'auto viewer')
