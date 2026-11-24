"""켜 둔 게임의 마우스 대응 값 읽기(읽기만): 전체 화면 깃발·화면 사각형·엔진이 기억한 커서 위치.
python -X utf8 peek_mouse.py [반복 횟수=1] [간격초=0.5]"""
import ctypes, ctypes.wintypes as wt, struct, sys, time
sys.path.insert(0, r'P:\AI\touka-ps2-kr\work\codex_watch\host')
import hostlib as H  # noqa: E402
from pathlib import Path

K = ctypes.windll.kernel32
pid = H.pids_of(Path(r'P:\AI\gclx-codexrun\game'), 'GUILTY CROWN LOST XMAS.exe')[0]
hp = K.OpenProcess(0x0010 | 0x0400, False, pid)


def rd(addr, n):
    b = ctypes.create_string_buffer(n); got = ctypes.c_size_t()
    if not K.ReadProcessMemory(hp, ctypes.c_void_p(addr), b, n, ctypes.byref(got)):
        return None
    return b.raw


def u32(a):
    return struct.unpack('<I', rd(a, 4))[0]


def i32(a):
    return struct.unpack('<i', rd(a, 4))[0]


U = ctypes.windll.user32; U.SetProcessDPIAware()
n = int(sys.argv[1]) if len(sys.argv) > 1 else 1; dt = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
for _ in range(n):
    m = u32(0x5b3114)
    pos = (i32(m + 8), i32(m + 0xc)) if m else None
    pt = wt.POINT(); U.GetCursorPos(ctypes.byref(pt))
    print({'cursor_screen': (pt.x, pt.y), 'engine_pos': pos,
           'full_62986c': i32(0x62986c), 'stretch_620594': i32(0x620594),
           'rect_629874': [i32(0x629874), i32(0x629878), i32(0x62987c), i32(0x629880)],
           'hwnd_629854': hex(u32(0x629854)), 'hwnd_629858': hex(u32(0x629858))})
    time.sleep(dt)
