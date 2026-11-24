"""cg.npa 안 CG 감상 썸네일(sys\\extra\\thum\\…) 목록. python -X utf8 list_thumbs.py <cg.npa> <out.json>"""
import collections, json, sys
sys.path.insert(0, r'F:\AI\gclx-4k\tools')
from title_hits import MNPA

a = MNPA(sys.argv[1])
th = [e['name'].replace('\\', '/') for e in a.entries if e['type'] == 2 and '/extra/thum/' in e['name'].replace('\\', '/').lower()]
print(len(th), th[:4])
print(collections.Counter(n.split('/')[3] if n.count('/') >= 4 else '-' for n in th))
json.dump(th, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
