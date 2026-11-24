"""사운드 화면 재생 위치 막대(사용자 11-24 「사운드 모드에서 진행 바를 만들어서 노래 위치를 조절할수 있게 해줘」).
- 오른쪽 열 빈 20번째 칸에 19번째 줄과 같은 꼴의 줄(kr_seek_row.png = kr_snd_bg.png 19번째 줄 그림, 이름 글자만 지움):
  이름 칸 「위치」, 긴 칸 = 진행 막대(채움 0x163A36·머리 0x8BE9D7 = 고른 줄 색), 오른쪽에 「1:23 / 4:56」.
- 곡이 재생 중일 때만 보인다. 막대 위에 커서를 올리면 그 자리 시각(「→ 2:40」), 누르면 그 자리로 간다.
- 위치 옮기기는 엔진 명령 SetStream(소리, 밀리초) — 원작 대본이 소리 시작 위치에 쓰는 명령이고, 코덱스 가사 시험이
  재생 중 SetStream 으로 PassageTime 이 옮겨지는 것을 확인했다. 가사(kr_lyrics.nss KrLyTick)는 0.1초마다
  PassageTime 으로 구간을 다시 찾으므로 따라간다.
- 입력: staging/nss_lyrics.npa(코덱스 가사판) → 출력: staging/nss_play.npa, 시험판 nss_variants/nss.test_seek.npa
python -I -X utf8 patch_seek.py
"""
import sys, hashlib
from pathlib import Path
W = Path(__file__).resolve().parents[1]
sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, str(Path(__file__).resolve().parent))   # title_hints 등 같은 폴더 모듈(-I 로 돌려도)
from npa_build import build
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
import zlib
from npa_assets import NPA, KEYS

def rd(arc, e):
    with arc.path.open('rb') as f: f.seek(arc.base + e['offset']); buf = bytearray(f.read(e['stored_size']))
    if arc.enc:
        name = bytes.fromhex(e['name_hex']); key = ((0x20101118 - sum(name)) * len(name) + arc.k1 * arc.k2) * e['size'] & 255
        for j in range(min(len(buf), 0x1000 + len(name))): buf[j] = (KEYS[buf[j]] - key - j) & 255
    if arc.comp:
        try: return zlib.decompress(buf)
        except zlib.error: return bytes(buf)
    return bytes(buf)

K = 'cp949'
def sub(b, old, new, n=1):
    o, w = old.encode(K), new.encode(K)
    assert b.count(o) == n, (old, b.count(o))
    return b.replace(o, w)

SEEK_FN = r'''
//★ 재생 위치 막대(Claude 11-24, 사용자 「진행 바를 마지막 칸에 위치시키는게 아니라 해당 음악 목록 그 바에 놓는게 좋을거 같아」):
// 재생 중인 곡 줄의 긴 칸(304x24)이 곧 진행 막대 - 지난 만큼 밝은 청록과 머리 선, 시각은 줄 바로 아래 오른쪽 작게.
// 커서를 올리면 그 자리 시각, 누르면 그 자리로(SetStream). 재생 중인 줄은 단추로 만들지 않는다(같은 곡을 다시 누르면
// 원래도 아무 일 없었다) → 그 줄을 누르면 위치만 옮긴다. 줄 자리: 왼쪽 x108·y=59+44(n-1), 오른쪽 x606·y=59+44(n-11).
// 식은 한 줄에 연산 하나(엔진에 곱셈 우선이 없는 듯).
function KuSeekRow()
{
	$KUS_W=-1;$KUS_KEY=-1;$KUS_ON=false;$KUS_STALE=false;$KUS_DK=-1;$KUS_LB=0;$KUS_FA=0;$KUS_TA=0;$KUS_DA=0;
	if($KU_NOW>0){
		$KUS_ON=true;
		if($KU_NOW<=10){$KUS_X0=108;$KUS_Y=$KU_NOW-1;}else{$KUS_X0=606;$KUS_Y=$KU_NOW-11;}
		$KUS_Y=$KUS_Y*44;$KUS_Y=$KUS_Y+59;
		$KUS_X1=$KUS_X0+304;$KUS_Y1=$KUS_Y+24;$KUS_TX=$KUS_X0+206;$KUS_TY=$KUS_Y+24;
		// 11-24 막대 갱신(KuSeekTick)은 곡 제목 풀이 프로세스(KuHintLoop)가 같이 돌린다 - 프로세스 둘이 함께 그림을 만들면
		// 곡이 나오는 동안 화면이 1~2초씩 멈췄다(사용자 「사운드 모드 반응이 굉장히 느린데?」, 숨긴 시험 28초에 10~11번 → 하나로 합쳐 1번).
	}
}

// 나눗셈은 소수가 된다(11-24 시험: 3492/1000/60*60 이 다시 3.492 → 나머지 0) → 몫마다 Integer() 로 자른다. 값은 변수에 담아 넘긴다.
// 다시 그리는 그림은 이름 둘을 번갈아 쓴다(같은 이름을 한 프레임에 지우고 만들면 새것이 사라질 때가 있었다).
function KuSeekTick()
{
	$kxDur=-1;$kxPos=-1;$kxCX=-1;$kxCY=-1;
	$kxDur=DurationTime("@kubgm");
	$kxPos=PassageTime("@kubgm");
	if($kxDur>0){
		CursorPosition($kxCX,$kxCY);
		$kxIn=false;
		if($kxCX>=$KUS_X0&&$kxCX<$KUS_X1&&$kxCY>=$KUS_Y&&$kxCY<$KUS_Y1){$kxIn=true;}
		$kxHT=-1;
		if($kxIn){$kxOff=$kxCX-$KUS_X0;$kxMul=$kxOff*$kxDur;$kxHQ=$kxMul/304;$kxHT=Integer($kxHQ);}
		// 누름 표시는 막대 위에서 누른 것만 쓰고 지운다. 다른 곳에서 누른 표시는 건드리지 않는다(곡 줄·멈춤·닫기 단추가 쓴다 -
		// 전에는 매 프레임 지워서 곡이 나오는 동안 다른 단추가 안 눌렸다, 숨긴 시험 sk3). 막대 밖에서 본 표시는 낡은 것으로 적어 두었다가
		// 막대에 들어오면 옮기지 않고 지운다(빈 곳을 누른 뒤 막대에 올리기만 해도 옮겨지던 일을 막음).
		if($SYSTEM_l_button_down){
			if($kxIn){
				$SYSTEM_l_button_down=false;
				if($KUS_STALE){$KUS_STALE=false;}else{SetStream("@kubgm",$kxHT);$kxPos=$kxHT;}
			}else{$KUS_STALE=true;}
		}else{$KUS_STALE=false;}
		if($kxPos>$kxDur){$kxPos=$kxDur;}
		$kxPW=$kxPos*304;$kxWQ=$kxPW/$kxDur;$kxWid=Integer($kxWQ);
		if($kxWid!=$KUS_W){
			$KUS_W=$kxWid;$kxHX=$KUS_X0+$kxWid;
			if($KUS_FA==0){
				if($kxWid>0){CreateColor("ku_lskfB",2011,$KUS_X0,$KUS_Y,$kxWid,24,0x245F56);}
				CreateColor("ku_lskhB",2012,$kxHX,$KUS_Y,2,24,0x8BE9D7);
				Delete("ku_lskfA");Delete("ku_lskhA");$KUS_FA=1;
			}else{
				if($kxWid>0){CreateColor("ku_lskfA",2011,$KUS_X0,$KUS_Y,$kxWid,24,0x245F56);}
				CreateColor("ku_lskhA",2012,$kxHX,$KUS_Y,2,24,0x8BE9D7);
				Delete("ku_lskfB");Delete("ku_lskhB");$KUS_FA=0;
			}
		}
		$kxSQ=$kxPos/1000;$kxSec=Integer($kxSQ);$kxKey=$kxSec;
		if($kxIn){$kxSQ=$kxHT/1000;$kxSec=Integer($kxSQ);$kxKey=$kxSec+100000;}
		if($kxKey!=$KUS_KEY){
			$KUS_KEY=$kxKey;
			$kxMQ=$kxSec/60;$kxMin=Integer($kxMQ);$kxM60=$kxMin*60;$kxRem=$kxSec-$kxM60;
			$kxTQ=$kxDur/1000;$kxTot=Integer($kxTQ);$kxTMQ=$kxTot/60;$kxTMin=Integer($kxTMQ);$kxT60=$kxTMin*60;$kxTRem=$kxTot-$kxT60;
			if($kxIn){
				$kxTxt=String("→ %d:%02d",$kxMin,$kxRem);
				SetFont("Noto Sans KR", 13, 8BE9D7, 000000, 600, RIGHTDOWN);
			}else{
				$kxTxt=String("%d:%02d / %d:%02d",$kxMin,$kxRem,$kxTMin,$kxTRem);
				SetFont("Noto Sans KR", 13, B8B8B8, 000000, 500, RIGHTDOWN);
			}
			if($KUS_TA==0){KuText("ku_lsktB",2013,$KUS_TX,$KUS_TY,100,20,$kxTxt);Delete("ku_lsktA");$KUS_TA=1;}
			else{KuText("ku_lsktA",2013,$KUS_TX,$KUS_TY,100,20,$kxTxt);Delete("ku_lsktB");$KUS_TA=0;}
		}
		if($KUS_DBG){
			if($SYSTEM_l_button_down){$KUS_LB=$KUS_LB+1;}
			$kxDQ=$kxPos/500;$kxDK=Integer($kxDQ);
			if($kxDK!=$KUS_DK){
				$KUS_DK=$kxDK;
				$kxDbg=String("p%d d%d w%d s%d m%d r%d tm%d tr%d in%d lb%d",$kxPos,$kxDur,$kxWid,$kxSec,$kxMin,$kxRem,$kxTMin,$kxTRem,$kxIn,$KUS_LB);
				SetFont("Noto Sans KR", 14, FFFF80, 000000, 500, RIGHTDOWN);
				if($KUS_DA==0){KuText("ku_lskdB",2013,530,486,480,26,$kxDbg);Delete("ku_lskdA");$KUS_DA=1;}
				else{KuText("ku_lskdA",2013,530,486,480,26,$kxDbg);Delete("ku_lskdB");$KUS_DA=0;}
			}
		}
	}
}
'''

def patch(snd: bytes) -> bytes:
    snd = sub(snd, '\tFade("*/MouseOver/*",0,0,null,false);\r\n\tFade("*/MouseClick/*",0,0,null,false);\r\n\tFade("ku_cover",200,0,null,true);',
              '\tKuSeekRow();\r\n\tKuHintRow();\r\n\tFade("*/MouseOver/*",0,0,null,false);\r\n\tFade("*/MouseClick/*",0,0,null,false);\r\n\tFade("ku_cover",200,0,null,true);')
    # 11-24 KuHintRow = 곡 제목 풀이(title_hints.py, 사용자 「원작에서 저게 무슨 의미가 있는지 해석을 하단 하얀 바에 플로팅으로」).
    # 나갈 때 두 프로세스를 멈춘다(끝에 Delete("*") 가 있지만 그 전 1초 동안 그리지 않게)
    snd = sub(snd, '\twhile($KU_RUN){\r\n\t\tKuList();\r\n\t}\r\n', '\twhile($KU_RUN){\r\n\t\tKuList();\r\n\t}\r\n\t$KUH_ON=false;$KUS_ON=false;\r\n')
    # 11-24 곡이 나오는 중 다른 곡을 누르면 3.1초 멈춤(다른 세션 「사운드 모드 성능」 표지 시험 lk_tr_open_074642): KuList 의 KuClear 가
    # 돌고 있는 풀이 프로세스를 Delete 로 지우면 엔진이 그 스레드를 100+1500+1500ms 기다린다 → 먼저 고리를 끝내고($KUH_RUN 꺼짐) 지운다.
    snd = sub(snd, 'function KuList()\r\n{\r\n\tKuCover();\r\n',
              'function KuList()\r\n{\r\n\t$KUH_ON=false;$KUS_ON=false;\r\n'
              '\t$kxW=0;while($KUH_RUN){Wait(4);$kxW=$kxW+1;if($kxW>=100){$KUH_RUN=false;}}\r\n\tKuCover();\r\n')
    # 같이: 곡 바꾸기의 Wait(300) 은 곡이 나오고 있을 때만(아무 곡도 없을 때도 0.3초 기다렸다). 막대(PassageTime)를 먼저 멈춰
    # Delete("@kubgm") 과 엇갈리지 않게. 가림막 걷기 200ms 는 기다리지 않는다(남은 가림막은 다음 KuCover·나가기의 Delete 가 지움).
    snd = sub(snd, 'function KuFade()\r\n{\r\n\tKrLyStopFor("@kubgm");SetVolume("@kubgm", 300, 0, NULL);\r\n\tWait(300);\r\n\tDelete("@kubgm");\r\n}',
              'function KuFade()\r\n{\r\n\t$KUS_ON=false;\r\n'
              '\tif($KU_NOW>0){KrLyStopFor("@kubgm");SetVolume("@kubgm", 300, 0, NULL);Wait(300);}\r\n\tDelete("@kubgm");\r\n}')
    snd = sub(snd, '\tFade("ku_cover",200,0,null,true);\r\n\tDelete("ku_cover");\r\n', '\tFade("ku_cover",200,0,null,false);\r\n')
    # 「사운드」 글은 풀이 프로세스가 만든다(본 대본이 만든 것은 프로세스에서 지울 수 없었다, 숨긴 시험 hn5)
    snd = sub(snd, '\tKuText("ku_llabel",2022,18,546,420,34,"사운드");\r\n', '\t// 「사운드」 글은 KuHintTick 이 만든다(11-24)\r\n')
    snd = sub(snd, '\t$SYSTEM_r_button_down=false;\r\n\t$KU_LOOP=true;',
              '\t$SYSTEM_r_button_down=false;\r\n\t$SYSTEM_l_button_down=false;\r\n\t$KU_LOOP=true;')
    # 11-24 막대 갱신은 select 안이 아니라 따로 도는 프로세스(KuSeekLoop)에서 - select 안에서 돌리면 곡이 나오는 동안
    # 다른 곡·멈춤·닫기 단추가 안 눌렸다(숨긴 시험 sk3·sk4). 가사(KrLyTick)도 프로세스로 돈다.
    import title_hints
    snd = sub(snd, '\r\nfunction KuCalc()', (SEEK_FN + title_hints.nss()).replace('\n', '\r\n') + '\r\nfunction KuCalc()')
    # 11-24 사용자 「사운드 모드 하단에 제목을 해석해 표기 메뉴를 추가하도록. 설정시 제목이 번역된다」
    # → 아래 띠 「■ 멈춤」 옆에 「제목 해석 · 끔/켬」(#KR_SNDTR, 전역이라 기억됨). 켜면 열린 곡의 제목을 해석으로(뜻을 모르는 gェ19 는 그대로).
    # 11-24 오후 사용자가 넘긴 새 문안(목록 칸 짧은 해석). 오전 판: 생명·오메가·출발 준비·친구들·공허·(gェ19 그대로)·신들·왕·파이·
    # 내 영혼을 풀어 줘·왕관·슬픔의 언덕·묵시록·집 ~이 구석에서~·창세기·생명-델타·현실·고립·나는 어디에?
    TITLE_KO = ['생명 (비오스)', '종말 (오메가)', '출격 완료', '동료들 (장의사)', '공허 (보이드)', 'GHQ (암호 표기)', '신들 (테오이)',
                '왕·군주 (바실레우스)', '원주율 (끝없는 굴레)', '영혼의 해방', '왕관 (크로네)', '슬픔의 언덕', '묵시록 (아포칼립스)',
                '안식처 ~이 모퉁이에서~', '규약된 창세', '생명의 변주', '모두의 현실', '고립·격리', '나는 어디에?']
    import re
    def tr(m):
        k = int(m.group(1)); ko = TITLE_KO[k - 1]
        if ko is None or m.group(2) == '아직 듣지 않은 곡'.encode(K):
            return m.group(0)
        alt = m.group(0).replace(b'"' + m.group(2) + b'");', b'"' + ko.encode(K) + b'");')
        return b'if(#KR_SNDTR){' + alt + b'}else{' + m.group(0) + b'}'
    snd, ntr = re.subn(rb'KuText\("ku_lt(\d\d)",2012,\d+,\d+,264,26,"([^"]*)"\);', tr, snd)
    assert ntr == 38, ntr      # 곡마다 열림·잠김 두 줄
    snd = sub(snd, '\tKuText("ku_lstop",2022,480,546,100,34,"■  멈춤");\r\n',
              '\tKuText("ku_lstop",2022,480,546,100,34,"■  멈춤");\r\n'
              '\tCreateChoice("KU_TRN");\r\n'
              '\tCreateColor("KU_TRN/MouseUsual/hit",2020,600,544,160,30,0x000000);\r\n'
              '\tRequest("KU_TRN/MouseUsual/hit",Erase);\r\n'
              '\tCreateColor("KU_TRN/MouseOver/img",2021,600,544,160,30,0xF2F2F2);\r\n'
              '\tCreateColor("KU_TRN/MouseClick/img",2021,600,544,160,30,0x58B6A4);\r\n'
              '\tSetFont("Noto Sans KR", 15, 7A7A7A, E6E6E6, 600, RIGHTDOWN);\r\n'
              '\tif(#KR_SNDTR){KuText("ku_ltrn",2022,614,546,140,34,"제목 해석 · 켬");}else{KuText("ku_ltrn",2022,614,546,140,34,"제목 해석 · 끔");}\r\n')
    snd = sub(snd, '\t\t\tcase KU_EXIT{',
              '\t\t\tcase KU_TRN{Request("@ku_se_ok",Play);if(#KR_SNDTR){#KR_SNDTR=false;}else{#KR_SNDTR=true;}$KU_LOOP=false;}\r\n\t\t\tcase KU_EXIT{')
    # 11-24 사용자 「사운드 모드에서 우클릭하면 메뉴로 나가는데 만일 재생중인 음악이 있다면 나가기 대신 현재 음악 멈춤으로」
    # → 곡이 나오는 중이면 오른쪽 클릭 = 「■ 멈춤」 단추와 같은 일, 아니면 원래대로 나가기
    snd = sub(snd, '\t\t\tif($SYSTEM_r_button_down){$SYSTEM_r_button_down=false;$KU_LOOP=false;$KU_RUN=false;break;}',
              '\t\t\tif($SYSTEM_r_button_down){$SYSTEM_r_button_down=false;if($KU_NOW>0){Request("@ku_se_ok",Play);KrLyStopFor("@kubgm");'
              'SetVolume("@kubgm", 500, 0, NULL);$KU_NOW=-1;$KU_LOOP=false;}else{$KU_LOOP=false;$KU_RUN=false;}break;}')
    # 11-24 재생 중인 줄은 단추로 만들지 않는다(그 줄을 누르면 위치만 옮기게): 줄마다 CreateChoice 와 그 hit·Over·Click 네 줄을 감싼다
    import re
    n = 0
    def wrap(m):
        nonlocal n; n += 1
        k = int(m.group(1))
        return ('\t\tif($KU_NOW!=%d){\r\n' % k).encode(K) + m.group(0) + b'\t\t}\r\n'
    snd = re.sub(rb'\t\tCreateChoice\("ku_r(\d\d)"\);\r\n(?:\t\t[^\r\n]*\r\n){4}', wrap, snd)
    assert n == 19, n
    return snd


RECALL = [   # 11-24 사용자 「회상에서 설명의 위치를 그림 아래에서 저 제목과 재생 사이로 옮겨줘. 여기서 재생에서 여기서는 빼줘」→「여기서 보기를 재생으로 바꿔줘」
    ('\t// 장면 요약: 큰 CG 아래(검수용으로만 열린 결말은 보이지 않음)\r\n\tif($kd_sum!=""){\r\n\t\tSetFont("Noto Sans KR", 15, C8C8C8, 000000, 500, RIGHTDOWN);\r\n'
     '\t\tKsText("ks_dsum",2012,26,434,636,100,$kd_sum);\r\n\t}\r\n', ''),
    ('\tKsText("ks_dttl",2012,694,194,310,120,$kd_tt);\r\n',
     '\tKsText("ks_dttl",2012,694,194,310,120,$kd_tt);\r\n\t// 장면 요약: 제목과 「재생」 사이(11-24; 검수용으로만 열린 결말은 보이지 않음)\r\n\tif($kd_sum!=""){\r\n'
     '\t\tSetFont("Noto Sans KR", 14, C8C8C8, 000000, 500, RIGHTDOWN);\r\n\t\tKsText("ks_dsum",2012,694,244,312,130,$kd_sum);\r\n\t}\r\n'),
    ('CreateColor("KS_PLAY/MouseUsual/hit",2010,694,362,312,46,0x000000);', 'CreateColor("KS_PLAY/MouseUsual/hit",2010,694,380,312,46,0x000000);'),
    ('CreateColor("KS_PLAY/MouseUsual/img",2010,694,362,312,46,0x2E2E2E);', 'CreateColor("KS_PLAY/MouseUsual/img",2010,694,380,312,46,0x2E2E2E);'),
    ('CreateColor("ks_dpbi",2011,697,364,297,42,0x0B0B0B);', 'CreateColor("ks_dpbi",2011,697,382,297,42,0x0B0B0B);'),
    ('CreateColor("ks_dpbr",2011,996,362,10,46,0x262626);', 'CreateColor("ks_dpbr",2011,996,380,10,46,0x262626);'),
    ('CreateColor("KS_PLAY/MouseOver/img",2012,697,364,297,42,0x163A36);', 'CreateColor("KS_PLAY/MouseOver/img",2012,697,382,297,42,0x163A36);'),
    ('CreateColor("KS_PLAY/MouseClick/img",2012,697,364,297,42,0x2A6F63);', 'CreateColor("KS_PLAY/MouseClick/img",2012,697,382,297,42,0x2A6F63);'),
    ('KsText("ks_dplay",2014,716,370,270,40,"▶  여기서 보기");', 'KsText("ks_dplay",2014,716,388,270,40,"▶  재생");'),
    ('KsText("ks_dnote",2012,694,418,320,48,', 'KsText("ks_dnote",2012,694,436,320,48,'),
]

def patch_recall(b: bytes) -> bytes:
    for old, new in RECALL:
        b = sub(b, old, new)
    # 11-24 사용자 「페이즈를 단계로 번역했는데 질병의 진행기를 뜻하는 페이즈니까 그대로 영어로…」 → 원작 표지처럼 「phase 01」
    # (표지 그림 cg/sys/phase/フェイズ.png 는 덧씌우기 묶음 cg.fix.npa 로 영어 원작 꼴, 여기는 장면 목록의 글)
    import re
    b, n = re.subn('\\$KS_PTAG\\[(\\d+)\\]="단계 (\\d\\d)"'.encode(K), lambda m: b'$KS_PTAG[' + m.group(1) + b']="phase ' + m.group(2) + b'"', b)
    assert n == 7, n   # 단계마다 하나(01~07)
    return b


if __name__ == '__main__':
    src = W / 'staging/nss_lyrics.npa'
    arc = NPA(src); ent = {e['name']: e for e in arc.entries}
    snd = patch(rd(arc, ent['kr_sound.nss']))
    row = (W / 'sound_seek/kr_seek_row.png').read_bytes()
    out = W / 'staging/nss_play.npa'
    import lyrics_style   # 11-24 가사: 상자 없이·한국어 노란색, 본편은 화면 위
    kly = lyrics_style.patch_script(rd(arc, ent['kr_lyrics.nss']))
    # 11-24 코덱스 보컬곡 자막 싱크 고침(gclx-song-20261123\timing-20261124: 184구간 조정·끝음 여운) — 코덱스가 우리 빌드의 가사 모듈
    # (d08735fc)을 바탕으로 고친 판(fc7097ce)을 그대로 쓴다. 바탕이 바뀌면(가사 모듈을 여기서 다시 고치면) 멈춰서 다시 맞출 것.
    _cx = (W / 'sound_seek/codex_kr_lyrics_timing_20261124.nss').read_bytes()
    assert hashlib.sha256(kly).hexdigest()[:8] == 'd08735fc', hashlib.sha256(kly).hexdigest()[:8]
    kly = _cx
    rec = patch_recall(rd(arc, ent['kr_scenario.nss']))
    lyr = lyrics_style.assets()
    assert all(n in ent for n in lyr)
    import keybar   # 11-24 맨 아래 키 목록(H·J 는 DLL kr_keys.inc)
    fn = rd(arc, ent['function.nss'])
    assert fn.count(keybar.LOADBOX_ADD[0].encode('cp932')) == 1 and fn.count(keybar.TYPEBEGIN[0].encode('cp932')) == 4
    fn = fn.replace(keybar.LOADBOX_ADD[0].encode('cp932'), keybar.LOADBOX_ADD[1].encode('cp932'))
    fn = fn.replace(keybar.TYPEBEGIN[0].encode('cp932'), keybar.TYPEBEGIN[1].encode('cp932'))
    boot = rd(arc, ent['0_boot.nss'])
    assert boot.count(keybar.BOOT_JP[0].encode('cp932')) == 1
    boot = boot.replace(keybar.BOOT_JP[0].encode('cp932'), keybar.BOOT_JP[1].encode('cp932'))
    import jp_twin   # 11-24 J: 장면마다 한국어 덩어리 뒤 if(#KR_JP){ 일본어 덩어리 }
    def _keybar_d(disabled=()):
        # 11-24 사용자 「하단 단축키 바에 … 게임 설정에 어울리는 UI를 제시해서 그걸로 바꿔 지금은 튄다」 → 시안 D 「설정 칸」
        # (원작 환경 설정의 번호 칸 + 이음줄, keybar_styles.style_D). disabled = 회상 판에서 어둡게 긋는 키.
        import io, keybar_styles
        b = io.BytesIO(); keybar_styles.style_D(keybar.KEYS, disabled).save(b, format='PNG'); return b.getvalue()
    import text_fixes   # 11-24 플레이 중 사용자가 짚은 한국어 고침(쌍둥이·교차 글을 만들기 전에)
    rd_fixed = lambda a, e: text_fixes.apply(e['name'], rd(a, e))
    twins = jp_twin.patch_all(arc, ent, rd_fixed)
    import jp_swap   # 11-24 J 를 누른 대사에서 바로 바꾸기(TypeBegin 갈고리·KrPassText·KrJSwapTick)
    fn = jp_swap.patch_function(fn)
    fn = keybar.patch_oldsave(fn)   # 11-24 옛 세이브에서도 키 목록·병기 받침이 생기게
    import logo_wheel   # 11-24 시작 로고 건너뛰기 설정·회상 휠로 쪽 넘기기·첫 장면 크레딧 작은 읽기 글 지우기
    boot = logo_wheel.patch_boot(boot)
    rec = logo_wheel.patch_recall(rec)
    cfg = logo_wheel.patch_config(rd(arc, ent['sys_config.nss']))
    twins['lx0010.nss'] = logo_wheel.patch_credits(twins['lx0010.nss'])
    sys.path.insert(0, str(W / 'movie_room'))
    import thumbs   # 11-24 영상 감상 썸네일 2x2 + 5장 영상(movie_room/thumbs.py)
    mov = thumbs.patch_room(rd(arc, ent['kr_movie.nss']))
    import stage_room   # 11-24 영상실 「연출」 쪽 + 연출 다시 보기 모듈 kr_spNN.nss(movie_room/stage_room.py·stage_replay.py)
    mov = stage_room.patch_room(mov)
    stage_mods = stage_room.modules(lambda f: twins[f] if f in twins else rd(arc, ent[f]))
    import recall_sp   # 11-24 회상 상세 「이 장면의 연출」 단추 + 그 연출 앞부터 장면 끝까지 kr_rpNN.nss(movie_room/recall_sp.py)
    stage_mods.update(recall_sp.modules(rec, lambda f: twins[f] if f in twins else rd(arc, ent[f])))
    rec = recall_sp.patch_recall(rec)
    build(src, out, replace={'kr_sound.nss': snd, 'kr_lyrics.nss': kly, 'kr_scenario.nss': rec, 'function.nss': fn, '0_boot.nss': boot, 'sys_config.nss': cfg,
                             'kr_movie.nss': mov, 'kr_cfg_page3.png': logo_wheel.make_page3_image(),
                             # 11-24 「번호가 앞에 가고 음악 분류가 뒤에」: scenario/make_ui_assets.py 로 다시 그린 사운드 바탕
                             'kr_snd_bg.png': (W / 'sound_seek/snd_bg/kr_snd_bg.png').read_bytes(), **lyr, **twins},
          add={'kr_keybar.png': _keybar_d(), 'kr_keybar_rp.png': _keybar_d(keybar.REPLAY_OFF),
               'kr_biback.png': jp_swap.biback_png(), **thumbs.assets(), **stage_mods,
               **__import__('title_hints').assets()})   # 11-24 곡 제목 풀이 그림(엔진 글로 만들면 곡 재생 중 멈춤)
    (W / 'sound_seek/kr_sound.seek.nss.txt').write_text(snd.decode(K, 'replace'), 'utf-8')
    # 시험판: 시작 때 창 모드·모두 열기(사용자 기록 사본을 쓰지 않으려고)
    A = '\tif(!#N2Start){'.encode('cp932'); assert boot.count(A) == 1
    boot = boot.replace(A, '\t#N2Start=true;#SYSTEM_window_full=false;#KS_ALLOPEN=true;$KUS_DBG=true;\r\n'.encode('cp932') + A, 1)
    tv = W / 'nss_variants/nss.test_seek.npa'
    build(out, tv, replace={'0_boot.nss': boot})
    print('nss_play', hashlib.sha256(out.read_bytes()).hexdigest()[:8], 'test', hashlib.sha256(tv.read_bytes()).hexdigest()[:8])
