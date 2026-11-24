"""화면 맨 아래 키 목록(사용자 11-24 「화면 최하단에 키보드 단축키 메뉴를 표시하게 해줘」 + 「H키를 배정해 그것만 키 리스트 숨기기로」).
- 그림 nss/kr_keybar.png(4096x80 = 엔진 1024x20, 25% 로 그림): 키는 청록 글자의 작은 키 모양, 뜻은 회색.
- 대사창(function.nss LoadBox 의 box01~03, y=388)과 같은 묶음: 별칭 boxKK + Lock + Hideable → 장면이 Fade("@box*") 로
  창을 지우면 같이 사라지고, Space(창 숨기기)에도 같이 숨는다. 글자 칸(400~550) 아래 y=554. 매 대사(TypeBegin)에 창과 같이 나타남.
- H 와 J 는 대본이 아니라 DLL(engine/src/kr_keys.inc)이 받는다: SetShortcut("H") 는 엔진 칸이 모자라 불리지 않았고(시험 kb3),
  대본 프로세스로 $SYSTEM_keydown_h 를 보는 길도 서지 않았다(kb4~6). DLL 은 H 면 이 그림만 안 그리고(n2hd-options.ini [Display] KeyBar),
  J 면 #KR_JP 를 뒤집는다(대사 기다리는 중·대사 기록/메뉴가 닫혀 있을 때만).
"""
import io
from PIL import Image, ImageDraw, ImageFont
KO = r'P:\AI\gclx-codexrun\game\fonts\NotoSansKR-VF.ttf'
KEYS = [('Enter', '다음'), ('Ctrl', '넘기기'), ('A', '자동'), ('B', '대사 기록'), ('S', '저장'), ('L', '불러오기'),
        ('M', '메뉴'), ('C', '설정'), ('F', '전체 화면'), ('F8', '화질'), ('Space', '창 숨기기'), ('J', '일본어'), ('K', '한국어'), ('H', '목록 숨기기')]
TEAL = (139, 233, 215, 255); GRAY = (178, 178, 178, 255); CAP = (22, 40, 38, 235); EDGE = (58, 95, 90, 255)


def render(keys=KEYS) -> bytes:
    S = 4
    fk = ImageFont.truetype(KO, 12 * S); fk.set_variation_by_axes([600])
    fl = ImageFont.truetype(KO, 13 * S); fl.set_variation_by_axes([500])
    W, H = 1024 * S, 20 * S
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    padx, gap_cap, gap_item = 5 * S, 4 * S, 9 * S
    parts = []
    for k, lab in keys:
        kw = d.textlength(k, font=fk) + 2 * padx; lw = d.textlength(lab, font=fl)
        parts.append((k, lab, kw, lw))
    total = sum(kw + gap_cap + lw for _, _, kw, lw in parts) + gap_item * (len(parts) - 1)
    x = (W - total) / 2; cy = H / 2
    for k, lab, kw, lw in parts:
        d.rounded_rectangle((x, 2 * S, x + kw, H - 2 * S), radius=3 * S, fill=CAP, outline=EDGE, width=S)
        d.text((x + kw / 2, cy), k, font=fk, fill=TEAL, anchor='mm')
        x += kw + gap_cap
        d.text((x, cy), lab, font=fl, fill=GRAY, anchor='lm')
        x += lw + gap_item
    assert total < W - 8 * S, total / S
    out = io.BytesIO(); im.save(out, format='PNG'); return out.getvalue()


LOADBOX_ADD = ('\tRequest("BoxMask01/box03", Hideable);\r\n',
               '\tRequest("BoxMask01/box03", Hideable);\r\n'
               '\t// Claude 11-24: key list at the bottom (hides with the text box; the DLL skips drawing it while H has it off)\r\n'
               '\tCreateTexture("krKeyBar", 19020, 0, 554, "nss/kr_keybar.png");\r\n'
               '\tSetVertex("krKeyBar",0,0);\r\n\tZoom("krKeyBar",0,250,250,null,false);\r\n\tRequest("krKeyBar",Smoothing);\r\n'
               '\tSetAlias("krKeyBar","boxKK");\r\n\tRequest("krKeyBar", Lock);\r\n\tRequest("krKeyBar", Hideable);\r\n'
               '\tFade("krKeyBar",0,0,null,false);\r\n'
               # 11-24 회상 다시 보기 판(저장·불러오기 칸을 어둡게 긋은 그림, 별칭 boxKQ) — 사용자 「회상 모드에선 작동하지 않는 S 키 …」
               '\tCreateTexture("krKeyBarRp", 19020, 0, 554, "nss/kr_keybar_rp.png");\r\n'
               '\tSetVertex("krKeyBarRp",0,0);\r\n\tZoom("krKeyBarRp",0,250,250,null,false);\r\n\tRequest("krKeyBarRp",Smoothing);\r\n'
               '\tSetAlias("krKeyBarRp","boxKQ");\r\n\tRequest("krKeyBarRp", Lock);\r\n\tRequest("krKeyBarRp", Hideable);\r\n'
               '\tFade("krKeyBarRp",0,0,null,false);\r\n')
TYPEBEGIN = ('\tFade("@box03",$BoxFadeTime,1000,null,false);\r\n',
             '\tFade("@box03",$BoxFadeTime,1000,null,false);\r\n'
             '\tif($KR_REPLAY){Fade("@boxKQ",$BoxFadeTime,1000,null,false);}else{Fade("@boxKK",$BoxFadeTime,1000,null,false);}\r\n')

def patch_oldsave(fn: bytes) -> bytes:
    """11-24 사용자 「현재 플레이 카피에서 하단 커맨드바가 안뜨는데 이유가 뭘까?」:
    LoadBox 는 SystemInit 의 if(!$BOX_Init) 안에서만 돈다. $BOX_Init 은 세이브에 담기므로 키 목록을 넣기 전 세이브를 불러오면
    LoadBox 가 다시 돌지 않아 키 목록·병기 받침이 생기지 않는다(패치 1.0 세이브를 쓰는 사람도 마찬가지).
    → 한국어판이 LoadBox 에 더한 그림(키 목록 둘·병기 받침)을 KrBoxAdd() 로 떼어 내고, 따로 된 깃발 $KR_BOX1124 로
    대사마다(TypeBegin 머리) 없으면 만든다. 새 그림을 LoadBox 에 더하면 깃발 이름도 바꿀 것."""
    E = 'cp932'
    a = '\t// Claude 11-24: key list at the bottom'.encode(E)
    z = '\tFade("krKeyBarRp",0,0,null,false);\r\n'.encode(E)   # 순서: 키 목록 → (병기 받침) → 회상판 키 목록
    assert fn.count(a) == 1 and fn.count(z) == 1
    i = fn.index(a); j = fn.index(z) + len(z)
    block = fn[i:j]
    for must in ('krKeyBar"', 'krBiBack', 'krKeyBarRp'):
        assert must.encode(E) in block, must
    fn = fn[:i] + '\t// Claude 11-24: the Korean edition box extras (key lists, bilingual backdrop) are made by KrBoxAdd (old saves too)\r\n'.encode(E) + fn[j:]
    chk = '\tif(!$KR_BOX1124){KrBoxAdd();$KR_BOX1124=true;}\r\n'.encode(E)
    n = fn.count(TYPEBEGIN[1].encode(E))
    assert n == 4, n
    fn = fn.replace(TYPEBEGIN[1].encode(E), chk + TYPEBEGIN[1].encode(E))
    return fn.rstrip() + b'\r\n\r\n' + '// Claude 11-24: made apart from LoadBox - $BOX_Init comes back from old saves and would skip them\r\nfunction KrBoxAdd()\r\n{\r\n'.encode(E) + block + b'}\r\n'


# 회상(다시 보기)에서 안 되는 키: 저장·불러오기($SYSTEM_save_lock·load_lock, kr_scenario KsPlay)
REPLAY_OFF = ('S', 'L')
# #KR_JP 를 숫자로 만들어 둔다(DLL 이 +0x10 의 double 만 뒤집는다). 0_boot 의 SetShortcut 줄 앞에.
BOOT_JP = ('\tSetShortcut("M", "nss/sys_menu.nss");', '\tif(!#KR_JP){#KR_JP=false;}\r\n\tSetShortcut("M", "nss/sys_menu.nss");')


if __name__ == '__main__':
    import sys
    open(sys.argv[1], 'wb').write(render())
