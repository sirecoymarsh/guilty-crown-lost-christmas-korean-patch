"""시험 게임 창이 뜨면 정해진 초마다 창 전체를 PrintWindow(PW_RENDERFULLCONTENT)로 떠서 BMP 로 남긴다(창에 실제로 합성된 화면 확인용).
python -I -X utf8 grab_window.py <게임 폴더> <출력 폴더> <초,초,...>"""
import ctypes, ctypes.wintypes as wt, sys, time, os
from pathlib import Path
sys.path.insert(0, r'P:\AI\touka-ps2-kr\work\codex_watch\host')
import hostlib as H
from PIL import Image
U, G = ctypes.windll.user32, ctypes.windll.gdi32
U.SetProcessDPIAware()
game, out, secs = Path(sys.argv[1]), Path(sys.argv[2]), [float(x) for x in sys.argv[3].split(',')]
out.mkdir(parents=True, exist_ok=True)
EXE = 'GUILTY CROWN LOST XMAS.exe'
t0 = None; hwnd = None
while time.time() - (t0 or time.time()) < max(secs) + 5:
    if not hwnd:
        for pid in H.pids_of(game, EXE):
            hwnd = H.window_of(pid)
            if hwnd:
                t0 = time.time(); break
        time.sleep(0.2); continue
    for s in list(secs):
        if time.time() - t0 >= s:
            secs.remove(s)
            r = wt.RECT(); U.GetWindowRect(hwnd, ctypes.byref(r)); c = wt.RECT(); U.GetClientRect(hwnd, ctypes.byref(c))
            w, h = r.right - r.left, r.bottom - r.top
            hdc = U.GetWindowDC(hwnd); mdc = G.CreateCompatibleDC(hdc); bmp = G.CreateCompatibleBitmap(hdc, w, h); G.SelectObject(mdc, bmp)
            ok = U.PrintWindow(hwnd, mdc, 2)
            class BIH(ctypes.Structure):
                _fields_ = [('biSize', wt.DWORD), ('biWidth', wt.LONG), ('biHeight', wt.LONG), ('biPlanes', wt.WORD), ('biBitCount', wt.WORD), ('biCompression', wt.DWORD), ('biSizeImage', wt.DWORD), ('biXPelsPerMeter', wt.LONG), ('biYPelsPerMeter', wt.LONG), ('biClrUsed', wt.DWORD), ('biClrImportant', wt.DWORD)]
            bi = BIH(ctypes.sizeof(BIH), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
            buf = ctypes.create_string_buffer(w * h * 4)
            G.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bi), 0)
            Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1).convert('RGB').save(out / f'win_{int(s):03d}.png')
            G.DeleteObject(bmp); G.DeleteDC(mdc); U.ReleaseDC(hwnd, hdc)
            print(f'{s}s printwindow={ok} window={w}x{h} client={c.right}x{c.bottom} at {r.left},{r.top}', flush=True)
    if not secs:
        break
    time.sleep(0.1)
