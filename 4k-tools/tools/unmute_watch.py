"""떠 있는 시험 사본 게임의 소리 세션이 생기면 음소거를 푼다(시험 때 건 음소거를 윈도가 실행 파일 경로별로 기억함). 최대 10분.
python -X utf8 unmute_watch.py"""
import sys, time
from pathlib import Path
sys.path.insert(0, r'P:\AI\touka-ps2-kr\work\codex_watch\host')
import hostlib as H  # noqa: E402
G, E = Path(r'P:\AI\gclx-4k-test\game'), 'GUILTY CROWN LOST XMAS.exe'
t0, seen = time.time(), False
while time.time() - t0 < 600:
    pids = H.pids_of(G, E)
    if not pids:
        print('게임 꺼짐'); break
    for pid in pids:
        for vol, meter in H.sessions_of(pid):
            seen = True
            if H.get_mute(vol):
                H.set_mute(vol, False); print(time.strftime('%H:%M:%S'), '음소거 풂')
    if seen:
        print(time.strftime('%H:%M:%S'), '소리 세션 확인, 음소거 아님'); break
    time.sleep(2)
