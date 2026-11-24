"""사운드 모드 준비: sound.npa 의 음악 파일, 대본이 음악을 부르는 꼴, 곡마다 처음 나오는 장면. python -X utf8 music_survey.py <게임 폴더> <nss.npa>
(사용자가 플레이 중 — 곡 이름·장면을 채팅에 길게 옮기지 말 것)"""
import collections, json, re, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

game, nss = Path(sys.argv[1]), Path(sys.argv[2])
here = Path(__file__).parent
snd = NPA(game / 'sound.npa')
names = [e['name'].replace('\\', '/') for e in snd.entries]
print(collections.Counter(n.split('/')[0] for n in names))
music = sorted(n for n in names if n.split('/')[0].lower() in ('bgm', 'song', 'music') and '.' in n)
print(len(music), 'music files'); print(music[:80])

arc = NPA(nss)
calls = collections.Counter()
first = {}
scenes = json.load(open(here / 'scenes.json', encoding='utf-8'))
order = {s['file']: i for i, s in enumerate(scenes)}
for e in sorted(arc.entries, key=lambda e: e['name']):
    try:
        t = arc.read(e).decode('cp932', 'replace')
    except Exception:
        continue
    for m in re.finditer(r'(CreateBGM|CreateSound|SoundPlay|SetBGM|PlayBGM|BGM\w*)\s*\(([^;\n]{0,120})', t):
        calls[m.group(1)] += 1
    for m in re.finditer(r'"(?:sound/)?(?:bgm|song)/([^"]+?)(?:\.ogg)?"', t, re.I):
        first.setdefault(m.group(1), []).append(e['name'])
    for m in re.finditer(r'CreateBGM\s*\(\s*"[^"]*"\s*,\s*"([^"]+)"', t):
        first.setdefault(m.group(1), []).append(e['name'])
print(calls.most_common(12))
use = {}
for k, v in first.items():
    vs = sorted(set(v), key=lambda f: order.get(f, 999))
    use[k] = {'first_scene': next((f for f in vs if f in order), None), 'files': vs[:6], 'n': len(v)}
json.dump(use, open(here / 'music_use.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(use), 'tracks referenced')
for k in sorted(use):
    print(k, use[k]['n'], use[k]['first_scene'], use[k]['files'][:3])
