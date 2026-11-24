"""모니터 배치·해상도·배율(DPI) 목록. python -X utf8 monitors.py"""
import ctypes, ctypes.wintypes as wt

U, S = ctypes.windll.user32, ctypes.windll.shcore
U.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))            # per-monitor v2: real pixels


class MI(ctypes.Structure):
    _fields_ = [('cbSize', wt.DWORD), ('rcMonitor', wt.RECT), ('rcWork', wt.RECT), ('dwFlags', wt.DWORD), ('szDevice', ctypes.c_wchar * 32)]


out = []
PROC = ctypes.WINFUNCTYPE(ctypes.c_int, wt.HMONITOR, wt.HDC, ctypes.POINTER(wt.RECT), wt.LPARAM)


def cb(h, dc, r, lp):
    mi = MI(); mi.cbSize = ctypes.sizeof(MI); U.GetMonitorInfoW(h, ctypes.byref(mi))
    dx, dy = wt.UINT(), wt.UINT(); S.GetDpiForMonitor(h, 0, ctypes.byref(dx), ctypes.byref(dy))
    m = mi.rcMonitor
    out.append((mi.szDevice, 'primary' if mi.dwFlags & 1 else '', (m.left, m.top, m.right, m.bottom), f'{m.right - m.left}x{m.bottom - m.top}', f'{dx.value * 100 // 96}%'))
    return 1


U.EnumDisplayMonitors(0, 0, PROC(cb), 0)
for o in out:
    print(*o)
