"""한 DLL 을 시험 사본에 넣고 차례로 시험한다(Claude 11-24): 잠금 고침 켬/끔·곡 바꾸기·본편 200초(verify_dll) → J/K 음악 잇기 켬/끔(jk_audio_lock).
python -X utf8 chain_dll.py <DLL 경로> <꼬리표> [--story-nss nss.play_333a6a67.npa] [--no-jk]
"""
import hashlib, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ab_run import GAME, EXE, H  # noqa: E402

PY = [sys.executable, '-X', 'utf8']
DLL = GAME / 'n2hd_runtime.dll'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def say(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def idle():
    quiet = None; t0 = time.time()
    while time.time() - t0 < 1500:
        if H.pids_of(GAME, EXE):
            quiet = None
        elif quiet is None:
            quiet = time.time()
        elif time.time() - quiet >= 10:
            return
        time.sleep(1)
    raise SystemExit('시험 사본이 25분 넘게 바쁨')


def run(cmd, tail=3400):
    r = subprocess.run(PY + cmd, cwd=HERE, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print((r.stdout or '').strip()[-tail:], flush=True)
    if r.returncode:
        print('   exit', r.returncode, (r.stderr or '')[-400:], flush=True)


def main():
    src, tag = Path(sys.argv[1]), sys.argv[2]
    story = sys.argv[sys.argv.index('--story-nss') + 1] if '--story-nss' in sys.argv else 'nss.play_333a6a67.npa'
    idle()
    shutil.copyfile(src, DLL)
    h = sha(DLL)
    assert h == sha(src)
    data = DLL.read_bytes()
    say('DLL', h, len(data), {m: (m.encode() in data) for m in ('N2HD_TEST_LOCKFIX_OFF', 'N2HD_BGMKEEP_OFF')})
    run(['verify_dll.py', tag, h[:8], '--story-nss', story])
    if '--no-jk' not in sys.argv:
        idle(); say('== J/K 음악 잇기 켬'); run(['jk_audio_lock.py', tag + '_on'])
        idle(); say('== J/K 음악 잇기 끔(N2HD_BGMKEEP_OFF=1)'); run(['jk_audio_lock.py', tag + '_off', '--off'])
    say('끝. 시험 사본 DLL', sha(DLL)[:8])


if __name__ == '__main__':
    main()
