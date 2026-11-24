"""10-27 글자 조사용 임시 기록(glyph/copy/draw/dirty/dump)을 걷어 낸다: n2hd_gpu_v8.cpp 는 조사 전 사본에 줄 구간 고침만 다시
얹고, runtime_hooks.cpp 의 dirtyTest 는 되돌린다. 한 번만 돌린다."""
import shutil, subprocess, sys
from pathlib import Path
eng = Path(r'F:\AI\gclx-4k\engine')
shutil.copyfile(eng / 'temp' / 'n2hd_gpu_v8.before_glyphlog.cpp', eng / 'src' / 'n2hd_gpu_v8.cpp')
subprocess.run([sys.executable, str(eng / 'patch_row_spans.py')], check=True)
p = eng / 'src' / 'runtime_hooks.cpp'; s = p.read_text('utf-8')
a = s.index('static void dirtyTest(){'); b = s.index('static void __cdecl hookClear(){jumpTick();dirtyTest();')
s = s[:a] + s[b:]
s = s.replace('static void __cdecl hookClear(){jumpTick();dirtyTest();N2HD_Clear();', 'static void __cdecl hookClear(){jumpTick();N2HD_Clear();')
assert 'dirtyTest' not in s
p.write_text(s, 'utf-8')
src = (eng / 'src' / 'n2hd_gpu_v8.cpp').read_text('utf-8')
assert 'glyph.log' not in src and 'copy.log' not in src and 'draw3.log' not in src and 'spanCompat' in src
print('ok')
