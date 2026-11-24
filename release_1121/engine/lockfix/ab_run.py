"""잠금 고침 켬/끔을 번갈아 숨긴 시험으로 잰다(Claude 11-24). 전용 사본 P:\\AI\\gclx-locktest\\game + lockfix\\nss 만 쓴다.
- 한 빌드(lockfix\\out DLL) 안 스위치 N2HD_TEST_LOCKFIX_OFF=1 로 끔 → 같은 DLL·같은 대본으로 A/B.
- 다른 세션의 시험 게임(P:\\AI\\gclx-reltest)이 돌고 있으면 끝날 때까지 기다렸다 시작한다(시험용 뮤텍스가 하나라 둘이 같이 못 뜬다).
- 시나리오: 타이틀 「사운드」(40초) → 곡 줄 누름(46초) → 48초부터 1초마다 다른 줄에 커서 올림(누르지 않음).
python -X utf8 ab_run.py <꼬리표> <대본> <순서: 예 off,on,off,on> [--row 번호] [--hover-from 48 --hover-to 75] [--entry-only]
"""
import argparse, json, os, struct, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, r'P:\AI\touka-ps2-kr\work\codex_watch\host')
import hostlib as H  # noqa: E402

TOOLS = Path(r'F:\AI\gclx-4k\tools')
RUNS = Path(r'F:\AI\gclx-4k\testrun')
GAME = Path(r'P:\AI\gclx-locktest\game')
OTHER = Path(r'P:\AI\gclx-reltest\game')
# 코덱스의 시험 게임(같은 시험 뮤텍스를 쓴다 — 09:1x save-rebase 의 run.cmd 가 띄우는 곳)
CODEX_GAMES = [Path(r'P:\AI\Codex\projects\gclx-song-20261123\awakening\game'),
               Path(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\runtime-game')]
NSS =Path(__file__).resolve().parent / 'nss'
EXE = 'GUILTY CROWN LOST XMAS.exe'
ROW_XY = {n: ((200 if n <= 10 else 700), 71 + 44 * ((n - 1) if n <= 10 else (n - 11))) for n in range(1, 20)}
HOVERS = [(700, 115), (200, 159), (700, 203), (200, 247), (700, 291), (200, 335)]


def wait_free(log):
    """다른 세션 시험(또는 내 앞 시험)이 끝나고 8초 동안 조용할 때까지."""
    quiet = None; t0 = time.time()
    while True:
        busy = H.pids_of(OTHER, EXE) or H.pids_of(GAME, EXE) or any(H.pids_of(d, EXE) for d in CODEX_GAMES)
        if busy:
            quiet = None
        elif quiet is None:
            quiet = time.time()
        elif time.time() - quiet >= 8:
            if time.time() - t0 > 10:
                log(f'waited {time.time() - t0:.0f}s for the other test run')
            return
        if time.time() - t0 > 1500:
            raise SystemExit('다른 시험이 25분 넘게 계속됨 — 그만둠')
        time.sleep(1)


def frames(run):
    rep = json.loads((run / 'report.json').read_text('utf-8'))
    raw = (run / 'profile' / 'frames.bin').read_bytes()
    ts = [t - rep['t0_epoch'] for t in struct.unpack('<%dd' % (len(raw) // 8), raw[:len(raw) // 8 * 8])]
    return rep, ts


def summarize(name, a, b):
    run = RUNS / name
    rep, ts = frames(run)
    seg = [t for t in ts if a <= t <= b]
    gaps = [(x, y - x) for x, y in zip(seg, seg[1:])]
    big = [(round(x, 1), round(g, 2)) for x, g in gaps if g > 0.6]
    locks = (run / 'profile' / 'locks.log')
    lk = locks.read_text(errors='replace').splitlines() if locks.exists() else []
    kinds = {}
    for line in lk:
        k = line.split()[1] if len(line.split()) > 1 else '?'
        kinds[k] = kinds.get(k, 0) + 1
    return dict(run=name, frames=len(seg), fps=round(len(seg) / max(b - a, 1e-9), 1), gaps_over_0_6=len(big), gap_sum=round(sum(g for _, g in big), 1),
                gaps=big, max_gap=round(max((g for _, g in gaps), default=0), 2), locks=kinds, clicks=rep.get('clicks_xy'), exited_early=rep.get('exited_early'),
                dialogs=[d for d in rep.get('dialogs_closed', []) if 'moved off' not in str(d)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tag'); ap.add_argument('nss'); ap.add_argument('order')
    ap.add_argument('--row', type=int, default=1)
    ap.add_argument('--hover-from', type=int, default=48); ap.add_argument('--hover-to', type=int, default=75)
    ap.add_argument('--seconds', type=int, default=0)
    ap.add_argument('--extra', action='append', default=[], help='run_test 에 그대로 넘길 인자(예 --extra=--env --extra=X=1)')
    a = ap.parse_args()
    out = Path(__file__).resolve().parent / f'ab_{a.tag}.log'

    def log(s):
        line = time.strftime('%H:%M:%S ') + s
        print(line, flush=True)
        with out.open('a', encoding='utf-8') as f:
            f.write(line + '\n')
    env = dict(os.environ, GCLX_GAME=str(GAME), GCLX_NSS_DIR=str(NSS))
    rx, ry = ROW_XY[a.row]
    seconds = a.seconds or a.hover_to + 2
    results = []
    for i, mode in enumerate(a.order.split(',')):
        name = f'lk_{a.tag}_{i + 1}{mode}_{time.strftime("%H%M%S")}'
        cmd = [sys.executable, '-X', 'utf8', 'run_test.py', name, '--nss', a.nss, '--seconds', str(seconds), '--shot-ms', '60000',
               '--click-xy', '40:440:392', '--click-xy', f'46:{rx}:{ry}']
        k = 0
        for sec in range(a.hover_from, a.hover_to + 1):
            x, y = HOVERS[k % len(HOVERS)]; k += 1
            if (x, y) == (rx, ry):
                x, y = HOVERS[k % len(HOVERS)]; k += 1
            cmd += ['--hover-xy', f'{sec}:{x}:{y}']
        for kv in ('N2HD_TEST_NO_INJECT=1', 'N2HD_TEST_CURSOR_FILE=1', 'N2HD_TEST_KEEPALIVE_MS=500', 'N2HD_TEST_FRAMES=1', 'N2HD_TEST_SHOT_START_MS=999000'):
            cmd += ['--env', kv]
        if mode == 'off':
            cmd += ['--env', 'N2HD_TEST_LOCKFIX_OFF=1']
        cmd += a.extra
        wait_free(log)
        log(f'start {name}')
        r = subprocess.run(cmd, cwd=TOOLS, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
        (RUNS / f'{name}.log').write_text((r.stdout or '') + '\n--- stderr\n' + (r.stderr or ''), 'utf-8')
        if r.returncode:
            log(f'  run_test exit {r.returncode}: {(r.stderr or r.stdout or "").strip()[-300:]}')
            continue
        s = summarize(name, a.hover_from - 0.5, seconds - 0.5)
        s['mode'] = mode
        results.append(s)
        log('  ' + json.dumps(s, ensure_ascii=False))
    (Path(__file__).resolve().parent / f'ab_{a.tag}.json').write_text(json.dumps(results, ensure_ascii=False, indent=1), 'utf-8')
    for mode in ('off', 'on'):
        rs = [r for r in results if r['mode'] == mode]
        if rs:
            log(f'{mode}: runs={len(rs)} gaps>0.6s={[r["gaps_over_0_6"] for r in rs]} sum={[r["gap_sum"] for r in rs]} fps={[r["fps"] for r in rs]} locks={[r["locks"] for r in rs]}')


if __name__ == '__main__':
    main()
