"""노래 가사 그림 다시 그리기(사용자 11-24 「인게임 노래 자막을 상단에 위치하고 한국어 가사 색은 노란색으로, 검은 박스는 없애줘」).
코덱스 build_lyrics.py 의 그림(4096x224, 검은 반투명 둥근 상자 + 원문 흰 글자 + 한국어 흰 글자, 검은 테두리)과 같은 자리·크기·글꼴에서
- 검은 상자를 없애고, 밝은 장면에서도 읽히게 테두리를 조금 굵게 + 부드러운 그림자,
- 한국어 줄은 노란색(원문 줄은 그대로 밝은 회백색).
본편 위치는 kr_lyrics.nss 의 $KLY_Y=326(대사창 위) → 화면 위(TOP_Y). 사운드 화면(484)·엔딩(504)은 그대로.
"""
import io, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

C = Path(r'P:\AI\Codex\projects\gclx-song-20261123')
KO_FONT = C / 'game/fonts/NotoSansKR-VF.ttf'
JP_FONT = C / 'assets/NotoSansCJKjp-Medium.otf'
TOP_Y = 14
YELLOW = (255, 226, 72, 255)
SRC = (236, 240, 242, 255)

f1 = ImageFont.truetype(str(KO_FONT), 80); f1.set_variation_by_axes([500])
f2 = ImageFont.truetype(str(KO_FONT), 96); f2.set_variation_by_axes([600])
jp = ImageFont.truetype(str(JP_FONT), 80)


def cues():
    return json.loads((C / 'data/lyrics.json').read_text('utf-8'))['cues']


def render(row) -> bytes:
    sf = jp if row['track'].startswith('lxsong') else f1
    W, H = 4096, 224
    lines = [((2048, 52), row['source'], sf, SRC, 7), ((2048, 153), row['ko'], f2, YELLOW, 8)]
    # 11-24 사용자 「상단 자막에 그림자 효과를 넣은거 같은데 오히려 지저분하다 제거하고 글자 표시만 남겨줘」 → 흐린 그림자 없앰,
    # 글자와 가는 검은 테두리만(흰 화면에서도 읽히게 테두리는 남김)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for (x, y), t, f, col, sw in lines:
        d.text((x, y), t, font=f, anchor='mm', fill=col, stroke_width=sw, stroke_fill=(0, 0, 0, 255))
    out = io.BytesIO(); im.save(out, format='PNG'); return out.getvalue()


def patch_script(kly: bytes) -> bytes:
    a = b'$KLY_Y=326;'
    assert kly.count(a) == 2, kly.count(a)
    return kly.replace(a, b'$KLY_Y=' + str(TOP_Y).encode() + b';')


def assets() -> dict:
    return {f"kr_ly_{r['id']:04d}.png": render(r) for r in cues()}


if __name__ == '__main__':   # 견본: 밝은 타이틀·어두운 장면 위에 몇 줄
    import sys
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    rows = cues(); pick = [rows[0], rows[120], [r for r in rows if r['track'] == 'lxsong01'][3], max(rows, key=lambda r: len(r['ko']))]
    bgs = [Image.open(p).convert('RGBA').resize((1024, 576)) for p in sys.argv[2:]]
    for k, bg in enumerate(bgs):
        bg = bg.resize((4096, 2304))
        for j, r in enumerate(pick):
            im = Image.open(io.BytesIO(render(r)))
            bg.alpha_composite(im, (0, TOP_Y * 4 + j * 240))
        bg.resize((2048, 1152)).convert('RGB').save(out / f'sample_{k}.png')
