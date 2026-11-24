"""시나리오 열람용 장면 표: 이야기 장면(선택지·빈 장면 뺌)을 단계(페이즈)별로, 대표 그림(감상 썸네일이 있는 첫 이벤트 CG, 없으면 배경)과 함께.
python -X utf8 build_scenes.py <nss.npa> <thumbs.json> <scenes.json>
(사용자는 이 작품을 플레이 중 — 이 표의 그림 이름·제목을 채팅에 옮기지 말 것)"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

arc = NPA(Path(sys.argv[1]))
thumbs = {t.split('/')[-1].rsplit('.', 1)[0]: t for t in json.load(open(sys.argv[2], encoding='utf-8'))}
src = {e['name']: arc.read(e).decode('cp932', 'replace') for e in arc.entries if e['name'].startswith('lx') and e['name'] != 'lx9999.nss'}


def content(d, name):
    i = d.find('scene ' + name + '\n')
    if i < 0:
        i = d.find('scene ' + name + '\r\n')
    return d[i:] if i >= 0 else d


def nexts(d):
    code = '\n'.join(l for l in d.splitlines() if not l.strip().startswith('//'))
    return re.findall(r'\$GameName\s*=\s*"([^"]+)"', code)


# story order = file name order (lx<단계><장면>[a|b][_갈래]: a/b and _01/_02 sort next to each other and before the joining scene)
order = sorted(src)
phase = 0; scenes = []; last_img = None
for n in order:
    d = src[n]; body = content(d, n)
    # Phase = 원작 세이브 칸 제목 「Phase NN 이름」 의 번호($PHASE_num, 장면 _MAIN 에서 정함). 막간(lx0300·0500·0600)은
    # 표지(PhaseSet·PhaseOn)가 다음 장면에서 뜨지만 세이브 화면은 이미 새 Phase 로 센다 → 세이브 화면을 따른다(11-02).
    m = re.search(r'\$PHASE_num\s*=\s*(\d+)', d)
    if m:
        phase = int(m.group(1))
    texts = len(re.findall(r'<PRE\b', body))
    imgs = re.findall(r'"cg/(ev|bg)/(?:l/)?([^"/]+?)\.(?:jpg|png)"', body)
    rep = next((f'{k}/{v}' for k, v in imgs if k == 'ev' and v in thumbs), None) or \
        next((f'{k}/{v}' for k, v in imgs if k == 'bg' and v in thumbs), None) or last_img
    if rep:
        last_img = rep
    choice = bool(re.search(r'SetChoice0\d\(', d)) and texts == 0
    ending = n.startswith('lx0605') and not n.endswith('_90ed.nss')
    if texts == 0 or choice or n.endswith('_90ed.nss'):
        continue
    scenes.append({'file': n, 'phase': max(phase, 1), 'texts': texts, 'thumb': thumbs.get(rep.split('/')[1]) if rep else None,
                   'cg': f'cg/{rep}.jpg' if rep else None, 'ending': ending,
                   'also': [n.replace('.nss', '_90ed.nss')] if ending else []})
Path(sys.argv[3]).write_text(json.dumps(scenes, ensure_ascii=False, indent=1), 'utf-8')
import collections
print(len(scenes), 'scenes', dict(collections.Counter(s['phase'] for s in scenes)), 'no thumb', sum(1 for s in scenes if not s['thumb']))
