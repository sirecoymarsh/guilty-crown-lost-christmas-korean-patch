"""J·K 를 누른 그 대사에서 바로 말 바꾸기(사용자 11-24 「일본어 전환이 실시간이 아니라 로딩이 끝나고 되네?」→「이거 어떻게 바꿀 수
없을까? 해당 구역 로딩된건 바뀌지 않네」, 이어서 「K를 누르면 한국어, JJ를 누르면 일한 병기, KK를 누르면 한일 병기로 고쳐줘.
J 일본어, 그 상태에서 J를 한번 더 누르면 일한 병기, 그 상태에서 J를 한번 더 누르면 다시 한국어. K도 마찬가지.」).
상태 #KR_JP: 0 한국어 · 1 일본어 · 2 일한 병기(일본어 위) · 3 한일 병기(한국어 위). DLL(kr_keys.inc)이 J·K 로 돌린다.

jp_twin.py 가 SetText(); TypeBegin(0); 덩어리(1,432개)마다 온전한 글 넷을 싣는다:
  $KR_IA·$KR_IB = 교차 글의 한 쪽 최대 줄 수
  [mtext] 일한 교차 → KrAltIJ();  [ntext] 한일 교차 → KrAltIK();
  if(#KR_JP==1||#KR_JP==2){ [ptext] 한국어 → KrAltFK(); [jtext] 일본어 } else { [qtext] 일본어 → KrAltFJ(); [text] 한국어 }
- 넷 중 지금 상태의 것 하나만 타이핑한다(KrJBegin: $textnumber 를 그것으로). 음성·덩어리 안 코드·쪽 기다림·대사 기록은 타이핑하는
  쪽에서만 일어난다. 나머지는 Enter 하지 않는다(안 그려짐·기록 안 됨·코드 안 돎).
- 병기 = 한 문장씩 교차(사용자 11-24 「가능하면 한 문장씩 교차하는 형식으로 만들어주겠어」): 앞 말 덩어리(음성·코드·쪽·<K> 그대로)의
  문장마다 바로 아래 다른 말 문장, 그다음 <K>(jp_twin.interleave). 쪽 최대 줄이 4줄을 넘으면 위로 올리고(줄 40px) 창 위로 올라간 만큼
  검은 받침(kr_biback.png, 별칭 boxKB).
- 대사 도중 J·K: KrJSwapTick 이 #KR_JP 바뀜을 보면 ExistSave(-947004)(DLL: 이 대사 시작 체크포인트를 꺼내 둠) → Load(-947002) 로
  그 대사를 처음부터 다시 — TypeBegin 시작에서 이어지며 KrJBegin 이 새 상태로 고른다. 체크포인트가 없으면 다음 대사부터.
- 그 밖의 덩어리(SetTextM 등 25곳)는 전처럼 다음 덩어리부터(병기 상태에서는 앞 말 하나만).
시험에서 안 것: Enter 안 한 글은 안 그려짐(js1) · 둘 다 <K> 에서 기다리면 Enter 에 멈춤(js2) · 엔진 식은 곱셈 우선이 없는 듯(js2) ·
그림(Texture)의 Move 는 변수 좌표면 안 보임 → 상수(js4) · 두 글이 쪽 기다림을 가지면 클릭을 번갈아 가져감(js4).
"""
# 받침 자리: 줄 수마다 상수(위 참고). 첫 줄 Y0 = 400-40(T-4), 받침 꼭대기 = Y0-56 = 504-40T. 13줄 넘으면 0.
def _biback_rows(pitch):
    rows = []
    for t in range(1, 21):
        y0 = min(400, 536 - pitch * t)     # 맨 아래 줄이 키 목록(554)에 닿지 않게 536 까지(js9)
        if y0 < 400:
            rows.append((t, max(0, y0 - 56)))
    return rows


# 받침 자리: 그림(Texture)은 Move 에 변수 좌표를 주면 안 보였다(js4) → 줄 수마다 상수로. 교차 글 줄 간격은 28px,
# 루비가 있는 덩어리만 40px(11-24). 첫 줄 Y0 = min(400, 536-간격*n), 받침 꼭대기 = Y0-56.
def _bb_moves(rows):
    return 'else '.join('if($KR_TOT==%d){Move("@boxKB",0,0,%d,null,false);}' % (t, yb) for t, yb in rows) + 'else{Move("@boxKB",0,0,0,null,false);}'


BIBACK_MOVE = ('\t\tif($KR_Y0<400){\r\n'
               '\t\t\tif($KR_IRB==1){' + _bb_moves(_biback_rows(40)) + '}\r\n'
               '\t\t\telse{' + _bb_moves(_biback_rows(28)) + '}\r\n'
               '\t\t\tFade("@boxKB",0,1000,null,false);\r\n'
               '\t\t}else{Fade("@boxKB",0,0,null,false);}\r\n')
FUNCS = (
    '\r\n// Claude 11-24: J/K story language. #KR_JP: 0 Korean, 1 Japanese, 2 Japanese over Korean, 3 Korean over Japanese.\r\n'
    '// Each standard line carries a full Korean and a full Japanese text (only one is typed) and a stripped copy of each\r\n'
    '// (no voice, code, waits or pages) shown under/over the typed one in the bilingual states. See sound_seek/jp_swap.py.\r\n'
    'function KrAltLoad()\r\n{\r\n'
    '\tSetMainTextFont();\r\n'
    '\tLoadText($構文名,$SYSTEM_present_preprocess,$SYSTEM_present_text,800,$KR_AH,0,$KR_AL);\r\n'
    '\tMove($SYSTEM_present_text, 0, 127, 400, null, true);\r\n'
    '\tRequest($SYSTEM_present_text, Erase);\r\n'
    '\tRequest($SYSTEM_present_text, Lock);\r\n'
    '\tRequest($SYSTEM_present_text, Hideable);\r\n'
    '\tFade($SYSTEM_present_text, 0, 0, null, false);\r\n'
    '}\r\n'
    'function KrAltIJ()\r\n{\r\n\t$KR_IJ=$SYSTEM_present_text;$KR_AH=560;if($KR_IRB==1){$KR_AL=40;}else{$KR_AL=28;}KrAltLoad();$KR_PASSON=true;\r\n}\r\n'
    'function KrAltIK()\r\n{\r\n\t$KR_IK=$SYSTEM_present_text;$KR_AH=560;if($KR_IRB==1){$KR_AL=40;}else{$KR_AL=28;}KrAltLoad();\r\n}\r\n'
    'function KrAltFK()\r\n{\r\n\t$KR_FK=$SYSTEM_present_text;$KR_PRESJ=1;$KR_AH=150;$KR_AL=40;KrAltLoad();\r\n}\r\n'
    'function KrAltFJ()\r\n{\r\n\t$KR_FJ=$SYSTEM_present_text;$KR_PRESJ=0;$KR_AH=150;$KR_AL=40;KrAltLoad();\r\n}\r\n'
    'function KrJBegin()\r\n{\r\n'
    '\tif($KR_PRESJ==1){$KR_FJ=$textnumber;}else{$KR_FK=$textnumber;}\r\n'
    '\t$KR_APPLIED=#KR_JP;$KR_PT=0;\r\n'
    '\tif($KR_APPLIED==1){$textnumber=$KR_FJ;}\r\n'
    '\telse if($KR_APPLIED==2){$textnumber=$KR_IJ;$KR_PT=$KR_IA;}\r\n'
    '\telse if($KR_APPLIED==3){$textnumber=$KR_IK;$KR_PT=$KR_IB;}\r\n'
    '\telse{$textnumber=$KR_FK;}\r\n'
    '\tFade($KR_FK,0,0,null,false);Fade($KR_FJ,0,0,null,false);Fade($KR_IJ,0,0,null,false);Fade($KR_IK,0,0,null,false);\r\n'
    '\tFade($textnumber,0,1000,null,false);\r\n'
    '\tRequest($textnumber, Enter);\r\n'
    '\tKrJLayout();\r\n'
    '\t$KR_JSW_RUN=true;CreateProcess("krJswap",150,0,0,"KrJSwapTick");SetAlias("krJswap","krJswap");Request("krJswap",Lock);Request("@krJswap",Start);\r\n'
    '}\r\n'
    'function KrJLayout()\r\n{\r\n'
    '\tif($KR_APPLIED==2||$KR_APPLIED==3){\r\n'
    '\t\t// interleaved text: 28px lines (40px when the block has ruby, $KR_IRB); the tallest page decides how far it rises (bottom 536).\r\n'
    '\t\t// one binary operation per statement (the original scripts never lean on * before - precedence)\r\n'
    '\t\t$KR_Y0=400;$KR_TOT=$KR_PT;\r\n'
    '\t\tif($KR_IRB==1){$KR_Y0=$KR_TOT*40;}else{$KR_Y0=$KR_TOT*28;}$KR_Y0=536-$KR_Y0;if($KR_Y0>400){$KR_Y0=400;}\r\n'
    '\t\tMove($textnumber,0,127,$KR_Y0,null,false);\r\n'
    '\t\t// dark backdrop under the lines that rise above the text window (bright scenes)\r\n'
    + BIBACK_MOVE +
    '\t}else{\r\n'
    '\t\tMove($textnumber,0,127,400,null,false);Fade("@boxKB",0,0,null,false);\r\n'
    '\t}\r\n'
    '}\r\n'
    'function KrJSwapTick()\r\n{\r\n'
    '\twhile($KR_JSW_RUN){\r\n'
    '\t\t$KR_MODE=#KR_JP;\r\n'
    '\t\tif($KR_MODE!=$KR_APPLIED){\r\n'
    '\t\t\t$KR_APPLIED=$KR_MODE;\r\n'
    '\t\t\t// restart this line in the new state: the DLL stages this line\'s checkpoint, then the backlog-jump load\r\n'
    '\t\t\tif(ExistSave(-947004)){$KR_JSW_RUN=false;Load(-947002);}\r\n'
    '\t\t}\r\n'
    '\t\tWait(50);\r\n'
    '\t}\r\n'
    '}\r\n')

START = ('\tRequest($textnumber, Enter);\r\n',
         '\tif($KR_PASSON){KrJBegin();}else{Request($textnumber, Enter);}\r\n')
END = ('\tFade($textnumber, 0, 0, null, true);\r\n',
       '\tFade($textnumber, 0, 0, null, true);\r\n'
       '\tif($KR_PASSON){$KR_JSW_RUN=false;Request("@krJswap",UnLock);Delete("@krJswap");'
       + ''.join('if(%s!=$textnumber){Request(%s,UnLock);Delete(%s);}' % (v, v, v) for v in ('$KR_FK', '$KR_FJ', '$KR_IJ', '$KR_IK')) +
       '$KR_PASSON=false;Fade("@boxKB",0,0,null,false);}\r\n')
# 병기 받침: LoadBox 에서 대사창과 한 묶음으로(별칭 boxKB → TypeBegin 의 Fade("@box*") 와 Space 숨기기를 따름). 대사창 그림(19000~) 아래 18990.
BIBACK = ('\tFade("krKeyBar",0,0,null,false);\r\n',
          '\tFade("krKeyBar",0,0,null,false);\r\n'
          '\t// Claude 11-24: dark backdrop for the bilingual modes (KrJLayout shows it when the lines rise above the window)\r\n'
          '\tCreateTexture("krBiBack", 18990, 0, 0, "nss/kr_biback.png");\r\n'
          '\tSetAlias("krBiBack","boxKB");\r\n\tRequest("krBiBack", Lock);\r\n\tRequest("krBiBack", Hideable);\r\n'
          '\tFade("krBiBack",0,0,null,false);\r\n')


def biback_png() -> bytes:
    """1024x576 검정: 위 56px 는 투명→55%, 그 아래는 55%(아래로 화면 밖까지 이어져 끝 경계가 안 보인다)."""
    import io
    from PIL import Image
    im = Image.new('RGBA', (1024, 576), (0, 0, 0, 0))
    a = Image.new('L', (1, 576))
    for y in range(576):
        t = min(1.0, y / 56)
        a.putpixel((0, y), round(140 * t * t * (3 - 2 * t)))
    im.putalpha(a.resize((1024, 576)))
    out = io.BytesIO(); im.save(out, format='PNG', optimize=True); return out.getvalue()


# 11-24 병기 비표준 덩어리 중 4~6줄(jp_twin $KR_TALL): 원래 글 칸(높이 150·줄 40)에 안 들어가 쪽이 갈릴 수 있어 앞 말만 보였다
# (사용자가 본 첫 장면 가운데 날짜 글). 그 덩어리만 줄 간격 28(루비 40)·높이 = 줄 수 × 간격 + 12, 대사창 글(Y 400)은 아래 536 에 맞춰 올린다.
TALL_OLD = '\t\tLoadText($構文名,$SYSTEM_present_preprocess,$SYSTEM_present_text,$LoadTextWsize,$LoadTextHsize,0,40);\r\n'
TALL_NEW = ('\t\t// Claude 11-24: bilingual non-standard blocks of 4-6 lines (jp_twin sets $KR_TALL = lines, $KR_TRB = ruby):\r\n'
            '\t\t// tighter pitch and a box as tall as the lines; window text is raised so its bottom stays at 536\r\n'
            '\t\tif($KR_TALL>0){\r\n'
            '\t\t\t$kxTP=28;if($KR_TRB){$kxTP=40;}\r\n'
            '\t\t\t$kxTH=$KR_TALL*$kxTP;$kxTH=$kxTH+12;\r\n'
            '\t\t\tif($SetTextY==400){$kxTY=536-$kxTH;if($kxTY<400){$SetTextY=$kxTY;}}\r\n'
            '\t\t\tLoadText($構文名,$SYSTEM_present_preprocess,$SYSTEM_present_text,$LoadTextWsize,$kxTH,0,$kxTP);\r\n'
            '\t\t\t$KR_TALL=0;$KR_TRB=0;\r\n'
            '\t\t}else{\r\n'
            '\t' + TALL_OLD +
            '\t\t}\r\n')


def patch_function(fn: bytes) -> bytes:
    E = 'cp932'
    assert fn.count(TALL_OLD.encode(E)) == 1
    fn = fn.replace(TALL_OLD.encode(E), TALL_NEW.encode(E))
    i = fn.index('function TypeBegin()'.encode(E))
    j = fn.index(b'\r\nfunction ', i + 10)
    body = fn[i:j]
    for a, b in (START, END):
        assert body.count(a.encode(E)) == 1, a
        body = body.replace(a.encode(E), b.encode(E))
    fn = fn[:i] + body + fn[j:]
    assert fn.count(BIBACK[0].encode(E)) == 1
    fn = fn.replace(BIBACK[0].encode(E), BIBACK[1].encode(E))
    return fn.rstrip() + b'\r\n' + FUNCS.encode(E)
