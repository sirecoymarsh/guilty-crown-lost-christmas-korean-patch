"""사운드 모드 곡 목록과 열림 조건 → music_list.json.
곡 = 원작 InitBGM 표(music.json, 주석 처리된 것 빼고) + 결말 노래 lxsong01/02.
열림 = 그 곡을 트는 이야기 장면 가운데 하나라도 읽음(회상과 같은 Conquest). 대본은 별칭 "@lx0NN" 이나 반복 꼴 "lx0NNa/b" 로 튼다.
선택지 대본(_00sl)은 바로 앞 이야기 장면으로, 결말 뒤 대본(_90ed)은 그 결말 장면으로 친다. 타이틀 곡은 처음부터 열림.
python -X utf8 music_unlock.py <nss.npa>"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

here = Path(__file__).parent
arc = NPA(Path(sys.argv[1]))
scenes = json.load(open(here / 'scenes.json', encoding='utf-8'))
sfiles = [s['file'] for s in scenes]
texts = {e['name']: arc.read(e).decode('cp932', 'replace') for e in arc.entries if e['name'].startswith('lx') and e['name'].endswith('.nss')}
boot = arc.read({e['name']: e for e in arc.entries}['0_boot.nss']).decode('cp932', 'replace')


def to_scene(f):
    if f in sfiles:
        return f
    if f.endswith('_90ed.nss'):
        base = f.replace('_90ed.nss', '.nss')
        return base if base in sfiles else None
    prev = [s for s in sfiles if s < f]   # 이야기 차례 = 파일 이름 차례
    return prev[-1] if prev else None


table = [t for t in json.load(open(here / 'music.json', encoding='utf-8')) if not t['disabled']]
tracks = []
for t in table:
    a = t['alias']
    pat = re.compile(r'"(?:@' + a + r'|' + a + r'[a-d])"')
    files = sorted(f for f, x in texts.items() if pat.search(x))
    sc = sorted({to_scene(f) for f in files} - {None}, key=sfiles.index)
    title = t['file'] == 'lxbgm06' and bool(re.search(r'"lxbgm06"', boot))
    tracks.append({'file': t['file'], 'name': t['comment'].split('. ', 1)[-1], 'scenes': sc, 'always': title, 'from': files})
ends = [s for s in scenes if s['ending']]
for k, s in enumerate(ends, 1):
    song = f'lxsong0{k}'
    tracks.append({'file': song, 'name': f'결말 {k}의 노래', 'scenes': [s['file']], 'always': False, 'from': [s['file']]})
json.dump(tracks, open(here / 'music_list.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for i, t in enumerate(tracks, 1):
    print(f'{i:02d}', t['file'], 'always' if t['always'] else f'{len(t["scenes"])} scenes (first #{sfiles.index(t["scenes"][0]) if t["scenes"] else None})')
