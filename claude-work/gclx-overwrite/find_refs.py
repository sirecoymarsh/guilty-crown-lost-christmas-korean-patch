"""한국어판 cg.npa 에서 바뀌거나 더해진 그림(545개)이 대본 어디서 어떻게 불리는지 찾는다.
python -I -X utf8 find_refs.py"""
import sys, os, json, re, collections
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from npa_assets import NPA
W = r'Y:\AI\claude-work\gclx-overwrite'
o = NPA(r'Y:\GAME\Guilty-Crown-Lost-Christmas_Win_EN_Full-rip\GUILTY CROWN LOST XMAS\cg.npa')
k = NPA(r'P:\AI\gclx-codexrun\game\cg.npa')
on = {e['name_hex']: e for e in o.entries if e['type'] == 2}
kn = {e['name_hex']: e for e in k.entries if e['type'] == 2}
import hashlib
diff = []
for h, e in kn.items():
    if h not in on:
        diff.append((h, 'added'))
    else:
        a = on[h]
        if a['size'] != e['size'] or a['stored_size'] != e['stored_size']:
            diff.append((h, 'changed'))
        else:
            # 같은 크기라도 내용이 다를 수 있다
            if hashlib.sha1(o.read(a)).digest() != hashlib.sha1(k.read(e)).digest():
                diff.append((h, 'changed_same_size'))
print('diff', collections.Counter(t for _, t in diff))
scripts = {}
for root, _, fs in os.walk(os.path.join(W, 'nss_dump')):
    for f in fs:
        if f.endswith('.nss'):
            scripts[f] = open(os.path.join(root, f), 'rb').read()
blob = b'\n'.join(scripts.values())
res = []
for h, t in diff:
    raw = bytes.fromhex(h)
    path = raw.replace(b'\\', b'/')
    lit = b'cg/' + path
    hits = [f for f, s in scripts.items() if lit in s]
    d = path.rsplit(b'/', 1)[0] + b'/'
    dir_hits = blob.count(b'cg/' + d)
    res.append({'name': raw.decode('cp932', 'replace'), 'hex': h, 'kind': t, 'literal_in': hits, 'dir_refs': dir_hits})
lit_ok = sum(1 for r in res if r['literal_in'])
print('literal referenced', lit_ok, 'of', len(res))
by_dir = collections.defaultdict(lambda: [0, 0, 0])
for r in res:
    d = r['name'].rsplit('\\', 1)[0]
    by_dir[d][0] += 1
    by_dir[d][1] += 1 if r['literal_in'] else 0
    by_dir[d][2] = r['dir_refs']
for d, v in sorted(by_dir.items()):
    print(f'{d:40s} files {v[0]:4d} literal {v[1]:4d} dir-prefix refs {v[2]}')
json.dump(res, open(os.path.join(W, 'refs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
