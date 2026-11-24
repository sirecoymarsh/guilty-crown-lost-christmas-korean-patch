"""남이 빌드한 DLL(코덱스 통합판 등)에서 잠금 고침이 듣는지 숨긴 시험으로 확인한다(Claude 11-24).
전용 사본 P:\\AI\\gclx-locktest\\game 의 DLL 해시를 먼저 확인하고 차례로:
 1) 사운드 화면 올림 켬/끔(ab_run, 설치판 대본 nss.test_inst_open)
 2) 곡 연달아 바꾸기(trace_run, 둘째 고침 대본 nss.test_trace2_open, 누름 12번)
 3) 본편 새 게임 200초(--story-nss, 기본 nss.normal)
python -X utf8 verify_dll.py <꼬리표> <DLL sha256 앞 8자> [--order off,on] [--skip-story] [--story-nss 파일] [--compare-story 이전 실행 이름]
"""
import argparse, hashlib, json, os, struct, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ab_run import TOOLS, RUNS, GAME, NSS, wait_free  # noqa: E402

CLICKS = '40:440:392,46:200:71,52:200:159,58:200:115,64:200:203,70:512:559,76:700:115,82:200:247,88:700:379,94:700:423,100:200:291,106:512:559'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def story_summary(name):
    run = RUNS / name
    rep = json.loads((run / 'report.json').read_text('utf-8'))
    fb = run / 'profile' / 'frames.bin'
    raw = fb.read_bytes() if fb.exists() else b''
    ts = [t - rep['t0_epoch'] for t in struct.unpack('<%dd' % (len(raw) // 8), raw[:len(raw) // 8 * 8])]
    seg = [t for t in ts if t >= 45]
    gaps = [(round(x, 1), round(y - x, 2)) for x, y in zip(seg, seg[1:]) if y - x > 0.6]
    lk = run / 'profile' / 'locks.log'
    lines = lk.read_text(errors='replace').splitlines() if lk.exists() else []
    return dict(run=name, frames_after_45s=len(seg), last_frame_s=round(ts[-1], 1) if ts else None, gaps_over_0_6=gaps[:12], n_gaps=len(gaps),
                locks_lines=len(lines), exited_early=rep.get('exited_early'), closed_by=rep.get('closed_by'),
                dialogs=[d for d in rep.get('dialogs_closed', []) if 'moved off' not in str(d)], shots=rep.get('shots') if isinstance(rep.get('shots'), int) else len(rep.get('shots') or []),
                clicks=rep.get('clicks_xy'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tag'); ap.add_argument('sha8')
    ap.add_argument('--order', default='off,on')
    ap.add_argument('--skip-story', action='store_true')
    ap.add_argument('--story-nss', default='nss.normal.npa')
    ap.add_argument('--compare-story', default='lk_story2_084952')
    a = ap.parse_args()
    dll = GAME / 'n2hd_runtime.dll'
    h = sha(dll)
    if not h.startswith(a.sha8):
        raise SystemExit(f'locktest DLL 은 {h[:8]} — 기대 {a.sha8}')
    print(time.strftime('%H:%M:%S'), 'DLL', h, flush=True)
    py = [sys.executable, '-X', 'utf8']
    kw = dict(capture_output=True, text=True, encoding='utf-8', errors='replace')

    r1 = subprocess.run(py + ['ab_run.py', a.tag, 'nss.test_inst_open.npa', a.order], cwd=HERE, **kw)
    print('== 1) 올림 켬/끔', flush=True)
    for line in (r1.stdout or '').splitlines():
        if ' off: ' in line or ' on: ' in line or 'run_test exit' in line or 'waited' in line:
            print('  ', line[:400])
    if r1.returncode:
        print('   exit', r1.returncode, (r1.stderr or '')[-300:])

    r2 = subprocess.run(py + ['trace_run.py', 'mc_' + a.tag, 'nss.test_trace2_open.npa', '--clicks', CLICKS, '--seconds', '113', '--quiet'], cwd=HERE, **kw)
    print('== 2) 곡 연달아 바꾸기', flush=True)
    print((r2.stdout or '')[-2600:])
    if r2.returncode:
        print('   exit', r2.returncode, (r2.stderr or '')[-300:])

    if not a.skip_story:
        wait_free(print)
        name = f'lk_story_{a.tag}_{time.strftime("%H%M%S")}'
        cmd = py + ['run_test.py', name, '--nss', a.story_nss, '--seconds', '200', '--shot-ms', '30000', '--click-xy', '40:440:296']
        for kv in ('N2HD_TEST_NO_INJECT=1', 'N2HD_TEST_CURSOR_FILE=1', 'N2HD_TEST_KEEPALIVE_MS=500', 'N2HD_TEST_FRAMES=1', 'N2HD_TEST_SHOT_START_MS=168000'):
            cmd += ['--env', kv]
        env = dict(os.environ, GCLX_GAME=str(GAME), GCLX_NSS_DIR=str(NSS))
        r3 = subprocess.run(cmd, cwd=TOOLS, env=env, **kw)
        (RUNS / f'{name}.log').write_text((r3.stdout or '') + '\n--- stderr\n' + (r3.stderr or ''), 'utf-8')
        print('== 3) 본편 새 게임 200초', a.story_nss, flush=True)
        if r3.returncode:
            print('   run_test exit', r3.returncode, (r3.stderr or r3.stdout or '')[-300:])
        else:
            print('  ', json.dumps(story_summary(name), ensure_ascii=False))
            if a.compare_story and (RUNS / a.compare_story / 'report.json').exists():
                print('   비교', json.dumps(story_summary(a.compare_story), ensure_ascii=False))
    h2 = sha(dll)
    print(time.strftime('%H:%M:%S'), 'DLL 끝', h2[:8], '그대로' if h2 == h else '바뀜!')


if __name__ == '__main__':
    main()
