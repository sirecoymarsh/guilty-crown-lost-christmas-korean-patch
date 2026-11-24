"""J/K 바꾸기(체크포인트 다시 불러오기) 때 게임 소리가 끊기는지 잰다: 숨긴 시험을 띄우고, 게임 프로세스의 소리 세션
최고값(음소거 앞단, IAudioMeterInformation)을 5ms 마다 적는다. 시각은 유닉스 초 — report.json 의 t0_epoch 로 맞춘다.
python -X utf8 jk_audio.py <시험 이름> <대본 변형> [J 시각…]
"""
import json, os, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, r'P:\AI\touka-ps2-kr\work\codex_watch\host')
import hostlib as H

name, nss = sys.argv[1], sys.argv[2]
jt = [int(x) for x in sys.argv[3:]] or [86, 96]
G = r'P:\AI\gclx-reltest\game'
env = dict(os.environ, GCLX_GAME=G, GCLX_NSS_DIR=r'F:\AI\gclx-4k\release_1121\nss_variants', GCLX_EXTRA_NPA='cg.fix.npa')
args = ['python', '-X', 'utf8', r'F:\AI\gclx-4k\tools\run_test.py', name, '--nss', nss, '--seconds', str(max(jt) + 16),
        '--shot-ms', '60000', '--click-xy', '40:440:296', '--keys', '--keys-from', '46', '--keys-until', '68',
        '--env', 'N2HD_TEST_NO_INJECT=1', '--env', 'N2HD_TEST_CURSOR_FILE=1', '--env', 'N2HD_TEST_KEEPALIVE_MS=500',
        '--env', 'N2HD_TEST_FRAMES=1', '--env', 'N2HD_TEST_SHOT_START_MS=999000'] + [x for e in os.environ.get('JK_EXTRA_ENV', '').split(',') if e for x in ('--env', e)]
for t in jt:
    args += ['--key-at', f'{t}:0x4A']
log = open(Path(r'F:\AI\gclx-4k\testrun') / f'{name}.log', 'w', encoding='utf-8')
p = subprocess.Popen(args, cwd=r'F:\AI\gclx-4k\tools', env=env, stdout=log, stderr=subprocess.STDOUT)
pid = None
t_start = time.time()
while pid is None and time.time() - t_start < 60:
    ps = H.pids_of(G, 'GUILTY CROWN LOST XMAS.exe')
    if ps:
        pid = ps[0]
    else:
        time.sleep(0.5)
print('game pid', pid, flush=True)
samples = []
meters = []
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
out = Path(r'F:\AI\gclx-4k\testrun') / name / 'audio_peaks.json'
out.write_text(json.dumps(samples), 'utf-8')
print('samples', len(samples), 'saved', out)
