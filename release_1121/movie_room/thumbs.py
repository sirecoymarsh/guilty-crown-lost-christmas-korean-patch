"""11-24 영상 감상을 썸네일 꼴로 + 빠진 영상(사용자 「영상을 썸네일 형식으로. 그리고 영상 더 있지 않아?」).
- 원작의 이야기 영상은 넷: 오프닝(lx9999)·아이캐치(lx0109 등)·2장 영상(lx0201)·5장 영상(lx0506, dx/mv_bikeend.ngs).
  그 밖의 dx 영상(mv_edcamo·mv_eddash·mv_efvd*·mv_void*·mv_select*·집중선)은 장면에 겹쳐 쓰는 효과 조각이라 감상 목록에 넣지 않는다.
- 꼴: 원작 CG 감상(cglib)의 모양을 빌린다 — 검은 바탕에 회색 1px 칸 테(모서리 눈금·가운데 점), 칸 아래쪽 검은 띠에 흰 제목,
  올림은 흰 1px 테(모서리를 깎은 원작 선택 커서 꼴). 회상 화면과 같은 말투. 2x2 큰 칸(420x236, 16:9).
- 열림: 5장 영상 = #lx0506_mv00(원작 MovieSkipPlay 가 켬) 또는 lx0506 끝까지 읽음 또는 「모두 열기」. 잠긴 칸은 그림 없이 자물쇠(회상과 같은 그림).
- 썸네일은 자막 없는 장면에서 뽑는다(thumb_candidates.py 로 후보를 보고 고름). 2장·5장 그림은 사용자 진도 밖이니 대화에 보이지 말 것.
- 기존 kr_movie.nss(코덱스 가사판의 KrLyStopFor 포함)를 그 자리에서 고친다.
"""
import io, re
from pathlib import Path
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent
K = 'cp949'
S = 4
# 11-24 오후: 1장 전투 영상(lx0106 dx/mvbattle0106.ngs)을 더해 다섯 — 이야기 순서로, 위 셋·아래 둘(가운데).
# (위에서 「원작 이야기 영상은 넷」이라 적은 것은 틀림: MovieSkipPlay 로 트는 이야기 영상은 lx0106·lx0201 둘 + 오프닝·5장 영상.
#  사용자 「스크루지가 엔드레이브를 부수는 장면이 영상에도 없다」로 찾음.)
CW, CH = 304, 171
SLOTS = [(32, 82), (360, 82), (688, 82), (196, 301), (524, 301)]
VIDEOS = [  # (제목, 썸네일 후보 파일, 고르면 할 일, 열림 줄들)
    ('오프닝', 'op_1.png',
     'KmBegin();CreateMovie("km_mv",31000,center,middle,false,false,"dx/mv_op.ngs");KmWaitMovie();',
     ['if(#mvOPplay){$KM_OK1=true;}']),
    ('1장 · 엔드레이브 격파', 'lx0106_7.png',   # 영상 속 내용대로(17.2초 베어 가르는 장면)
     'KmBegin();CreateMovie("km_mv",31000,center,middle,false,false,"dx/mvbattle0106.ngs");KmWaitMovie();',
     ['// 11-24 1장 전투 영상(lx0106 끝): 원작 MovieSkipPlay 가 #lx0106_mv01 을 켠다',
      'if(#lx0106_mv01){$KM_OK2=true;}',
      'if(!$KM_OK2){$kc_r=Conquest("nss/lx0106.nss","lx0106.nss",null);if($kc_r){$KM_OK2=true;}}']),
    ('아이캐치', 'eyecatch_5.png',
     'KmBegin();KmEyecatch();',
     ['if($KM_OK4){$KM_OK3=true;}',
      'if(!$KM_OK3){$kc_r=Conquest("nss/lx0109.nss","lx0109.nss",null);if($kc_r){$KM_OK3=true;}}',
      'if(!$KM_OK3){$kc_r=Conquest("nss/lx0300.nss","lx0300.nss",null);if($kc_r){$KM_OK3=true;}}',
      'if(!$KM_OK3){$kc_r=Conquest("nss/lx0500.nss","lx0500.nss",null);if($kc_r){$KM_OK3=true;}}']),
    ('2장 · 세피라 게노믹스', 'lx0201_2.png',   # 11-24 사용자 「2장 영상, 5장 영상에서 적당한 제목을 붙여줘」: 영상 속 내용대로
     'KmBegin();CreateMovie("km_mv",31000,center,middle,false,false,"dx/mv_lx0201.ngs");KmWaitMovie();',
     ['if(#lx0201_mv01){$KM_OK4=true;}']),
    ('5장 · 불길 속 질주', 'lx0506_3.png',        # (열리기 전엔 제목 없이 「아직 보지 않은 영상」)
     'KmBegin();CreateMovie("km_mv",31000,center,middle,false,false,"dx/mv_bikeend.ngs");KmWaitMovie();',
     ['// 11-24 5장 영상(lx0506): 원작 MovieSkipPlay 가 #lx0506_mv00 을 켠다',
      'if(#lx0506_mv00){$KM_OK5=true;}',
      'if(!$KM_OK5){$kc_r=Conquest("nss/lx0506.nss","lx0506.nss",null);if($kc_r){$KM_OK5=true;}}']),
]
CALC_ORDER = [1, 2, 4, 3, 5]   # 아이캐치(3)는 2장 영상(4)이 열렸는지를 보므로 4 를 먼저 셈
FRAME = (38, 38, 38, 255)   # 원작 cglib 바탕의 칸 테 색


def bg_png():
    im = Image.new('RGBA', (1024 * S, 576 * S), (0, 0, 0, 255)); d = ImageDraw.Draw(im)
    for x, y in SLOTS:
        x0, y0, x1, y1 = (x - 1) * S, (y - 1) * S, (x + CW + 1) * S, (y + CH + 1) * S
        d.rectangle((x0, y0, x1 - 1, y1 - 1), outline=FRAME, width=S)
        for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):       # 모서리 눈금(원작처럼 조금 더 진한 점)
            d.rectangle((cx - 2 * S, cy - 2 * S, cx + S, cy + S), fill=(60, 60, 60, 255))
        mx, my = (x + CW // 2) * S, (y + CH // 2) * S
        d.rectangle((mx - S, my - S, mx + S, my + S), fill=(60, 60, 60, 255))
    b = io.BytesIO(); im.save(b, format='PNG', optimize=True); return b.getvalue()


def cursor_png():
    """원작 선택 커서(192x108, 흰 1px 테, 모서리 깎임)를 큰 칸 크기로 다시 그림(선 굵기는 그대로 1px)."""
    w, h = CW * S, CH * S
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = 3 * S   # 깎인 모서리
    pts = [(c, 0), (w - 1 - c, 0), (w - 1, c), (w - 1, h - 1 - c), (w - 1 - c, h - 1), (c, h - 1), (0, h - 1 - c), (0, c), (c, 0)]
    d.line(pts, fill=(255, 255, 255, 255), width=S)
    b = io.BytesIO(); im.save(b, format='PNG', optimize=True); return b.getvalue()


def thumb_jpg(name):
    im = Image.open(HERE / 'thumbs_work' / name).convert('RGB').resize((CW * S, CH * S), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, format='JPEG', quality=90, optimize=True); return b.getvalue()


def assets():
    out = {'kr_mov_bg2.png': bg_png(), 'kr_mov_cur.png': cursor_png()}
    for k, v in enumerate(VIDEOS, 1):
        out[f'kr_mth{k:02d}.jpg'] = thumb_jpg(v[1])
    return out


def _tex(name, prio, x, y, path, zoom=250):
    return (f'\t\tCreateTexture("{name}",{prio},{x},{y},"{path}");\r\n'
            f'\t\tSetVertex("{name}",0,0);\r\n\t\tZoom("{name}",0,{zoom},{zoom},null,false);\r\n\t\tRequest("{name}",Smoothing);\r\n')


def _card(k, title):
    x, y = SLOTS[k - 1]
    lock_zoom = round(250 * CW / 192)          # 회상 자물쇠 그림(4배 768x432)을 큰 칸에
    return (f'\tif($KM_OK{k}){{\r\n'
            f'\t\tCreateChoice("km_r{k:02d}");\r\n'
            f'\t\tCreateColor("km_r{k:02d}/MouseUsual/hit",2010,{x},{y},{CW},{CH},0x000000);\r\n'
            f'\t\tRequest("km_r{k:02d}/MouseUsual/hit",Erase);\r\n'
            + _tex(f'km_lth{k:02d}', 2010, x, y, f'nss/kr_mth{k:02d}.jpg') +
            f'\t\tCreateColor("km_lbd{k:02d}",2011,{x},{y + CH - 32},{CW},32,0x000000);\r\n'
            f'\t\tFade("km_lbd{k:02d}",0,650,null,false);\r\n'
            f'\t\tSetFont("Noto Sans KR", 17, FFFFFF, 000000, 500, RIGHTDOWN);\r\n'
            f'\t\tKmText("km_lt{k:02d}",2012,{x + 12},{y + CH - 29},{CW - 24},26,"{k:02d}  {title}");\r\n'
            + _tex(f'km_r{k:02d}/MouseOver/img', 2013, x, y, 'nss/kr_mov_cur.png')
            + _tex(f'km_r{k:02d}/MouseClick/img', 2013, x, y, 'nss/kr_mov_cur.png') +
            f'\t}}else{{\r\n'
            # 잠긴 칸: 빈 칸 테만(회상 자물쇠 그림은 「읽지 않음」 글자가 박혀 있어 영상엔 안 맞음) + 가운데 회색 글
            f'\t\tSetFont("Noto Sans KR", 16, 5A5A5A, 000000, 500, RIGHTDOWN);\r\n'
            f'\t\tKmText("km_lt{k:02d}",2012,{x + CW // 2 - 76},{y + CH // 2 + 14},200,26,"아직 보지 않은 영상");\r\n'
            f'\t}}\r\n')


def patch_room(b: bytes) -> bytes:
    def one(old, new):
        nonlocal b
        o, n = old.encode(K), new.encode(K)
        assert b.count(o) == 1, (old[:60], b.count(o))
        b = b.replace(o, n)
    # 바탕: 사운드 줄 꼴 → CG 감상 꼴 큰 칸
    one('CreateTexture("km_lbg",2001,0,0,"nss/kr_mov_bg.png");', 'CreateTexture("km_lbg",2001,0,0,"nss/kr_mov_bg2.png");')
    # 줄 셋 → 카드 넷
    a = b.index('\tif($KM_OK1){'.encode(K)); z = b.index('\tFade("*/MouseOver/*",0,0,null,false);'.encode(K), a)
    b = b[:a] + ''.join(_card(k, v[0]) for k, v in enumerate(VIDEOS, 1)).encode(K) + b[z:]
    # 고르기: 원래 세 줄(km_r01~03)을 통째로 다섯으로(이야기 순서로 번호가 바뀜)
    a = b.index('\t\t\tcase km_r01{'.encode(K)); z = b.index('\t\t\tcase KM_EXIT{'.encode(K), a)
    b = b[:a] + ''.join(f'\t\t\tcase km_r{k:02d}{{Request("@km_se_ok",Play);{v[2]}$KM_LOOP=false;}}\r\n'
                        for k, v in enumerate(VIDEOS, 1)).encode(K) + b[z:]
    # 열림: KmCalc 본문을 통째로
    a = b.index('function KmCalc()\r\n{\r\n'.encode(K)) + len('function KmCalc()\r\n{\r\n'.encode(K))
    z = b.index('\r\n}'.encode(K), a) + 2
    body = ''
    for k in CALC_ORDER:
        body += f'\t$KM_OK{k}=false;if(#KS_ALLOPEN){{$KM_OK{k}=true;}}\r\n' + ''.join(f'\t{x}\r\n' for x in VIDEOS[k - 1][3])
    b = b[:a] + body.encode(K) + b[z:]
    one('//■ 목록: 세 줄, 아래 줄 = 영상 · 닫기', '//■ 목록: 칸 다섯(11-24 썸네일 - 원작 CG 감상 꼴, 위 셋·아래 둘), 아래 줄 = 영상 · 닫기')
    return b
