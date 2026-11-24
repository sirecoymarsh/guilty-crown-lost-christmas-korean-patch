"""대본(nss.npa) 안 문자열 찾기. python -X utf8 grep_nss.py <정규식> [최대줄]"""
import re, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA
a = NPA(Path(r'F:\AI\gclx-4k\nss_variants\nss.normal.npa'))
pat = re.compile(sys.argv[1]); limit = int(sys.argv[2]) if len(sys.argv) > 2 else 80; n = 0
for e in a.entries:
    try: d = a.read(e).decode('cp932', 'replace')
    except Exception: continue
    for i, l in enumerate(d.splitlines()):
        if pat.search(l):
            print(e['name'], i, l.strip()[:160]); n += 1
            if n >= limit: sys.exit()
