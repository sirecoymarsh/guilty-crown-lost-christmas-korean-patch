"""게임을 켤 때마다(앞 창, 사용자가 조작을 맡겼을 때만): 타이틀 그림이 보이고 <첫 지연>초에 빈 곳을 한 번 누르고(넘기려는 클릭),
<둘째 지연>초에 「불러오기」를 누른 뒤 판정. 첫 지연을 음수로 주면 첫 클릭 없이.
python -X utf8 fg_two_clicks.py <이름> <native|4k> <첫 지연> <둘째 지연> <횟수> [NAME=VALUE ...]"""
import subprocess, sys, time
import numpy as np
from PIL import ImageGrab
sys.path.insert(0, r'F:\AI\gclx-4k\tools')
import fg_probe as F
import fg_ab as A

name, mode, d1, d2, n = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
env = sys.argv[6:]
U = F.U
res = []
for i in range(n):
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
    tb = time.time()
    if d1 >= 0:
        time.sleep(max(0, tb + d1 - time.time())); F.click_at(3600, 2000)
    time.sleep(max(0, tb + d2 - 1.2 - time.time())); U.SetCursorPos(1800, 1418)
    time.sleep(max(0, tb + d2 - time.time())); F.click_at(1800, 1418); time.sleep(4)
    k, d = A.look(); res.append(k)
    if k == 'other':
        ImageGrab.grab().resize((1024, 540)).save(A.OUT / f'{name}_{mode}_fail{i}.png')
    print(i, mode, f'first {d1}s second {d2}s', k, d, flush=True)
A.kill()
print(name, mode, env, d1, d2, 'load', res.count('load'), 'other', res.count('other'), 'title(no action)', res.count('title'), 'of', len(res))
