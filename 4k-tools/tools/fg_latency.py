"""커서를 옮긴 뒤 타이틀 단추 강조가 바뀌기까지 걸리는 시간(앞 창, 사용자가 조작을 맡겼을 때만).
불러오기 ↔ 환경설정을 번갈아 n 번 옮기며, 새 단추 글자가 진해질 때까지 화면 조각을 빠르게 찍는다.
python -X utf8 fg_latency.py [n=6] [x0 y_load y_config]   (기본은 4K 창의 단추 자리)"""
import sys, time
import numpy as np
sys.path.insert(0, r'F:\AI\gclx-4k\tools')
import fg_probe as F
from PIL import ImageGrab

n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
x0, yl, yc = (int(v) for v in sys.argv[2:5]) if len(sys.argv) > 4 else (1800, 1418, 1552)
U = F.U


def darkness(y):
    im = np.asarray(ImageGrab.grab(bbox=(1690, y - 40, 2030, y + 40)).convert('L')).astype(int)
    return int((im < 40).sum())      # near-black pixels: the highlighted (MouseOver) label is black, the usual one grey


h = F.hwnd()
if U.GetForegroundWindow() != h:
    U.keybd_event(0x12, 0, 0, 0); U.SetForegroundWindow(h); U.keybd_event(0x12, 0, 2, 0); time.sleep(0.5)
    F.click_at(3600, 2000); time.sleep(1.0)
print('fg', U.GetForegroundWindow() == h)
U.SetCursorPos(x0, yl); time.sleep(1.5)
res = []
for i in range(n):
    target = yc if i % 2 == 0 else yl
    base = darkness(target)
    t0 = time.perf_counter(); U.SetCursorPos(x0, target)
    while time.perf_counter() - t0 < 4:
        if darkness(target) > base + 300:
            break
    dt = time.perf_counter() - t0
    res.append(round(dt * 1000)); time.sleep(0.8)
print('ms', res, 'median', sorted(res)[len(res) // 2])
