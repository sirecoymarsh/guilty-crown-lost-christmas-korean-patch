"""시험 게임 창이 어느 모니터에라도 걸치면 곧바로 모든 모니터 밖(주 모니터 오른쪽)으로 되돌리고 기록한다(사용자 화면 보호).
정해진 초에는 창을 PrintWindow 로 떠서 남긴다. python -I -X utf8 guard_window.py <게임 폴더> <출력 폴더> <초,초,...> <최대 초>"""
import ctypes, ctypes.wintypes as wt, sys, time
from pathlib import Path
sys.path.insert(0, r'P:\AI\touka-ps2-kr\work\codex_watch\host')
import hostlib as H
from PIL import Image
U, G = ctypes.windll.user32, ctypes.windll.gdi32
U.SetProcessDPIAware()
U.MonitorFromRect.restype = ctypes.c_void_p
game, out, secs, limit = Path(sys.argv[1]), Path(sys.argv[2]), [float(x) for x in sys.argv[3].split(',') if x], float(sys.argv[4])
out.mkdir(parents=True, exist_ok=True)
EXE = 'GUILTY CROWN LOST XMAS.exe'
PW = U.GetSystemMetrics(0)
start = time.time(); t0 = None; hwnd = None; moves = 0


class BIH(ctypes.Structure):
    _fields_ = [('biSize', wt.DWORD), ('biWidth', wt.LONG), ('biHeight', wt.LONG), ('biPlanes', wt.WORD), ('biBitCount', wt.WORD), ('biCompression', wt.DWORD),
                ('biSizeImage', wt.DWORD), ('biXPelsPerMeter', wt.LONG), ('biYPelsPerMeter', wt.LONG), ('biClrUsed', wt.DWORD), ('biClrImportant', wt.DWORD)]


def grab(name):
    r = wt.RECT(); U.GetWindowRect(hwnd, ctypes.byref(r)); c = wt.RECT(); U.GetClientRect(hwnd, ctypes.byref(c))
    w, h = r.right - r.left, r.bottom - r.top
    hdc = U.GetWindowDC(hwnd); mdc = G.CreateCompatibleDC(hdc); bmp = G.CreateCompatibleBitmap(hdc, w, h); G.SelectObject(mdc, bmp)
    ok = U.PrintWindow(hwnd, mdc, 2)
    bi = BIH(ctypes.sizeof(BIH), w, -h, 1, 32, 0, 0, 0, 0, 0, 0); buf = ctypes.create_string_buffer(w * h * 4)
    G.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bi), 0)
    Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1).convert('RGB').save(out / name)
    G.DeleteObject(bmp); G.DeleteDC(mdc); U.ReleaseDC(hwnd, hdc)
    print(f'grab {name} ok={ok} window={w}x{h} client={c.right}x{c.bottom} at {r.left},{r.top}', flush=True)


while time.time() - start < limit:
    if not hwnd:
        for pid in H.pids_of(game, EXE):
            hwnd = H.window_of(pid)
            if hwnd:
                t0 = time.time(); break
        time.sleep(0.05); continue
    if not U.IsWindow(hwnd):
        break
    r = wt.RECT(); U.GetWindowRect(hwnd, ctypes.byref(r))
    if U.MonitorFromRect(ctypes.byref(r), 0):          # MONITOR_DEFAULTTONULL: 걸친 모니터가 있다
        U.SetWindowPos(hwnd, 1, PW + 40, 120, 0, 0, 0x0001 | 0x0010)
        moves += 1
        print(f'{time.time() - t0:6.2f}s window was on screen at {r.left},{r.top},{r.right},{r.bottom} -> moved off', flush=True)
    for s in list(secs):
        if time.time() - t0 >= s:
            secs.remove(s); grab(f'win_{int(s):03d}.png')
    time.sleep(0.05)
print('done moves', moves)
