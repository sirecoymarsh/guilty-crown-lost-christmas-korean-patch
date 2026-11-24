"""본편 가사 자리·모양 시험 대본: 0_boot 를 짧은 장면으로 바꿔 본편 경로(CreateBGM + SoundPlay "@lx001")로 βios 를 틀고
첫 가사(39.1초) 앞으로 SetStream. 배경은 왼쪽 어둡게·오른쪽 밝게(상자 없는 글자가 양쪽에서 읽히나).
python -I -X utf8 make_probe.py → nss_variants/nss.test_lyprobe.npa
"""
import sys
from pathlib import Path
W = Path(__file__).resolve().parents[1]
sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_build import build
probe = '''#include "nss/function.nss"
chapter main
{
	#SYSTEM_window_full=false;$SYSTEM_menu_lock=true;
	CreateColor("bgA",1,0,0,1024,576,0xEDEDED);
	CreateColor("bgB",2,0,0,512,576,0x1C2A3A);
	CreateBGM("lx001","lxbgm01");SoundPlay("@lx001",0,1000,true);
	Wait(800);SetStream("@lx001",37000);
	Wait(300000);
}
'''.replace('\n', '\r\n').encode('cp932')
out = W / 'nss_variants/nss.test_lyprobe.npa'
build(W / 'staging/nss_play.npa', out, replace={'0_boot.nss': probe})
print(out.name)
