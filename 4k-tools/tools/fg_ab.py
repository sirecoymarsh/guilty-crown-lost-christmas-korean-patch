"""타이틀 「불러오기」 클릭 반복 시험(앞 창, 사용자가 조작을 맡겼을 때만, 11-02). 매번: 불러오기 위로 커서 → 클릭 → 3.5초 뒤 화면을
기준 화면(타이틀/불러오기)과 견줘 판정 → 불러오기면 「닫기」로 타이틀에 돌아와 다시, 아니면(새 게임 등) 게임을 끄고 다시 띄운다.
python -X utf8 fg_ab.py <이름> <횟수> <native|4k> [NAME=VALUE ...]
세이브는 사용자 평소 자리(세이브 칸은 안 건드림 — 불러오기 화면은 열고 닫기만)."""
import subprocess, sys, time
import numpy as np
from pathlib import Path
from PIL import Image, ImageGrab
sys.path.insert(0, r'F:\AI\gclx-4k\tools')
import fg_probe as F

name, trials, mode, env = (sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4:]) if __name__ == '__main__' else ('', 0, '4k', [])
GAME = Path(r'P:\AI\gclx-codexrun\game'); OUT = F.OUT
REF = {k: np.asarray(Image.open(OUT / f).convert('L').resize((256, 135))).astype(float)
       for k, f in (('title', 'back_title.png'), ('load', 'click_load2.png'))}
U = F.U


def look():
    g = np.asarray(ImageGrab.grab().convert('L').resize((256, 135))).astype(float)
    d = {k: float(np.mean((g - r) ** 2)) for k, r in REF.items()}
    k = min(d, key=d.get)
    return (k if d[k] < 900 else 'other'), {k: round(v) for k, v in d.items()}


def kill():
    out = subprocess.run(['tasklist', '/FO', 'CSV'], capture_output=True, text=True, encoding='cp949', errors='replace').stdout
    for line in out.splitlines():
        if 'GUILTY CROWN' in line:
            subprocess.run(['taskkill', '/PID', line.split('","')[1], '/F'], capture_output=True)
    time.sleep(2)


def launch():
    kill()
    if mode == 'native':
        ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine='\"%s\"'; CurrentDirectory='%s'}; $r.ReturnValue"
              % (GAME / 'GUILTY CROWN LOST XMAS.exe', GAME))
        subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True)
    else:
        subprocess.run([sys.executable, '-X', 'utf8', r'F:\AI\gclx-4k\tools\fg_launch.py', *env], capture_output=True)
    time.sleep(3); U.SetCursorPos(3600, 2000)
    t0 = time.time()
    while time.time() - t0 < 80:
        time.sleep(2)
        if F.hwnd() and look()[0] == 'title':
            time.sleep(3); break
    F.click_at(3600, 2000); time.sleep(1.2)


res = []
if __name__ == '__main__':
    launch()
for i in range(trials):
    U.SetCursorPos(1800, 1418); time.sleep(1.2)
    F.click_at(1800, 1418); time.sleep(3.5)
    k, d = look(); res.append(k); print(i, k, d, flush=True)
    if k == 'load':
        U.SetCursorPos(3624, 1811); time.sleep(1.0); F.click_at(3624, 1811); time.sleep(4.5)
        k2, _ = look()
        if k2 != 'title':
            print('  back ->', k2); launch()
    elif k == 'other':
        ImageGrab.grab().resize((1024, 540)).save(OUT / f'{name}_fail{i}.png'); launch()
    else:
        time.sleep(1)
if __name__ == '__main__':
    kill()
    print(name, mode, env, 'load', res.count('load'), 'other', res.count('other'), 'title(no action)', res.count('title'), 'of', len(res))
