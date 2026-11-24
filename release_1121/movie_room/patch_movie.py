"""영상 감상(사용자 11-23 「영상 감상. 오프닝, 중간 영상, 아이캐치를 타이틀에서 다시 봐. 중간 영상 4K 연결도 이때 같이」).
원작에는 영상 감상이 없다. 타이틀 「사운드」 아래 「영상」 단추 → kr_movie.nss(사운드 화면과 같은 틀의 세 줄 목록).
- 01 오프닝: dx/mv_op.ngs(원작 lx9999 와 같은 CreateMovie). 열림 = #mvOPplay(원작이 오프닝을 끝까지 튼 뒤 켬).
- 02 아이캐치: lx0109 의 아이캐치 연출 덩어리(영상 + 톱니 효과음 + 한국어 로고)를 그대로 옮김. 열림 = lx0109·lx0300·lx0500 끝까지 읽음 또는 03 이 열림.
- 03 2장 영상: dx/mv_lx0201.ngs. 열림 = #lx0201_mv01(원작 MovieSkipPlay 가 켬).
- 셋 다 회상 「모두 열기」(#KS_ALLOPEN)면 열림. 보는 중 클릭·키로 건너뜀(WaitKey). 4K 판은 DLL 이 영상 이름으로 바꿔 끼움.
assemble.py 가 apply_boot · kr_movie · assets 를 쓴다.
"""
import re
from pathlib import Path
HERE = Path(__file__).resolve().parent
J = 'cp932'   # 0_boot 은 원작대로 cp932
K = 'cp949'   # 한국어 화면 글자는 cp949(사운드·회상 대본과 같음)


def _sub(b, old, new, n=1):
    old, new = old.encode(J), new.encode(J)
    assert b.count(old) == n, (old[:60], b.count(old))
    return b.replace(old, new)


SOUND_BTN = '''	CreateChoice("Title_Sound");
	CreateTexture("Title_Sound/MouseUsual/hit", 0, 416, 398, "nss/kr_title_sound-000.png");
	CreateTexture("Title_Sound/MouseUsual/img", 1000, 416, 398, "nss/kr_title_sound-001.png");
	SetVertex("Title_Sound/MouseUsual/img", 0, 0);
	Zoom("Title_Sound/MouseUsual/img", 0, 250, 250, null, false);
	Request("Title_Sound/MouseUsual/img", Smoothing);
	CreateTexture("Title_Sound/MouseOver/img", 1000, 416, 398, "nss/kr_title_sound-002.png");
	SetVertex("Title_Sound/MouseOver/img", 0, 0);
	Zoom("Title_Sound/MouseOver/img", 0, 250, 250, null, false);
	Request("Title_Sound/MouseOver/img", Smoothing);
	CreateTexture("Title_Sound/MouseClick/img", 1000, 416, 398, "nss/kr_title_sound-003.png");
	SetVertex("Title_Sound/MouseClick/img", 0, 0);
	Zoom("Title_Sound/MouseClick/img", 0, 250, 250, null, false);
	Request("Title_Sound/MouseClick/img", Smoothing);
'''.replace('\n', '\r\n')


def _col(names, y0, d):
    return ''.join(f'\t\tMove("Title_{n}/*/*", 0, 416, {y0 + i * d}, null, false);\r\n' for i, n in enumerate(names))


LAYOUT = ('\t//■ボタン配置（Claude 11-02：回想・サウンド、11-23：映像を「つづきから」の下に。多い時はロゴに掛からないよう278から詰める）\r\n'
          '\tif(#ENDING_OF_XMAS&&#ENDING_OF_TOBECONTINUED)\r\n\t{\r\n'
          + _col(['Start', 'LOAD', 'Scenario', 'Sound', 'Movie', 'CG', 'Config', 'Liner', 'Exit'], 278, 28) +
          '\t}\r\n\telse if(#ENDING_OF_XMAS||#ENDING_OF_TOBECONTINUED)\r\n\t{\r\n'
          + _col(['Start', 'LOAD', 'Scenario', 'Sound', 'Movie', 'CG', 'Config', 'Exit'], 278, 28) +
          '\t}\r\n\telse\r\n\t{\r\n'
          + _col(['Start', 'LOAD', 'Scenario', 'Sound', 'Movie', 'Config', 'Exit'], 278, 32) +
          '\t}\r\n')

FOCUS = '''function TitleFocusKr(){
	SetNextFocus("Title_LOAD/MouseUsual/hit", "Title_Scenario/MouseUsual/hit",DOWN);
	SetNextFocus("Title_LOAD/MouseUsual/hit", "Title_Scenario/MouseUsual/hit",RIGHT);
	SetNextFocus("Title_Scenario/MouseUsual/hit", "Title_LOAD/MouseUsual/hit",UP);
	SetNextFocus("Title_Scenario/MouseUsual/hit", "Title_LOAD/MouseUsual/hit",LEFT);
	SetNextFocus("Title_Scenario/MouseUsual/hit", "Title_Sound/MouseUsual/hit",DOWN);
	SetNextFocus("Title_Scenario/MouseUsual/hit", "Title_Sound/MouseUsual/hit",RIGHT);
	SetNextFocus("Title_Sound/MouseUsual/hit", "Title_Scenario/MouseUsual/hit",UP);
	SetNextFocus("Title_Sound/MouseUsual/hit", "Title_Scenario/MouseUsual/hit",LEFT);
	SetNextFocus("Title_Sound/MouseUsual/hit", "Title_Movie/MouseUsual/hit",DOWN);
	SetNextFocus("Title_Sound/MouseUsual/hit", "Title_Movie/MouseUsual/hit",RIGHT);
	SetNextFocus("Title_Movie/MouseUsual/hit", "Title_Sound/MouseUsual/hit",UP);
	SetNextFocus("Title_Movie/MouseUsual/hit", "Title_Sound/MouseUsual/hit",LEFT);
	if(#ENDING_OF_XMAS||#ENDING_OF_TOBECONTINUED){
		SetNextFocus("Title_Movie/MouseUsual/hit", "Title_CG/MouseUsual/hit",DOWN);
		SetNextFocus("Title_Movie/MouseUsual/hit", "Title_CG/MouseUsual/hit",RIGHT);
		SetNextFocus("Title_CG/MouseUsual/hit", "Title_Movie/MouseUsual/hit",UP);
		SetNextFocus("Title_CG/MouseUsual/hit", "Title_Movie/MouseUsual/hit",LEFT);
	}else{
		SetNextFocus("Title_Movie/MouseUsual/hit", "Title_Config/MouseUsual/hit",DOWN);
		SetNextFocus("Title_Movie/MouseUsual/hit", "Title_Config/MouseUsual/hit",RIGHT);
		SetNextFocus("Title_Config/MouseUsual/hit", "Title_Movie/MouseUsual/hit",UP);
		SetNextFocus("Title_Config/MouseUsual/hit", "Title_Movie/MouseUsual/hit",LEFT);
	}
}
'''.replace('\n', '\r\n')


def apply_boot(b):
    # 1) 단추: 「사운드」 단추 바로 뒤
    b = _sub(b, SOUND_BTN, SOUND_BTN + '\r\n' + SOUND_BTN.replace('Title_Sound', 'Title_Movie').replace('kr_title_sound', 'kr_title_movie').replace(', 398, ', ', 434, '))
    # 2) 배치: 11-02 배치 덩어리를 통째로 바꿈
    s = b.find('\t//■ボタン配置（Claude 11-02'.encode(J))
    e = b.find('\r\n\r\n\tFade("タイトル*",0,0,null,false);'.encode(J), s)
    assert s > 0 and e > s and b.count('\t//■ボタン配置（Claude 11-02'.encode(J)) == 1
    b = b[:s] + LAYOUT.encode(J) + b[e + 2:]
    # 3) 긴 타이틀 등장: 사운드 다음
    b = _sub(b, '\t\tFade("Title_Sound/MouseUsual/*",300,1000,null,false);\r\n\t\tWait(100);\r\n',
             '\t\tFade("Title_Sound/MouseUsual/*",300,1000,null,false);\r\n\t\tWait(100);\r\n\t\tFade("Title_Movie/MouseUsual/*",300,1000,null,false);\r\n\t\tWait(100);\r\n')
    # 4) 키보드 초점
    m = re.search(rb'function TitleFocusKr\(\)\{\r\n.*?\r\n\}\r\n', b, re.S)
    assert m and b.count(b'function TitleFocusKr(){') == 1
    b = b[:m.start()] + FOCUS.encode(J) + b[m.end():]
    # 5) 고르기: $TitleSelect=5
    b = _sub(b, '\t\t\tcase Title_Sound{\r\n\t\t\t\tCreateSE("決定サウンド",$TitleClickSE);\r\n\t\t\t\tSoundPlay("決定サウンド",0,650,false);\r\n\t\t\t\t$TitleSelect=4;\r\n\t\t\t}\r\n',
             '\t\t\tcase Title_Sound{\r\n\t\t\t\tCreateSE("決定サウンド",$TitleClickSE);\r\n\t\t\t\tSoundPlay("決定サウンド",0,650,false);\r\n\t\t\t\t$TitleSelect=4;\r\n\t\t\t}\r\n\r\n'
             '\t\t\tcase Title_Movie{\r\n\t\t\t\tCreateSE("決定サウンド",$TitleClickSE);\r\n\t\t\t\tSoundPlay("決定サウンド",0,650,false);\r\n\t\t\t\t$TitleSelect=5;\r\n\t\t\t}\r\n')
    # 6) 타이틀을 지우고 영상 감상 → 끝나면 타이틀 처음부터(사운드와 같음)
    b = _sub(b, '\t\t\tcall_chapter nss/kr_sound.nss;\r\n\t\t\tTitleClear();\r\n\t\t\t$TitleSelect=false;\r\n\t\t}\r\n',
             '\t\t\tcall_chapter nss/kr_sound.nss;\r\n\t\t\tTitleClear();\r\n\t\t\t$TitleSelect=false;\r\n\t\t}\r\n'
             '\t\t//★：映像鑑賞（Claude 11-23）\r\n\t\tif($TitleSelect==5){\r\n\t\t\tRequest("タイトル*", UnLock);\r\n\t\t\tRequest("決定サウンド", UnLock);\r\n'
             '\t\t\tDelete("*");\r\n\t\t\tWait(300);\r\n\t\t\tcall_chapter nss/kr_movie.nss;\r\n\t\t\tTitleClear();\r\n\t\t\t$TitleSelect=false;\r\n\t\t}\r\n')
    return b


def eyecatch_block(lx0109):
    """lx0109 의 아이캐치 연출 덩어리(「//★演出：アイキャッチ」 다음 줄 ~ 「//$SYSTEM_menu_lock=false;」 줄)."""
    a = lx0109.find('//★演出：アイキャッチ\r\n'.encode(J))
    z = lx0109.find('//$SYSTEM_menu_lock=false;\r\n'.encode(J), a)
    assert a > 0 and z > a and lx0109.count('//★演出：アイキャッチ'.encode(J)) == 1
    blk = lx0109[a:z + len('//$SYSTEM_menu_lock=false;\r\n')]
    assert b'GC_eyecatch_E.ngs' in blk and blk.count(b'MenuLock(true);') == 1 and blk.count(b'MenuLock(false);') == 1
    return blk


def _row(k, title):
    y = 58 + 44 * (k - 1)
    return (f'\tif($KM_OK{k}){{\r\n'
            f'\t\tCreateChoice("km_r0{k}");\r\n'
            f'\t\tCreateColor("km_r0{k}/MouseUsual/hit",2010,26,{y},476,26,0x000000);\r\n'
            f'\t\tRequest("km_r0{k}/MouseUsual/hit",Erase);\r\n'
            f'\t\tCreateColor("km_r0{k}/MouseOver/img",2011,108,{y + 1},304,24,0x262626);\r\n'
            f'\t\tCreateColor("km_r0{k}/MouseClick/img",2011,108,{y + 1},304,24,0x2A6F63);\r\n'
            f'\t\tSetFont("Noto Sans KR", 16, DADADA, 000000, 600, RIGHTDOWN);\r\n'
            f'\t\tKmText("km_lt0{k}",2012,120,{y + 1},264,26,"{title}");\r\n'
            f'\t}}else{{\r\n'
            f'\t\tSetFont("Noto Sans KR", 16, 4A4A4A, 000000, 500, RIGHTDOWN);\r\n'
            f'\t\tKmText("km_lt0{k}",2012,120,{y + 1},264,26,"아직 보지 않은 영상");\r\n'
            f'\t}}\r\n')


HEAD = '''// Claude 11-23: 영상 감상(사용자 「영상 감상. 오프닝, 중간 영상, 아이캐치를 타이틀에서 다시 봐」). 원작에는 영상 감상이 없다.
// 사운드 화면(kr_sound.nss)과 같은 틀: 원작 환경 설정 줄 꼴 바탕(kr_mov_bg.png) + 원작 감상 화면 은빛 띠(kr_bars.png) + 원작 닫기 단추.
// 열림 = 원작이 켜는 깃발(#mvOPplay · #lx0201_mv01) 또는 그 장면을 끝까지 읽음(Conquest) 또는 회상 「모두 열기」(#KS_ALLOPEN).
// 함수에 식·인자를 넘기지 않는다(이 엔진은 인자가 밀린다 - n2system 대본 함정). 재생은 원작 명령 그대로, 4K 판은 DLL 이 이름으로 바꿔 끼움.
#include "nss/function.nss"
#include "nss/function_move.nss"
#include "nss/function_select.nss"

chapter main
{
	$SYSTEM_menu_lock = true;
	$SYSTEM_backlog_lock = true;
	SetVolume("@*", 500, 0, NULL);
	Wait(500);
	KmCalc();
	$KM_RUN=true;
	while($KM_RUN){
		KmList();
	}
	CreateColor("kz_black",31000,0,0,1024,576,BLACK);
	Fade("kz_black",0,0,null,true);
	Fade("kz_black",300,1000,null,true);
	Wait(300);
	Delete("*");
}

function KmCover()
{
	Delete("km_cover");
	CreateTexture("km_cover",30000,0,0,SCREEN);
}

function KmSounds()
{
	CreateSound("km_se_ok",SE,"sound/se/SE_システム_エクストラ_決定.ogg");
	CreateSound("km_se_end",SE,"sound/se/SE_システム_エクストラ_終了.ogg");
	SetAlias("km_se_ok","km_se_ok");
	SetAlias("km_se_end","km_se_end");
}

function KmText($mt_nm,$mt_p,$mt_x,$mt_y,$mt_w,$mt_h,$mt_t)
{
	CreateText($mt_nm,$mt_p,$mt_x,$mt_y,$mt_w,$mt_h,$mt_t);
	Request($mt_nm,NoLog);
	Request($mt_nm,PushText);
}

function KmClear()
{
	Delete("km_l*");
	Delete("km_r*");
	Delete("KM_*");
}

//■ 보기 전: 검게 덮고 목록을 지운다
function KmBegin()
{
	CreateColor("km_black",30500,0,0,1024,576,BLACK);
	Fade("km_black",0,0,null,true);
	Fade("km_black",300,1000,null,true);
	KmClear();
	Delete("km_cover");
}

//■ 영상 하나: 끝나거나 클릭·키를 누르면 끝(원작 lx9999 의 다시 볼 때와 같은 WaitKey)
function KmWaitMovie()
{
	$km_t=DurationTime("km_mv");
	WaitKey($km_t);
	Fade("km_mv",300,0,null,true);
	Delete("km_mv");
}

//■ 아이캐치: lx0109 의 연출 덩어리 그대로(검은 화면을 바탕으로 찍고 시작)
function KmEyecatch()
{
	Delete("km_black");
@@EYECATCH@@
}

//■ 목록: 세 줄, 아래 줄 = 영상 · 닫기
function KmList()
{
	KmCover();
	Delete("km_black");
	KmClear();
	KmSounds();
	CreateTexture("km_lbg",2001,0,0,"nss/kr_mov_bg.png");
	SetVertex("km_lbg",0,0);
	Zoom("km_lbg",0,250,250,null,false);
	Request("km_lbg",Smoothing);
	CreateTexture("km_lbar",2015,0,0,"nss/kr_bars.png");
	SetVertex("km_lbar",0,0);
	Zoom("km_lbar",0,250,250,null,false);
	Request("km_lbar",Smoothing);
	CreateChoice("KM_EXIT");
	CreateTexture("KM_EXIT/MouseUsual/hit",0,924,542,"cg/sys/extra/cglib/hit02.png");
	CreateTexture("KM_EXIT/MouseUsual/img",2020,924,542,"cg/sys/extra/cglib/exit-001.png");
	SetVertex("KM_EXIT/MouseUsual/img",0,0);
	Zoom("KM_EXIT/MouseUsual/img",0,250,250,null,false);
	Request("KM_EXIT/MouseUsual/img",Smoothing);
	CreateTexture("KM_EXIT/MouseOver/img",2021,924,542,"cg/sys/extra/cglib/exit-002.png");
	SetVertex("KM_EXIT/MouseOver/img",0,0);
	Zoom("KM_EXIT/MouseOver/img",0,250,250,null,false);
	Request("KM_EXIT/MouseOver/img",Smoothing);
	CreateTexture("KM_EXIT/MouseClick/img",2021,924,542,"cg/sys/extra/cglib/exit-003.png");
	SetVertex("KM_EXIT/MouseClick/img",0,0);
	Zoom("KM_EXIT/MouseClick/img",0,250,250,null,false);
	Request("KM_EXIT/MouseClick/img",Smoothing);
	SetFont("Noto Sans KR", 15, 8A8A8A, E6E6E6, 500, RIGHTDOWN);
	KmText("km_llabel",2022,18,546,420,34,"영상");
@@ROWS@@	Fade("*/MouseOver/*",0,0,null,false);
	Fade("*/MouseClick/*",0,0,null,false);
	Fade("km_cover",200,0,null,true);
	Delete("km_cover");
	$SYSTEM_r_button_down=false;
	$KM_LOOP=true;
	while($KM_LOOP){
		select{
			if($SYSTEM_r_button_down){$SYSTEM_r_button_down=false;$KM_LOOP=false;$KM_RUN=false;break;}
			case km_r01{Request("@km_se_ok",Play);KmBegin();CreateMovie("km_mv",31000,center,middle,false,false,"dx/mv_op.ngs");KmWaitMovie();$KM_LOOP=false;}
			case km_r02{Request("@km_se_ok",Play);KmBegin();KmEyecatch();$KM_LOOP=false;}
			case km_r03{Request("@km_se_ok",Play);KmBegin();CreateMovie("km_mv",31000,center,middle,false,false,"dx/mv_lx0201.ngs");KmWaitMovie();$KM_LOOP=false;}
			case KM_EXIT{Request("@km_se_end",Play);$KM_LOOP=false;$KM_RUN=false;}
		}
	}
}

//■ 열림
function KmCalc()
{
	$KM_OK1=false;if(#KS_ALLOPEN){$KM_OK1=true;}
	if(#mvOPplay){$KM_OK1=true;}
	$KM_OK3=false;if(#KS_ALLOPEN){$KM_OK3=true;}
	if(#lx0201_mv01){$KM_OK3=true;}
	$KM_OK2=false;if(#KS_ALLOPEN){$KM_OK2=true;}
	if($KM_OK3){$KM_OK2=true;}
	if(!$KM_OK2){$kc_r=Conquest("nss/lx0109.nss","lx0109.nss",null);if($kc_r){$KM_OK2=true;}}
	if(!$KM_OK2){$kc_r=Conquest("nss/lx0300.nss","lx0300.nss",null);if($kc_r){$KM_OK2=true;}}
	if(!$KM_OK2){$kc_r=Conquest("nss/lx0500.nss","lx0500.nss",null);if($kc_r){$KM_OK2=true;}}
}
'''

TITLES = ['오프닝', '아이캐치', '2장 영상']


def kr_movie(lx0109, sound_nss):
    """kr_movie.nss 바이트. 일본어(효과음 파일 이름·아이캐치 덩어리)는 cp932, 나머지 한국어는 cp949."""
    # 효과음 파일 이름은 사운드 화면 대본에서 바이트 그대로 빌린다(cp932 이름)
    m_ok = re.search(rb'CreateSound\("ku_se_ok",SE,"([^"]+)"\);', sound_nss)
    m_end = re.search(rb'CreateSound\("ku_se_end",SE,"([^"]+)"\);', sound_nss)
    assert m_ok and m_end
    rows = ''.join(_row(k, t) for k, t in enumerate(TITLES, 1))
    head, tail = HEAD.split('@@EYECATCH@@')
    head = head.replace('\n', '\r\n')
    tail = tail.replace('@@ROWS@@', rows).replace('\n', '\r\n').replace('\r\r\n', '\r\n')
    hb = head.encode(K)
    hb = hb.replace('"sound/se/SE_システム_エクストラ_決定.ogg"'.encode(K, 'replace'), b'"' + m_ok.group(1) + b'"')
    hb = hb.replace('"sound/se/SE_システム_エクストラ_終了.ogg"'.encode(K, 'replace'), b'"' + m_end.group(1) + b'"')
    assert m_ok.group(1) in hb and m_end.group(1) in hb
    return hb + eyecatch_block(lx0109) + tail.encode(K)


def assets():
    return {p.name: p.read_bytes() for p in sorted((HERE / 'assets').iterdir()) if p.suffix == '.png'}
