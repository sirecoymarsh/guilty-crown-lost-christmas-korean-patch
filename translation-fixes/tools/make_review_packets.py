"""번역 검수용 묶음을 만든다: 이야기 순서대로 파일 경계에서 N개로 나눈 JSONL.

쓰는 법: python make_review_packets.py <full_translation.json> <출력 폴더> <묶음 수>
"""
import sys, json, re
from pathlib import Path


def main(src, outdir, n):
    n = int(n); out = Path(outdir); out.mkdir(parents=True, exist_ok=False)
    units = json.loads(Path(src).read_text('utf-8-sig'))['units']
    files = []
    for u in units:
        if not files or files[-1][0] != u['file']: files.append([u['file'], []])
        files[-1][1].append(u)
    target = len(units) / n; packs = [[]]; count = 0
    for name, us in files:
        if count >= target * len(packs) and len(packs) < n: packs.append([])
        packs[-1].extend(us); count += len(us)
    index = []
    for k, us in enumerate(packs, 1):
        p = out / f'packet{k:02d}.jsonl'
        with p.open('w', encoding='utf-8') as fh:
            for u in us:
                c = u['context']
                fh.write(json.dumps(dict(
                    id=u['id'], speaker=c.get('speaker'), addressee=c.get('addressee'), kind=c.get('kind'),
                    scene=c.get('scene'), ja_notes=[d for d in u['direction_comments'] if d.strip()][:4],
                    en=re.sub(r'\r\n', '\n', u['source']), ko=re.sub(r'\r\n', '\n', u['target'])),
                    ensure_ascii=False) + '\n')
        index.append(dict(packet=p.name, units=len(us), first=us[0]['id'], last=us[-1]['id'],
                          files=sorted({u['file'] for u in us}, key=lambda f: [x[0] for x in files].index(f))))
    (out / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2), 'utf-8')
    for i in index: print(i['packet'], i['units'], i['first'], '→', i['last'])


if __name__ == '__main__':
    if len(sys.argv) != 4: raise SystemExit(__doc__)
    main(*sys.argv[1:])
