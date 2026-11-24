"""길티 크라운 4배 리마스터 비교 시안(프롤로그 그림만 — 사용자 미플레이).
레콘키스타 방식(vn-art-4k-remaster 스킬): high-fidelity-4x + 섞기, 투명 그림은 가장자리 색 메우기, 투명도는 AI 없이.

  python -X utf8 sample_compare.py            -> F:\\AI\\gclx-4k\\sample1\\{src,in,ai,out}\\..., report.json
열: bilinear(지금 4K 화면에 가까움) / lanczos(AI 없음) / ai(high-fidelity-4x 그대로) / blend(섞기)
"""
import json, subprocess, sys, time, re
from pathlib import Path
import cv2
import numpy as np

sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(r'F:\AI\gclx-4k\sample1')
CG = r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\outputs\korean-game-candidate\game\cg.npa'
UP = Path(r'P:\AI\Codex\projects\image-upscaling-tools\apps\Upscayl-2.15.0\resources')
SAMPLES = {
    'bg_street': 'bg/bg001001_3_六本木街並み1.jpg',
    'ev_present': 'ev/ev0105プレゼントダァト兵キャンサー化.jpg',
    'st_present': 'st/stプレゼント_通常_smile1.png',
    'bu_scrooge': 'bu/buスクルージ_通常_normal.png',
}
EDGE_LO, EDGE_HI, FEATHER = 40, 120, 9


def gpu_event_id():
    q = "*[System[Provider[@Name='nvlddmkm']]]"
    r = subprocess.run(['wevtutil', 'qe', 'System', f'/q:{q}', '/c:1', '/rd:true', '/f:xml'], capture_output=True, text=True)
    m = re.search(r'<EventRecordID>(\d+)<', r.stdout)
    return int(m.group(1)) if m else None


def edge_fill(rgb, clear):
    if not clear.any() or clear.all():
        return rgb
    _, labels = cv2.distanceTransformWithLabels(clear.astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(~clear)
    lab2i = np.zeros(labels.max() + 1, np.int64)
    lab2i[labels[ys, xs]] = np.arange(len(ys))
    out = rgb.copy()
    out[clear] = rgb[ys[lab2i[labels[clear]]], xs[lab2i[labels[clear]]]]
    soft = cv2.GaussianBlur(out, (0, 0), 1.5)
    out[clear] = soft[clear]
    return out


def blend(src, ai):
    h, w = src.shape[:2]
    g = cv2.cvtColor(src, cv2.COLOR_RGB2GRAY).astype(np.float32)
    edge = cv2.GaussianBlur(cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)), (3, 3), 0)
    m = np.clip((edge - EDGE_LO) / (EDGE_HI - EDGE_LO), 0, 1)
    m = cv2.GaussianBlur(cv2.resize(m, (w * 4, h * 4), interpolation=cv2.INTER_LINEAR), (FEATHER, FEATHER), 0)
    soft = cv2.resize(src, (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4)
    return cv2.blendLinear(np.ascontiguousarray(ai), soft, m, 1 - m), float(m.mean())


def alpha4(a1):
    """투명도 4배: Lanczos → 가운데 기준 경사 2배 → 1배 완전 투명/불투명 칸 고정 (레콘키스타 mask4, 255=보임)"""
    h, w = a1.shape
    v = cv2.resize(a1.astype(np.float32), (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4)
    v = np.clip((v - 127.5) * 2 + 127.5, 0, 255)
    v[np.repeat(np.repeat(a1 == 0, 4, 0), 4, 1)] = 0
    v[np.repeat(np.repeat(a1 == 255, 4, 0), 4, 1)] = 255
    return v.astype(np.uint8)


def main():
    for d in ('src', 'in', 'ai', 'out'):
        (ROOT / d).mkdir(parents=True, exist_ok=True)
    arc = NPA(CG)
    ent = {e['name'].replace('\\', '/'): e for e in arc.entries if e['type'] == 2}
    report = {}
    for key, name in SAMPLES.items():
        raw = np.frombuffer(arc.read(ent[name]), np.uint8)
        img = cv2.imdecode(raw, cv2.IMREAD_UNCHANGED)
        rgb = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2RGB)
        alpha = img[:, :, 3] if img.ndim == 3 and img.shape[2] == 4 else None
        cv2.imencode('.png', img)[1].tofile(str(ROOT / 'src' / f'{key}.png'))
        fed = edge_fill(rgb, alpha == 0) if alpha is not None else rgb
        cv2.imencode('.png', cv2.cvtColor(fed, cv2.COLOR_RGB2BGR))[1].tofile(str(ROOT / 'in' / f'{key}.png'))
        before = gpu_event_id()
        t0 = time.perf_counter()
        r = subprocess.run([str(UP / 'bin' / 'upscayl-bin.exe'), '-i', str(ROOT / 'in' / f'{key}.png'), '-o', str(ROOT / 'ai' / f'{key}.png'),
                            '-s', '4', '-m', str(UP / 'models'), '-n', 'high-fidelity-4x', '-f', 'png'], capture_output=True, text=True)
        sec = time.perf_counter() - t0
        after = gpu_event_id()
        if after != before:
            raise SystemExit(f'GPU 드라이버 오류 기록이 새로 생김({before}→{after}) — 멈춤. {r.stderr[-300:]}')
        ai = cv2.imread(str(ROOT / 'ai' / f'{key}.png'), cv2.IMREAD_COLOR)
        h, w = rgb.shape[:2]
        if ai is None or ai.shape[:2] != (h * 4, w * 4) or ai.mean() < 2:
            raise SystemExit(f'{key}: AI 결과 이상 {None if ai is None else ai.shape} mean {None if ai is None else ai.mean():.1f}')
        ai = cv2.cvtColor(ai, cv2.COLOR_BGR2RGB)
        small = cv2.resize(ai, (w, h), interpolation=cv2.INTER_AREA).astype(np.int16)
        mad = float(np.abs(small - fed.astype(np.int16)).mean())
        bl, kept = blend(fed, ai)
        variants = {'bilinear': cv2.resize(rgb, (w * 4, h * 4), interpolation=cv2.INTER_LINEAR),
                    'lanczos': cv2.resize(rgb, (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4), 'ai': ai, 'blend': bl}
        a4 = None
        if alpha is not None:
            a4 = alpha4(alpha)
            alin = cv2.resize(alpha, (w * 4, h * 4), interpolation=cv2.INTER_LINEAR)
        for tag, v in variants.items():
            if alpha is not None:
                a = alin if tag == 'bilinear' else a4
                out = np.dstack([v, a])
                cv2.imencode('.png', cv2.cvtColor(out, cv2.COLOR_RGBA2BGRA))[1].tofile(str(ROOT / 'out' / f'{key}.{tag}.png'))
            else:
                cv2.imencode('.png', cv2.cvtColor(v, cv2.COLOR_RGB2BGR))[1].tofile(str(ROOT / 'out' / f'{key}.{tag}.png'))
        report[key] = {'name': name, 'size_1x': [w, h], 'alpha': alpha is not None, 'ai_seconds': round(sec, 1),
                       'ai_vs_source_mad': round(mad, 2), 'blend_ai_share_pct': round(100 * kept, 1)}
        print(key, report[key], flush=True)
    (ROOT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), 'utf-8')


if __name__ == '__main__':
    main()
