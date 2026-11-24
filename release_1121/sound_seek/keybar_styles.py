"""11-24 사용자 「하단 커맨드 아이콘을 게임 UI에 맞는걸로 제안해주지 않겠어?」 — 키 목록 그림 시안 셋.
게임 UI 에서 빌린 것: 메뉴 단추의 비스듬한 은빛 칼날(sys/menu), 대사창의 거의 검정 바탕과 위쪽 회색 가는 선(sys/adv/window01),
강조 창의 진홍(window03 #FF1450 쪽), 대사 기록·회상의 육각 무늬, 설정 탭의 둥근 어두운 칸.
A 칼날: 키 = 기운 은빛 평행사변형 + 검은 글자.   B 육각: 키 = 양끝이 뾰족한 길쭉한 육각 테 + 흰 글자.
C 선: 키 칸 없이 진홍 글자, 항목 사이 작은 마름모, 위에 양끝이 흐려지는 가는 선.
python -X utf8 keybar_styles.py <out_dir>  → keybar_A.png … (4096x80) 와 실제 화면에 얹은 비교 그림
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import keybar

KO = keybar.KO
S = 4
W, H = 1024 * S, 20 * S
SILVER_HI, SILVER_LO = (236, 236, 240), (150, 150, 160)
INK = (20, 20, 24, 255)
LABEL = (196, 196, 202, 255)
CRIMSON = (255, 38, 96, 255)


def fonts(kpx=11.5, lpx=12.5, kw=700, lw=500):
    fk = ImageFont.truetype(KO, round(kpx * S)); fk.set_variation_by_axes([kw])
    fl = ImageFont.truetype(KO, round(lpx * S)); fl.set_variation_by_axes([lw])
    return fk, fl


def grad_fill(im, poly, top, bot):
    """다각형 안을 위→아래 은빛 그러데이션으로."""
    mask = Image.new('L', im.size, 0); ImageDraw.Draw(mask).polygon(poly, fill=255)
    g = Image.new('RGBA', im.size)
    gd = ImageDraw.Draw(g)
    ys = [p[1] for p in poly]; y0, y1 = int(min(ys)), int(max(ys)) + 1
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        c = tuple(round(top[i] * (1 - t) + bot[i] * t) for i in range(3)) + (255,)
        gd.line((0, y, im.width, y), fill=c)
    im.paste(g, (0, 0), mask)


def layout(d, keys, fk, fl, capw, gap_cap, gap_item):
    parts = [(k, lab, capw(d, k), d.textlength(lab, font=fl)) for k, lab in keys]
    total = sum(kw + gap_cap + lw for _, _, kw, lw in parts) + gap_item * (len(parts) - 1)
    assert total < W - 8 * S, total / S
    return parts, (W - total) / 2


def style_A(keys):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fk, fl = fonts(10.5, 12)
    sl = 3 * S                                    # 기울기(위가 오른쪽으로)
    parts, x = layout(d, keys, fk, fl, lambda d, k: d.textlength(k, font=fk) + 2 * 4 * S + sl, 4 * S, 7.5 * S)
    t, b = 3 * S, H - 3 * S
    for k, lab, kw, lw in parts:
        poly = [(x + sl, t), (x + kw, t), (x + kw - sl, b), (x, b)]
        grad_fill(im, poly, SILVER_HI, SILVER_LO)
        d.line([(x + sl, t), (x + kw, t)], fill=(255, 255, 255, 255), width=S // 2)   # 위 테 밝게
        d.text((x + kw / 2, H / 2), k, font=fk, fill=INK, anchor='mm')
        x += kw + 4 * S
        d.text((x, H / 2), lab, font=fl, fill=LABEL, anchor='lm')
        x += lw + 7.5 * S
    return im


def style_B(keys):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fk, fl = fonts(10.5, 12, 600)
    tip = 4 * S
    parts, x = layout(d, keys, fk, fl, lambda d, k: d.textlength(k, font=fk) + 2 * 4 * S + 2 * tip - 4 * S, 3.5 * S, 7.5 * S)
    t, b, m = 2.5 * S, H - 2.5 * S, H / 2
    for k, lab, kw, lw in parts:
        poly = [(x, m), (x + tip, t), (x + kw - tip, t), (x + kw, m), (x + kw - tip, b), (x + tip, b)]
        d.polygon(poly, fill=(18, 18, 22, 230))
        d.line(poly + [poly[0]], fill=(200, 200, 208, 255), width=S, joint='curve')
        d.text((x + kw / 2, m), k, font=fk, fill=(245, 245, 248, 255), anchor='mm')
        x += kw + 3.5 * S
        d.text((x, m), lab, font=fl, fill=LABEL, anchor='lm')
        x += lw + 7.5 * S
    return im


def style_C(keys):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fk, fl = fonts(11.5, 12, 800)
    dia = 2 * S
    parts, x = layout(d, keys, fk, fl, lambda d, k: d.textlength(k, font=fk), 3.5 * S, 14 * S)
    # 위 가는 선: 가운데 밝고 양끝으로 사라짐(대사창 위 테처럼)
    for xx in range(0, W, 2):
        a = max(0.0, 1 - abs(xx - W / 2) / (W * 0.46)) ** 1.4
        d.line((xx, 0, xx + 1, 0), fill=(170, 170, 178, round(200 * a)), width=1)
    m = H / 2 + 1 * S
    for i, (k, lab, kw, lw) in enumerate(parts):
        if i:
            cx = x - 7 * S
            d.polygon([(cx, m - dia), (cx + dia, m), (cx, m + dia), (cx - dia, m)], fill=(120, 120, 128, 255))
        d.text((x, m), k, font=fk, fill=CRIMSON, anchor='lm')
        x += kw + 3.5 * S
        d.text((x, m), lab, font=fl, fill=LABEL, anchor='lm')
        x += lw + 14 * S
    return im


SERIF = r'P:\AI\gclx-codexrun\game\fonts\NotoSerifKR-VF.ttf'


def style_D(keys, disabled=()):
    """D 설정 칸(11-24 사용자 「게임 설정에 어울리는 UI를 제시해서 그걸로 바꿔 지금은 튄다」): 원작 환경 설정의 번호 칸
    (채움 3C·왼쪽 띠 30·명조 굵은 밝은 회색 글자)을 키 칸으로, 설정 줄의 가는 이음줄(26) 하나 뒤에 차분한 회색 뜻."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fk = ImageFont.truetype(SERIF, round(11 * S)); fk.set_variation_by_axes([700])
    fl = ImageFont.truetype(KO, round(12 * S)); fl.set_variation_by_axes([500])
    pad, link, gap = 4 * S, 4 * S, 8 * S
    parts, x = layout(d, keys, fk, fl, lambda d, k: d.textlength(k, font=fk) + 2 * pad, link + 3 * S, gap)
    t, b = 2 * S, H - 2 * S
    m = H / 2
    # disabled(11-24 회상): 그 칸은 어둡게, 키부터 뜻까지 가로줄(사용자 「작동하지 않는 S 키 같은 것들은 밑줄을 그어 …」)
    for k, lab, kw, lw in parts:
        off = k in disabled; x_start = x
        d.rectangle((x, t, x + kw - 1, b - 1), fill=(34, 34, 34, 255) if off else (60, 60, 60, 255))
        d.rectangle((x, t, x + 3 * S - 1, b - 1), fill=(28, 28, 28, 255) if off else (48, 48, 48, 255))
        d.text((x + 1.5 * S + kw / 2, m), k, font=fk, fill=(96, 96, 96, 255) if off else (208, 208, 208, 255), anchor='mm')
        x += kw
        d.rectangle((x, m - S / 2, x + link - 1, m + S / 2 - 1), fill=(40, 40, 40, 255) if off else (58, 58, 58, 255))   # 이음줄
        x += link + 3 * S
        d.text((x, m), lab, font=fl, fill=(88, 88, 88, 255) if off else (170, 170, 170, 255), anchor='lm')
        x += lw
        if off:
            d.rectangle((x_start - S, m - S / 2, x + S - 1, m + S / 2 - 1), fill=(150, 150, 150, 255))
        x += gap
    return im


STYLES = {'A': style_A, 'B': style_B, 'C': style_C, 'D': style_D}


def on_shot(bar, shot, label):
    """실제 화면(3840x2160)의 아래 1/3 에 얹어 본다(엔진 y=554, 폭 1024 → 3.75배)."""
    s = shot.copy().convert('RGBA')
    b = bar.resize((3840, 75), Image.LANCZOS)
    s.alpha_composite(b, (0, round(554 * 3.75)))
    c = s.crop((0, 1500, 3840, 2160)).convert('RGB')
    d = ImageDraw.Draw(c); f = ImageFont.truetype(KO, 64); f.set_variation_by_axes([700])
    d.rectangle((0, 0, 150, 90), fill=(0, 0, 0)); d.text((30, 8), label, font=f, fill=(255, 220, 60))
    return c


if __name__ == '__main__':
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    shot = Image.open(sys.argv[2]) if len(sys.argv) > 2 else None
    rows = []
    cur = Image.open(__import__('io').BytesIO(keybar.render()))
    for name, fn in [('지금', None)] + list(STYLES.items()):
        bar = cur if fn is None else fn(keybar.KEYS)
        if fn: bar.save(out / f'keybar_{name}.png')
        if shot: rows.append(on_shot(bar, shot, name))
    if rows:
        full = Image.new('RGB', (3840, sum(r.height for r in rows)))
        y = 0
        for r in rows: full.paste(r, (0, y)); y += r.height
        full.save(out / 'keybar_compare_full.png')
        # 오른쪽 절반 확대(글자 크기 그대로 보이게)
        zoom = Image.new('RGB', (1920, 165 * len(rows)))
        for i, r in enumerate(rows):
            zoom.paste(r.crop((0, 495, 1920, 660)), (0, 165 * i))
        zoom.save(out / 'keybar_compare_left.png')
        zoom2 = Image.new('RGB', (1920, 165 * len(rows)))
        for i, r in enumerate(rows):
            zoom2.paste(r.crop((1920, 495, 3840, 660)), (0, 165 * i))
        zoom2.save(out / 'keybar_compare_right.png')
