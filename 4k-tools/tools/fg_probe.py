"""앞 창 시험(사용자가 조작을 맡겼을 때만, 11-02): 게임 창 상태와 화면 찍기, 게임 창 안에서만 커서 옮기기·클릭.
python -X utf8 fg_probe.py info
python -X utf8 fg_probe.py shot <이름>                  화면 전체를 F:\\AI\\gclx-4k\\testrun\\fg\\<이름>.png
python -X utf8 fg_probe.py hover <엔진x> <엔진y> <이름>  커서를 엔진 좌표(1024x576) 자리로 옮기고 0.6초 뒤 찍기
python -X utf8 fg_probe.py click <엔진x> <엔진y> <이름>  그 자리 왼쪽 클릭 뒤 1.5초 뒤 찍기
엔진 좌표 → 화면 좌표는 창 바깥 사각형 기준(엔진 0x46b620 과 같은 셈), 전체 화면이면 창 크기에 비례."""
import ctypes, ctypes.wintypes as wt, sys, time
from pathlib import Path
from PIL import ImageGrab

sys.path.insert(0, r'P:\AI\touka-ps2-kr\work\codex_watch\host')
import hostlib as H  # noqa: E402

U = ctypes.windll.user32
U.SetProcessDPIAware()
GAME = Path(r'P:\AI\gclx-codexrun\game')
OUT = Path(r'F:\AI\gclx-4k\testrun\fg'); OUT.mkdir(parents=True, exist_ok=True)


def hwnd():
    pids = H.pids_of(GAME, 'GUILTY CROWN LOST XMAS.exe')
    return H.window_of(pids[0]) if pids else None


def info(h):
    r, c = wt.RECT(), wt.RECT()
    U.GetWindowRect(h, ctypes.byref(r)); U.GetClientRect(h, ctypes.byref(c))
    style = U.GetWindowLongW(h, -16) & 0xffffffff
    p = wt.POINT(); U.ClientToScreen(h, ctypes.byref(p))
    return {'rect': [r.left, r.top, r.right, r.bottom], 'client': [c.right, c.bottom], 'client_origin': [p.x, p.y],
            'style': hex(style), 'fg': U.GetForegroundWindow() == h, 'screen': [U.GetSystemMetrics(0), U.GetSystemMetrics(1)]}


def to_screen(h, ex, ey):
    i = info(h)
    ox, oy = i['client_origin']; cw, ch = i['client']
    return int(ox + ex * cw / 1024), int(oy + ey * ch / 576)


def shot(name):
    p = OUT / f'{name}.png'; ImageGrab.grab(all_screens=False).save(p); return str(p)


def click_at(x, y):
    U.SetCursorPos(x, y); time.sleep(0.2)
    U.mouse_event(0x0002, 0, 0, 0, 0); time.sleep(0.12); U.mouse_event(0x0004, 0, 0, 0, 0)


if __name__ == '__main__':
    h = hwnd()
    if not h:
        raise SystemExit('게임 창 없음')
    cmd = sys.argv[1]
    if cmd == 'info':
        print(info(h))
    elif cmd == 'shot':
        print(shot(sys.argv[2]))
    elif cmd in ('hover', 'click'):
        x, y = to_screen(h, int(sys.argv[2]), int(sys.argv[3]))
        if cmd == 'hover':
            U.SetCursorPos(x, y); time.sleep(0.6)
        else:
            click_at(x, y); time.sleep(1.5)
        pt = wt.POINT(); U.GetCursorPos(ctypes.byref(pt))
        print({'screen_xy': [x, y], 'cursor': [pt.x, pt.y], 'shot': shot(sys.argv[4]), **info(h)})
