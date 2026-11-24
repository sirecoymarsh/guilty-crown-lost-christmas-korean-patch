"""원작 InitBGM 표(function.nss: CreateBGM("lx0NN","lxbgmNN");//번호. 곡 이름) + 곡마다 처음 나오는 이야기 장면 → music.json.
대본은 별칭 "@lx0NN" 으로 곡을 튼다(SoundPlay/BGM 함수). 엔딩 곡 lxsong01/02 는 결말 장면(TheEND)에서.
python -X utf8 music_table.py <nss.npa>   (사용자가 플레이 중 — 곡 목록을 채팅에 옮길 때 처음 나오는 장면은 적지 말 것)"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

here = Path(__file__).parent
arc = NPA(Path(sys.argv[1])); ent = {e['name']: e for e in arc.entries}
fn = arc.read(ent['function.nss']).decode('cp932', 'replace').replace('\r', '')
i = fn.find('function InitBGM()'); body = fn[i:fn.find('\nfunction ', i + 10)]
tracks = []
for m in re.finditer(r'^(\s*)(//)?\s*CreateBGM\("(lx\d+)","(\w+)"\);\s*//\s*(.*)$', body, re.M):
    tracks.append({'alias': m.group(3), 'file': m.group(4), 'comment': m.group(5).strip(), 'disabled': bool(m.group(2))})
scenes = json.load(open(here / 'scenes.json', encoding='utf-8'))
files = [s['file'] for s in scenes]
texts = {}
for e in arc.entries:
    if e['name'].startswith('lx'):
        texts[e['name']] = arc.read(e).decode('cp932', 'replace')
for t in tracks:
    pat = re.compile(r'"@' + t['alias'] + r'"')
    hit = [f for f in sorted(texts) if pat.search(texts[f])]
    t['uses'] = len(hit)
    # 처음 나오는 이야기 장면: 회상 장면 차례에서 가장 앞(장면 표에 없는 파일은 그다음 장면으로 셈)
    order = [f for f in files if f in hit]
    t['first_scene'] = order[0] if order else (hit[0] if hit else None)
json.dump(tracks, open(here / 'music.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for t in tracks:
    print(('#' if t['disabled'] else ' '), t['alias'], t['file'], t['uses'], t['comment'])
