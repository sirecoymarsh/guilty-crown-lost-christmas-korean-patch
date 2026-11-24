"""게임을 켤 때마다 첫 클릭 하나만 시험(앞 창, 사용자가 조작을 맡겼을 때만): 타이틀 배경이 보인 뒤 <지연>초에 「불러오기」를 누르고 판정.
배경은 타이틀 오른쪽 그림이 밝아지는 것으로 잡는다(메뉴 글자는 그 뒤 몇 초에 걸쳐 하나씩 나타남).
python -X utf8 fg_first_click.py <이름> <native|4k> <지연초> <횟수>"""
import subprocess, sys, time
import numpy as np
from PIL import ImageGrab
sys.path.insert(0, r'F:\AI\gclx-4k\tools')
import fg_probe as F
import fg_ab as A   # look(), kill(), launch helpers share the reference screens

name, mode, delay, n = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4])
A.mode = mode; A.env = []
U = F.U
res = []
for i in range(n):
    A.kill()
    if mode == 'native':
        ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine='\"%s\"'; CurrentDirectory='%s'}; $r.ReturnValue"
              % (A.GAME / 'GUILTY CROWN LOST XMAS.exe', A.GAME))
        subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True)
    else:
        subprocess.run([sys.executable, '-X', 'utf8', r'F:\AI\gclx-4k\tools\fg_launch.py'], capture_output=True)
    time.sleep(3); U.SetCursorPos(1800, 1418)
    t0 = time.time()
    while time.time() - t0 < 90:
        m = float(np.asarray(ImageGrab.grab(bbox=(2400, 1000, 3400, 1800)).convert('L')).mean())
        if m > 150:
            break
        time.sleep(0.2)
    tb = time.time()
    time.sleep(delay)
    F.click_at(1800, 1418); time.sleep(4)
    k, d = A.look(); res.append(k)
    print(i, f'click {delay}s after title art', k, d, flush=True)
A.kill()
print(name, mode, delay, 'load', res.count('load'), 'other', res.count('other'), 'title(no action)', res.count('title'), 'of', len(res))
