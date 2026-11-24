"""원작에 음악 감상(사운드 모드)이 있는지: nss.npa 의 파일 이름과 대본 전체에서 감상 화면 흔적을 찾는다. python -X utf8 sound_mode_check.py <nss.npa> <게임 폴더>"""
import re, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

arc = NPA(Path(sys.argv[1]))
names = [e['name'] for e in arc.entries]
print('extra/sound/music files:', [n for n in names if re.search(r'extra|sound|music|bgm|omake|おまけ|鑑賞', n, re.I)])
pat = re.compile(r'サウンド|ミュージック|音楽鑑賞|BGM鑑賞|サウンドモード|MUSIC|Music|SOUND ?MODE|Title_(?:Sound|Music|Extra|CG)\w*|extra_\w+\.nss|ExtraMode\w*|おまけ')
for e in sorted(arc.entries, key=lambda e: e['name']):
    try:
        t = arc.read(e).decode('cp932', 'replace').replace('\r', '')
    except Exception:
        continue
    hits = {}
    for m in pat.finditer(t):
        hits.setdefault(m.group(0), 0)
        hits[m.group(0)] += 1
    if hits:
        print(e['name'], hits)
# 타이틀 단추 목록(원작)
boot = arc.read({x['name']: x for x in arc.entries}['0_boot.nss']).decode('cp932', 'replace')
print('title choices:', sorted(set(re.findall(r'CreateChoice\("(Title_\w+)"\)', boot))))
print('title cases:', sorted(set(re.findall(r'case\s+(Title_\w+)', boot))))
game = Path(sys.argv[2])
print('game folder npa:', sorted(p.name for p in game.glob('*.npa')))
sysnpa = NPA(game / 'system.npa')
print('system.npa sample:', [e['name'] for e in sysnpa.entries][:40])
