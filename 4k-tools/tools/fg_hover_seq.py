"""앞 창 강조 시험: 게임을 앞으로 → 불러오기 → 환경설정 → 바깥에 커서를 두고 차례로 찍어 한 장으로.
python -X utf8 fg_hover_seq.py <이름>   (화면 좌표는 4K 창 기준 단추 자리)"""
import sys, time
sys.path.insert(0, r'F:\AI\gclx-4k\tools')
import fg_probe as F
from PIL import Image

name = sys.argv[1]
U, h = F.U, F.hwnd()
U.keybd_event(0x12, 0, 0, 0); U.SetForegroundWindow(h); U.keybd_event(0x12, 0, 2, 0); time.sleep(0.6)
print('fg', U.GetForegroundWindow() == h, F.info(h))
shots = []
for tag, (x, y) in (('load', (1800, 1418)), ('config', (1800, 1552)), ('off', (3000, 1900))):
    U.SetCursorPos(x, y); time.sleep(1.2); shots.append(F.shot(f'{name}_{tag}'))
o = Image.new('RGB', (1500, 600))
for i, p in enumerate(shots):
    o.paste(Image.open(p).crop((1650, 1200, 2150, 1800)), (i * 500, 0))
o.save(F.OUT / f'{name}_seq.png'); print(F.OUT / f'{name}_seq.png')
