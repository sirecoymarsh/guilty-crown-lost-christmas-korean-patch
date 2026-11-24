"""사운드 화면 곡 제목 풀이(사용자 11-24 「원작에서 저게 무슨 의미가 있는지 해석을 하단 하얀 바에 플로팅으로 띄워줘. VOiD 같은거나 오메가 바이오스 뮤」).
열린 곡 줄에 커서를 올리면 아래 흰 띠 왼쪽(「사운드」 자리)에 그 제목의 뜻이 떠오른다. 줄에서 벗어나면 「사운드」로 돌아온다.
- 곡 이름은 원작 애니메이션 사운드트랙(사와노 히로유키) 제목. 18·19 는 이 게임의 결말 노래.
- 작품 속 낱말과 이어지는 풀이는 그 낱말이 이 게임에 처음 나온 장면을 읽은 뒤에만(스포일러 막기):
  보이드 = lx0206(「보이드 게놈」), 아포칼립스 = lx0103(「아포칼립스 바이러스」).
- 11-24 사용자 「사운드 모드 반응이 굉장히 느린데?」: 커서를 옮길 때마다 엔진 글(CreateText)을 새로 만들면 곡이 나오는 동안
  화면이 1~2초씩 멈췄다(숨긴 시험, 곡+커서 28초: 풀이 있는 판 0.6초 넘는 멈춤 8번 10.2초, 글 만들기만 뺀 판 2번, 틱 100ms 판 6번).
  → 풀이와 「사운드」 글을 미리 그림(4배, Zoom 250)으로 그려 두고 그림만 바꾼다(가사 그림처럼 곡이 나오는 동안 바꿔도 멈추지 않는다).
"""
from pathlib import Path

# (번호, 기본 풀이, (읽어야 할 장면, 그 뒤 풀이) 또는 None)
# 11-24 오후 사용자가 넘긴 새 문안(다른 에이전트 「제목 본뜻 + 게임 속 상징·연출 의미」 19곡, 14px 424px 안)으로 바꿈.
# 곡 이름 글자는 게임 표기 그대로(gェ19·κrOnё·Rё∀L - 문안의 gエ19·κrOnë·Rë∀L 는 줄 제목과 맞춤). 05 는 lx0206, 14 는 lx0603 뒤 문구.
HINTS = [
    (1, 'βios ― ‘생명’ · 캐롤에게서 보이드를 뽑아 쓰는 각성 테마', None),
    (2, 'Ω ― ‘오메가(종말)’ · 파국으로 치닫는 괴물들의 사투 테마', None),
    (3, 'Ready to Go ― ‘출격 완료’ · 포위망 돌파와 다아트 심문 테마', None),
    (4, 'ƒriends ― ‘동료들’ · 트리톤이 ‘장의사’ 리더 가이로 서는 테마', None),
    (5, 'VOiD ― ‘공허’ 속 작은 자아(i) · 상실된 기억과 텅 빈 내면',
        ('lx0206', 'VOiD ― ‘공허’ 속 작은 자아(i) · 물질화한 영혼, 보이드의 비밀')),
    (6, 'gェ19 ― ‘GHQ’의 문자 암호 · 배후 결사 다아트의 음모와 실험', None),
    (7, 'θεοι ― ‘신들’ · 인간을 벗어난 강화 게놈과 캔서화의 공포', None),
    (8, 'Βασιλευζ ― ‘왕·군주’ · 가짜 왕 스크루지와 프레젠트의 격돌', None),
    (9, 'π ― ‘원주율(끝없는 수)’ · 최종본에서 교체되어 남은 미공개 곡', None),
    (10, 'Release My Soul ― ‘영혼의 해방’ · 속죄 루트 구원의 클라이맥스', None),
    (11, 'κrOnё ― ‘왕관(Krone)’ · 고독한 왕과 무기가 맺는 숙명의 유대', None),
    (12, 'Hill Of Sorrow ― ‘슬픔의 언덕’ · 실험대에서 깨어난 첫 탈주 테마', None),
    (13, 'Αποκσλυψιζ ― ‘묵시록(아포칼립스)’ · 엔드레이브 강습과 재앙 전투', None),
    (14, 'Home ~in this corner~ ― ‘안식처’ · 찰나의 평온과 따스한 위안',
         ('lx0603', 'Home ~in this corner~ ― ‘안식처’ · 평온한 아침과 코퀴토스의 진실 대비')),
    (15, 'Genesi§ ― ‘규약된 창세(§)’ · 이브 폭주와 성경적 심판의 강림', None),
    (16, 'βιοζ-δ ― ‘생명의 변주(δ)’ · 보이드의 진실 앞에 무너지는 진혼곡', None),
    (17, 'Rё∀L ― ‘모두(∀)의 현실’ · ‘죄의 왕관’으로 세상을 부수는 파멸곡', None),
    (18, 'ISOLATION ― ‘고립·격리’ · 속죄 엔딩곡, 둘이 이어 낸 세계의 구원', None),
    (19, 'Where am I ? ― ‘나는 어디에?’ · 응보 엔딩곡, 자아 상실과 파멸', None),
]
_HINTS_1124 = [   # 오전 판(사전 풀이) - 되돌릴 때
    (1, 'βios  ―  그리스어 비오스 「삶·생명」 · 「바이오」의 뿌리 말', None),
    (2, 'Ω  ―  그리스 문자의 마지막 글자 오메가 「끝·마지막」', None),
    (3, 'Ready to Go  ―  영어 「갈 준비가 됐다·출발 준비 완료」', None),
    (4, 'friends  ―  영어 「친구들·동료들」', None),
    (5, 'VOiD  ―  영어 void 「텅 빈 것·공허」',
        ('lx0206', 'VOiD  ―  영어 「텅 빈 것·공허」 · 작품 속 「보이드 게놈」의 보이드')),
    (6, 'gェ19  ―  로마자 g·가타카나 ェ·숫자 19를 섞은 사와노 식 제목', None),
    (7, 'θεοι  ―  그리스어 테오이 「신들」', None),
    (8, 'Βασιλευζ  ―  그리스어 바실레우스 「왕·임금」', None),
    (9, 'π  ―  그리스 문자 파이 「원주율」 · 끝없이 이어지는 수', None),
    (10, 'Release My Soul  ―  영어 「내 영혼을 놓아 줘」', None),
    (11, 'κrOnё  ―  독일어 Krone 「왕관」 · 제목 Guilty Crown의 Crown', None),
    (12, 'Hill Of Sorrow  ―  영어 「슬픔의 언덕」', None),
    (13, 'Αποκσλυψιζ  ―  그리스어 아포칼립시스 「계시·묵시록」',
         ('lx0103', 'Αποκσλυψιζ  ―  그리스어 「묵시록」 · 작품 속 아포칼립스 바이러스')),
    (14, 'Home ~in this corner~  ―  영어 「집 · 이 한구석에서」', None),
    (15, 'Genesi§  ―  Genesis 「창세기·기원」 · 끝 s 자리에 § 기호', None),
    (16, 'βιοζ-δ  ―  βios를 그리스 글자로 쓰고 델타 δ 「바뀐 판」을 붙임', None),
    (17, 'Rё∀L  ―  REAL 「진짜·현실」 · E는 키릴 문자 ё · A는 뒤집은 ∀', None),
    (18, 'ISOLATION  ―  영어 「고립·홀로 떨어짐」', None),
    (19, 'Where am I ?  ―  영어 「나는 어디에 있는가」', None),
]

X, Y, W, H = 18, 546, 446, 34      # 아래 띠 「사운드」 자리(11-24 오후 430→446: 새 문안 14번 439px — 멈춤 글 x480 앞, 단추 칸 x452 과 겹치는 5px 는 올림 때만)
FONT_PATH = r'P:\AI\Codex\projects\gclx-song-20261123\game\fonts\NotoSansKR-VF.ttf'
LABEL = ('사운드', 15, (0x8A, 0x8A, 0x8A), 0)        # 원래 「사운드」 글(kr_sound.nss KuList: 15·8A8A8A·500, y546)
HINT_STYLE = (14, (0x3A, 0x3A, 0x3A), 4)             # 풀이(엔진 글일 때 14·3A3A3A·500, y547 → 그림 안 4화소(1배 1화소) 아래)


def all_texts():
    for n, base, gate in HINTS:
        yield base
        if gate:
            yield gate[1]


def names() -> dict:
    """그림 이름 → 글. 00 = 「사운드」, NN = 풀이, NNg = 작품 속 뜻까지 쓴 풀이."""
    out = {'kr_hint_00.png': LABEL[0]}
    for n, base, gate in HINTS:
        out[f'kr_hint_{n:02d}.png'] = base
        if gate:
            out[f'kr_hint_{n:02d}g.png'] = gate[1]
    return out


def render(text: str, size: int, col, dy: int) -> bytes:
    import io
    from PIL import Image, ImageDraw, ImageFont
    S = 4
    f = ImageFont.truetype(FONT_PATH, size * S); f.set_variation_by_axes([500])
    im = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    assert d.textlength(text, font=f) <= (W - 6) * S, text
    d.text((S, dy + S), text, font=f, fill=(0xE6, 0xE6, 0xE6, 200), anchor='la')   # 엔진 글의 RIGHTDOWN 밝은 그림자 꼴
    d.text((0, dy), text, font=f, fill=col + (255,), anchor='la')
    out = io.BytesIO(); im.save(out, format='PNG', optimize=True); return out.getvalue()


def assets() -> dict:
    out = {}
    for name, text in names().items():
        size, col, dy = (LABEL[1], LABEL[2], LABEL[3]) if name == 'kr_hint_00.png' else HINT_STYLE
        out[name] = render(text, size, col, dy)
    return out


NSS_HEAD = '''
//★ 곡 제목 풀이(Claude 11-24, 사용자 「원작에서 저게 무슨 의미가 있는지 해석을 하단 하얀 바에 플로팅으로 띄워줘」):
// 열린 곡 줄에 커서를 올리면 아래 흰 띠 왼쪽(「사운드」 자리)에 제목 뜻이 떠오른다. 줄 자리: 왼쪽 x26~502·오른쪽 x524~1000,
// y=58+44k 높이 26. select 안이 아니라 따로 도는 프로세스(곡 단추 누름을 막지 않게).
// 11-24 사용자 「사운드 모드 반응이 굉장히 느린데?」 - 커서를 옮길 때마다 글이나 그림을 새로 만들면 곡이 나오는 동안 1~2초씩 멈췄다
// (프로세스 둘이 같이 만들 때 가장 심함). 그래서 막대 갱신도 이 프로세스가 같이 돌리고, 풀이 그림(kr_hint_*.png)은 목록을 그릴 때
// 이 프로세스가 한 번 다 만들어 숨겨 두었다가 커서를 옮기면 보이기·숨기기만 한다(본 대본이 만든 그림은 프로세스에서 못 건드려
// 「사운드」 그림도 여기서 만든다).
function KuHintRow()
{
	$KUH_R=-1;$KUH_SH=0;$KUH_ON=true;
'''

NSS_LOOP = '''	KuHintMake();
	if($KUH_PA==1){$KUH_PA=0;$khPN="ku_lhprocB";}else{$KUH_PA=1;$khPN="ku_lhprocA";}
	CreateProcess($khPN,150,0,0,"KuHintLoop");
	Request($khPN,Start);
}

// $KUH_RUN: 고리가 도는 동안 true. 다시 그리기(KuList)는 $KUH_ON 을 끄고 이것이 꺼질 때까지 기다린 뒤 지운다
// - 돌고 있는 프로세스를 Delete 로 지우면 엔진이 그 스레드를 100+1500+1500ms 기다리다 끊어 3.1초 멈췄다(다른 세션 「사운드 모드 성능」 11-24).
function KuHintLoop()
{
	$KUH_RUN=true;
	while($KUH_ON){
		KuHintTick();
		if($KUS_ON){KuSeekTick();}
		Wait(16);
	}
	$KUH_RUN=false;
}

function KuHintTick()
{
	$khX=-1;$khY=-1;
	CursorPosition($khX,$khY);
	$khR=0;
	if($khY>=58&&$khY<498){
		$khD=$khY-58;$khQ=$khD/44;$khK=Integer($khQ);$khM=$khK*44;$khO=$khD-$khM;
		if($khO<26){
			if($khX>=26&&$khX<502){$khR=$khK+1;}
			if($khX>=524&&$khX<1000){$khR=$khK+11;}
		}
	}
	if($khR>19){$khR=0;}
	if($khR!=$KUH_R){
		$KUH_R=$khR;
		$khN=0;
'''

NSS_TAIL = '''		if($khN!=$KUH_SH){
			KuHintShow();
			KuHintHide();
			$KUH_SH=$khN;
		}
	}
}
'''


def nss() -> str:
    """KuHintRow(목록을 그릴 때 한 번) · KuHintLoop(프로세스: KuHintMake 뒤 KuHintTick·KuSeekTick) · KuHintShow/Hide."""
    gates, pick, make, show, hide = [], [], [], [], []
    # 11-24 그림은 본 대본(KuHintRow, 가림막을 걷기 전)이 만들고 별칭을 단다 - 프로세스 안에서 20장을 만들면 엔진 명령마다 렌더 스레드의
    # 한 프레임을 기다려 0.7~1초 걸리고 하나씩 번쩍였다(다른 세션 「사운드 모드 성능」 표지 시험). 프로세스는 "@별칭" 으로 Fade 만
    # (본 대본이 만든 것도 별칭으로는 프로세스에서 다룰 수 있다 - kr_lyrics.nss 의 krly_img 와 같은 꼴).
    tex = lambda nm, f: (f'CreateTexture("{nm}",2022,{X},{Y},{f});SetAlias("{nm}","{nm}");SetVertex("{nm}",0,0);'
                         f'Zoom("{nm}",0,250,250,null,false);Request("{nm}",Smoothing);')
    make.append('\t' + tex('ku_lh00', '"nss/kr_hint_00.png"') + '\n')
    show.append('\tif($khN==0){Fade("@ku_lh00",0,1000,null,false);}\n')
    hide.append('\tif($KUH_SH==0){Fade("@ku_lh00",0,0,null,false);}\n')
    for n, base, gate in HINTS:
        nm = f'ku_lh{n:02d}'
        if gate:
            sc = gate[0]
            gates.append(f'\t$KUH_G{n}=false;if(#KS_ALLOPEN){{$KUH_G{n}=true;}}\n'
                         f'\tif(!$KUH_G{n}){{$kc_r=Conquest("nss/{sc}.nss","{sc}.nss",null);if($kc_r){{$KUH_G{n}=true;}}}}\n')
            make.append(f'\tif($KU_OK{n}){{$khF="nss/kr_hint_{n:02d}.png";if($KUH_G{n}){{$khF="nss/kr_hint_{n:02d}g.png";}}'
                        + tex(nm, '$khF') + f'Fade("{nm}",0,0,null,false);}}\n')
        else:
            make.append(f'\tif($KU_OK{n}){{' + tex(nm, f'"nss/kr_hint_{n:02d}.png"') + f'Fade("{nm}",0,0,null,false);}}\n')
        pick.append(f'\t\tif($khR=={n}){{if($KU_OK{n}){{$khN={n};}}}}\n')
        show.append(f'\tif($khN=={n}){{Fade("@{nm}",0,1000,null,false);}}\n')
        hide.append(f'\tif($KUH_SH=={n}){{Fade("@{nm}",0,0,null,false);}}\n')
    funcs = ('\n// 목록을 그릴 때 한 번: 「사운드」와 열린 곡의 풀이 그림을 모두 만들어 둔다(풀이는 숨김)\nfunction KuHintMake()\n{\n' + ''.join(make) + '}\n'
             + '\n// 새로 보일 그림($khN)을 먼저 보이고, 앞 그림($KUH_SH)을 숨긴다(빈 띠가 한 번도 안 찍히게)\nfunction KuHintShow()\n{\n' + ''.join(show) + '}\n'
             + '\nfunction KuHintHide()\n{\n' + ''.join(hide) + '}\n')
    return NSS_HEAD + ''.join(gates) + NSS_LOOP + ''.join(pick) + NSS_TAIL + funcs


if __name__ == '__main__':   # 견본 그림을 폴더에
    import sys
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    for name, png in assets().items():
        (out / name).write_bytes(png)
    print(len(names()), 'images')
