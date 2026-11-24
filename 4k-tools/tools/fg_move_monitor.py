"""게임 창을 다른 모니터로 옮겨(사용자가 조작을 맡겼을 때만) 화면 모양과 마우스 대응을 본다.
python -X utf8 fg_move_monitor.py to <x> <y>     창 왼쪽 위를 실제 화소 좌표 x,y 로(예: -5280 0 = 150% 모니터)
python -X utf8 fg_move_monitor.py back          주 모니터 원래 자리(128,0)로
python -X utf8 fg_move_monitor.py look <이름>    창 사각형(실제 화소)과 그 모니터 화면 찍기"""
import ctypes, ctypes.wintypes as wt, sys, time
from pathlib import Path
from PIL import ImageGrab

U = ctypes.windll.user32
U.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
sys.path.insert(0, r'P:\AI\touka-ps2-kr\work\codex_watch\host')
import hostlib as H  # noqa: E402

OUT = Path(r'F:\AI\gclx-4k\testrun\fg')
h = H.window_of(H.pids_of(Path(r'P:\AI\gclx-codexrun\game'), 'GUILTY CROWN LOST XMAS.exe')[0])


def rect():
    r = wt.RECT(); U.GetWindowRect(h, ctypes.byref(r)); return [r.left, r.top, r.right, r.bottom]


cmd = sys.argv[1]
if cmd == 'to':
    U.SetWindowPos(h, 0, int(sys.argv[2]), int(sys.argv[3]), 0, 0, 0x0001 | 0x0004 | 0x0010); time.sleep(1.5)
elif cmd == 'back':
    U.SetWindowPos(h, 0, 128, 0, 0, 0, 0x0001 | 0x0004 | 0x0010); time.sleep(1.5)
print('rect (physical)', rect(), 'dpi', U.GetDpiForWindow(h))
if cmd == 'look':
    r = rect()
    hm = U.MonitorFromWindow(h, 2)

    class MI(ctypes.Structure):
        _fields_ = [('cbSize', wt.DWORD), ('rcMonitor', wt.RECT), ('rcWork', wt.RECT), ('dwFlags', wt.DWORD)]
    mi = MI(); mi.cbSize = ctypes.sizeof(MI); U.GetMonitorInfoW(hm, ctypes.byref(mi)); m = mi.rcMonitor
    im = ImageGrab.grab(bbox=(m.left, m.top, m.right, m.bottom), all_screens=True)
    p = OUT / f'{sys.argv[2]}.png'; im.save(p); im.resize((im.width // 4, im.height // 4)).save(OUT / f'{sys.argv[2]}_small.png')
    print('monitor', (m.left, m.top, m.right, m.bottom), p)
