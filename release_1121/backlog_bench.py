"""백로그(대사 기록) 속도 측정: 출고 시험 사본에서 4K 렌더러와 원래 1배 렌더러(N2HD_TEST_NATIVE)를 번갈아 2번씩.
한 판: lx0010 에서 시작 → 48~108초 Enter 로 기록 쌓기 → 115초 휠 올림 10번(열기+스크롤) → 125초 휠 내림 10번(스크롤+닫기)
→ 138초 다시 열기(휠 3번) → 150초 클릭(4K 판은 DLL 시험 스위치로 3묶음 전 점프). 창은 4096x2160 숨긴 창(사용자 TV 크기).
PresentMon(--date_time)으로 Present 마다 시각을 받아 run_test 의 사건 시각(epoch)과 맞춘다.
python -I -X utf8 backlog_bench.py [--rounds 2]
"""
import csv, datetime, json, os, subprocess, sys, time
from pathlib import Path
W = Path(__file__).resolve().parent
TOOLS = Path(r'F:\AI\gclx-4k\tools'); RUNS = Path(r'F:\AI\gclx-4k\testrun')
PM = Path(r'P:/AI/Codex/projects/guilty-crown-lost-christmas-ui-opening/work/revisions/frame-time-20261102/PresentMon-2.6.0-x64.exe')
EXE = 'GUILTY CROWN LOST XMAS.exe'
rounds = int(sys.argv[sys.argv.index('--rounds') + 1]) if '--rounds' in sys.argv else 2
tag = time.strftime('%H%M')
env = dict(os.environ, GCLX_GAME=r'P:\AI\gclx-reltest\game', GCLX_NSS_DIR=str(W / 'nss_variants'), RUN_TEST_WINDOW='4096x2160')
USE_PM = False   # 11-21: 원래 렌더러는 GDI BitBlt 로 보여 PresentMon 에 안 잡힘 → DLL 시험 기록 frames.bin(N2HD_TEST_FRAMES)
MODES = [('4k', ['--jump-back', '3']), ('native', ['--native'])]
results = []


def presents(csvp):
    rows = list(csv.DictReader(open(csvp, encoding='utf-8-sig')))
    key = next((k for k in rows[0] if 'Date' in k or 'date' in k), None) if rows else None
    out = []
    for r in rows:
        try:
            t = datetime.datetime.fromisoformat(r[key].strip()).timestamp() if key else None
        except Exception:
            continue
        if t:
            out.append(t)
    return sorted(out), key


def window(ts, a, b):
    seg = [t for t in ts if a <= t <= b]
    gaps = [(y - x) * 1000 for x, y in zip(seg, seg[1:])]
    if len(seg) < 2:
        return {'frames': len(seg), 'max_gap_ms': None}
    gaps_lead = (seg[0] - a) * 1000                      # 사건 뒤 첫 Present 까지
    return {'frames': len(seg), 'fps': round(len(seg) / (b - a), 1), 'first_present_ms': round(gaps_lead), 'max_gap_ms': round(max(gaps)),
            'gaps_over_50': sum(g > 50 for g in gaps), 'gaps_over_100': sum(g > 100 for g in gaps), 'stall_ms_over_50': round(sum(g for g in gaps if g > 50))}


ORDER = sys.argv[sys.argv.index('--order') + 1].split(',') if '--order' in sys.argv else None
PLAN = [(i + 1, m) for i, m in enumerate(ORDER)] if ORDER else [(r, m) for r in range(1, rounds + 1) for m, _ in MODES]
for rnd, mname in PLAN:
    for mode, extra in [x for x in MODES if x[0] == mname]:
        run = f'bl{tag}_{mode}_{rnd}'
        pm_csv = W / 'qa' / f'pm_{run}.csv'
        cmd = [sys.executable, '-X', 'utf8', str(TOOLS / 'run_test.py'), run, '--nss', 'nss.test_cfg.npa', '--seconds', '172', '--shot-ms', '0',
               '--key-every', '0.3', '--keys-from', '48', '--keys-until', '108', '--wheel-at', '115', '--wheel-down-at', '125',
               '--wheel-at2', '138', '--click-at', '150', '--env', 'N2HD_TEST_FRAMES=1'] + extra
        p = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pm = None
        if USE_PM:
          time.sleep(12)
          pm = subprocess.Popen([str(PM), '--process_name', EXE, '--output_file', str(pm_csv), '--date_time', '--timed', '165',
                               '--terminate_after_timed', '--no_console_stats', '--stop_existing_session'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p.wait()
        if pm: pm.wait(timeout=240)
        rep = json.loads((RUNS / run / 'report.json').read_text('utf-8'))
        ev = rep.get('events', []); t0 = rep.get('t0_epoch')
        import struct
        fb = RUNS / run / 'profile' / 'frames.bin'
        raw = fb.read_bytes() if fb.exists() else b''
        ts, key = sorted(struct.unpack('<%dd' % (len(raw) // 8), raw[:len(raw) // 8 * 8])), 'frames.bin'
        up = [t for n, t in ev if n == 'wheel_up']; down = [t for n, t in ev if n == 'wheel_down']; clk = [t for n, t in ev if n == 'click']
        first_series = [t for t in up if t - t0 < 130]; second = [t for t in up if t - t0 >= 130]
        res = {'run': run, 'mode': mode, 'csv_time_column': key, 'presents': len(ts), 'events': len(ev),
               'reading_95_105s': window(ts, t0 + 95, t0 + 105) if t0 else None,
               'open_first_wheel_6s': window(ts, first_series[0], first_series[0] + 6) if first_series else None,
               'scroll_wheels_2_10': window(ts, first_series[1], first_series[-1] + 1) if len(first_series) > 1 else None,
               'close_wheel_down_8s': window(ts, down[0], down[-1] + 2) if down else None,
               'reopen_4s': window(ts, second[0], second[0] + 4) if second else None,
               'click_jump_6s': window(ts, clk[0], clk[0] + 6) if clk else None,
               'exited_early': rep.get('exited_early'), 'dialogs': rep.get('dialogs_closed')}
        results.append(res)
        print(json.dumps(res, ensure_ascii=False), flush=True)
(W / 'qa' / f'backlog_bench_{tag}.json').write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding='utf-8')
