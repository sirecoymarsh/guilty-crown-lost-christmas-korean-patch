"""4배 결과 전수 대조: 결과를 원본 크기로 줄여 원본과 견준다(색 평균 차이·색 치우침·투명도 잃음/늘어남·크기).
python -X utf8 audit_all.py  →  F:\AI\gclx-4k\audit_all.json + 요약"""
import json, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\reconquista_flowchart_20261024\build\pylib')
import imagecodecs
from npa_adapter import NPA
ROOT = Path(r'F:\AI\gclx-4k'); H = ROOT / 'hires'
CG = r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\outputs\korean-game-candidate\game\cg.npa'

def check(item):
    key, v, data = item
    src = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_UNCHANGED)
    if src.ndim == 2: src = cv2.cvtColor(src, cv2.COLOR_GRAY2BGR)
    out = imagecodecs.jpegxl_decode((H / f'{key}.jxl').read_bytes(), numthreads=2)
    r = dict(key=key, name=v['name'], method=v['method'])
    h, w = src.shape[:2]
    if [out.shape[1], out.shape[0]] != v['out'] or (src.shape[2] == 4) != (out.shape[2] == 4):
        r['bad'] = f'크기/채널 {out.shape} vs {v["out"]} src {src.shape}'; return r
    out = out[:, :, [2, 1, 0, 3]] if out.shape[2] == 4 else out[:, :, ::-1]
    small = cv2.resize(out, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)
    s = src.astype(np.float32)
    if src.shape[2] == 4:
        a1, a2 = s[:, :, 3], small[:, :, 3]
        vis = a1 >= 250
        tot = float(a1.sum()) or 1.0
        r['alpha_lost_pct'] = round(100 * float(np.clip(a1 - a2, 0, None).sum()) / tot, 2)
        r['alpha_gain_pct'] = round(100 * float(np.clip(a2 - a1, 0, None).sum()) / tot, 2)
    else:
        vis = np.ones((h, w), bool)
    d = small[:, :, :3] - s[:, :, :3]
    if vis.any():
        r['mad'] = round(float(np.abs(d[vis]).mean()), 2)
        r['shift'] = [round(float(x), 2) for x in d[vis].mean(0)]
    r['dark'] = bool(out[:, :, :3].mean() < 2 and src[:, :, :3].mean() > 8)
    return r

if __name__ == '__main__':
    m = json.loads((H / 'manifest.json').read_text('utf-8'))
    arc = NPA(CG); ent = {e['name'].replace(chr(92), '/'): e for e in arc.entries if e['type'] == 2}
    def items():
        for k, v in m.items():
            yield k, v, arc.read(ent[v['name']])
    with ProcessPoolExecutor(5) as ex:
        res = list(ex.map(check, items(), chunksize=4))
    (ROOT / 'audit_all.json').write_text(json.dumps(res, ensure_ascii=False, indent=0), 'utf-8')
    bad = [r for r in res if r.get('bad') or r.get('dark')]
    print('전체', len(res), '| 크기·채널 이상·검은 그림', len(bad), bad[:3])
    print('버전 1 아님', sum(1 for v in m.values() if v.get('version') != 1))
    mad = np.array([r.get('mad', 0) for r in res]); sh = np.array([max(abs(x) for x in r.get('shift', [0])) for r in res])
    print('색 평균 차이 50/90/99/최대', np.percentile(mad, [50, 90, 99, 100]).round(2))
    print('색 치우침(채널 평균) 50/99/최대', np.percentile(sh, [50, 99, 100]).round(2))
    al = [r for r in res if 'alpha_lost_pct' in r]
    lost = np.array([r['alpha_lost_pct'] for r in al]); gain = np.array([r['alpha_gain_pct'] for r in al])
    print('투명 그림', len(al), '| 잃은 투명도% 50/99/최대', np.percentile(lost, [50, 99, 100]).round(2), '| 늘어난 투명도% 50/99/최대', np.percentile(gain, [50, 99, 100]).round(2))
    for lab, key_ in (('색 차이 큰 것', lambda r: r.get('mad', 0)), ('투명도 잃은 것', lambda r: r.get('alpha_lost_pct', 0)), ('색 치우침 큰 것', lambda r: max(abs(x) for x in r.get('shift', [0])))):
        print('--', lab)
        for r in sorted(res, key=key_, reverse=True)[:6]:
            print('  ', r['key'], r['name'][:46], r['method'], r.get('mad'), r.get('shift'), r.get('alpha_lost_pct'))
