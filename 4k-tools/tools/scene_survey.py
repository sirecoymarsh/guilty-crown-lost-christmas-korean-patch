"""길티 크라운 장면 구조 조사(읽기만): 이야기 대본(lx*.nss)마다 다음 장면 연결($GameName / call_chapter / chapter 이름), PhaseSet 번호,
쓰는 배경·이벤트 CG, 대사 블록 수, 읽음 깃발 후보를 뽑아 JSON 으로. python -X utf8 scene_survey.py <nss.npa> <out.json>
(사용자는 이 작품을 플레이 중 — 결과의 대사 내용은 채팅에 옮기지 말 것)"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

arc = NPA(Path(sys.argv[1]))
out = {}
for e in arc.entries:
    n = e['name']
    if not n.lower().startswith('lx') or n.lower() == 'lx9999.nss':
        continue
    d = arc.read(e).decode('cp932', 'replace')
    code = '\n'.join(l for l in d.splitlines() if not l.strip().startswith('//'))
    out[n] = {
        'next': re.findall(r'\$GameName\s*=\s*"([^"]+)"', code),
        'calls': re.findall(r'call_chapter\s+([^;\s]+)', code),
        'phase': re.findall(r'PhaseSet\((\d+)\)', code),
        'bg': sorted(set(re.findall(r'"(cg/bg/[^"]+)"', code)))[:6],
        'ev': sorted(set(re.findall(r'"(cg/ev/[^"]+)"', code)))[:12],
        'texts': len(re.findall(r'<PRE\b', d)),
        'flags': sorted(set(re.findall(r'(#[A-Za-z_][\w]*)\s*=\s*true', code)))[:10],
        'movies': sorted(set(re.findall(r'"(dx/[^"]+\.ngs)"', code)))[:4],
    }
Path(sys.argv[2]).write_text(json.dumps(out, ensure_ascii=False, indent=1), 'utf-8')
print(len(out), 'scripts')
