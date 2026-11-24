"""엔딩 노래 두 곡(lxsong01·02)을 꺼내 목소리 높이(기본 주파수)의 분포를 잰다 — 여성(이토 카나코)·남성 구분용.
python -I -X utf8 pitch.py"""
import sys, subprocess
from pathlib import Path
import numpy as np
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from npa_assets import NPA
FF = r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\vendor\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe'
H = Path(__file__).parent
a = NPA(r'P:\AI\gclx-codexrun\game\sound.npa')
for e in a.entries:
    n = e['name'].lower().replace(chr(92), '/')
    if e['type'] == 2 and n in ('bgm/lxsong01.ogg', 'bgm/lxsong02.ogg'):
        (H / n.split('/')[-1]).write_bytes(a.read(e))
SR = 16000
for name in ('lxsong01', 'lxsong02'):
    raw = subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-i', str(H / f'{name}.ogg'), '-ac', '1', '-ar', str(SR),
                          '-af', 'highpass=f=90,lowpass=f=1100', '-f', 's16le', '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    N, hop = 1024, 512
    f0s = []
    for i in range(0, len(x) - N, hop):
        f = x[i:i + N] * np.hanning(N)
        if np.sqrt((f ** 2).mean()) < 0.02:
            continue
        r = np.fft.irfft(np.abs(np.fft.rfft(f, 2 * N)) ** 2)[:N]
        r /= r[0] + 1e-9
        lo, hi = SR // 1000, SR // 90           # 90~1000 Hz
        k = lo + int(np.argmax(r[lo:hi]))
        if r[k] > 0.6:                         # 뚜렷한 주기만
            f0s.append(SR / k)
    f0s = np.array(f0s)
    q = np.percentile(f0s, [25, 50, 75])
    print(name, 'voiced frames', len(f0s), 'F0 p25/p50/p75 =', [round(v) for v in q],
          'share>250Hz', round(float((f0s > 250).mean()), 2), 'share<180Hz', round(float((f0s < 180).mean()), 2))
