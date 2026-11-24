"""11-24 영상 감상 썸네일 후보 뽑기(사용자 「영상을 썸네일 형식으로. 그리고 영상 더 있지 않아?」).
영상마다 고르게 8장을 뽑아 비교 그림을 만든다. 2장·5장 영상은 사용자 진도 밖 — 후보 그림을 사용자에게 보이지 말 것.
python -I -X utf8 thumb_candidates.py
"""
import subprocess, re, sys
from pathlib import Path
from PIL import Image, ImageDraw
FF = r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\vendor\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe'
GAME = Path(r'P:\AI\gclx-codexrun\game')
OUT = Path(__file__).resolve().parent / 'thumbs_work'
VIDS = {'op': GAME / 'dx4k/mv_op.mp4', 'eyecatch': GAME / 'dx4k/GC_eyecatch_E.mp4',
        'lx0201': GAME / 'dx4k/mv_lx0201.mp4', 'lx0506': GAME / 'dx/mv_bikeend.ngs',
        'lx0106': GAME / 'dx/mvbattle0106.ngs'}   # 11-24 1장 전투 영상(빠졌던 넷째 이야기 영상)


def duration(p):
    r = subprocess.run([FF, '-hide_banner', '-i', str(p)], capture_output=True, text=True, errors='replace')
    m = re.search(r'Duration: (\d+):(\d+):([\d.]+)', r.stderr)
    s = re.search(r'Stream .*Video: .*?, (\d{3,5})x(\d{3,5})', r.stderr)
    return (int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))), (s.group(1), s.group(2)) if s else None


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    for key, p in VIDS.items():
        if sys.argv[1:] and key not in sys.argv[1:]:   # python thumb_candidates.py lx0106 → 그 영상만
            continue
        d, wh = duration(p)
        print(key, round(d, 2), wh)
        tiles = []
        for i in range(8):
            t = d * (i + 0.5) / 8
            f = OUT / f'{key}_{i}.png'
            subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-ss', f'{t:.2f}', '-i', str(p), '-frames:v', '1', str(f)], check=True)
            im = Image.open(f).convert('RGB').resize((480, 270))
            ImageDraw.Draw(im).text((6, 4), f'{i} {t:.1f}s', fill=(255, 255, 0))
            tiles.append(im)
        sheet = Image.new('RGB', (480 * 4, 270 * 2))
        for k, im in enumerate(tiles):
            sheet.paste(im, ((k % 4) * 480, (k // 4) * 270))
        sheet.save(OUT / f'sheet_{key}.png')
