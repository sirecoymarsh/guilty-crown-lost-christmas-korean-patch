"""결말 1 끝부분 시험 대본: lx0604_20sl(마지막 선택)에서 시작, 착한 점수 8 → 「산다」 쪽 첫째 선택 → lx0605a → 엔딩 롤 → 타이틀.
완주 경로 A 가 lx0604_10sl 의 「산다」 되풀이(원작 설계: 「포기한다」를 골라야 넘어감)에서 맴돌아 결말 1 을 못 봤다(11-21).
(그 뒤 assemble.py 의 경로 A 도 lx0604_10sl 에서는 둘째를 고르게 고침.) 기존 nss_variants 는 건드리지 않고 새 파일만 쓴다.
python -I -X utf8 variant_end_a.py
"""
import sys
from pathlib import Path
W = Path(__file__).resolve().parent
sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA
from npa_build import build
E = 'cp932'
fin = W / 'staging/nss_final.npa'
route = NPA(W / 'nss_variants/nss.test_route_a.npa'); re_ = {e['name']: e for e in route.entries}
boot = route.read(re_['0_boot.nss'])
old = '$GameContiune=1;$GameName="lx0010.nss";'.encode(E)
assert boot.count(old) == 1
boot = boot.replace(old, '$GameContiune=1;$GameName="lx0604_20sl.nss";#KR_TEST_GOOD=8;'.encode(E), 1)
fa = NPA(fin); fe = {e['name']: e for e in fa.entries}
start = fa.read(fe['0_boot_開始スクリプト.nss'])
g = '\t$GOOD_MAN_POINT=0;'.encode(E)
assert start.count(g) == 1
start = start.replace(g, g + 'if(#KR_TEST_GOOD>0){$GOOD_MAN_POINT=#KR_TEST_GOOD;}'.encode(E), 1)
rep = {n: route.read(re_[n]) for n in ('function.nss', 'function_select.nss')}
rep.update({'0_boot.nss': boot, '0_boot_開始スクリプト.nss': start})
add = {n: route.read(re_[n]) for n in ('kr_cmd_trace.png', 'kr_cmd_tracepick.png', 'kr_cmd_tracetitle.png')}
build(fin, W / 'nss_variants/nss.test_end_a.npa', replace=rep, add=add)
print('ok')
