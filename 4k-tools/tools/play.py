"""사용자가 보려고 시험 사본(P:\\AI\\gclx-4k-test\\game)을 평소처럼 띄운다: Korean4K.exe(4K 실행기)를 WMI 로 — Claude 앱 밖 프로세스.
시험(run_test.py)이 남긴 음소거를 풀어 소리가 나게 한다. 시험 모드 환경 변수는 안 씀(세이브는 평소 자리).
python -X utf8 play.py
"""
import sys, time
from pathlib import Path
sys.path.insert(0, r'P:\AI\touka-ps2-kr\work\codex_watch\host')
import hostlib as H  # noqa: E402
import subprocess

LOG = '--log' in sys.argv   # 사용자가 실제로 하는 화면의 프레임 통계: N2HD_ART_LOG=1 → game\hires\art.log 에 10초마다 stat 줄(세이브·화면은 평소 그대로)
argv = [a for a in sys.argv[1:] if a != '--log']
GAME = Path(argv[0] if argv else r'P:\AI\gclx-4k-test\game')   # 합본: P:\AI\gclx-codexrun\game
EXE = 'GUILTY CROWN LOST XMAS.exe'
if H.pids_of(GAME, EXE):
    raise SystemExit('이미 떠 있음')
cmdline = '\"%s\"' % (GAME / 'Korean4K.exe')
if LOG:
    cmdline = 'cmd /c \"set N2HD_ART_LOG=1&& \"%s\"\"' % (GAME / 'Korean4K.exe')
    log = GAME / 'hires' / 'art.log'
    print('log from byte', log.stat().st_size if log.exists() else 0, time.strftime('%H:%M:%S'))
ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments "
      "@{CommandLine='%s'; CurrentDirectory='%s'}; $r.ReturnValue" % (cmdline, GAME))
print('WMI', subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, text=True).stdout.strip())
# 소리 세션은 첫 소리(경고 화면 뒤)에 생기고, 윈도가 시험 때 건 음소거를 exe 경로별로 기억해 그대로 켜진다
# → 세션이 생길 때까지 기다렸다 푼다(11-02 「소리가 안나」: 15초 만에 그만둬서 못 풀었다).
t0, unmuted, hwnd, seen = time.time(), 0, None, 0
while time.time() - t0 < 120:
    for pid in H.pids_of(GAME, EXE):
        hwnd = hwnd or H.window_of(pid)
        for vol, meter in H.sessions_of(pid):
            seen += 1
            if H.get_mute(vol):
                H.set_mute(vol, False)
                unmuted += 1
    if hwnd and seen and time.time() - t0 > 15:
        break
    if not H.pids_of(GAME, EXE) and time.time() - t0 > 10:
        break
    time.sleep(1)
print('창', bool(hwnd), '소리 세션', bool(seen), '음소거 풀기', unmuted, '살아 있음', bool(H.pids_of(GAME, EXE)))
