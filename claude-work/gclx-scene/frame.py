import sys
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
from npa_assets import NPA
from PIL import Image
import io
for a in ('cg.npa', 'cg1.npa'):
    arc = NPA(Path(r'P:\AI\gclx-codexrun\game') / a)
    for e in arc.entries:
        n = bytes.fromhex(e['name_hex']).decode('cp932', 'replace') if 'name_hex' in e else e['name']
        if 'title' in n and ('上下枠' in n or '背景' in n):
            b = arc.read(e); im = Image.open(io.BytesIO(b))
            print(a, n, im.size, im.mode, im.getbbox() if im.mode == 'RGBA' else '')
            if '上下枠' in n:
                im.save('title_frame.png')
