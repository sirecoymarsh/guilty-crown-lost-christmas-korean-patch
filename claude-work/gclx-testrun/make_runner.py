"""F: 가 가득 찼을 때(11-24) 숨긴 시험 결과를 Y: 에 쓰는 run_test.py 사본을 만든다. python -I -X utf8 make_runner.py"""
from pathlib import Path
src = Path(r'F:\AI\gclx-4k\tools\run_test.py').read_text('utf-8')
old = "RUNS = Path(r'F:\\AI\\gclx-4k\\testrun')"
assert src.count(old) == 1, src.count(old)
src = src.replace(old, "RUNS = Path(r'Y:\\AI\\claude-work\\gclx-testrun')   # 11-24 F: 가득 참 → Y: 로 쓰는 사본")
src = "import sys as _s; _s.path.insert(0, r'F:\\AI\\gclx-4k\\tools')\n" + src
Path(r'Y:\AI\claude-work\gclx-testrun\run_test_y.py').write_text(src, 'utf-8')
print('ok')
