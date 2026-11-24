import json, re
from pathlib import Path
res = json.loads(Path('stage_scan.json').read_text('utf-8'))
byf = {}
for r in res: byf.setdefault(r['file'], []).append(r)
AMBIENT = ('mvsnow01.ngs', 'mvfire01.ngs', 'mvk200.ngs', 'mvk100.ngs', 'mvnoize.ngs')


def active(r):
    return (r['anim'] >= 6 and r['ms'] >= 2500) or any(not m.startswith('mv0003') and m not in AMBIENT for m in r['movies'])


cl = []
for f, segs in byf.items():
    cur = None; gap = 0
    for r in segs:
        if active(r):
            if cur and gap <= 2:
                cur['segs'].append(r); cur['texts'] += gap + 1
            else:
                cur = {'file': f, 'segs': [r], 'texts': 0}; cl.append(cur)
            gap = 0
        else:
            gap += 1
            if gap > 2: cur = None
out = []
for c in cl:
    s = c['segs']; ms = sum(x['ms'] for x in s); an = sum(x['anim'] for x in s)
    ev = []; mv = []; notes = []
    for x in s:
        ev += [e for e in x['ev'] if e not in ev]; mv += [m for m in x['movies'] if m not in mv]; notes += x['notes']
    special = [m for m in mv if not m.startswith('mv0003') and m not in AMBIENT]
    if (ms < 9000 or an < 25) and not special:
        continue
    out.append({'file': c['file'], 'ks': s[0]['ks'], 'start': s[0]['start'], 'end': s[-1]['end'], 'sec': round(ms / 1000, 1), 'anim': an,
                'texts': c['texts'], 'after': s[0]['after'], 'ev': ev, 'movies': mv, 'notes': notes, 'skip': sum((x['skipmovie'] for x in s), [])})
Path('clusters.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), 'utf-8')


def good(n):
    if len(n) < 5 or re.search(r'そのうち読み込み|読み込み分割|ここまで|SE|ＳＥ|BGM|ＢＧＭ|♪|セット$|^ev|^cg|^se|Revision|ペンディング', n):
        return False
    return bool(re.search(r'[぀-ヿ一-鿿]', n))


with open('clusters.txt', 'w', encoding='utf-8') as fo:
    for i, o in enumerate(out):
        evs = [e for e in o['ev'] if not e.startswith('ev9')]
        sp = [m for m in o['movies'] if not m.startswith('mv0003')]
        fo.write(f"#{i} {o['file']} [{o['ks'][0]}] {o['start']}-{o['end']} {o['sec']}s a{o['anim']} t{o['texts']} mv{sp} ev{len(o['ev'])}:{','.join(e[:16] for e in evs[:3])}\n")
        g = []
        for n in o['notes']:
            if good(n) and n not in g: g.append(n)
        fo.write('   ' + ' | '.join(x[:40] for x in g[:5]) + '\n')
print(len(out))
