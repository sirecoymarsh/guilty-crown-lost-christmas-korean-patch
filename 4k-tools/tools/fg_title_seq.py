"""앞 창 타이틀 시험(사용자가 조작을 맡겼을 때만): Alt 없이 빈 곳을 한 번 눌러 앞으로 → 시작 → 불러오기 → 환경설정 순서로
커서만 옮기며 찍고, 마지막에 환경설정을 눌러 무엇이 열리는지 찍는다. python -X utf8 fg_title_seq.py <이름> [click]"""
import sys, time
sys.path.insert(0, r'F:\AI\gclx-4k\tools')
import fg_probe as F
from PIL import Image

name = sys.argv[1]
U, h = F.U, F.hwnd()
F.click_at(3600, 2000)                      # empty corner of the title, as a person would to focus the game
time.sleep(1.5)
print('fg', U.GetForegroundWindow() == h)
shots = []
for tag, (x, y) in (('start', (1800, 1283)), ('load', (1800, 1418)), ('config', (1800, 1552))):
    U.SetCursorPos(x, y); time.sleep(1.5); shots.append(F.shot(f'{name}_{tag}'))
if len(sys.argv) > 2 and sys.argv[2] == 'click':
    F.click_at(1800, 1552); time.sleep(3); shots.append(F.shot(f'{name}_after_click'))
o = Image.new('RGB', (500 * len(shots), 600))
for i, p in enumerate(shots):
    o.paste(Image.open(p).crop((1650, 1200, 2150, 1800)), (i * 500, 0))
o.save(F.OUT / f'{name}_seq.png'); print(F.OUT / f'{name}_seq.png')
