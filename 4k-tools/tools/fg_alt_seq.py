"""Alt+Tab 처럼 다른 창으로 갔다가 Alt 를 누른 채 게임으로 돌아온 뒤, 누르지 않고 커서만 시작→불러오기→환경설정.
python -X utf8 fg_alt_seq.py <이름>"""
import sys, time
sys.path.insert(0, r'F:\AI\gclx-4k\tools')
import fg_probe as F
from PIL import Image

name = sys.argv[1]
U, h = F.U, F.hwnd()
tray = U.FindWindowW('Shell_TrayWnd', None)
U.SetCursorPos(3600, 2000); time.sleep(0.5)
U.keybd_event(0x12, 0, 0, 0); U.SetForegroundWindow(tray); U.keybd_event(0x12, 0, 2, 0); time.sleep(1)
U.keybd_event(0x12, 0, 0, 0); U.SetForegroundWindow(h); time.sleep(0.15); U.keybd_event(0x12, 0, 2, 0); time.sleep(1)
print('fg', U.GetForegroundWindow() == h)
shots = []
for tag, (x, y) in (('start', (1800, 1283)), ('load', (1800, 1418)), ('config', (1800, 1552))):
    U.SetCursorPos(x, y); time.sleep(1.5); shots.append(F.shot(f'{name}_{tag}'))
time.sleep(2); shots.append(F.shot(f'{name}_end'))
o = Image.new('RGB', (500 * len(shots), 600))
for i, p in enumerate(shots):
    o.paste(Image.open(p).crop((1650, 1200, 2150, 1800)), (i * 500, 0))
o.save(F.OUT / f'{name}_seq.png'); print(F.OUT / f'{name}_seq.png')
