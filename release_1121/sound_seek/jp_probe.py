"""J(본문 일본어↔한국어) 실험 2(11-24): 일본어 덩어리를 한국어 덩어리 바로 뒤 if(#KR_JP){ } 안에 둔다.
실험 1(장면 끝에 둔 [jtext0020] 을 이름으로 LoadText)은 대사가 아예 안 나오고 넘어갔다 → 장면 밖 덩어리는 등록이 안 된다.
PRE 덩어리를 지나가는 것이 '지금 글'을 정하는 것이라면, 조건 안의 일본어 덩어리를 지나갈 때만 일본어가 뜬다.
시험판은 #KR_JP=true 로 시작. python -I -X utf8 jp_probe.py → nss_variants/nss.test_jp1.npa
"""
import sys
from pathlib import Path
W = Path(__file__).resolve().parents[1]
sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_build import build
sys.path.insert(0, str(W / 'sound_seek'))
from patch_seek import NPA, rd
src = W / 'nss_variants/nss.test_seek.npa'
arc = NPA(src); ent = {e['name']: e for e in arc.entries}
lx = rd(arc, ent['lx0010.nss'])
A = b'</PRE>\r\n\tSetText();\r\n\tTypeBegin(0);'
i = lx.find(b'[text0020]'); j = lx.find(A, i)
assert i > 0 and j > i
jp = ('</PRE>\r\nif(#KR_JP){\r\n<PRE @box0>\r\n[jtext0020]\r\nきらびやかなイルミネイション。<K>\r\nあかりをうけてかがやくゆき。<K>\r\nクリスマスのまちなみ。\r\n\r\n</PRE>\r\n}\r\n').encode('cp949')
lx = lx[:j] + jp + lx[j + len(b'</PRE>\r\n'):]
boot = rd(arc, ent['0_boot.nss'])
B = '$KUS_DBG=true;'.encode('cp932'); assert boot.count(B) == 1
boot = boot.replace(B, B + '#KR_JP=true;'.encode('cp932'))
out = W / 'nss_variants/nss.test_jp1.npa'
build(src, out, replace={'lx0010.nss': lx, '0_boot.nss': boot})
print(out.name)
