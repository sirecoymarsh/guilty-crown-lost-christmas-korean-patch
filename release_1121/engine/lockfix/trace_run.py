"""사운드 화면 단계별 시간 재기(Claude 11-24): make_trace_variant.py 의 표지 대본을 숨긴 시험으로 돌리고 trace.log 를 풀어 적는다.
python -X utf8 trace_run.py <꼬리표> <대본> --clicks 40:440:392,46:200:71,53:200:115 [--seconds 62] [--off] [--env NAME=VALUE ...]
표지: s0 진입 · s1 Wait(500) 뒤 · s2 KuCalc 뒤 · s3 KuList 시작 · s4 가림막/지우기/효과음 뒤 · s5 줄 만든 뒤 · s6 막대·풀이 준비 뒤 · s7 조작 가능
      s8 곡 누름(KuFade 시작) · s9 SoundPlay 뒤
누름마다: 도구가 단추를 뗀 시각 → 첫 표지(곡이면 s8, 멈춤이면 s3)까지 = 반응 지연, s8→s9, s3→s4(지우기), s4→s7, 뗀 뒤 조작 가능까지.
"""
import argparse, ctypes, json, os, struct, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ab_run import TOOLS, RUNS, GAME, NSS, wait_free  # noqa: E402

LABEL = {'s0': '진입', 's1': 'Wait(500) 뒤', 's2': 'KuCalc 뒤', 's3': 'KuList 시작', 's4': '가림막·지우기 뒤', 's5': '줄 만든 뒤',
         's6': '막대·풀이 준비 뒤', 's7': '조작 가능', 's8': '곡 누름(KuFade)', 's9': 'SoundPlay 뒤'}


def analyze(name, quiet=False):
    run = RUNS / name
    rep = json.loads((run / 'report.json').read_text('utf-8'))
    tr = run / 'profile' / 'trace.log'
    rows = []
    if tr.exists():
        for line in tr.read_text(errors='replace').splitlines():
            p = line.split()
            if len(p) >= 2 and p[1].startswith('trace_s'):
                rows.append((int(p[0]), p[1][6:8]))
    # GetTickCount(부팅 뒤 ms) → 시험 시계(초): 부팅 시각 = 지금 − GetTickCount64
    k32 = ctypes.windll.kernel32; k32.GetTickCount64.restype = ctypes.c_ulonglong
    boot = time.time() - k32.GetTickCount64() / 1000.0
    ev = [((boot + (t & 0xffffffff) / 1000.0) - rep['t0_epoch'], k) for t, k in rows]
    if k32.GetTickCount64() > 0xffffffff:                       # 49일 넘게 켜 둔 PC: 32비트 틱이 한 바퀴 돎
        wraps = k32.GetTickCount64() >> 32
        ev = [(t + wraps * 4294967.296, k) for t, k in ev]
    out = []
    prev = None
    for t, k in ev:
        d = '' if prev is None else f'+{(t - prev) * 1000:6.0f}ms'
        out.append(f'  {t:8.3f}s  {k} {LABEL.get(k, ""):<16} {d}')
        prev = t
    clicks = [(c[0], c[1]) for c in rep.get('clicks_xy', [])]
    res = []
    for i, (spec, sent) in enumerate(clicks[1:], 1):            # 첫 누름은 타이틀의 「사운드」
        nxt = clicks[i + 1][1] if i + 1 < len(clicks) else 1e9
        seg = [(t, k) for t, k in ev if sent - 1.2 <= t < nxt - 1.2]   # 누름은 올림 0.3초 + 누름 0.25초 뒤에 적힌다
        d = dict(click=spec, sent=round(sent, 2))
        first = next(((t, k) for t, k in seg if k in ('s8', 's3')), None)
        if not first:
            d['result'] = '반응 없음'
            res.append(d); continue
        d['first'] = first[1]; d['react_ms'] = round((first[0] - sent) * 1000)
        tt = {}
        for t, k in seg:
            tt.setdefault(k, t)
        if 's8' in tt and 's9' in tt:
            d['s8_s9'] = round((tt['s9'] - tt['s8']) * 1000)
        if 's3' in tt and 's4' in tt:
            d['s3_s4'] = round((tt['s4'] - tt['s3']) * 1000)
        if 's4' in tt and 's7' in tt:
            d['s4_s7'] = round((tt['s7'] - tt['s4']) * 1000)
        if 's7' in tt:
            d['ready_ms'] = round((tt['s7'] - sent) * 1000)
        res.append(d)
    lk = run / 'profile' / 'locks.log'
    kinds = {}
    if lk.exists():
        for line in lk.read_text(errors='replace').splitlines():
            p = line.split()
            if len(p) > 1:
                kinds[p[1]] = kinds.get(p[1], 0) + 1
    raw = (run / 'profile' / 'frames.bin').read_bytes()
    ts = [t - rep['t0_epoch'] for t in struct.unpack('<%dd' % (len(raw) // 8), raw[:len(raw) // 8 * 8])]
    big = [(round(x, 1), round(y - x, 2)) for x, y in zip(ts, ts[1:]) if y - x > 0.6 and x > 39]
    summary = dict(run=name, clicks=res, locks=kinds, frame_gaps=big, exited_early=rep.get('exited_early'),
                   dialogs=[d for d in rep.get('dialogs_closed', []) if 'moved off' not in str(d)])
    if not quiet:
        print('\n'.join(out))
    return summary, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tag'); ap.add_argument('nss')
    ap.add_argument('--clicks', required=True)
    ap.add_argument('--seconds', type=int, default=62)
    ap.add_argument('--off', action='store_true')
    ap.add_argument('--env', action='append', default=[])
    ap.add_argument('--quiet', action='store_true')
    ap.add_argument('--shot-ms', type=int, default=60000, help='화면 찍기 간격(ms); --shot-start 와 함께')
    ap.add_argument('--shot-start', type=int, default=999000, help='이 ms 부터 화면을 찍는다(기본: 안 찍음). 4K BMP 한 장 33MB')
    a = ap.parse_args()
    name = f'lk_{a.tag}_{time.strftime("%H%M%S")}'
    cmd = [sys.executable, '-X', 'utf8', 'run_test.py', name, '--nss', a.nss, '--seconds', str(a.seconds), '--shot-ms', str(a.shot_ms)]
    for c in a.clicks.split(','):
        cmd += ['--click-xy', c]
    for kv in ['N2HD_TEST_NO_INJECT=1', 'N2HD_TEST_CURSOR_FILE=1', 'N2HD_TEST_KEEPALIVE_MS=500', 'N2HD_TEST_FRAMES=1', f'N2HD_TEST_SHOT_START_MS={a.shot_start}'] + a.env:
        cmd += ['--env', kv]
    if a.off:
        cmd += ['--env', 'N2HD_TEST_LOCKFIX_OFF=1']
    wait_free(print)
    env = dict(os.environ, GCLX_GAME=str(GAME), GCLX_NSS_DIR=str(NSS))
    r = subprocess.run(cmd, cwd=TOOLS, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    (RUNS / f'{name}.log').write_text((r.stdout or '') + '\n--- stderr\n' + (r.stderr or ''), 'utf-8')
    if r.returncode:
        raise SystemExit(f'run_test exit {r.returncode}: {(r.stderr or r.stdout or "").strip()[-400:]}')
    summary, out = analyze(name, a.quiet)
    here = Path(__file__).resolve().parent
    (here / f'trace_{a.tag}.txt').write_text(name + '\n' + '\n'.join(out) + '\n', 'utf-8')
    (here / f'trace_{a.tag}.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1), 'utf-8')
    print(name)
    for c in summary['clicks']:
        print('  ', json.dumps(c, ensure_ascii=False))
    print('   locks', summary['locks'], 'frame gaps>0.6s', summary['frame_gaps'], 'dialogs', summary['dialogs'])


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--analyze':
        s, _ = analyze(sys.argv[2])
        print(json.dumps(s, ensure_ascii=False, indent=1))
    else:
        main()
