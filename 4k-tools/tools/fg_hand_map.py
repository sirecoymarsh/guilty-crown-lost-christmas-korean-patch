"""타이틀에서 커서를 격자로 옮기며 손 모양 커서(엔진이 단추 위라고 여김)가 뜨는 자리를 지도로(앞 창, 사용자가 조작을 맡겼을 때만).
python -X utf8 fg_hand_map.py <이름> <native|4k> [NAME=VALUE ...]
결과: fg\\<이름>_<mode>_hand.png (타이틀 화면 위에 손=빨강 점, 아님=회색 점) 과 손이 뜬 엔진 좌표 범위."""
import ctypes, ctypes.wintypes as wt, subprocess, sys, time
import numpy as np
from PIL import ImageGrab, ImageDraw
sys.path.insert(0, r'F:\AI\gclx-4k\tools')
import fg_probe as F
import fg_ab as A

name, mode, env = sys.argv[1], sys.argv[2], sys.argv[3:]
U = F.U


class CI(ctypes.Structure):
    _fields_ = [('cbSize', wt.DWORD), ('flags', wt.DWORD), ('hCursor', wt.HANDLE), ('pt', wt.POINT)]


HAND = U.LoadCursorW(None, 32649)
A.kill()
if mode == 'native':
    ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine='\"%s\"'; CurrentDirectory='%s'}; $r.ReturnValue"
          % (A.GAME / 'GUILTY CROWN LOST XMAS.exe', A.GAME))
    subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True)
else:
    subprocess.run([sys.executable, '-X', 'utf8', r'F:\AI\gclx-4k\tools\fg_launch.py', *env], capture_output=True)
time.sleep(3); U.SetCursorPos(3600, 2000)
t0 = time.time()
while time.time() - t0 < 90:
    if float(np.asarray(ImageGrab.grab(bbox=(2400, 1000, 3400, 1800)).convert('L')).mean()) > 150:
        break
    time.sleep(0.2)
time.sleep(12)
F.click_at(3600, 2050); time.sleep(1)          # focus (bottom-right corner, outside any button)
shot = ImageGrab.grab()
d = ImageDraw.Draw(shot)
hits = []
for ey in range(250, 576, 8):                  # engine coordinates 1024x576 → screen 128 + x*3.75, y*3.75
    for ex in range(300, 1000, 24):
        sx, sy = int(128 + ex * 3.75), int(ey * 3.75)
        U.SetCursorPos(sx, sy); time.sleep(0.09)
        U.SetCursorPos(sx + 1, sy); time.sleep(0.09)
        ci = CI(); ci.cbSize = ctypes.sizeof(CI); U.GetCursorInfo(ctypes.byref(ci))
        hand = ci.hCursor == HAND
        if hand:
            hits.append((ex, ey))
        d.ellipse([sx - 9, sy - 9, sx + 9, sy + 9], fill=(230, 0, 0) if hand else (150, 150, 150))
A.kill()
shot.resize((1024, 540)).save(A.OUT / f'{name}_{mode}_hand.png')
if hits:
    xs, ys = [h[0] for h in hits], [h[1] for h in hits]
    print(name, mode, env, 'hand points', len(hits), 'engine x', min(xs), max(xs), 'y', min(ys), max(ys))
    rows = sorted(set(ys))
    for y in rows:
        print('  y', y, 'x', [x for x, yy in hits if yy == y])
else:
    print(name, mode, env, 'no hand points')
