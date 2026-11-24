"""J/K 음악 잇기 전수 시험 돌리개(11-24): 장면마다 숨긴 시험 하나 — 새 게임이 그 장면에서 시작, Enter 1.6초마다,
J·K 를 9초마다 번갈아. bgmkeep.log(DLL 결정)·trace.log(대사마다 시각+장면)·소리 세션 최고값(음소거 앞단, 5ms)을 남긴다.
시험 사본 P:\AI\gclx-reltest\game 의 DLL 은 놀이 사본과 같은 f95a48b5 여야 한다.
python -X utf8 jk_sweep.py <이름 앞머리> lx0106 [lx0303 …]
"""
import ctypes, json, os, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, r'P:\AI\touka-ps2-kr\work\codex_watch\host')
import hostlib as H

G = r'P:\AI\gclx-reltest\game'
RUNS = Path(r'F:\AI\gclx-4k\testrun')
pre, scenes = sys.argv[1], sys.argv[2:]
# 11-25 A/B: 장면 이름 뒤에 :v1 이면 N2HD_BGMKEEP_V1=1(오전 판 동작), :e20 이면 J/K 20초 간격. 결과 폴더 이름은 <앞머리>_<장면>_<n>
jobs = []
for n, a in enumerate(scenes):
    parts = a.split(':'); jobs.append((parts[0], parts[1:], n))
SEC = 280
for sc, opts, idx in jobs:
    name = f'{pre}_{sc}_{idx}' + ''.join('_' + o for o in opts if o in ('v1', 'off'))
    every = next((int(o[1:]) for o in opts if o.startswith('e')), 9)
    env = dict(os.environ, GCLX_GAME=G, GCLX_NSS_DIR=r'F:\AI\gclx-4k\release_1121\nss_variants', GCLX_EXTRA_NPA='cg.fix.npa')
    args = ['python', '-X', 'utf8', r'F:\AI\gclx-4k\tools\run_test.py', name, '--nss', f'nss.test_jk_{sc}.npa', '--seconds', str(SEC),
            '--shot-ms', '60000', '--click-xy', '40:440:296', '--keys-from', '47', '--key-every', '1.6',
            '--env', 'N2HD_TEST_NO_INJECT=1', '--env', 'N2HD_TEST_CURSOR_FILE=1', '--env', 'N2HD_TEST_KEEPALIVE_MS=500',
            '--env', 'N2HD_TEST_SHOT_START_MS=999000', '--env', 'N2HD_TEST_BGMKEEP_TRACE=1'] + (['--env', 'N2HD_BGMKEEP_V1=1'] if 'v1' in opts else []) + (['--env', 'N2HD_BGMKEEP_OFF=1'] if 'off' in opts else [])
    t, k = 56, 0
    while t < SEC - 8:
        args += ['--key-at', f'{t}:{"0x4A" if k % 2 == 0 else "0x4B"}']; t += every; k += 1
    log = open(RUNS / f'{name}.log', 'w', encoding='utf-8')
    p = subprocess.Popen(args, cwd=r'F:\AI\gclx-4k\tools', env=env, stdout=log, stderr=subprocess.STDOUT)
    pid, t_start = None, time.time()
    while pid is None and time.time() - t_start < 60:
        ps_ = H.pids_of(G, 'GUILTY CROWN LOST XMAS.exe')
        if ps_: pid = ps_[0]
        else: time.sleep(0.5)
    tick0, ep0 = ctypes.windll.kernel32.GetTickCount(), time.time()   # GetTickCount(ms) ↔ 유닉스 초
    samples, meters = [], []
    # 11-25: 진짜 마우스가 화면 오른쪽 끝에 붙으면(시험이 커서를 끌어감) 곧바로 시험을 끝낸다
    class PT(ctypes.Structure): _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long)]
    right = ctypes.windll.user32.GetSystemMetrics(76) + ctypes.windll.user32.GetSystemMetrics(78) - 1   # SM_XVIRTUALSCREEN + SM_CXVIRTUALSCREEN - 1
    pinned, last_c, curlog = 0, 0, []
    while p.poll() is None:
        if time.time() - last_c > 0.5:
            last_c = time.time(); pt = PT(); ctypes.windll.user32.GetCursorPos(ctypes.byref(pt)); curlog.append((round(last_c, 2), pt.x, pt.y))
            pinned = pinned + 1 if pt.x >= right - 1 and len(curlog) > 1 and curlog[-2][1:] == curlog[-1][1:] else 0   # 같은 점에 붙어 있을 때만(사람 손은 y 가 흔들림)
            if pinned >= 4 and False:   # 11-25: 사용자 손이 오른쪽 끝에 머물러도 걸려서 끔 — 기록(cursor.json)만 남긴다. DLL 이 SetCursorPos 를 막음(jk4_lx0506 206초 확인)
                print(name, 'CURSOR PINNED at right edge - stopping', flush=True)
                for q in H.pids_of(G, 'GUILTY CROWN LOST XMAS.exe'):
                    subprocess.run(['taskkill', '/F', '/PID', str(q)], capture_output=True)
                p.kill(); (RUNS / f'{pre}_STOPPED').write_text('cursor pinned', 'utf-8'); break
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
    (RUNS / name / 'audio_peaks.json').write_text(json.dumps({'tick0': tick0, 'ep0': ep0, 'samples': samples}), 'utf-8')
    (RUNS / name / 'cursor.json').write_text(json.dumps(curlog), 'utf-8')
    if (RUNS / f'{pre}_STOPPED').exists(): break
    print(name, 'pid', pid, 'samples', len(samples), flush=True)
