"""시나리오 열람(Claude 11-02, 사용자 결정: 기신비상식 차트 · 읽은 장면만 · 한 장면 보고 돌아옴 · 제목만)을 nss.npa 에 넣는다.
- kr_scenario.nss: 단계(페이즈)별 쪽 = 원작 CG 감상 화면 틀(5x4 칸, 이전/다음/닫기), 칸 = 감상 썸네일 + 제목 띠,
  잠긴 칸 = 「읽지 않음」(원작 「없음」과 같은 글꼴), 칸을 누르면 상세(큰 CG·단계·차례·제목·「여기서 보기」·이전/다음 장면),
  「여기서 보기」= 그 장면 본문만 call_scene → 끝나면 그 상세로. 읽음 = Conquest("nss/X","X",null)(장면 끝까지 본 기록, 공용 cqst).
- 0_boot.nss: 타이틀 「시나리오」 단추(불러오기 다음) · 단추 자리 다시 놓기 · 고르면 $TitleSelect=3 → 타이틀을 모두 지우고 열람 → 끝나면 TitleClear 로 타이틀 처음부터.
- 그림: kr_title_scenario-000..003.png(단추, make_title_button.py), kr_scn_lock.png(make_tile_label.py) 를 nss.npa 에 같이.
python -X utf8 gen_viewer.py <원래 nss.npa> <scenes.json> <titles.json|-> <출력 nss.npa>
글자 인코딩: 원작처럼 한국어는 cp949, 일본어 파일 이름은 cp932 — J(...) 로 감싼 조각만 cp932."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, r'F:\AI\gclx-4k\tools')
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA
from npa_build import build

src_npa, scenes_json, titles_json, out_npa = sys.argv[1:5]
HERE = Path(__file__).parent
scenes = json.load(open(scenes_json, encoding='utf-8'))
titles = json.load(open(titles_json, encoding='utf-8')) if titles_json != '-' else {}

# ---------------------------------------------------------------- data
# 쪽 = 이야기 차례대로 20칸씩(사용자 11-02 「페이지로 장을 나누기보다, 순차적으로 채우고 페이즈는 따로 표시」).
# Phase 는 그 Phase 첫 칸의 꼬리표 「Phase NN」 과 상세 화면 윗줄 「Phase NN 이름」(원작 세이브 칸 제목과 같은 꼴)으로.
PER = 20
npages = (len(scenes) + PER - 1) // PER
phase_names = json.load(open(HERE / 'phase_names.json', encoding='utf-8'))
pstart = {}
for i, s in enumerate(scenes):
    pstart.setdefault(s['phase'], i)
ending_no = {}
for s in scenes:
    if s['ending']:
        ending_no[s['file']] = len(ending_no) + 1


def esc(t):
    """반각 . , 는 이 엔진 글자 안에서 멈춤 명령 - &. &, 로(원작 대사와 같은 탈출)."""
    return re.sub(r'(?<!&)([.,])', r'&\1', t)


def title_of(i, s):
    t = titles.get(s['file'])
    if t:
        return t
    if s['ending']:
        return f'결말 {ending_no[s["file"]]}'
    return f'장면 {i - pstart[s["phase"]] + 1:02d}'


def pos_of(i, s):
    """상세 화면 둘째 줄: 몇 번째 장면(결말은 결말 번호 - 열린 뒤에만 보이는 화면)."""
    if s['ending']:
        return f'{i + 1}번째 장면 · 결말 {ending_no[s["file"]]}'
    return f'{i + 1}번째 장면'


def phase_line(s):
    """상세 화면 윗줄 = 원작 세이브 칸 제목 꼴 「Phase NN 이름」(sys_save.nss String("Phase %02d %s"))."""
    return phase_names[str(s['phase'])]   # 번호는 원작 표지 그림(단계·숫자)이 보인다


data = ['function KsData()', '{',
        '\t$KS_FILE=null;Array($KS_FILE);DeleteArray($KS_FILE);',
        '\t$KS_TH=null;Array($KS_TH);DeleteArray($KS_TH);',
        '\t$KS_CG=null;Array($KS_CG);DeleteArray($KS_CG);',
        '\t$KS_TT=null;Array($KS_TT);DeleteArray($KS_TT);',
        '\t$KS_PH=null;Array($KS_PH);DeleteArray($KS_PH);',
        '\t$KS_K=null;Array($KS_K);DeleteArray($KS_K);',
        '\t$KS_ALSO=null;Array($KS_ALSO);DeleteArray($KS_ALSO);',
        '\t$KS_PS=null;Array($KS_PS);DeleteArray($KS_PS);',
        '\t$KS_PC=null;Array($KS_PC);DeleteArray($KS_PC);',
        '\t$KS_POS=null;Array($KS_POS);DeleteArray($KS_POS);',
        '\t$KS_LBL=null;Array($KS_LBL);DeleteArray($KS_LBL);',
        '\t$KS_EN=null;Array($KS_EN);DeleteArray($KS_EN);',
        '\t$KS_PG=null;Array($KS_PG);DeleteArray($KS_PG);',
        '\t$KS_PTAG=null;Array($KS_PTAG);DeleteArray($KS_PTAG);',
        '\t$KS_PHL=null;Array($KS_PHL);DeleteArray($KS_PHL);',
        '\t$KS_SUM=null;Array($KS_SUM);DeleteArray($KS_SUM);']
# 장면 요약(사용자 11-02 「각 시나리오별로 간단한 요약도」): 상세 화면 큰 CG 아래. 지침 SUMMARY_BRIEF.md, 모은 것 summaries.json
summaries = json.load(open(HERE / 'summaries.json', encoding='utf-8'))
for i, s in enumerate(scenes):
    # $KS_EN: 결말이면 「결말 N」 - 실제로 본 결말만 제목을 보이고, 검수용 모두 열기로만 열린 결말은 번호 그대로(사용자 지도 규칙)
    en = f'결말 {ending_no[s["file"]]}' if s['ending'] else ''
    tag = f'단계 {s["phase"]:02d}' if pstart[s['phase']] == i else ''
    data.append(f'\t$KS_FILE[{i}]="{s["file"]}";$KS_TH[{i}]=J("cg/{s["thumb"]}");$KS_CG[{i}]=J("{s["cg"]}");'
                f'$KS_TT[{i}]="{esc(title_of(i, s))}";$KS_PH[{i}]={s["phase"]};$KS_K[{i}]={i + 1};$KS_ALSO[{i}]="{s["also"][0] if s["also"] else ""}";'
                f'$KS_POS[{i}]="{pos_of(i, s)}";$KS_EN[{i}]="{en}";$KS_PG[{i}]={i // PER + 1};$KS_PTAG[{i}]="{tag}";$KS_PHL[{i}]="{esc(phase_line(s))}";'
                f'$KS_SUM[{i}]="{esc(summaries.get(s["file"], ""))}";')
for n in range(1, npages + 1):
    start = (n - 1) * PER
    data.append(f'\t$KS_PS[{n}]={start};$KS_PC[{n}]={min(PER, len(scenes) - start)};$KS_LBL[{n}]="회상 · {n} / {npages}쪽";')
data += [f'\t$KS_NPAGE={npages};$KS_N={len(scenes)};', '}']

# 상세 화면 큰 CG: 1024x576 은 625‰ 로 틀(24,60 640x360)에 꼭 맞고, 세로로 긴 그림·옆으로 긴 그림만 틀 안에 들도록 줄여 가운데에.
# 값은 모두 상수로 쓴다(이 엔진은 Zoom·Move 에 변수를 넘기면 어긋났다). 크기는 cg_sizes.py 가 잰 cg_sizes.json.
cg_sizes = json.load(open(HERE / 'cg_sizes.json', encoding='utf-8'))
place = ['function KsCgPlace()', '{']
first = True
for s in scenes:
    w, h = cg_sizes[s['cg']]
    if (w, h) == (1024, 576):
        continue
    z = min(640 * 1000 // w, 360 * 1000 // h)
    x, y = 24 + (640 - w * z // 1000) // 2, 60 + (360 - h * z // 1000) // 2
    cond = 'if' if first else 'else if'
    first = False
    place.append(f'\t{cond}($kd_file=="{s["file"]}"){{CreateTexture("ks_dcg",2005,{x},{y},$kd_cg);SetVertex("ks_dcg",0,0);Zoom("ks_dcg",0,{z},{z},null,false);}}')
place.append(('\telse' if not first else '\tif(true)') + '{CreateTexture("ks_dcg",2005,24,60,$kd_cg);SetVertex("ks_dcg",0,0);Zoom("ks_dcg",0,625,625,null,false);}')
place += ['\tRequest("ks_dcg",Smoothing);', '}']
data += place
DATA = '\n'.join(data)

SE_OK = 'J("sound/se/SE_システム_エキストラ_決定.ogg")'
SE_END = 'J("sound/se/SE_システム_エキストラ_終了.ogg")'
BG = 'J("cg/sys/extra/cglib/背景.png")'
CUR = 'J("cg/sys/extra/cglib/選択カーソル.png")'

NSS = (Path(__file__).parent / 'viewer_template.nss').read_text('utf-8')


def card_cases():
    return '\n'.join(f'\t\t\tcase @ks_c{i:02d}{{KsPick({i});}}' for i in range(20))


body = NSS.replace('«CARD_CASES»', card_cases()) + '\n' + DATA + '\n'
FLAGS = '"逃げろ！","自分を取り戻す","解放する","玄周を助ける","キャロルの手を離さない","生きる"'
body = body.replace('«FLAGS»', 'J(' + FLAGS.replace('"', '\x01') + ')')
for k, v in (('«SE_OK»', SE_OK), ('«SE_END»', SE_END), ('«BG»', BG), ('«CUR»', CUR)):
    body = body.replace(k, v)


def encode(text):
    """Korean (and everything else) in cp949; J("...") pieces in cp932 (the engine looks files up by these bytes)."""
    out = bytearray(); pos = 0
    for m in re.finditer(r'J\(("[^"]*"|\x01[^)]*)\)', text):
        out += text[pos:m.start()].encode('cp949')
        seg = m.group(1)
        if seg.startswith('\x01'):
            out += seg.replace('\x01', '"').encode('cp932')
        else:
            out += seg.encode('cp932')
        pos = m.end()
    out += text[pos:].encode('cp949')
    return bytes(out).replace(b'\n', b'\r\n')


nss = encode(body)
assert b'J(' not in nss and b'\xc2\xab' not in nss and '«'.encode('cp949', 'replace') not in nss

# ---------------------------------------------------------------- kr_sound.nss (사운드 모드)
# 곡 표 music_list.json(music_unlock.py): 원작 InitBGM 표 + 결말 노래. 줄·선택·열림 계산은 모두 상수로 풀어 쓴다.
tracks = json.load(open(HERE / 'music_list.json', encoding='utf-8'))
SL = json.load(open(HERE / 'snd_layout.json'))   # make_ui_assets.py 가 그린 줄 자리
rows, cases, calc = [], [], ['function KuCalc()', '{', '\t$kc_r=false;']
for k, t in enumerate(tracks, 1):
    col, r = (k - 1) // SL['rows'], (k - 1) % SL['rows']
    x, y = SL['col_x'][col], SL['row_y0'] + r * SL['pitch']
    nm = f'ku_r{k:02d}'
    label = esc(t['name'])
    # 이름 칸 안쪽(바탕 그림의 0B 칸): 올림 26, 누름·재생 중은 원작 단계 표지의 청록 쪽
    ix, iy, iw, ih = x + SL['item_x'] + 2, y + 1, SL['item_w'] - 12, SL['h'] - 2
    rw, tx = SL.get('row_w', SL['num_x'] + SL['num_w']), x + SL['item_x'] + 14
    rows += [f'\tif($KU_OK{k}){{',
             f'\t\tCreateChoice("{nm}");',
             f'\t\tCreateColor("{nm}/MouseUsual/hit",2010,{x},{y},{rw},{SL["h"]},0x000000);',
             f'\t\tRequest("{nm}/MouseUsual/hit",Erase);',
             f'\t\tCreateColor("{nm}/MouseOver/img",2011,{ix},{iy},{iw},{ih},0x262626);',
             f'\t\tCreateColor("{nm}/MouseClick/img",2011,{ix},{iy},{iw},{ih},0x2A6F63);',
             f'\t\tif($KU_NOW=={k}){{CreateColor("ku_ln{k:02d}",2010,{ix},{iy},{iw},{ih},0x163A36);SetFont("Noto Sans KR", 14, 8BE9D7, 000000, 600, RIGHTDOWN);KuText("ku_lp{k:02d}",2012,{ix + iw - 24},{y + 2},24,24,"▶");}}',
             '\t\tSetFont("Noto Sans KR", 16, DADADA, 000000, 600, RIGHTDOWN);',
             f'\t\tKuText("ku_lt{k:02d}",2012,{tx},{y + 1},{iw - 40},26,"{label}");',
             '\t}else{',
             '\t\tSetFont("Noto Sans KR", 16, 4A4A4A, 000000, 500, RIGHTDOWN);',
             f'\t\tKuText("ku_lt{k:02d}",2012,{tx},{y + 1},{iw - 40},26,"아직 듣지 않은 곡");',
             '\t}']
    cases.append(f'\t\t\tcase {nm}{{Request("@ku_se_ok",Play);if($KU_NOW!={k}){{KuFade();CreateBGM("kubgm","{t["file"]}");SoundPlay("@kubgm",300,1000,true);$KU_NOW={k};}}$KU_LOOP=false;}}')
    if t['always']:
        calc.append(f'\t$KU_OK{k}=true;')
        continue
    calc.append(f'\t$KU_OK{k}=false;if(#KS_ALLOPEN){{$KU_OK{k}=true;}}')
    for f in t['scenes']:
        calc.append(f'\tif(!$KU_OK{k}){{$kc_r=Conquest("nss/{f}","{f}",null);if($kc_r){{$KU_OK{k}=true;}}}}')
calc.append('}')
SND = (HERE / 'sound_template.nss').read_text('utf-8')
SND = SND.replace('«ROWS»', '\n'.join(rows)).replace('«CASES»', '\n'.join(cases)).replace('«CALC»', '\n'.join(calc))
for k, v in (('«SE_OK»', SE_OK), ('«SE_END»', SE_END), ('«BG»', BG)):
    SND = SND.replace(k, v)
snd_nss = encode(SND)
assert b'J(' not in snd_nss and '«'.encode('cp949', 'replace') not in snd_nss

# ---------------------------------------------------------------- 0_boot.nss
arc = NPA(Path(src_npa))
ent = {e['name']: e for e in arc.entries}
boot = arc.read(ent['0_boot.nss'])


def sub(b, old, new, n=1):
    o, w = old.encode('cp932') if isinstance(old, str) else old, new.encode('cp932') if isinstance(new, str) else new
    assert b.count(o) == n, (old[:60] if isinstance(old, str) else old[:60], b.count(o))
    return b.replace(o, w)


SCN = '''	//■シナリオ閲覧（Claude 11-02）
	CreateChoice("Title_Scenario");
	CreateTexture("Title_Scenario/MouseUsual/hit", 0, 416, 362, "nss/kr_title_scenario-000.png");
	CreateTexture("Title_Scenario/MouseUsual/img", 1000, 416, 362, "nss/kr_title_scenario-001.png");
	SetVertex("Title_Scenario/MouseUsual/img", 0, 0);
	Zoom("Title_Scenario/MouseUsual/img", 0, 250, 250, null, false);
	Request("Title_Scenario/MouseUsual/img", Smoothing);
	CreateTexture("Title_Scenario/MouseOver/img", 1000, 416, 362, "nss/kr_title_scenario-002.png");
	SetVertex("Title_Scenario/MouseOver/img", 0, 0);
	Zoom("Title_Scenario/MouseOver/img", 0, 250, 250, null, false);
	Request("Title_Scenario/MouseOver/img", Smoothing);
	CreateTexture("Title_Scenario/MouseClick/img", 1000, 416, 362, "nss/kr_title_scenario-003.png");
	SetVertex("Title_Scenario/MouseClick/img", 0, 0);
	Zoom("Title_Scenario/MouseClick/img", 0, 250, 250, null, false);
	Request("Title_Scenario/MouseClick/img", Smoothing);

	//■サウンド（Claude 11-02）
	CreateChoice("Title_Sound");
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

'''
# 1) the button, created right after the Load button block
m = re.search(rb'\tRequest\("Title_LOAD/MouseClick/img", Smoothing\);\r?\n', boot)
assert m and boot.count(m.group()) == 1
boot = boot[:m.end()] + b'\r\n' + SCN.encode('cp932').replace(b'\n', b'\r\n') + boot[m.end():]
# 2) layout: original moves (no-ending / one-ending) replaced by a column with the new button after Load
old_layout = re.search(rb'\tif\(!\(#ENDING_OF_XMAS\|\|#ENDING_OF_TOBECONTINUED\)\)\r?\n\t\{\r?\n\t\tMove\("Title_Start/\*/\*".*?\r?\n\t\}\r?\n\tif\(!\(#ENDING_OF_XMAS&&#ENDING_OF_TOBECONTINUED\)\)\r?\n\t\{\r?\n\t\tMove\("Title_Exit/\*/\*", 0, 416, 434, null, false\);\r?\n\t\}\r?\n', boot, re.S)
assert old_layout, 'layout block'
def _col(names, y0, d):
    return ''.join(f'\t\tMove("Title_{n}/*/*", 0, 416, {y0 + i * d}, null, false);\n' for i, n in enumerate(names))


LAYOUT = ('\t//■ボタン配置（Claude 11-02：回想・サウンドを「つづきから」の下に。多い時はロゴに掛からないよう278から詰める）\n'
          '\tif(#ENDING_OF_XMAS&&#ENDING_OF_TOBECONTINUED)\n\t{\n'
          + _col(['Start', 'LOAD', 'Scenario', 'Sound', 'CG', 'Config', 'Liner', 'Exit'], 278, 28) +
          '\t}\n\telse if(#ENDING_OF_XMAS||#ENDING_OF_TOBECONTINUED)\n\t{\n'
          + _col(['Start', 'LOAD', 'Scenario', 'Sound', 'CG', 'Config', 'Exit'], 278, 32) +
          '\t}\n\telse\n\t{\n'
          + _col(['Start', 'LOAD', 'Scenario', 'Sound', 'Config', 'Exit'], 290, 36) +
          '\t}\n')
boot = boot[:old_layout.start()] + LAYOUT.encode('cp932').replace(b'\n', b'\r\n') + boot[old_layout.end():]
# 3) long title fade-in: the new button right after Load
boot = sub(boot, '\t\tFade("Title_LOAD/MouseUsual/*",300,1000,null,false);\r\n\t\tWait(100);\r\n',
           '\t\tFade("Title_LOAD/MouseUsual/*",300,1000,null,false);\r\n\t\tWait(100);\r\n\t\tFade("Title_Scenario/MouseUsual/*",300,1000,null,false);\r\n\t\tWait(100);\r\n\t\tFade("Title_Sound/MouseUsual/*",300,1000,null,false);\r\n\t\tWait(100);\r\n')
# 4) keyboard focus: Load <-> Scenario <-> (CG | Config)
boot = sub(boot, 'function TitleFocus(){\r\n', 'function TitleFocus(){\r\n\tTitleFocusKr();\r\n')
FOCUS = '''function TitleFocusKr(){
	SetNextFocus("Title_LOAD/MouseUsual/hit", "Title_Scenario/MouseUsual/hit",DOWN);
	SetNextFocus("Title_LOAD/MouseUsual/hit", "Title_Scenario/MouseUsual/hit",RIGHT);
	SetNextFocus("Title_Scenario/MouseUsual/hit", "Title_LOAD/MouseUsual/hit",UP);
	SetNextFocus("Title_Scenario/MouseUsual/hit", "Title_LOAD/MouseUsual/hit",LEFT);
	SetNextFocus("Title_Scenario/MouseUsual/hit", "Title_Sound/MouseUsual/hit",DOWN);
	SetNextFocus("Title_Scenario/MouseUsual/hit", "Title_Sound/MouseUsual/hit",RIGHT);
	SetNextFocus("Title_Sound/MouseUsual/hit", "Title_Scenario/MouseUsual/hit",UP);
	SetNextFocus("Title_Sound/MouseUsual/hit", "Title_Scenario/MouseUsual/hit",LEFT);
	if(#ENDING_OF_XMAS||#ENDING_OF_TOBECONTINUED){
		SetNextFocus("Title_Sound/MouseUsual/hit", "Title_CG/MouseUsual/hit",DOWN);
		SetNextFocus("Title_Sound/MouseUsual/hit", "Title_CG/MouseUsual/hit",RIGHT);
		SetNextFocus("Title_CG/MouseUsual/hit", "Title_Sound/MouseUsual/hit",UP);
		SetNextFocus("Title_CG/MouseUsual/hit", "Title_Sound/MouseUsual/hit",LEFT);
	}else{
		SetNextFocus("Title_Sound/MouseUsual/hit", "Title_Config/MouseUsual/hit",DOWN);
		SetNextFocus("Title_Sound/MouseUsual/hit", "Title_Config/MouseUsual/hit",RIGHT);
		SetNextFocus("Title_Config/MouseUsual/hit", "Title_Sound/MouseUsual/hit",UP);
		SetNextFocus("Title_Config/MouseUsual/hit", "Title_Sound/MouseUsual/hit",LEFT);
	}
}
'''
# TitleFocusKr runs first, then the original calls would overwrite Load DOWN / Config UP: run it last instead
boot = sub(boot, 'function TitleFocus(){\r\n\tTitleFocusKr();\r\n', 'function TitleFocus(){\r\n')
tf = re.search(rb'function TitleFocus\(\)\{\r?\n.*?\r?\n\}\r?\n', boot, re.S)
assert tf
boot = boot[:tf.end() - len(b'}\r\n')] + b'\tTitleFocusKr();\r\n}\r\n' + FOCUS.encode('cp932').replace(b'\n', b'\r\n') + boot[tf.end():]
# 5) the choice: like Start (leaves the select), $TitleSelect=3
boot = sub(boot, '\t\t\tcase Title_LOAD{', '\t\t\tcase Title_Scenario{\r\n\t\t\t\tCreateSE("決定サウンド",$TitleClickSE);\r\n\t\t\t\tSoundPlay("決定サウンド",0,650,false);\r\n\t\t\t\t$TitleSelect=3;\r\n\t\t\t}\r\n\r\n'
           '\t\t\tcase Title_Sound{\r\n\t\t\t\tCreateSE("決定サウンド",$TitleClickSE);\r\n\t\t\t\tSoundPlay("決定サウンド",0,650,false);\r\n\t\t\t\t$TitleSelect=4;\r\n\t\t\t}\r\n\r\n\t\t\tcase Title_LOAD{')
# 6) after the title: clear it like a new game, run the viewer, then rebuild the title from scratch
anchor = b'\t\t//\x81\x9a\x81F\x8c\x8b\x89\xca\r\n\t\tif($TitleSelect==1){'
assert boot.count(anchor) == 1, boot.count(anchor)
VIEW = '''		//★：シナリオ閲覧（Claude 11-02）
		if($TitleSelect==3){
			Request("タイトル*", UnLock);
			Request("決定サウンド", UnLock);
			Delete("*");
			Wait(300);
			call_chapter nss/kr_scenario.nss;
			TitleClear();
			$TitleSelect=false;
		}
		//★：サウンド（Claude 11-02）
		if($TitleSelect==4){
			Request("タイトル*", UnLock);
			Request("決定サウンド", UnLock);
			Delete("*");
			Wait(300);
			call_chapter nss/kr_sound.nss;
			TitleClear();
			$TitleSelect=false;
		}
'''
boot = boot.replace(anchor, VIEW.encode('cp932').replace(b'\n', b'\r\n') + anchor, 1)

files = {n: (HERE / 'build' / n).read_bytes() for n in
         ('kr_title_scenario-000.png', 'kr_title_scenario-001.png', 'kr_title_scenario-002.png', 'kr_title_scenario-003.png', 'kr_scn_lock.png',
          'kr_bars.png', 'kr_snd_bg.png', 'kr_title_sound-000.png', 'kr_title_sound-001.png', 'kr_title_sound-002.png', 'kr_title_sound-003.png')}
files['kr_scenario.nss'] = nss
files['kr_sound.nss'] = snd_nss
(HERE / 'build' / 'kr_sound.nss.txt').write_text(snd_nss.decode('cp949', 'replace'), 'utf-8')
build(src_npa, out_npa, replace={'0_boot.nss': boot}, add=files)
(HERE / 'build' / 'kr_scenario.nss.txt').write_text(nss.decode('cp949', 'replace'), 'utf-8')
(HERE / 'build' / '0_boot.patched.txt').write_text(boot.decode('cp932', 'replace'), 'utf-8')
print('nss →', out_npa, len(nss), 'bytes viewer,', len(scenes), 'scenes,', npages, 'pages')
