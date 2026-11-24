"""길티 크라운 그림 4배 리마스터 일괄(사용자 결정 10-26: 인물=섞기, 배경·이벤트 CG=섞기+JPEG 덩어리 다듬기).
vn-art-4k-remaster 스킬 절차: AI(high-fidelity-4x)는 한 장에 프로세스 하나, 매 장 뒤 nvlddmkm 오류 기록 확인,
결과 검사(크기·검은 그림·원본 크기로 줄여 원본과 평균 차이 ≤12), 섞기·다듬기·투명도는 CPU 일꾼 몇 개가 나눠 함.
결과: F:\\AI\\gclx-4k\\hires\\<key>.jxl (긴 변 ≤4096, inventory.json 의 배율), manifest.json (이름→key·크기·통계)
이어 하기: 이미 manifest 에 있고 파일이 있으면 건너뜀. 멈추기: F:\\AI\\gclx-4k\\STOP 파일.
  python -X utf8 remaster_batch.py [--limit N] [--workers 3]
"""
import argparse, ctypes, hashlib, json, math, os, re, shutil, subprocess, sys, time
import numpy as np
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path

sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\reconquista_flowchart_20261024\build\pylib')
ROOT = Path(r'F:\AI\gclx-4k')
OUT, TMP, MANIFEST, LOG = ROOT / 'hires', ROOT / 'tmp', ROOT / 'hires' / 'manifest.json', ROOT / 'batch.log'
CG = r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\outputs\korean-game-candidate\game\cg.npa'
UP = Path(r'P:\AI\Codex\projects\image-upscaling-tools\apps\Upscayl-2.15.0\resources')
EDGE_LO, EDGE_HI, FEATHER, VERSION = 40, 120, 9, 1
DISTANCE, RETRY_DISTANCE, MIN_PSNR, SPEED = 0.5, 0.3, 40.0, 3
MIN_FREE = 6 << 30


def log(msg):
    line = time.strftime('%m-%d %H:%M:%S ') + msg
    print(line, flush=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def key_of(name):
    return hashlib.sha1(name.lower().encode('utf-8')).hexdigest()[:12]


def gpu_event_id():
    q = "*[System[Provider[@Name='nvlddmkm']]]"
    r = subprocess.run(['wevtutil', 'qe', 'System', f'/q:{q}', '/c:1', '/rd:true', '/f:xml'], capture_output=True)
    m = re.search(rb'<EventRecordID>(\d+)<', r.stdout)
    return int(m.group(1)) if m else None


def dwm_gpu_gb():
    """dwm 이 쥔 GPU 전용 메모리(GB). 10-26 22:59 장치 못 만듦 때 33GB(카드 16GB) — 장마다 띄우는 AI 프로세스가 늘리는지 지켜본다."""
    ps = ("$d=(Get-Process dwm).Id; ((Get-Counter '\\GPU Process Memory(*)\\Dedicated Usage').CounterSamples | "
          "Where-Object { $_.InstanceName -match \"pid_${d}_\" } | Measure-Object CookedValue -Sum).Sum")
    r = subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, text=True)
    try:
        return round(float(r.stdout.strip()) / 2**30, 2)
    except ValueError:
        return None


# ---------- CPU 쪽(일꾼) ----------
def edge_fill(rgb, clear):
    import cv2, numpy as np
    if not clear.any() or clear.all():
        return rgb
    _, labels = cv2.distanceTransformWithLabels(clear.astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(~clear)
    lab2i = np.zeros(labels.max() + 1, np.int64)
    lab2i[labels[ys, xs]] = np.arange(len(ys))
    out = rgb.copy()
    i = lab2i[labels[clear]]
    out[clear] = rgb[ys[i], xs[i]]
    soft = cv2.GaussianBlur(out, (0, 0), 1.5)
    out[clear] = soft[clear]
    return out


def edge_weight(src):
    import cv2, numpy as np
    g = cv2.cvtColor(src, cv2.COLOR_RGB2GRAY).astype(np.float32)
    edge = cv2.GaussianBlur(cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)), (3, 3), 0)
    return np.clip((edge - EDGE_LO) / (EDGE_HI - EDGE_LO), 0, 1)


def deblock(src, m1):
    """JPEG 덩어리: 선이 없는 평평한 곳만 양방향 필터로 다듬는다(선은 그대로)"""
    import cv2, numpy as np
    flat = (1 - m1)[..., None]
    sm = cv2.bilateralFilter(src, 7, 18, 5)
    return (src * (1 - flat) + sm * flat).astype(np.uint8)


def alpha4(a1):
    """투명도 4배: Lanczos. 대비 2배(가장자리 또렷하게)는 완전 투명과 불투명이 1칸 안에서 만나는 테두리에만 —
    전체에 걸면 투명도 25% 밑이 다 지워진다(10-26 효과·빛 번짐 258장이 옅은 부분을 잃음)."""
    import cv2, numpy as np
    h, w = a1.shape
    v = cv2.resize(a1.astype(np.float32), (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4)
    k = np.ones((3, 3), np.uint8)
    hard = ((cv2.erode(a1, k) == 0) & (cv2.dilate(a1, k) == 255)).astype(np.uint8)
    m = cv2.resize(cv2.dilate(hard, k).astype(np.float32), (w * 4, h * 4), interpolation=cv2.INTER_LINEAR)
    m = cv2.GaussianBlur(m, (5, 5), 0)
    v = np.clip(np.clip((v - 127.5) * 2 + 127.5, 0, 255) * m + v * (1 - m), 0, 255)
    v[np.repeat(np.repeat(a1 == 0, 4, 0), 4, 1)] = 0
    v[np.repeat(np.repeat(a1 == 255, 4, 0), 4, 1)] = 255
    return v.astype(np.uint8)


def psnr(a, b):
    mse = float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)) if a.size else 0.0
    return 99.0 if mse == 0 else 10 * math.log10(255 * 255 / mse)


def encode(arr, threads=2):
    """투명 그림은 보이는 곳(알파>0)의 색과 알파만 잰다 — JPEG XL 은 안 보이는 곳 색을 마음대로 바꾼다."""
    import imagecodecs
    for d in (DISTANCE, RETRY_DISTANCE, 0.1, 0.0):      # 잔무늬가 많은 그림(불길)은 0.3 에서 40 dB 미만 → 거의 무손실, 끝으로 무손실
        data = imagecodecs.jpegxl_encode(arr, distance=d, effort=7, decodingspeed=SPEED, numthreads=threads)
        back = imagecodecs.jpegxl_decode(data, numthreads=threads)
        if back.shape != arr.shape:
            raise ValueError(f'JPEG XL 모양 {back.shape} != {arr.shape}')
        if arr.ndim == 3 and arr.shape[2] == 4:
            vis = arr[:, :, 3] > 0
            p = min(psnr(arr[:, :, :3][vis], back[:, :, :3][vis]), psnr(arr[:, :, 3], back[:, :, 3]))
        else:
            p = psnr(arr, back)
        if p >= MIN_PSNR:
            return data, d, p
    raise ValueError(f'JPEG XL {p:.1f} dB at distance {d}')


def finish(row, src_path, ai_path):
    """한 장 마무리: 섞기(+다듬기)·투명도·배율 맞추기·JPEG XL. 돌려주는 값: (key, manifest 줄)"""
    import cv2, numpy as np
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    t0 = time.perf_counter()
    img = cv2.imdecode(np.fromfile(str(src_path), np.uint8), cv2.IMREAD_UNCHANGED)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    rgb = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2RGB)
    alpha = img[:, :, 3] if img.shape[2] == 4 else None
    h, w = rgb.shape[:2]
    ow, oh = row['out']
    stats = {}
    if row['method'] == 'lanczos':
        big = cv2.resize(img if alpha is not None else img[:, :, :3], (ow, oh), interpolation=cv2.INTER_LANCZOS4)
        out = cv2.cvtColor(big, cv2.COLOR_BGRA2RGBA if alpha is not None else cv2.COLOR_BGR2RGB)
    else:
        fed = edge_fill(rgb, alpha == 0) if alpha is not None else rgb
        ai = cv2.imread(str(ai_path), cv2.IMREAD_COLOR)
        if ai is None or ai.shape[:2] != (h * 4, w * 4):
            raise ValueError(f'AI 결과 크기 {None if ai is None else ai.shape[:2]} (원본 {h}x{w})')
        if ai.mean() < 2 and fed.mean() > 8:
            raise ValueError('AI 결과가 검다(GPU 사고)')
        ai = np.ascontiguousarray(ai[:, :, ::-1])
        small = cv2.resize(ai, (w, h), interpolation=cv2.INTER_AREA).astype(np.int16)
        mad = float(np.abs(small - fed.astype(np.int16)).mean())
        if mad > 12:
            raise ValueError(f'AI 결과가 원본과 다르다(평균 차이 {mad:.1f})')
        m1 = edge_weight(fed)
        base = deblock(fed, m1) if row['method'] == 'blend_deblock' else fed
        m = cv2.GaussianBlur(cv2.resize(m1, (w * 4, h * 4), interpolation=cv2.INTER_LINEAR), (FEATHER, FEATHER), 0)
        soft = cv2.resize(base, (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4)
        out = cv2.blendLinear(ai, soft, m, 1 - m)
        stats.update(ai_mad=round(mad, 2), ai_share_pct=round(100 * float(m.mean()), 1))
        if alpha is not None:
            out = np.dstack([out, alpha4(alpha)])
        if (ow, oh) != (w * 4, h * 4):
            out = cv2.resize(out, (ow, oh), interpolation=cv2.INTER_AREA)
    check = cv2.resize(out[:, :, :3], (w, h), interpolation=cv2.INTER_AREA).astype(np.int16)
    diff = np.abs(check - rgb.astype(np.int16))
    vis = (alpha == 255) if alpha is not None else np.ones((h, w), bool)   # 투명한 곳 밑 색은 메웠으니 완전히 보이는 곳만
    stats['source_mad'] = round(float(diff[vis].mean()) if vis.any() else 0.0, 2)
    data, d, p = encode(np.ascontiguousarray(out))
    key = key_of(row['name'])
    tmp = OUT / f'{key}.jxl.tmp'
    tmp.write_bytes(data)
    os.replace(tmp, OUT / f'{key}.jxl')
    for f in (src_path, ai_path):
        try:
            Path(f).unlink()
        except (FileNotFoundError, TypeError):
            pass
    return key, dict(name=row['name'], version=VERSION, method=row['method'], w=w, h=h, out=[ow, oh], alpha=alpha is not None,
                     distance=d, psnr=round(p, 2), jxl_bytes=len(data), seconds=round(time.perf_counter() - t0, 1), **stats)


# ---------- 주 프로세스(GPU) ----------
def save(manifest):
    tmp = MANIFEST.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=0, sort_keys=True), 'utf-8')
    os.replace(tmp, MANIFEST)


def main():
    import cv2, numpy as np
    from npa_adapter import NPA
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--workers', type=int, default=3)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    rows = json.loads((ROOT / 'inventory.json').read_text('utf-8'))['rows']
    manifest = json.loads(MANIFEST.read_text('utf-8')) if MANIFEST.exists() else {}
    todo = [r for r in rows if not (manifest.get(key_of(r['name']), {}).get('version') == VERSION and (OUT / f'{key_of(r["name"])}.jxl').exists())]
    if args.limit:
        todo = todo[:args.limit]
    log(f'시작: 할 일 {len(todo)} / 전체 {len(rows)} (이미 {len(manifest)}), dwm GPU {dwm_gpu_gb()}GB')
    arc = NPA(CG)
    ent = {e['name'].replace('\\', '/'): e for e in arc.entries if e['type'] == 2}
    failed, done, t0, no_ai = [], 0, time.perf_counter(), 0
    gpu0 = gpu_event_id()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        jobs = {}

        def collect(block):
            nonlocal done
            if not jobs:
                return
            finished, _ = wait(list(jobs), return_when=FIRST_COMPLETED) if block else (([j for j in jobs if j.done()]), None)
            for j in finished:
                row = jobs.pop(j)
                try:
                    key, info = j.result()
                    manifest[key] = info
                    done += 1
                except Exception as ex:
                    failed.append(row['name'])
                    log(f'실패 {row["name"]}: {ex}')
                if done and done % 25 == 0:
                    save(manifest)
                    el = time.perf_counter() - t0
                    log(f'{done}/{len(todo)} {el / 60:.1f}분, 남은 어림 {el / done * (len(todo) - done) / 60:.0f}분, F: 여유 {shutil.disk_usage("F:/").free / 2**30:.1f}GB, dwm GPU {dwm_gpu_gb()}GB')

        for row in todo:
            if (ROOT / 'STOP').exists():
                log('STOP 파일 — 멈춤'); break
            if shutil.disk_usage('F:/').free < MIN_FREE:
                log('F: 여유 6GB 미만 — 멈춤'); break
            while len(jobs) >= args.workers * 2:
                collect(True)
            collect(False)
            key = key_of(row['name'])
            img = cv2.imdecode(np.frombuffer(arc.read(ent[row['name']]), np.uint8), cv2.IMREAD_UNCHANGED)
            src_path = TMP / f'{key}.src.png'
            cv2.imencode('.png', img)[1].tofile(str(src_path))
            ai_path = None
            if row['method'] != 'lanczos':
                if img.ndim == 2:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                rgb = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2RGB)
                fed = edge_fill(rgb, img[:, :, 3] == 0) if img.shape[2] == 4 else rgb
                in_path, ai_path = TMP / f'{key}.in.png', TMP / f'{key}.ai.png'
                cv2.imencode('.png', cv2.cvtColor(fed, cv2.COLOR_RGB2BGR))[1].tofile(str(in_path))
                r = subprocess.run([str(UP / 'bin' / 'upscayl-bin.exe'), '-i', str(in_path), '-o', str(ai_path), '-s', '4',
                                    '-m', str(UP / 'models'), '-n', 'high-fidelity-4x', '-f', 'png'], capture_output=True)
                in_path.unlink(missing_ok=True)
                g = gpu_event_id()
                if g != gpu0:
                    log(f'GPU 드라이버 오류 기록 새로 생김({gpu0}→{g}) {row["name"]} — 멈춤')
                    break
                if not ai_path.exists():
                    failed.append(row['name']); log(f'실패 {row["name"]}: AI 출력 없음 rc={r.returncode}')
                    no_ai += 1
                    if no_ai >= 3:   # 10-26 22:59: nvlddmkm 기록 없이 vkCreateDevice 가 막혀 남은 299장을 1초씩 실패로 넘겼다
                        log('AI 출력 없음 3장 연속 — GPU 장치를 못 만드는 상태로 보고 멈춤 (재부팅·프로그램 정리 뒤 다시)'); break
                    continue
                no_ai = 0
            jobs[pool.submit(finish, row, src_path, ai_path)] = row
        while jobs:
            collect(True)
    save(manifest)
    rows_ = list(manifest.values())
    log(json.dumps({'끝남': len(rows_), '실패': failed[:20], '실패수': len(failed), 'JXL_GB': round(sum(r['jxl_bytes'] for r in rows_) / 2**30, 2),
                    '최저_dB': min((r['psnr'] for r in rows_), default=None), '원본차이_최대': max((r['source_mad'] for r in rows_), default=None)},
                   ensure_ascii=False))


if __name__ == '__main__':
    main()
