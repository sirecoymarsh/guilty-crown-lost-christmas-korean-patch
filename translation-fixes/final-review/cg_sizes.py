"""cg.npa 안 그림의 원래 크기를 무리별로 표본 조사한다(읽기만 함)."""
import sys, io, collections, random
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
arc = NPA(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\outputs\korean-game-candidate\game\cg.npa')
files = [e for e in arc.entries if e['type'] == 2]
print('예시 이름', [e['name'] for e in files[:5]])
groups = collections.defaultdict(list)
for e in files:
    parts = e['name'].replace(chr(92), '/').split('/')
    groups['/'.join(parts[:2]) if len(parts) > 2 else parts[0]].append(e)
print({k: len(v) for k, v in sorted(groups.items())})
random.seed(2)
sizes = collections.Counter()
for k, v in groups.items():
    for e in random.sample(v, min(10, len(v))):
        try:
            im = Image.open(io.BytesIO(arc.read(e))); sizes[(k, im.size)] += 1
        except Exception:
            sizes[(k, 'err')] += 1
for k, v in sorted(sizes.items(), key=str):
    print(k, v)
