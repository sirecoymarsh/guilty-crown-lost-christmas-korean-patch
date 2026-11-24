"""영상실 「연출」 쪽(11-24 사용자 「CG 연출도 영상실에서 다시 볼 수 있게 해줘 자꾸 빠지는 것들이 있는데 스크루지가 캐롤에게서
처음으로 검을 꺼내는 장면같은게 어디에도 없어」).
- 영상실 아래 띠 왼쪽 「영상 · 연출」 두 단추로 쪽을 바꾼다. 연출 쪽 = 회상(kr_scenario)과 같은 원작 CG 감상 꼴 5x4 칸·쪽 띠·이전/다음/닫기.
- 칸 = stage_items.json(대본 전체 조사 → 49곳). 열림 = 그 장면을 끝까지 읽음(Conquest, 회상과 같음) 또는 「모두 열기」.
  잠긴 칸은 회상 자물쇠 그림, 마지막으로 열린 칸이 있는 쪽까지만 넘어감(회상과 같은 스포일러 막기).
- 고르면 stage_replay.py 가 만든 kr_spNN.nss 를 회상 재생(KsPlay)과 같은 준비로 부르고, 끝나면 이 쪽으로 돌아온다.
- 대본 함정: 함수에 식을 넘기지 않는다(글자 그대로 숫자만), 첨자 변수는 처음에 -1, 칸 이름은 km_ 로 시작하지 않게(km_s* 는 소리).
"""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
K = 'cp949'
ITEMS = json.loads((HERE / 'stage_items.json').read_text('utf-8'))
JP = {'@BG@': 'cg/sys/extra/cglib/背景.png', '@CUR@': 'cg/sys/extra/cglib/選択カーソル.png'}


def _enc(text: str) -> bytes:
    """한국어는 cp949, 일본어 파일 이름은 cp932 로(원작 파일 이름 그대로)."""
    out = b''
    for part in text.split('\x00'):
        if part.startswith('JP:'):
            out += part[3:].encode('cp932')
        else:
            out += part.encode(K)
    return out


def jp(s):
    return '\x00JP:' + s + '\x00'


def data_fn():
    s = ('function KmStageData()\n{\n'
         '\t$KMS_MOD=null;Array($KMS_MOD);DeleteArray($KMS_MOD);\n'
         '\t$KMS_SC=null;Array($KMS_SC);DeleteArray($KMS_SC);\n'
         '\t$KMS_TT=null;Array($KMS_TT);DeleteArray($KMS_TT);\n'
         '\t$KMS_TH=null;Array($KMS_TH);DeleteArray($KMS_TH);\n')
    for k, it in enumerate(ITEMS):
        s += (f'\t$KMS_MOD[{k}]="kr_sp{k + 1:02d}.nss";$KMS_SC[{k}]="{it["file"]}";$KMS_TT[{k}]="{it["title"]}";'
              f'$KMS_TH[{k}]="{jp(it["thumb"])}";\n')
    s += f'\t$KMS_N={len(ITEMS)};\n}}\n'
    return s


NSS = r'''
//■ 연출(Claude 11-24): 대본 속 CG 연출 다시 보기 - 회상과 같은 원작 CG 감상 꼴. 장면을 끝까지 읽어야 열린다.
function KmTabs()
{
	CreateChoice("KM_TAB0");
	CreateColor("KM_TAB0/MouseUsual/hit",2020,10,544,52,30,0x000000);
	Request("KM_TAB0/MouseUsual/hit",Erase);
	CreateColor("KM_TAB0/MouseOver/img",2021,10,544,52,30,0xF2F2F2);
	CreateColor("KM_TAB0/MouseClick/img",2021,10,544,52,30,0x58B6A4);
	CreateChoice("KM_TAB1");
	CreateColor("KM_TAB1/MouseUsual/hit",2020,64,544,52,30,0x000000);
	Request("KM_TAB1/MouseUsual/hit",Erase);
	CreateColor("KM_TAB1/MouseOver/img",2021,64,544,52,30,0xF2F2F2);
	CreateColor("KM_TAB1/MouseClick/img",2021,64,544,52,30,0x58B6A4);
	if($KM_TAB==1){SetFont("Noto Sans KR", 15, 8A8A8A, E6E6E6, 500, RIGHTDOWN);}else{SetFont("Noto Sans KR", 15, 2A2A2A, E6E6E6, 700, RIGHTDOWN);}
	KmText("km_ltab0",2022,18,546,60,34,"영상");
	if($KM_TAB==1){SetFont("Noto Sans KR", 15, 2A2A2A, E6E6E6, 700, RIGHTDOWN);}else{SetFont("Noto Sans KR", 15, 8A8A8A, E6E6E6, 500, RIGHTDOWN);}
	KmText("km_ltab1",2022,72,546,60,34,"연출");
}

function KmBtn($kmb_nm,$kmb_x,$kmb_y,$kmb_img)
{
	$kmb_hit=$kmb_nm+"/MouseUsual/hit";
	$kmb_u=$kmb_nm+"/MouseUsual/img";
	$kmb_o=$kmb_nm+"/MouseOver/img";
	$kmb_c=$kmb_nm+"/MouseClick/img";
	$kmb_f1="cg/sys/extra/cglib/"+$kmb_img+"-001.png";
	$kmb_f2="cg/sys/extra/cglib/"+$kmb_img+"-002.png";
	$kmb_f3="cg/sys/extra/cglib/"+$kmb_img+"-003.png";
	CreateChoice($kmb_nm);
	CreateTexture($kmb_hit,0,$kmb_x,$kmb_y,"cg/sys/extra/cglib/hit02.png");
	CreateTexture($kmb_u,2020,$kmb_x,$kmb_y,$kmb_f1);
	SetVertex($kmb_u,0,0);
	Zoom($kmb_u,0,250,250,null,false);
	Request($kmb_u,Smoothing);
	CreateTexture($kmb_o,2021,$kmb_x,$kmb_y,$kmb_f2);
	SetVertex($kmb_o,0,0);
	Zoom($kmb_o,0,250,250,null,false);
	Request($kmb_o,Smoothing);
	CreateTexture($kmb_c,2021,$kmb_x,$kmb_y,$kmb_f3);
	SetVertex($kmb_c,0,0);
	Zoom($kmb_c,0,250,250,null,false);
	Request($kmb_c,Smoothing);
}

function KmStageOpen()
{
	$KMS_OPEN=false;
	$kso_s=$KMS_SC[$kso_n];
	$kso_f="nss/"+$kso_s;
	$kso_r=Conquest($kso_f,$kso_s,null);
	if($kso_r){$KMS_OPEN=true;}
	if(#KS_ALLOPEN){$KMS_OPEN=true;}
}

function KmStageMax()
{
	$KMS_MAXP=1;
	$kso_n=0;
	while($kso_n<$KMS_N){
		KmStageOpen();
		if($KMS_OPEN){$KMS_MAXP=Integer($kso_n/20)+1;}
		$kso_n++;
	}
}

function KmStagePage($kmp_d)
{
	$KMS_PAGE=$KMS_PAGE+$kmp_d;
	if($KMS_PAGE>$KMS_MAXP){$KMS_PAGE=1;}
	if($KMS_PAGE<1){$KMS_PAGE=$KMS_MAXP;}
	$KM_LOOP=false;
}

function KmStageList()
{
	KmCover();
	Delete("km_black");
	KmClear();
	KmSounds();
	if($KMS_PAGE>$KMS_MAXP){$KMS_PAGE=$KMS_MAXP;}
	CreateTexture("km_lbg",2001,0,0,"@BG@");
	KmBtn("KM_SBACK",732,542,"back");
	KmBtn("KM_SNEXT",831,542,"next");
	KmBtn("KM_EXIT",924,542,"exit");
	$kml_bar=String("cg/sys/extra/cglib/no%03d.png",$KMS_PAGE);
	CreateTexture("km_lbar",2015,0,0,$kml_bar);
	SetVertex("km_lbar",0,0);
	Zoom("km_lbar",0,250,250,null,false);
	Request("km_lbar",Smoothing);
	KmTabs();
	$kml_base=($KMS_PAGE-1)*20;
	$kml_i=0;
	while($kml_i<20){
		$kml_n=$kml_base+$kml_i;
		if($kml_n<$KMS_N){
			$kml_nx=$kml_i%5;
			$kml_x=($kml_nx*200)+16;
			$kml_ny=Integer($kml_i/5);
			$kml_y=($kml_ny*124)+36;
			$kso_n=$kml_n;
			KmStageOpen();
			if($KMS_OPEN){
				$kml_cn=String("kmsc%02d",$kml_i);
				$kml_hit=$kml_cn+"/MouseUsual/hit";
				$kml_ov=$kml_cn+"/MouseOver/img";
				$kml_ck=$kml_cn+"/MouseClick/img";
				$kml_th=String("km_lsth%02d",$kml_i);
				$kml_bd=String("km_lsbd%02d",$kml_i);
				$kml_tt=String("km_lstt%02d",$kml_i);
				$kml_file=$KMS_TH[$kml_n];
				$kml_k=$kml_n+1;
				$kml_txt=String("%02d  ",$kml_k);
				$kml_ttl=$KMS_TT[$kml_n];
				$kml_txt=$kml_txt+$kml_ttl;
				$kml_by=$kml_y+80;
				$kml_tx=$kml_x+7;
				$kml_ty=$kml_y+83;
				CreateChoice($kml_cn);
				SetAlias($kml_cn,$kml_cn);
				CreateColor($kml_hit,2010,$kml_x,$kml_y,192,108,0x000000);
				Request($kml_hit,Erase);
				CreateTexture($kml_th,2010,$kml_x,$kml_y,$kml_file);
				CreateColor($kml_bd,2011,$kml_x,$kml_by,192,28,0x000000);
				Fade($kml_bd,0,650,null,false);
				SetFont("Noto Sans KR", 15, FFFFFF, 000000, 500, RIGHTDOWN);
				KmText($kml_tt,2012,$kml_tx,$kml_ty,184,24,$kml_txt);
				CreateTexture($kml_ov,2013,$kml_x,$kml_y,"@CUR@");
				CreateTexture($kml_ck,2013,$kml_x,$kml_y,"@CUR@");
			}else{
				$kml_lk=String("km_lslk%02d",$kml_i);
				CreateTexture($kml_lk,2010,$kml_x,$kml_y,"nss/kr_scn_lock.png");
				SetVertex($kml_lk,0,0);
				Zoom($kml_lk,0,250,250,null,false);
				Request($kml_lk,Smoothing);
			}
		}
		$kml_i++;
	}
	Fade("*/MouseOver/*",0,0,null,false);
	Fade("*/MouseClick/*",0,0,null,false);
	Fade("km_cover",250,0,null,true);
	Delete("km_cover");
	$SYSTEM_r_button_down=false;
	$SYSTEM_mousewheel_down=false;
	$SYSTEM_mousewheel_up=false;
	$KM_LOOP=true;
	while($KM_LOOP){
		select{
			if($SYSTEM_r_button_down){$SYSTEM_r_button_down=false;$KM_LOOP=false;$KM_RUN=false;break;}
			if($SYSTEM_mousewheel_down){$SYSTEM_mousewheel_down=false;Request("@km_se_ok",Play);KmStagePage(1);break;}
			if($SYSTEM_mousewheel_up){$SYSTEM_mousewheel_up=false;Request("@km_se_ok",Play);KmStagePage(-1);break;}
@CASES@
			case KM_SNEXT{Request("@km_se_ok",Play);KmStagePage(1);}
			case KM_SBACK{Request("@km_se_ok",Play);KmStagePage(-1);}
			case KM_TAB0{Request("@km_se_ok",Play);$KM_TAB=0;$KM_LOOP=false;}
			case KM_EXIT{Request("@km_se_end",Play);$KM_LOOP=false;$KM_RUN=false;}
		}
	}
}

function KmStagePick($kpi)
{
	Request("@km_se_ok",Play);
	$KMS_SEL=(($KMS_PAGE-1)*20)+$kpi;
	KmStagePlay();
	$KM_LOOP=false;
}

//■ 연출 하나 재생: 회상 재생(KsPlay)과 같은 준비로 kr_spNN.nss 를 부른다. 앞부분을 덮는 검은 판 kz_spv 는 그 모듈이 걷는다.
function KmStagePlay()
{
	$kp_ts=#SYSTEM_text_speed;
	$kp_ti=$SYSTEM_text_interval;
	$kp_r0=#ClearRoll00;
	$kp_r1=#ClearRoll01;
	CreateColor("kz_black",31000,0,0,1024,576,BLACK);
	Fade("kz_black",0,0,null,true);
	Fade("kz_black",400,1000,null,true);
	KrLyStopFor("@*");SetVolume("@*", 400, 0, NULL);
	Wait(400);
	Delete("*");
	ClearBacklog();
	$BOX_Init = true;
	$BGM_Init = true;
	$Logo = true;
	$GameStart = 1;
	$PLACE_title = false;
	$SYSTEM_menu_lock=false;
	$SYSTEM_save_lock=true;
	$SYSTEM_load_lock=true;
	$SYSTEM_backselect_lock=true;
	$SYSTEM_title_lock=false;
	$SYSTEM_skip_lock=false;
	$SYSTEM_text_erase_lock=false;
	$SYSTEM_backlog_lock=false;
	$SYSTEM_twitter_lock=false;
	$SYSTEM_super_lock=false;
	$LOCAL_extra_lock=true;
	$SYSTEM_skip=false;
	#SYSTEM_skip_express=false;
	$SYSTEM_text_auto=false;
	$SYSTEM_text_auto_lock=false;
	$SYSTEM_text_erase=false;
	$SYSTEM_text_waitkey=true;
	CreateWindow("EFWIN", 20000, 0, 0, 1024, 576, false);
	SetAlias("EFWIN", "EFWIN");
	Request("EFWIN", Lock);
	CreateName("GLOBAL_PROCESS");
	SetAlias("GLOBAL_PROCESS","GLOBAL_PROCESS");
	Request("GLOBAL_PROCESS",Lock);
	CreateColor("kz_spv",31000,0,0,1024,576,BLACK);
	SetAlias("kz_spv","kz_spv");
	$KR_REPLAY=true;
	$GameName=$KMS_SC[$KMS_SEL];
	$ConGameName="nss/"+$GameName;
	$GameName2=$GameName+"_MAIN";
	$AllRead=true;
	$kms_m=$KMS_MOD[$KMS_SEL];
	$ks_call="nss/"+$kms_m+"->"+$kms_m;
	call_scene $ks_call;
	$KR_REPLAY=false;
	#SYSTEM_text_speed=$kp_ts;
	$SYSTEM_text_interval=$kp_ti;
	$SYSTEM_text_waitkey=true;
	#ClearRoll00=$kp_r0;
	#ClearRoll01=$kp_r1;
	TextBoxDelete(0);
	CreateColor("kz_black",31000,0,0,1024,576,BLACK);
	Fade("kz_black",0,0,null,true);
	Fade("kz_black",500,1000,null,true);
	KrLyStopFor("@*");SetVolume("@*", 500, 0, NULL);
	Wait(500);
	Request("EFWIN", UnLock);
	Request("GLOBAL_PROCESS", UnLock);
	Delete("*");
	ClearBacklog();
	$SYSTEM_skip=false;
	#SYSTEM_skip_express=false;
	$SYSTEM_text_auto=false;
	$SYSTEM_menu_lock=true;
	$SYSTEM_backlog_lock=true;
	$SYSTEM_save_lock=false;
	$SYSTEM_load_lock=false;
	$SYSTEM_backselect_lock=false;
	$GameName=false;
	CreateColor("kz_black",31000,0,0,1024,576,BLACK);
	KmCover();
	Delete("kz_black");
}
'''


def nss_text() -> str:
    cases = ''.join(f'\t\t\tcase @kmsc{i:02d}{{KmStagePick({i});}}\n' for i in range(20))
    t = NSS.replace('@CASES@\n', cases).replace('"@BG@"', '"' + jp(JP['@BG@']) + '"').replace('"@CUR@"', '"' + jp(JP['@CUR@']) + '"')
    return t + '\n' + data_fn()


def patch_room(b: bytes) -> bytes:
    def one(old, new):
        nonlocal b
        o, n = old.encode(K), _enc(new)
        assert b.count(o) == 1, (old[:70], b.count(o))
        b = b.replace(o, n)
    one('\tKmCalc();\r\n\t$KM_RUN=true;\r\n\twhile($KM_RUN){\r\n\t\tKmList();\r\n\t}',
        '\tKmCalc();\r\n'
        '\t// 11-24 「연출」 쪽(stage_room.py)\r\n'
        '\t$KM_TAB=0;$KMS_PAGE=1;$KMS_SEL=-1;$kml_n=-1;$kml_i=-1;$kml_base=-1;$kso_n=-1;$kpi=-1;\r\n'
        '\tKmStageData();\r\n\tKmStageMax();\r\n'
        '\t$KM_RUN=true;\r\n\twhile($KM_RUN){\r\n\t\tif($KM_TAB==1){KmStageList();}else{KmList();}\r\n\t}')
    one('\tSetFont("Noto Sans KR", 15, 8A8A8A, E6E6E6, 500, RIGHTDOWN);\r\n\tKmText("km_llabel",2022,18,546,420,34,"영상");\r\n',
        '\tKmTabs();   // 11-24 아래 띠 「영상 · 연출」\r\n')
    one('\t\t\tcase KM_EXIT{', '\t\t\tcase KM_TAB1{Request("@km_se_ok",Play);$KM_TAB=1;$KM_LOOP=false;}\r\n\t\t\tcase KM_EXIT{')
    one('function KmClear()\r\n{\r\n', 'function KmClear()\r\n{\r\n\tDelete("kmsc*");\r\n')
    b = b + _enc(nss_text().replace('\n', '\r\n'))
    return b


def modules(get_scene) -> dict:
    """get_scene(파일 이름) → 그 장면 모듈 바이트(최종 빌드판). kr_spNN.nss 들."""
    import stage_replay as sr
    out = {}
    for k, it in enumerate(ITEMS, 1):
        mb, _ = sr.build_module(get_scene(it['file']), it['file'], it['start'], it['end'])
        out[f'kr_sp{k:02d}.nss'] = mb.replace(b'scene kr_sp.nss', f'scene kr_sp{k:02d}.nss'.encode())
    return out
