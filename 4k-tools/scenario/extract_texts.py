"""장면별 한국어 본문(대사·지문)만 뽑아 제목 짓기 자료로. python -X utf8 extract_texts.py <nss.npa> <scenes.json> <out_dir>
태그·주석·명령 줄은 빼고 <PRE> 블록 글만. 루비는 「본문(읽기)」로. &. &, 탈출은 되돌림."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

arc = NPA(Path(sys.argv[1])); ent = {e['name']: e for e in arc.entries}
scenes = json.load(open(sys.argv[2], encoding='utf-8')); out = Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
for i, s in enumerate(scenes):
    names = [s['file']] + s.get('also', [])
    lines = []
    for n in names:
        b = arc.read(ent[n])
        t = b.decode('cp949', 'replace')
        for m in re.finditer(r'<PRE[^>]*>(.*?)</PRE>', t, re.S):
            blk = m.group(1)
            blk = re.sub(r'<RUBY TEXT="([^"]*)">(.*?)</RUBY>', r'\2(\1)', blk)
            blk = re.sub(r'<[^>]+>', '', blk)
            blk = re.sub(r'^\[[^\]]*\]\s*$', '', blk, flags=re.M)
            blk = blk.replace('&.', '.').replace('&,', ',')
            blk = '\n'.join(l.strip() for l in blk.splitlines() if l.strip() and not l.strip().startswith('//'))
            if blk:
                lines.append(blk)
    (out / f'{i:02d}_{s["file"].replace(".nss", "")}.txt').write_text(
        f'# 장면 {i:02d} {s["file"]} 단계 {s["phase"]}\n\n' + '\n\n'.join(lines) + '\n', 'utf-8')
print(len(scenes), 'files ->', out)
