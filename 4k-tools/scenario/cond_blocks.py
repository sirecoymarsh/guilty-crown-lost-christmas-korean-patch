"""앞 선택에 따라 나오거나 안 나오는 대사 묶음(if(조건){…<PRE>…}, 조건이 1 이 아닌 것)을 장면별로 찾아 cond_blocks.json 에.
요약은 그 장면에 온 모든 플레이어에게 참이어야 해서, 요약 쓰는 쪽에 이 묶음을 알려 준다. python -X utf8 cond_blocks.py <nss.npa>"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

here = Path(__file__).parent
arc = NPA(Path(sys.argv[1])); ent = {e['name']: e for e in arc.entries}
scenes = json.load(open(here / 'scenes.json', encoding='utf-8'))
out = {}
for i, s in enumerate(scenes):
    t = arc.read(ent[s['file']]).decode('cp949', 'replace').replace('\r', '')
    body = t[t.find('scene ' + s['file'] + '\n'):]
    for m in re.finditer(r'\n\s*if\s*\(([^\n]*?)\)\s*\{', body):
        cond = m.group(1).strip()
        if cond == '1':
            continue
        depth, k = 1, m.end()
        while depth and k < len(body):
            depth += {'{': 1, '}': -1}.get(body[k], 0)
            k += 1
        inner = body[m.end():k - 1]
        lines = []
        for p in re.findall(r'<PRE[^>]*>(.*?)</PRE>', inner, re.S):
            p = re.sub(r'<RUBY TEXT="([^"]*)">(.*?)</RUBY>', r'\2(\1)', p)
            p = re.sub(r'<[^>]+>', '', p).replace('&.', '.').replace('&,', ',')
            lines += [l.strip() for l in p.splitlines() if l.strip() and not l.strip().startswith('//') and not l.strip().startswith('[')]
        if lines:
            out.setdefault(f'{i:02d}_{s["file"]}', []).append({'condition': cond, 'first': lines[0], 'last': lines[-1], 'lines': len(lines)})
json.dump(out, open(here / 'cond_blocks.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print({k: [(b['lines'], b['condition'][:30]) for b in v] for k, v in out.items()})
