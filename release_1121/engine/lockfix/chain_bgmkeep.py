"""11-24 10:1x 차례 시험(Claude): ① 놀이 사본에 지금 깔린 코덱스 DLL 의 잠금 고침 ② 공용 src + 음악 잇기(bgm_keep) 빌드의
잠금 고침·본편 ③ 그 빌드의 J/K 음악 잇기 켬/끔. 시험 사본 P:\\AI\\gclx-locktest\\game 만 쓴다.
python -X utf8 chain_bgmkeep.py <놀이 사본 DLL 사본 경로> [--skip-a]
"""
import hashlib, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ab_run import GAME, EXE, H  # noqa: E402

PY = [sys.executable, '-X', 'utf8']
KW = dict(capture_output=True, text=True, encoding='utf-8', errors='replace')
DLL = GAME / 'n2hd_runtime.dll'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def say(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def idle(extra=None):
    """앞 시험(verify_dll cdx2)이 끝나고 시험 사본 게임이 12초 동안 없을 때까지."""
    quiet = None; t0 = time.time()
    while time.time() - t0 < 1500:
        busy = H.pids_of(GAME, EXE) or (extra and not extra())
        if busy:
            quiet = None
        elif quiet is None:
            quiet = time.time()
        elif time.time() - quiet >= 12:
            return
        time.sleep(1)
    raise SystemExit('시험 사본이 25분 넘게 바쁨')


def put(src):
    for _ in range(20):
        try:
            shutil.copyfile(src, DLL); break
        except PermissionError:
            time.sleep(3)
    h = sha(DLL)
    assert h == sha(src), 'DLL 복사 불일치'
    return h


def run(cmd, tail=3200):
    r = subprocess.run(PY + cmd, cwd=HERE, **KW)
    out = (r.stdout or '').strip()
    print(out[-tail:], flush=True)
    if r.returncode:
        print('   exit', r.returncode, (r.stderr or '')[-400:], flush=True)
    return r.returncode


def main():
    play = Path(sys.argv[1])
    mc = HERE / 'trace_mc_cdx2.json'
    started = time.time()
    idle(lambda: mc.exists() and mc.stat().st_mtime > started - 1200)
    if '--skip-a' not in sys.argv:
        h = put(play); say('== A) 놀이 사본의 코덱스 DLL', h[:8])
        run(['verify_dll.py', 'cdx3', h[:8], '--skip-story'])
        idle()
    say('== B) 빌드: lockfix\\src (공용 + bgm_keep)')
    out = HERE / 'out' / 'n2hd_runtime.dll'
    before = out.stat().st_mtime if out.exists() else 0
    b = subprocess.run(['cmd', '/c', str(HERE / 'build_lockfix.cmd')], cwd=HERE, capture_output=True, text=True, errors='replace')
    if not out.exists() or out.stat().st_mtime <= before:
        print((b.stdout or '')[-1800:]); print((b.stderr or '')[-600:])
        raise SystemExit('빌드 실패')
    errs = [ln for ln in (b.stdout or '').splitlines() if ' error ' in ln or 'fatal' in ln]
    data = out.read_bytes()
    say('built', sha(out), len(data), 'bytes', 'errors', errs[:3],
        'markers', {m: (m.encode() in data) for m in ('N2HD_BGMKEEP_OFF', 'N2HD_TEST_LOCKFIX_OFF', 'bgmkeep.log', 'locks.log')})
    h = put(out)
    run(['verify_dll.py', 'bk', h[:8], '--story-nss', 'nss.play_333a6a67.npa'])
    idle()
    say('== C) J/K 음악 잇기 켬')
    run(['jk_audio_lock.py', 'bk_on'])
    idle()
    say('== C) J/K 음악 잇기 끔(N2HD_BGMKEEP_OFF=1)')
    run(['jk_audio_lock.py', 'bk_off', '--off'])
    say('끝. 시험 사본 DLL', sha(DLL)[:8])


if __name__ == '__main__':
    main()
