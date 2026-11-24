"""J/K 바꾸기(다시 불러오기) 때 배경 음악이 어떻게 되는지 보는 시험판: 대사마다(TypeBegin 머리) 탐침 프로세스를 새로 띄워
화면 왼쪽 위에 재생 중인 BGM(PassageTime>0)의 이름·위치·남은 시간을 0.25초마다 쓴다. 다시 불러오면 프로세스가 사라지므로
대사 시작마다 세대 번호($KRP_ID)를 올려 새로 띄우고, 옛 것은 번호가 다르면 끝난다.
python -I -X utf8 make_bgmprobe.py → nss_variants/nss.test_bgmprobe.npa
"""
import sys
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
import patch_seek as ps
from npa_assets import NPA
from npa_build import build
import keybar

V = Path(r'F:\AI\gclx-4k\release_1121\nss_variants')
src = V / 'nss.test_seek.npa'
arc = NPA(src); ent = {e['name']: e for e in arc.entries}
fn = ps.rd(arc, ent['function.nss'])
E = 'cp932'
names = ['lx%03d' % i for i in range(1, 20)] + ['lx001a', 'lx001b', 'lx004a', 'lx004b', 'lx014a', 'lx014b', 'lx018a', 'lxsong01', 'lxsong02']
probe = ['function KrProbeLoop()', '{', '\t$krpMine=$KRP_ID;', '\twhile($KRP_ID==$krpMine){', '\t\t$krpS="";']
for n in names:
    probe.append(f'\t\t$krpT=PassageTime("@{n}");$krpR=RemainTime("@{n}");if($krpR>0){{$krpU=String(" {n} %d %d",$krpT,$krpR);$krpS=$krpS+$krpU;}}')
probe += ['\t\t$krpG=String("G%d ",$KRP_ID);$krpS=$krpG+$krpS;',
          '\t\tSetFont("Noto Sans KR", 18, FFFF60, 000000, 600, RIGHTDOWN);',
          '\t\tif($KRP_TA==0){CreateText("krp_tB",30000,8,6,1000,30,$krpS);Request("krp_tB",NoLog);Request("krp_tB",PushText);Delete("krp_tA");$KRP_TA=1;}',
          '\t\telse{CreateText("krp_tA",30000,8,6,1000,30,$krpS);Request("krp_tA",NoLog);Request("krp_tA",PushText);Delete("krp_tB");$KRP_TA=0;}',
          '\t\tWait(250);', '\t}', '}']
start = ('\t$KRP_ID=$KRP_ID+1;$KRP_TA=0;'
         'if($KRP_PA==1){$KRP_PA=0;$krpPN="krprobeB";}else{$KRP_PA=1;$krpPN="krprobeA";}'
         'CreateProcess($krpPN,150,0,0,"KrProbeLoop");Request($krpPN,Start);\r\n')
anchor = keybar.TYPEBEGIN[1].encode(E)
chk = '\tif(!$KR_BOX1124){KrBoxAdd();$KR_BOX1124=true;}\r\n'.encode(E)
assert fn.count(chk + anchor) == 4
i = fn.index('function TypeBegin()'.encode(E)); j = fn.index(chk + anchor, i)
fn = fn[:j] + start.encode(E) + fn[j:]
fn = fn.rstrip() + b'\r\n\r\n' + '\r\n'.join(probe).encode(E) + b'\r\n'
build(src, V / 'nss.test_bgmprobe.npa', replace={'function.nss': fn})
print('ok')
