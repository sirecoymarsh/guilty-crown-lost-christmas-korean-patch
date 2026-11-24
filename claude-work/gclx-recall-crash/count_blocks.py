import sys, re
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek')
sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from patch_seek import rd
from npa_assets import NPA
pre = re.compile(rb'<PRE[^>]*>\s*\[([^\]\r\n]*)\]')
res = {}
for label, path in (('lyrics', r'F:\AI\gclx-4k\release_1121\staging\nss_lyrics.npa'), ('play', r'F:\AI\gclx-4k\release_1121\staging\nss_play.npa')):
    arc = NPA(path)
    for e in arc.entries:
        n = e['name']
        if not n.endswith('.nss'): continue
        b = rd(arc, e)
        m = pre.findall(b)
        res.setdefault(n, {})[label] = (len(m), max((len(x) for x in m), default=0), len(b))
rows = sorted(res.items(), key=lambda kv: -kv[1].get('play', (0,))[0])
print('scene  lyrics_blocks  play_blocks  maxname  play_bytes')
for n, d in rows[:25]:
    l = d.get('lyrics', (0, 0, 0)); p = d.get('play', (0, 0, 0))
    print(f'{n:28s} {l[0]:6d} {p[0]:6d} {p[1]:4d} {p[2]:9d}')
print('total', sum(d.get('lyrics',(0,))[0] for d in res.values()), sum(d.get('play',(0,))[0] for d in res.values()))
