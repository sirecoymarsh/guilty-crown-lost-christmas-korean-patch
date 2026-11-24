"""clusters.json(대본 전체 조사) → 영상실 「연출」 목록 F:\\AI\\gclx-4k\\release_1121\\movie_room\\stage_items.json.
시작·끝은 대사 이름표([textNNNN])로 적는다(줄 번호는 다시 빌드하면 바뀔 수 있음). 제목은 짧게(칸 184px), 열리기 전엔 안 보임.
"""
import sys, json, re
from pathlib import Path
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_assets import NPA
import patch_seek as ps

C = json.loads(Path('clusters.json').read_text('utf-8'))
arc = NPA(Path(r'F:\AI\gclx-4k\release_1121\staging\nss_play.npa')); ent = {e['name']: e for e in arc.entries}
thum = set(l.split('\t')[1].replace('\\', '/') for l in Path('thum_list.txt').read_text('utf-8').splitlines())

# (클러스터 번호들, 제목, 시작 TypeBegin 줄 바꿈, 끝 TypeBegin 줄 바꿈) — None 이면 클러스터 그대로
PLAN = [
    ([0], '불타는 롯폰기'), ([1, 2], '프레젠트의 회오리'), ([3], '에덴 베베의 추격'), ([4], '미사일과 결정 공격'),
    ([5], '보이드 결정'), ([8], '게이트 잠입'), ([9], '총구를 피하다'),
    ([10], '검을 꺼내다', 5328, 6159), ([10], '엔드레이브 격파', 6159, None),
    ([14], '연구원의 캔서화'), ([16], '저격수의 조준경'), ([17], '나팔총 돌격'), ([19], '레일건 일격'), ([20], '케이도 추격'),
    ([21], '패스트 추격전'), ([22], '빛에 삼켜지다'), ([24], '아비규환의 롯폰기'), ([27, 28], '회오리 속으로'),
    ([29], '에덴 베베 기동'), ([30], '위장 추격'), ([31], '협공을 피하다'), ([32], '보이드 꺼내기'),
    ([33], '패스트의 목소리'), ([34], '골목 질주'), ([35], '잔해 사이로'), ([36], '벽을 달리다'), ([37], '등에 올라타다'),
    ([39], '바이크형 던지기'), ([41], '보이드 포'), ([42], '보이드 미사일 폭풍'),
    ([43], '피의 비'), ([44], '성해포 잘라내기'), ([45], '미사일을 피하다'), ([47], '정면 충돌'),
    ([48], '보이드 난무'), ([49], '천사의 고리 요격'), ([50], '불길 속의 빛'), ([51], '마지막 결착'), ([52], '벼락 같은 창'),
    ([53], '결정검과 결정화'), ([54], '마나 결정화'), ([55], '롯폰기 소멸'), ([56], '이엣 투 컴'), ([57], '아바돈'),
    ([58], '부서지는 보이드들'), ([59], '결말 연출 1'), ([60], '결말 연출 2'), ([61], '마지막 보이드 1'), ([62], '마지막 보이드 2'),
]


def label_at(lines, tb):
    for i in range(tb - 1, 0, -1):
        m = re.match(r'\[(text\w+)\]\s*$', lines[i - 1].strip())
        if m: return m.group(1)
        if re.match(r'\s*TypeBegin\w*\(', lines[i - 1]) and i != tb: break
    return None


def thumb_for(text):
    for kind in ('ev', 'bg'):
        for m in re.finditer(r'cg/%s/(?:[lmx]/)?([^"/]+?)(?:_[lmx]\d*)?\.(?:jpg|png)' % kind, text):
            n = m.group(1)
            for cand in (n, re.sub(r'_(?:キャラのみ|背景|bg|a|b|c|本体のみ|腕のみ)$', '', n)):
                p = f'sys/extra/thum/{kind}/{cand}.jpg'
                if p in thum: return 'cg/' + p
    return ''


items = []
for row in PLAN:
    ids, title = row[0], row[1]
    cs = [C[i] for i in ids]; f = cs[0]['file']
    assert all(c['file'] == f for c in cs)
    st = row[2] if len(row) > 2 else cs[0]['start']
    en = row[3] if len(row) > 3 else cs[-1]['end']
    src = ps.rd(arc, ent[f]); lines = src.decode('latin-1').split('\r\n')
    tbs = [i for i, l in enumerate(lines, 1) if re.match(r'\s*TypeBegin\w*\(', l)]
    # 경계가 주석 처리된 TypeBegin 줄(//	TypeBegin)이면 가까운 진짜 줄로: 시작은 앞, 끝은 뒤
    if st != 1 and not re.match(r'\s*TypeBegin', lines[st - 1]):
        st = max([t for t in tbs if t <= st] or [1])
    last_close = max(i for i, l in enumerate(lines, 1) if l.strip() == '}')
    if en is not None and en < last_close - 1 and not re.match(r'\s*TypeBegin', lines[en - 1]):
        en = min([t for t in tbs if t >= en] or [None]) if any(t >= en for t in tbs) else None
    first = st == 1
    sl = None if first else label_at(lines, st)
    el = None if (en is None or en >= last_close - 1) else label_at(lines, en)
    a = 0 if sl is None else st; b = last_close if el is None else en
    body = src[sum(len(x) + 2 for x in lines[:max(a - 1, 0)]):sum(len(x) + 2 for x in lines[:b])].decode('cp932', 'replace')
    th = thumb_for(body)
    if title == '엔드레이브 격파': th = 'cg/sys/extra/thum/ev/ev0206スクルージ重機エンドレイヴ撃破.jpg'
    if not th: th = 'cg/sys/extra/thum/bg/bg900000_1_空汎用.jpg'
    items.append({'file': f, 'start': sl, 'end': el, 'title': title, 'thumb': th, 'clusters': ids})
out = Path(r'F:\AI\gclx-4k\release_1121\movie_room\stage_items.json')
out.write_text(json.dumps(items, ensure_ascii=False, indent=1), 'utf-8')
print(len(items), sum(1 for x in items if not x['thumb']), 'no thumb')
for x in items[:12]: print(x['file'], x['start'], x['end'], x['title'], x['thumb'][-30:])
