"""숨긴 프레임 측정: 프롤로그 자동 진행을 같은 빌드에서 스위치를 번갈아 켜고 끄며 여러 번 돌리고, hires\\art.log 의 10초 통계로 판정.
python -X utf8 perf_ab.py <이름> <초> <변형들: 이름=ENV1=V1;ENV2=V2 … (빈 값이면 기본)> [--rounds N]
예) perf_ab.py fp 110 "on=" "off=N2HD_FAST_PNG=0" --rounds 2
결과: testrun\\<이름>_<변형>_<n>\\perf.json, 맨 끝에 표. 간격 묶음 <12/20/35/50/100/+ ms (60fps=16.7ms → <20, 30~40fps → 20~35)."""
import json, os, re, subprocess, sys, time
from pathlib import Path

GAME = Path(os.environ.get('GCLX_GAME', r'P:\AI\gclx-codexrun\game'))
LOG = GAME / 'hires' / 'art.log'
PM = Path(r'P:/AI/Codex/projects/guilty-crown-lost-christmas-ui-opening/work/revisions/frame-time-20261102/PresentMon-2.6.0-x64.exe')
TOOLS = Path(__file__).parent
args = [a for a in sys.argv[1:] if not a.startswith('--')]
rounds = int(sys.argv[sys.argv.index('--rounds') + 1]) if '--rounds' in sys.argv else 2
if '--rounds' in sys.argv:
    args.remove(sys.argv[sys.argv.index('--rounds') + 1])
name, secs, variants = args[0], int(args[1]), args[2:]
STAT = re.compile(r'^stat t=(\d+) presents=(\d+) .*?hist<12/20/35/50/100/\+=(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)')
rows = []
for rnd in range(1, rounds + 1):
    for v in variants:
        vn, _, envs = v.partition('=')
        run = f'{name}_{vn}_{rnd}'
        start = LOG.stat().st_size if LOG.exists() else 0
        cmd = [sys.executable, '-X', 'utf8', str(TOOLS / 'run_test.py'), run, '--nss', os.environ.get('PERF_NSS', 'nss.test_auto.npa'),
               '--seconds', str(secs), '--shot-ms', '0']
        for kv in [e for e in envs.split(';') if e]:
            cmd += ['--env', kv]
        t0 = time.time()
        # 변형 이름이 big 으로 시작하면 창을 사용자 TV 크기(4096x2160)로 모든 모니터 밖에 둔다(run_test.py RUN_TEST_WINDOW)
        penv = dict(os.environ, RUN_TEST_WINDOW='4096x2160') if vn.startswith('big') else dict(os.environ)
        penv.pop('RUN_TEST_WINDOW', None) if not vn.startswith('big') else None
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', env=penv)
        pm_csv = TOOLS.parent / 'perf' / f'pm_{run}.csv'
        pm = None
        if PM.exists():   # PresentMon: 시작 40초 뒤부터 60초(게임 밖에서 프레임마다)
            time.sleep(40)
            pm_csv.unlink(missing_ok=True)
            pm = subprocess.Popen([str(PM), '--process_name', 'GUILTY CROWN LOST XMAS.exe', '--output_file', str(pm_csv), '--timed', '60',
                                   '--terminate_after_timed', '--no_console_stats', '--stop_existing_session'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        out = proc.communicate()[0]
        if pm:
            pm.wait(timeout=120)
        with open(LOG, 'rb') as f:
            f.seek(start); new = f.read().decode('utf-8', 'replace').splitlines()
        st = [tuple(map(int, m.groups())) for m in map(STAT.match, new) if m]
        # 처음 40초(시작·로고)는 빼고 마지막 통계까지의 차이
        base = next((s for s in st if s[0] - st[0][0] >= 40000), st[0] if st else None)
        last = st[-1] if st else None
        res = {'run': run, 'variant': vn, 'env': envs, 'stats': len(st), 'exited_early': '"exited_early"' in out}
        if base and last and last[0] > base[0]:
            dt = (last[0] - base[0]) / 1000.0
            h = [last[i] - base[i] for i in range(2, 8)]
            n = sum(h) or 1
            res.update({'seconds': round(dt, 1), 'fps': round((last[1] - base[1]) / dt, 1), 'hist': h,
                        'pct_ge20': round(100 * sum(h[2:]) / n, 1), 'pct_ge35': round(100 * sum(h[3:]) / n, 1), 'long100': h[5]})
        res['longframes'] = sum(1 for l in new if l.startswith('longframe'))
        if pm_csv.exists():
            import csv as _csv
            pr = list(_csv.DictReader(open(pm_csv, encoding='utf-8-sig')))
            vals = lambda k: sorted(float(r[k]) for r in pr if r.get(k) not in (None, '', 'NA'))
            bp, cb = vals('MsBetweenPresents'), vals('MsCPUBusy')
            if bp:
                res['pm_fps'] = round(1000 * len(bp) / sum(bp), 1)
                res['pm_cpu_med'] = round(cb[len(cb) // 2], 2) if cb else None
                res['pm_cpu_p95'] = round(cb[int(len(cb) * .95)], 2) if cb else None
                res['pm_mode'] = pr[0].get('PresentMode')
        res['fastpng_lines'] = sum(1 for l in new if 'fastpng' in l)
        (TOOLS.parent / 'testrun' / run).mkdir(parents=True, exist_ok=True)
        (TOOLS.parent / 'testrun' / run / 'perf.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), 'utf-8')
        rows.append(res)
        print(json.dumps(res, ensure_ascii=False), flush=True)
print('\n변형  회  초  fps  20ms이상%  35ms이상%  100ms이상  긴프레임')
for r in rows:
    print(r['variant'], r['run'][-1], r.get('seconds'), r.get('fps'), r.get('pct_ge20'), r.get('pct_ge35'), r.get('long100'), r['longframes'],
          'PM', r.get('pm_fps'), r.get('pm_cpu_med'), r.get('pm_cpu_p95'), r.get('pm_mode'))
