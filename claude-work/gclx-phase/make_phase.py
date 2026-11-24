"""단계 표지 글자 「단계」 → 원작대로 영어 「phase」(사용자 11-24 「질병의 진행기를 뜻하는 페이즈니까 그대로 영어로 남기던가…」).
원작 그림(cg/sys/phase/フェイズ.png, 80x31: 흰 Arial 꼴 글자 + 청록 0,130,106 번짐)을 같은 자리·같은 크기로 4배(320x124) 다시 그린다.
한국어판 function_lc_toho.nss 는 이 그림을 Zoom 250 으로 띄우므로 4배 그림이 맞다.
python -I -X utf8 make_phase.py → phase_4x.png, 비교 compare.png
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = Path(__file__).resolve().parent
ORIG = Path(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\extracted\cg.npa\sys\phase\フェイズ.png')
FONT = r'C:\Windows\Fonts\arial.ttf'
S = 4
GLOW = (0, 130, 106)


def white_bbox(im):
    m = Image.new('L', im.size, 0)
    px = im.load(); mp = m.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a > 200 and r > 200 and g > 200 and b > 200:
                mp[x, y] = 255
    return m.getbbox()


def render():
    o = Image.open(ORIG).convert('RGBA')
    bx0, by0, bx1, by1 = white_bbox(o)             # 원작 흰 글자 자리(1배)
    W, H = o.width * S, o.height * S
    # 글꼴 크기: 흰 글자 높이(위 ascender h 부터 아래 p 꼬리까지)에 맞춘다
    target_h = (by1 - by0) * S
    size = 10
    for size in range(40, 200):
        f = ImageFont.truetype(FONT, size)
        l, t, r, b = f.getbbox('phase')
        if b - t >= target_h:
            break
    f = ImageFont.truetype(FONT, size)
    l, t, r, b = f.getbbox('phase')
    # 원작 글자는 Arial 보다 옆으로 넓다 → 조금 띄워 그린 뒤 가로로 늘려 원작 흰 글자 폭(bx0~bx1)에 맞춘다
    word = 'phase'
    gap = size * 0.07
    widths = [f.getlength(ch) for ch in word]
    tw = int(sum(widths) + gap * (len(word) - 1) + size)
    th = H
    tmp = Image.new('L', (tw, th), 0)
    d = ImageDraw.Draw(tmp)
    x = -f.getbbox('p')[0] + size * 0.1
    y = by0 * S - t
    for ch, w in zip(word, widths):
        d.text((x, y), ch, font=f, fill=255)
        x += w + gap
    l0, _, r0, _ = tmp.getbbox()
    tmp = tmp.crop((l0, 0, r0, th))
    span = (bx1 - bx0) * S
    tmp = tmp.resize((span, th), Image.LANCZOS)
    text = Image.new('L', (W, H), 0)
    text.paste(tmp, (bx0 * S, 0))
    glow_a = text.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(9))
    glow_a = glow_a.point(lambda v: min(255, int(v * 1.2)))
    out = Image.new('RGBA', (W, H), GLOW + (0,))
    out.putalpha(glow_a)
    white = Image.new('RGBA', (W, H), (255, 255, 255, 0)); white.putalpha(text)
    out.alpha_composite(white)
    return o, out, (bx0, by0, bx1, by1), size


if __name__ == '__main__':
    o, out, bb, size = render()
    out.save(HERE / 'phase_4x.png')
    print('orig white bbox', bb, 'font size', size)
    bg = (8, 14, 16, 255)
    a = Image.new('RGBA', o.size, bg); a.alpha_composite(o)
    small = out.resize(o.size, Image.LANCZOS)
    b = Image.new('RGBA', o.size, bg); b.alpha_composite(small)
    big = Image.new('RGBA', out.size, bg); big.alpha_composite(out)
    sheet = Image.new('RGBA', (out.width * 2 + 20, out.height * 2 + 20), (40, 40, 40, 255))
    sheet.alpha_composite(a.resize(out.size, Image.NEAREST), (0, 0))
    sheet.alpha_composite(b.resize(out.size, Image.NEAREST), (out.width + 20, 0))
    sheet.alpha_composite(big, (out.width + 20, out.height + 20))
    sheet.alpha_composite(a.resize(out.size, Image.LANCZOS), (0, out.height + 20))
    sheet.save(HERE / 'compare.png')
