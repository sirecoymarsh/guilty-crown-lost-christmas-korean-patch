"""투명 그림마다 옛 alpha4(대비 2배)가 1배 투명도를 얼마나 바꾸는지 잰다 — 옅은 빛·연기가 지워지는 그림 찾기.
python -X utf8 alpha_scan.py  →  F:\AI\gclx-4k\alpha_scan.json"""
import json, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA
CG = r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\outputs\korean-game-candidate\game\cg.npa'
ROOT = Path(r'F:\AI\gclx-4k')

def old_alpha4(a1):
    h, w = a1.shape
    v = cv2.resize(a1.astype(np.float32), (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4)
    v = np.clip((v - 127.5) * 2 + 127.5, 0, 255)
    v[np.repeat(np.repeat(a1 == 0, 4, 0), 4, 1)] = 0
    v[np.repeat(np.repeat(a1 == 255, 4, 0), 4, 1)] = 255
    return v

def new_alpha4(a1):
    sys.path.insert(0, r'F:\AI\gclx-4k\tools')
    from remaster_batch import alpha4
    return alpha4(a1).astype(np.float32)

def scan(item):
    name, data = item
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None or img.ndim != 3 or img.shape[2] != 4:
        return None
    a1 = img[:, :, 3]
    vis = a1 > 0
    if not vis.any():
        return None
    h, w = a1.shape
    o4, n4 = old_alpha4(a1), new_alpha4(a1)
    total = float(a1[vis].astype(np.float64).sum())
    def lost(x4):
        back = cv2.resize(x4, (w, h), interpolation=cv2.INTER_AREA)
        return round(100 * float(np.clip(a1.astype(np.float64) - back, 0, None)[vis].sum()) / total, 2)
    soft = float(((a1 > 0) & (a1 < 255)).mean())
    vis4 = np.repeat(np.repeat(vis, 4, 0), 4, 1)
    return dict(name=name, lost_pct=lost(o4), lost_new_pct=lost(n4), soft_pct=round(100 * soft, 2),
                old_new_diff=round(float(np.abs(o4 - n4)[vis4].mean()), 2))

if __name__ == '__main__':
    rows = json.loads((ROOT / 'inventory.json').read_text('utf-8'))['rows']
    names = [r['name'] for r in rows if r['method'] != 'lanczos']
    arc = NPA(CG)
    ent = {e['name'].replace(chr(92), '/'): e for e in arc.entries if e['type'] == 2}
    items = [(n, arc.read(ent[n])) for n in names]
    with ProcessPoolExecutor(6) as ex:
        res = [r for r in ex.map(scan, items, chunksize=8) if r]
    (ROOT / 'alpha_scan.json').write_text(json.dumps(res, ensure_ascii=False, indent=0), 'utf-8')
    lost = np.array([r['lost_pct'] for r in res])
    print('투명 그림', len(res), '잃는 투명도 % 분위 50/90/99/최대', np.percentile(lost, [50, 90, 99, 100]).round(2))
    for t in (1, 2, 5, 10, 20):
        sel = [r for r in res if r['lost_pct'] >= t]
        by = {}
        for r in sel: by[r['name'].split('/')[0]] = by.get(r['name'].split('/')[0], 0) + 1
        print(f'{t}% 이상 잃음: {len(sel)}장', by, '| 새 방식으로', sum(r['lost_new_pct'] >= t for r in res), '장')
    for kind in ('st', 'bu', 'fa', 'fw'):
        d = [r['old_new_diff'] for r in res if r['name'].startswith(kind + '/')]
        if d: print(kind, len(d), '옛↔새 4배 투명도 평균 차이 50/99/최대', np.percentile(d, [50, 99, 100]).round(2))
