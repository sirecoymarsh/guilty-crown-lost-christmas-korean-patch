"""큰 투명 그림을 TILE 줄씩 끊어 따로 담는다: <key>_0.jxl, <key>_1.jxl ... (manifest 에 tile=TILE).
libjxl 은 투명 그림의 알파를 그림 크기 ×4바이트 한 덩어리로 푼다(15 MP → 60 MB). 게임은 32비트라 몇 분 뒤엔
그만한 빈 주소가 없어 4배 그림을 못 올렸다(10-27 시험). 512줄 조각이면 4096 폭에서 8 MB.
<key>.jxl 을 풀어 조각마다 같은 기준(encode: 보이는 곳 40 dB 이상)으로 다시 담는다. 원래 <key>.jxl 은 남겨 둔다.
python -X utf8 tile_alpha.py [--limit N]
"""
import argparse, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
sys.path.insert(0, r'F:\AI\gclx-4k\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\reconquista_flowchart_20261024\build\pylib')
H = Path(r'F:\AI\gclx-4k\hires')
TILE, MIN_PIXELS = 512, 2_100_000


def tile_one(key):
    import numpy as np, imagecodecs
    from remaster_batch import encode
    out = imagecodecs.jpegxl_decode((H / f'{key}.jxl').read_bytes(), numthreads=2)
    worst, total, n = 99.0, 0, 0
    for i, y in enumerate(range(0, out.shape[0], TILE)):
        data, d, p = encode(np.ascontiguousarray(out[y:y + TILE]))
        tmp = H / f'{key}_{i}.jxl.tmp'
        tmp.write_bytes(data)
        os.replace(tmp, H / f'{key}_{i}.jxl')
        worst, total, n = min(worst, p), total + len(data), i + 1
    return key, n, round(worst, 2), total


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--limit', type=int, default=0); ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    mp = H / 'manifest.json'
    m = json.loads(mp.read_text('utf-8'))
    todo = [k for k, v in m.items() if v['alpha'] and v['out'][0] * v['out'][1] > MIN_PIXELS and v.get('tile') != TILE]
    if a.limit:
        todo = todo[:a.limit]
    print('나눌 그림', len(todo), flush=True)
    t0, done = time.perf_counter(), 0
    with ProcessPoolExecutor(a.workers) as ex:
        for key, n, worst, total in ex.map(tile_one, todo):
            m[key].update(tile=TILE, tile_count=n, tile_psnr_min=worst, tile_bytes=total)
            done += 1
            if done % 50 == 0 or done == len(todo):
                tmp = mp.with_suffix('.json.tmp'); tmp.write_text(json.dumps(m, ensure_ascii=False, indent=0, sort_keys=True), 'utf-8'); os.replace(tmp, mp)
                print(f'{done}/{len(todo)} {time.perf_counter() - t0:.0f}초', flush=True)
    print('끝', len(todo))
