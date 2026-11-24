"""시험 대본(타이틀 없이 lx0010·자동 진행)을 주어진 원래 대본에서 만든다. make_codex_run.py 와 같은 고침.
python -X utf8 make_test_nss_from.py <원래 nss.npa> <시험 nss.npa>"""
import sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
arc = NPA(src)
ent = {e['name']: e for e in arc.entries}
boot = arc.read(ent['0_boot.nss'])
a = '\tif(!#N2Start){'.encode('cp932')
assert boot.count(a) == 1
boot = boot.replace(a, '\t#N2Start=true;#SYSTEM_window_full=false;\r\n'.encode('cp932') + a, 1)
b = '\twhile(1)\r\n\t{\r\n\t\t$スクリプトバージョン'.encode('cp932')
assert boot.count(b) == 1
boot = boot.replace(b, '\t$GameContiune=1;$GameName="lx0010.nss";\r\n'.encode('cp932') + b, 1)
start = arc.read(ent['0_boot_開始スクリプト.nss'])
c = '$SYSTEM_text_auto=false;'.encode('cp932')
assert start.count(c) >= 1
start = start.replace(c, '$SYSTEM_text_auto=true;'.encode('cp932'))
dst.write_bytes(arc.pack({'0_boot.nss': boot, '0_boot_開始スクリプト.nss': start}))
chk = NPA(dst)
ce = {e['name']: e for e in chk.entries}
assert chk.read(ce['0_boot.nss']) == boot and chk.read(ce['0_boot_開始スクリプト.nss']) == start
print('시험 대본 →', dst)
