"""타이틀에서 불러오기 → 닫기로 돌아온 뒤 환경설정을 누르면 무엇이 열리는지(앞 창, 사용자가 조작을 맡겼을 때만).
python -X utf8 fg_return_seq.py <이름>"""
import sys, time
sys.path.insert(0, r'F:\AI\gclx-4k\tools')
import fg_probe as F
from PIL import Image

name = sys.argv[1]
U, h = F.U, F.hwnd()
if U.GetForegroundWindow() != h:
    U.keybd_event(0x12, 0, 0, 0); U.SetForegroundWindow(h); U.keybd_event(0x12, 0, 2, 0); time.sleep(0.5)
    F.click_at(3600, 2000); time.sleep(1.0)
shots = []
U.SetCursorPos(1800, 1418); time.sleep(1.2); F.click_at(1800, 1418); time.sleep(3.5); shots.append(F.shot(f'{name}_load'))
U.SetCursorPos(3624, 1811); time.sleep(1.2); F.click_at(3624, 1811); time.sleep(4); shots.append(F.shot(f'{name}_back'))
U.SetCursorPos(1800, 1552); time.sleep(1.5); shots.append(F.shot(f'{name}_hover_config'))
F.click_at(1800, 1552); time.sleep(3.5); shots.append(F.shot(f'{name}_after_click'))
o = Image.new('RGB', (1024 * len(shots), 540))
for i, p in enumerate(shots):
    o.paste(Image.open(p).resize((1024, 540)), (i * 1024, 0))
o.save(F.OUT / f'{name}_seq.png'); print(F.OUT / f'{name}_seq.png')
