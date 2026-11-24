"""0_boot.nss·extra_cglib.nss 에서 사운드 모드 흔적 줄(주석인지 함께). python -X utf8 sound_mode_lines.py <nss.npa>"""
import re, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

arc = NPA(Path(sys.argv[1])); ent = {e['name']: e for e in arc.entries}
for name in ('0_boot.nss', 'extra_cglib.nss'):
    t = arc.read(ent[name]).decode('cp932', 'replace').replace('\r', '').split('\n')
    for i, ln in enumerate(t):
        if re.search(r'サウンド|extra_soundlib|extra_media|extra_gallery|Title_Extra0[12]', ln):
            print(name, i + 1, ln.strip()[:140])
