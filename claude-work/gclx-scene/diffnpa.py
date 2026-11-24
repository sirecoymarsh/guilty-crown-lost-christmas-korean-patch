"""두 nss 묶음의 항목별 차이. python -I -X utf8 diffnpa.py <옛.npa> <새.npa>"""
import sys
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from pathlib import Path
from npa_assets import NPA
import patch_seek as ps
a, b = NPA(Path(sys.argv[1])), NPA(Path(sys.argv[2]))
ea = {e['name']: e for e in a.entries if e['type'] == 2}; eb = {e['name']: e for e in b.entries if e['type'] == 2}
print('only old', sorted(set(ea) - set(eb))); print('only new', sorted(set(eb) - set(ea)))
ch = [n for n in sorted(set(ea) & set(eb)) if ps.rd(a, ea[n]) != ps.rd(b, eb[n])]
print('changed', ch)
