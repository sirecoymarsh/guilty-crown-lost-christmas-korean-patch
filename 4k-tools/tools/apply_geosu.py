"""巨獣 7곳 「거수」→「거대한 짐승」(사용자 11-01 「거대한 짐승은 좋아 나머지는 유지」·「7곳 모두」; 코덱스 오프라인이라 Claude가 반영 「네가 다 처리하도록」).
코덱스 배포 대본(47c58383)을 읽어 세 대본만 바꾼 nss.npa 를 쓴다. 루비 읽기는 그대로, 조사만 받침에 맞게. &. &, 탈출은 그대로.
python -X utf8 apply_geosu.py <원본 nss.npa> <새 nss.npa>
"""
import sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

EDITS = {
    'lx0010.nss': [('강철의 거수&.', '강철의 거대한 짐승&.', 2)],                       # text0610·text0650
    'lx0507_10.nss': [('>거수가</RUBY>', '>거대한 짐승이</RUBY>', 1),                   # text0030
                      ('거수가 몸을 일으킨다', '거대한 짐승이 몸을 일으킨다', 1),           # text0043
                      ('거수가 노려보듯이', '거대한 짐승이 노려보듯이', 1)],               # text0071
    'lx0511_10.nss': [('>거수를</RUBY>', '>거대한 짐승을</RUBY>', 1),                   # text0010
                      ('창이 거수에게', '창이 거대한 짐승에게', 1)],                       # text0050
}
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
arc = NPA(src)
ent = {e['name']: e for e in arc.entries}
out = {}
for name, edits in EDITS.items():
    b = arc.read(ent[name])
    for old, new, n in edits:
        o, w = old.encode('cp949'), new.encode('cp949')
        assert b.count(o) == n, (name, old, b.count(o))
        b = b.replace(o, w)
    assert '거수'.encode('cp949') not in b, name
    out[name] = b
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_bytes(arc.pack(out))
chk = NPA(dst)
ce = {e['name']: e for e in chk.entries}
assert set(ce) == set(ent)
for e in arc.entries:
    if e['name'] in out:
        assert chk.read(ce[e['name']]) == out[e['name']], e['name']
    else:                          # 바꾸지 않은 항목은 저장 바이트 그대로(function_lc_wam.nss 는 원본부터 2바이트라 풀리지 않음)
        assert chk.raw(ce[e['name']]) == arc.raw(e), e['name']
print('7곳 반영 →', dst)
