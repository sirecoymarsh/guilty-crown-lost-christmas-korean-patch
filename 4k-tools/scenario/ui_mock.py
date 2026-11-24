"""꾸민 회상·사운드 화면 미리보기(게임을 띄우지 않고 같은 그림·자리·글꼴로 합성). 앞 장면만 씀(사용자 플레이 중).
python -X utf8 ui_mock.py <ui_survey 폴더> <build 폴더> <출력 png>"""
import io, json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

survey, build, outp = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
HERE = Path(__file__).parent
SANS = r'P:\AI\gclx-codexrun\game\fonts\NotoSansKR-VF.ttf'
cg = NPA(Path(r'P:\AI\gclx-codexrun\game\cg.npa')); ent = {e['name'].replace('\\', '/'): e for e in cg.entries}
scenes = json.load(open(HERE / 'scenes.json', encoding='utf-8'))
titles = json.load(open(HERE / 'titles.json', encoding='utf-8'))
summ = json.load(open(HERE / 'summaries.json', encoding='utf-8'))
pn = json.load(open(HERE / 'phase_names.json', encoding='utf-8'))
SL = json.load(open(HERE / 'snd_layout.json'))
tracks = json.load(open(HERE / 'music_list.json', encoding='utf-8'))


def F(px, w=500):
    f = ImageFont.truetype(SANS, px)
    try:
        f.set_variation_by_axes([w])
    except Exception:
        pass
    return f


def img(path):
    path = path[3:] if path.startswith('cg/') else path
    return Image.open(io.BytesIO(cg.read(ent[path]))).convert('RGBA')


def put(base, im, x, y, zoom=1.0):
    if zoom != 1.0:
        im = im.resize((max(1, round(im.width * zoom)), max(1, round(im.height * zoom))), Image.LANCZOS)
    base.alpha_composite(im, (round(x), round(y)))


def text(d, x, y, s, px, col, w=500):
    d.text((x, y), s, font=F(px, w), fill=col)


def btns(base):
    for nm, x in (('back', 732), ('next', 831), ('exit', 924)):
        put(base, img(f'sys/extra/cglib/{nm}-001.png'), x, 542, 0.25)


def wrap(d, s, px, width):
    out, cur = [], ''
    for ch in s:
        if d.textlength(cur + ch, font=F(px)) > width:
            out.append(cur); cur = ch
        else:
            cur += ch
    return out + [cur]


# ---- 1) 회상 목록 1쪽(일부 읽음)
L = Image.new('RGBA', (1024, 576), (0, 0, 0, 255)); d = ImageDraw.Draw(L)
put(L, img('sys/extra/cglib/背景.png'), 0, 0)
read = {0, 1, 3}
for i in range(20):
    x, y = (i % 5) * 200 + 16, (i // 5) * 124 + 36
    s = scenes[i]
    if i in read:
        put(L, img(s['thumb']), x, y)
        band = Image.new('RGBA', (192, 28), (0, 0, 0, 166)); L.alpha_composite(band, (x, y + 80))
        text(d, x + 7, y + 83, f'{i + 1:02d}  {titles[s["file"]]}', 15, (255, 255, 255, 255))
        if i in (0, 1):
            L.alpha_composite(Image.new('RGBA', (74, 24), (0, 0, 0, 178)), (x, y))
            text(d, x + 6, y + 2, f'단계 {s["phase"]:02d}', 13, (0x8B, 0xE9, 0xD7, 255), 600)
    else:
        put(L, Image.open(build / 'kr_scn_lock.png').convert('RGBA'), x, y, 0.25)
put(L, img('sys/extra/cglib/no001.png'), 0, 0, 0.25)
btns(L)
text(d, 448, 547, '검수: 안 읽은 장면도 열기', 14, (0x7A, 0x7A, 0x7A, 255))

# ---- 2) 상세(2번째 장면)
D = Image.new('RGBA', (1024, 576), (0, 0, 0, 255)); d = ImageDraw.Draw(D)
s = scenes[1]
D.alpha_composite(Image.new('RGBA', (644, 364), (0x3A, 0x3A, 0x3A, 255)), (22, 58))
D.alpha_composite(Image.new('RGBA', (640, 360), (0, 0, 0, 255)), (24, 60))
put(D, img(s['cg']), 24, 60, 0.625)
put(D, img('sys/phase/フェイズ.png'), 692, 50, 0.25)
put(D, img(f'sys/phase/{s["phase"]}/数字.png'), 692, 72)
text(d, 786, 88, pn[str(s['phase'])], 17, (0x8B, 0xE9, 0xD7, 255), 600)
line = img('sys/phase/線１.png').resize((317, 24)); D.alpha_composite(line, (692, 134))
text(d, 694, 166, '2번째 장면', 15, (0x8A, 0x8A, 0x8A, 255))
text(d, 694, 194, titles[s['file']], 26, (255, 255, 255, 255), 600)
D.alpha_composite(Image.new('RGBA', (312, 46), (0x2E, 0x2E, 0x2E, 255)), (694, 362))
D.alpha_composite(Image.new('RGBA', (297, 42), (0x0B, 0x0B, 0x0B, 255)), (697, 364))
D.alpha_composite(Image.new('RGBA', (10, 46), (0x26, 0x26, 0x26, 255)), (996, 362))
text(d, 716, 370, '▶  여기서 보기', 20, (0xDA, 0xDA, 0xDA, 255), 600)
text(d, 694, 418, '끝까지 보면 이 화면으로 돌아옵니다.', 14, (0x7A, 0x7A, 0x7A, 255))
for k, ln in enumerate(wrap(d, summ[s['file']], 15, 630)):
    text(d, 26, 434 + k * 22, ln, 15, (0xC8, 0xC8, 0xC8, 255))
put(D, Image.open(build / 'kr_bars.png').convert('RGBA'), 0, 0, 0.25)
btns(D)
text(d, 18, 546, '회상 · 1 / 5쪽', 15, (0x8A, 0x8A, 0x8A, 255))

# ---- 3) 사운드(4곡 열림, 1번 재생 중)
S = Image.new('RGBA', (1024, 576), (0, 0, 0, 255)); d = ImageDraw.Draw(S)
put(S, Image.open(build / 'kr_snd_bg.png').convert('RGBA'), 0, 0, 0.25)
opened = {1, 2, 5, 12}
for k, t in enumerate(tracks, 1):
    col, r = (k - 1) // SL['rows'], (k - 1) % SL['rows']
    x, y = SL['col_x'][col], SL['row_y0'] + r * SL['pitch']
    ix, iy, iw, ih = x + SL['item_x'] + 2, y + 1, SL['item_w'] - 12, SL['h'] - 2
    tx = x + SL['item_x'] + 14
    if k in opened:
        if k == 1:
            S.alpha_composite(Image.new('RGBA', (iw, ih), (0x16, 0x3A, 0x36, 255)), (ix, iy))
            text(d, ix + iw - 24, y + 2, '▶', 14, (0x8B, 0xE9, 0xD7, 255), 600)
        text(d, tx, y + 1, t['name'], 16, (0xDA, 0xDA, 0xDA, 255), 600)
    else:
        text(d, tx, y + 1, '아직 듣지 않은 곡', 16, (0x4A, 0x4A, 0x4A, 255))
put(S, Image.open(build / 'kr_bars.png').convert('RGBA'), 0, 0, 0.25)
put(S, img('sys/extra/cglib/exit-001.png'), 924, 542, 0.25)
text(d, 18, 546, '사운드', 15, (0x8A, 0x8A, 0x8A, 255))
text(d, 480, 546, '■  멈춤', 15, (0x7A, 0x7A, 0x7A, 255), 600)

out = Image.new('RGB', (1024, 576 * 3 + 16), (40, 40, 40))
for i, im in enumerate((L, D, S)):
    out.paste(im.convert('RGB'), (0, i * (576 + 8)))
out.save(outp)
print('->', outp)
