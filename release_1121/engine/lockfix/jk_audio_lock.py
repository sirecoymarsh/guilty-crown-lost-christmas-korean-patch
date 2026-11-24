"""J/K 다시 시작 때 소리가 끊기는지 내 시험 사본에서 잰다(Claude 11-24).
배포 세션의 Y:\\AI\\claude-work\\gclx-snd-perf\\jk_audio.py 와 같은 방법(게임 소리 세션 최고값을 5ms 마다)이고,
게임 폴더만 P:\\AI\\gclx-locktest\\game(그 안의 DLL 을 시험) 로 바꾸고 결과 풀이를 붙였다.
python -X utf8 jk_audio_lock.py <꼬리표> [--off] [--nss nss.test_bgm.npa] [--j 86,96]
 --off : N2HD_BGMKEEP_OFF=1 (음악 잇기 끔, 비교용)
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, r'P:\AI\touka-ps2-kr\work\codex_watch\host')
import hostlib as H  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ab_run import TOOLS, RUNS, GAME, EXE, NSS, wait_free  # noqa: E402

# run_test 는 게임 폴더의 nss.npa 가 <대본 폴더>\nss.normal.npa 와 같은지 먼저 본다 → 시험 사본과 짝인 lockfix\nss 를 쓴다
# (nss.test_bgm.npa 는 release_1121\nss_variants 에서 복사해 둔다).
NSS_DIR = str(NSS)


def analyze(name, jt):
    run = RUNS / name
    rep = json.loads((run / 'report.json').read_text('utf-8'))
    samples = json.loads((run / 'audio_peaks.json').read_text('utf-8'))
    t0 = rep['t0_epoch']
    a, b = min(jt) - 1.0, max(jt) + 8.0
    bins = {}
    for t, v in samples:
        s = t - t0
        if a <= s <= b:
            k = int((s - a) / 0.05)
            bins[k] = max(bins.get(k, 0.0), v)
    silent = sorted(k for k, v in bins.items() if v < 0.001)
    spans = []
    for k in silent:                                   # 이어진 조용한 칸을 구간으로
        if spans and k == spans[-1][1] + 1:
            spans[-1][1] = k
        else:
            spans.append([k, k])
    spans = [(round(a + x * 0.05, 2), round(a + (y + 1) * 0.05, 2)) for x, y in spans]
    log = run / 'profile' / 'bgmkeep.log'
    lines = log.read_text(errors='replace').splitlines() if log.exists() else []
    after = [ln for ln in lines if ' after ' in ln]
    return dict(run=name, window=[a, b], bins=len(bins), silent_bins=len(silent), silent_spans=spans[:8],
                bgmkeep_after=[ln.split(' ', 1)[1][:150] for ln in after][:6], bgmkeep_lines=len(lines),
                exited_early=rep.get('exited_early'),
                dialogs=[d for d in rep.get('dialogs_closed', []) if 'moved off' not in str(d)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tag'); ap.add_argument('--off', action='store_true')
    ap.add_argument('--nss', default='nss.test_bgm.npa'); ap.add_argument('--j', default='86,96')
    a = ap.parse_args()
    jt = [int(x) for x in a.j.split(',')]
    name = f'lk_jk_{a.tag}_{time.strftime("%H%M%S")}'
    env = dict(os.environ, GCLX_GAME=str(GAME), GCLX_NSS_DIR=NSS_DIR, GCLX_EXTRA_NPA='cg.fix.npa')
    args = [sys.executable, '-X', 'utf8', 'run_test.py', name, '--nss', a.nss, '--seconds', str(max(jt) + 16),
            '--shot-ms', '60000', '--click-xy', '40:440:296', '--keys', '--keys-from', '46', '--keys-until', '68']
    envs = ['N2HD_TEST_NO_INJECT=1', 'N2HD_TEST_CURSOR_FILE=1', 'N2HD_TEST_KEEPALIVE_MS=500', 'N2HD_TEST_FRAMES=1',
            'N2HD_TEST_SHOT_START_MS=999000', 'N2HD_TEST_BGMKEEP_TRACE=1'] + (['N2HD_BGMKEEP_OFF=1'] if a.off else [])
    for e in envs:
        args += ['--env', e]
    for t in jt:
        args += ['--key-at', f'{t}:0x4A']
    wait_free(print)
    log = open(RUNS / f'{name}.log', 'w', encoding='utf-8')
    p = subprocess.Popen(args, cwd=TOOLS, env=env, stdout=log, stderr=subprocess.STDOUT)
    pid = None; t_start = time.time()
    while pid is None and time.time() - t_start < 60:
        ps = H.pids_of(GAME, EXE)
        if ps:
            pid = ps[0]
        else:
            time.sleep(0.5)
    samples, meters = [], []
    while p.poll() is None:
        if not meters:
            meters = H.sessions_of(pid) if pid else []
            if not meters:
                time.sleep(0.2); continue
        try:
            samples.append((time.time(), max(H.peak(m) for _, m in meters)))
        except Exception:
            meters = []
        time.sleep(0.005)
    for v, m in meters:
        H.release(v); H.release(m)
    (RUNS / name / 'audio_peaks.json').write_text(json.dumps(samples), 'utf-8')
    res = analyze(name, jt)
    res['mode'] = 'off' if a.off else 'on'; res['samples'] = len(samples)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == '__main__':
    main()
