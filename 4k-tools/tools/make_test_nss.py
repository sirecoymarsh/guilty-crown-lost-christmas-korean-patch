"""시험 사본 전용 nss.npa: 첫 실행 「전체 화면?」 창 건너뛰기·창 모드 고정, 타이틀 없이 바로 새 게임, 자동 진행.
(게임 출고본에는 쓰지 않음.) python -X utf8 make_test_nss.py
"""
import sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

SRC = Path(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\outputs\korean-game-candidate\game\nss.npa')
DST = Path(r'P:\AI\gclx-4k-test\game\nss.npa')
arc = NPA(SRC)
ent = {e['name']: e for e in arc.entries}
boot = arc.read(ent['0_boot.nss'])
a = '\tif(!#N2Start){'.encode('cp932')
assert boot.count(a) == 1
boot = boot.replace(a, '\t#N2Start=true;#SYSTEM_window_full=false;\r\n'.encode('cp932') + a, 1)
b = '\twhile(1)\r\n\t{\r\n\t\t$スクリプトバージョン'.encode('cp932')
assert boot.count(b) == 1, boot.count(b)
boot = boot.replace(b, '\t$GameContiune=1;$GameName="lx0010.nss";\r\n'.encode('cp932') + b, 1)   # 타이틀 「시작」이 정하는 첫 장면
start = arc.read(ent['0_boot_開始スクリプト.nss'])
c = '$SYSTEM_text_auto=false;'.encode('cp932')
assert start.count(c) >= 1   # 시작·끝 두 곳
start = start.replace(c, '$SYSTEM_text_auto=true;'.encode('cp932'))
DST.write_bytes(arc.pack({'0_boot.nss': boot, '0_boot_開始スクリプト.nss': start}))
chk = NPA(DST)
ce = {e['name']: e for e in chk.entries}
assert chk.read(ce['0_boot.nss']) == boot and chk.read(ce['0_boot_開始スクリプト.nss']) == start
print('시험용 nss.npa →', DST)
