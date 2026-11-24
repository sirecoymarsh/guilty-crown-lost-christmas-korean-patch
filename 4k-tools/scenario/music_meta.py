"""sound.npa 음악 파일의 길이·Vorbis 꼬리표(TITLE 등)·반복 지점(LOOPSTART) → music_meta.json. python -X utf8 music_meta.py <게임 폴더>"""
import json, re, struct, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

here = Path(__file__).parent
snd = NPA(Path(sys.argv[1]) / 'sound.npa')
out = {}
for e in snd.entries:
    n = e['name'].replace('\\', '/')
    if not n.startswith('bgm/') or not n.endswith('.ogg'):
        continue
    b = snd.read(e)
    info = {'bytes': len(b)}
    i = b.find(b'\x01vorbis')
    if i >= 0:
        rate = struct.unpack('<I', b[i + 12:i + 16])[0]
        info['rate'] = rate
        j = b.rfind(b'OggS')
        gran = struct.unpack('<q', b[j + 6:j + 14])[0]
        info['seconds'] = round(gran / rate, 1)
    k = b.find(b'\x03vorbis')
    if k >= 0:
        p = k + 7
        vlen = struct.unpack('<I', b[p:p + 4])[0]; p += 4 + vlen
        cnt = struct.unpack('<I', b[p:p + 4])[0]; p += 4
        tags = []
        for _ in range(min(cnt, 40)):
            ln = struct.unpack('<I', b[p:p + 4])[0]; p += 4
            tags.append(b[p:p + ln].decode('utf-8', 'replace')); p += ln
        info['tags'] = tags
    out[n] = info
json.dump(out, open(here / 'music_meta.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for n, v in sorted(out.items()):
    print(n, v.get('seconds'), v.get('tags'))
