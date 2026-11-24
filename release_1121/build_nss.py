"""11-21 새 번역(코덱스 3차 검수 반영본 + J00927 「다아트의 사자」)을 지금 놀이 사본 대본(56e322db) 위에 넣는다.
코덱스 폴더는 읽기만: 파서·탈출·NPA 묶기·파생 문자열 묶기 논리를 빌려 쓴다.
출력: staging/nss.npa, registry_1121.json, engine/backlog_ruby_map.h, qa/build.json
python -I -X utf8 build_nss.py
"""
from pathlib import Path
import json, re, hashlib, sys, importlib.util, shutil
W = Path(__file__).resolve().parent
P = Path(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening')
J = P / 'work/revisions/japanese-original-source-20261025'
NEWREG = P / 'outputs/third-reading-codex-review-20261117/길티크라운_3차_검수반영_번역.json'
BASE = Path(r'F:\AI\gclx-4k\release_1121\backup_before_1121\nss.npa')   # 11-21 설치 전 놀이 사본 대본 56e322db(설치 뒤 놀이 사본에는 설정 셋째 쪽이 이미 들어가 있다)
OLDHDR = Path(r'F:\AI\gclx-4k\engine\flip_1102\src\backlog_ruby_map.h')
sys.path.insert(0, str(P / 'work/tools'))
from npa_assets import NPA
from npa_pack_stream import pack
sys.path.insert(0, str(P / 'work/revisions/gemini-game-integration-20261026/scripts'))
from current_parser import parse_current
sp = importlib.util.spec_from_file_location('punct', P / 'work/revisions/lx0201-backlog-punctuation-20261025/escape_punct_audited.py')
punct = importlib.util.module_from_spec(sp)
sp.loader.exec_module(punct)


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s): return re.sub(r'\r+\n|\r', '\n', s)
def sv(p, v): Path(p).write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


# 1. 장부: 새 번역 + J00927 (사용자 10-26 결정 「다아트의 사자」, 11-21 「다 고쳐」)
reg = json.loads(NEWREG.read_text('utf-8'))
FIX = {'J00927': ('「다아트가 보낸 자들이 아닌가?」', '「다아트의 사자가 아닌가?」',
                  '사용자 결정(2026-10-26 「다아트의 사자」 유지, 11-21 재확인)으로 낱말만 되돌림.', 'ダァトの使い -> 다아트의 사자'),
       # 11-21 사용자 「닌자처럼 펑」: ドロロンパ(닌자가 연기와 함께 사라지는 소리 ドロン)를 소리만 옮긴 「도로롱파」 — 같은 대사 두 곳
       'J00091': ('「그럼 이쪽도 도로롱파, 하고」', '「그럼 이쪽도 닌자처럼 펑, 하고」', '사용자 결정(11-21): 일본식 의성어를 한국어 의성어로.', 'ドロロンパ -> 닌자처럼 펑'),
       'J01605': ('「그럼 이쪽도 도로롱파, 하고」', '「그럼 이쪽도 닌자처럼 펑, 하고」', '사용자 결정(11-21): 일본식 의성어를 한국어 의성어로.', 'ドロロンパ -> 닌자처럼 펑'),
       # 11-21 사용자 「응, 고쳐 줘」: 일본식 토하는·숨 막히는 소리를 한국어 의성어로(비명은 그대로)
       'J01043': ('「크보옥…… 크갸아아악!」', '「커허억…… 크갸아아악!」', '사용자 결정(11-21): 일본식 의성어를 한국어 의성어로.', 'グボォッ -> 커허억'),
       'J01081': ('「아…… 아아…… 게보오옥!」', '「아…… 아아…… 우웨에엑!」', '사용자 결정(11-21): 일본식 의성어를 한국어 의성어로.', 'ゲボォォッ -> 우웨에엑'),
       'J01082': ('「싫어…… 싫…… 크게에에에엑!」', '「싫어…… 싫…… 꾸에에에에엑!」', '사용자 결정(11-21): 일본식 의성어를 한국어 의성어로.', 'グゲェェェェェ -> 꾸에에에에엑'),
       # 11-21 사용자 「구베라학은 좀 그렇네」: 만화식 단말마 ぐべらはぁっ(못을 토하며 터지는 병사)
       'J01056': ('「구베라학!」', '「쿠하아악!」', '사용자 결정(11-21 「쿠하아악!이 원래 의도에 맞다」): 일본식 단말마를 한국어 의성어로.', 'ぐべらはぁっ -> 쿠하아악'),
       # 11-21 사용자 「그렇게 고쳐 줘」: 의성어 후보 228개 대조에서 남은 두 곳
       'J01028': ('「……크보오억!」', '「……쿠오아악!」', '사용자 결정(11-21): 일본식 단말마를 한국어 의성어로(원문 끝 アッ 살림).', 'ヴボオアッ -> 쿠오아악'),
       'J00486': ('「으꺗!」', '「우꺅!」', '사용자 결정(11-21): 촉음을 받침 ㅅ으로 옮긴 낯선 글자를 한국어 의성어로.', 'うきゃっ -> 우꺅')}
for u in reg['units']:
    if u['short_id'] in FIX:
        a, b, why, what = FIX[u['short_id']]
        assert u['target_with_controls'] == a, u['target_with_controls']
        for k in ('target', 'target_with_controls', 'target_display', 'target_reading'):
            u[k] = b
        u['decision'] = 'U'
        u['review_reason'] = why
        u['provenance']['user_decision'] = what + ' (Claude 반영 2026-11-21)'
reg['active_revision'] = 'claude-release-20261121'
reg['claude_release_note'] = 'J00927 사용자 결정 반영; 나머지는 3차 검수 반영본 그대로'
sv(W / 'registry_1121.json', reg)
byid = {u['id']: u for u in reg['units']}
assert len(byid) == 2422

# 2. 본 단위 바꿔 넣기
(W / 'staging').mkdir(exist_ok=True)
shutil.copy2(BASE, W / 'staging/base_nss.npa')
base = W / 'staging/base_nss.npa'
assert sha(base) == sha(BASE)
arc = NPA(base)
ent = {e['name']: e for e in arc.entries}


def parse(name, b):
    class In:
        def read_bytes(self): return b
        def __str__(self): return name
    z = In(); z.name = name; z.stem = name[:-4]
    d = parse_current(z)
    return d['units'] + d['history'] + d['phase_titles']


files = sorted({u['file'] for u in reg['units']})
cur, changed, found = {}, [], set()
for name in files:
    b = arc.read(ent[name]); edits = []
    for p in parse(name, b):
        u = byid.get(p['id'])
        if not u:
            continue
        found.add(p['id'])
        before = b[p['start_byte']:p['end_byte']]
        text = norm(before.decode('cp949'))
        if p['lane'] == 'PRE':
            text = text.replace('&.', '.').replace('&,', ',')
        want = norm(u['target_with_controls'])
        if text == want:
            continue
        nl = re.search(rb'\r*\n', before); nl = nl.group() if nl else b'\r\n'
        after = want.encode('cp949').replace(b'\n', nl)
        if p['lane'] == 'PRE':
            after = punct.escape_body(after)[0]
        edits.append((p['start_byte'], p['end_byte'], after)); changed.append(u['short_id'])
    edits.sort(); assert all(x[1] <= y[0] for x, y in zip(edits, edits[1:]))
    out = b
    for s, e, v in reversed(edits):
        out = out[:s] + v + out[e:]
    cur[name] = out
missing = set(byid) - found
assert not missing, sorted(missing)[:10]

# 3. 파생 문자열($SYSTEM_last_text·CreateOratorioTxtSet)을 새 문안으로 다시 묶기 (코덱스 bind_derived_displays 와 같은 규칙)
rows = reg['units']
hist = [u for u in rows if u['lane'] == 'SetBacklog_raw_history']
def nrm(s): return re.sub(r'\s+', '', re.sub(r'<[^>]*>', '', s))
rxlast = re.compile(rb'\$SYSTEM_last_text\s*=\s*"([^"\r\n]*)"')
rxora = re.compile(rb'\bCreateOratorioTxtSet\(([^\r\n]*)\);')
derived = []
for name in files:
    orig = (J / 'extracted/nss-original' / name).read_bytes(); c = cur[name]; edits = []
    for kind, rx in (('last_text', rxlast), ('oratorio', rxora)):
        om = list(rx.finditer(orig)); cm = list(rx.finditer(c)); assert len(om) == len(cm), (name, kind)
        for i, (o, m) in enumerate(zip(om, cm)):
            if kind == 'oratorio':
                os_ = list(re.finditer(rb'"([^"\r\n]*)"', o.group(1)))[-1]
                cs = list(re.finditer(rb'"([^"\r\n]*)"', m.group(1)))[-1]
                jp = os_.group(1).decode('cp932'); s, e = m.start(1) + cs.start(1), m.start(1) + cs.end(1)
            else:
                jp = o.group(1).decode('cp932'); s, e = m.span(1)
            want = nrm(jp); hs_ = [u for u in hist if u['scene'] + '.nss' == name]; ch = []
            for x in range(len(hs_)):
                for n in range(1, 5):
                    us = hs_[x:x + n]
                    if len(us) == n and nrm(''.join(u['source'] for u in us)) == want:
                        ch.append(us)
            if not ch:
                ch = [[u] for u in rows if u['scene'] + '.nss' == name and nrm(u['source']) == want]
            assert ch, (name, kind, i, jp)
            vals = {' '.join(u['target_display'].strip() for u in us) for us in ch}
            assert len(vals) == 1, (name, kind, i, vals)
            text = vals.pop(); v = text.encode('cp949')
            if kind == 'oratorio':
                v = punct.escape_body(v)[0]
            before = c[s:e]
            if before != v:
                edits.append((s, e, v))
            derived.append({'file': name, 'kind': kind, 'ordinal': i, 'before': before.decode('cp949'), 'after': text, 'changed': before != v})
    edits.sort(); assert all(x[1] <= y[0] for x, y in zip(edits, edits[1:]))
    for s, e, v in reversed(edits):
        c = c[:s] + v + c[e:]
    assert punct.escape_script(c) == (c, 0), name
    cur[name] = c
over = {n: c for n, c in cur.items() if c != arc.read(ent[n])}
pack(base, W / 'staging/nss.npa', over)

# 4. 다시 읽어 맞춰 보기 + 안 바뀐 항목은 바이트 동일
fin = NPA(W / 'staging/nss.npa'); fe = {e['name']: e for e in fin.entries}
assert set(fe) == set(ent)
rb = 0
for name in files:
    fresh = fin.read(fe[name]); assert fresh == cur[name]
    for p in parse(name, fresh):
        u = byid.get(p['id'])
        if not u:
            continue
        t = norm(fresh[p['start_byte']:p['end_byte']].decode('cp949'))
        if p['lane'] == 'PRE':
            t = t.replace('&.', '.').replace('&,', ',')
        assert t == norm(u['target_with_controls']), p['id']
        rb += 1
same = 0
with base.open('rb') as f0, (W / 'staging/nss.npa').open('rb') as f1:
    for name, e in ent.items():
        if name in over:
            continue
        z = fe[name]; assert e['stored_size'] == z['stored_size'], name
        f0.seek(arc.base + e['offset']); f1.seek(fin.base + z['offset'])
        assert f0.read(e['stored_size']) == f1.read(z['stored_size']), name
        same += 1

# 5. 대사 기록 루비 표 (코덱스 build_review 와 같은 꼴)
rx = re.compile(r'<RUBY TEXT="([^"]*)">(.*?)</RUBY>', re.S)
def plain(s): return re.sub(r'\s', '', re.sub(r'<[^>]*>', '', s).replace('&.', '.').replace('&,', ','))
rrows = []
for u in reg['units']:
    t = u['target_with_controls']; text = ''; spans = []; end = 0
    for m in rx.finditer(t):
        text += plain(t[end:m.start()]); st = len(text); text += plain(m[2]); spans.append((st, len(text) - st, m[1])); end = m.end()
    text += plain(t[end:])
    if spans:
        rrows.append((u['index'], text, spans))
assert len(rrows) == 165, len(rrows)
def lit(s): return 'L"' + ''.join('\\x%04x' % ord(c) for c in s) + '"'
h = ['// Generated from reviewed registry; replace this map in the CURRENT engine source.',
     'struct RubySpanDef {int start,length;const wchar_t* reading;};',
     'struct RubyUnitDef {int id;const wchar_t* plain;const RubySpanDef* spans;int count;};']
for i, (_, _, spans) in enumerate(rrows):
    h.append('static const RubySpanDef rubySpans%d[]={%s};' % (i, ','.join('{%d,%d,%s}' % (a, b, lit(r)) for a, b, r in spans)))
h.append('static const RubyUnitDef rubyUnits[]={' + ','.join('{%d,%s,rubySpans%d,%d}' % (ix, lit(pl), i, len(sp)) for i, (ix, pl, sp) in enumerate(rrows)) + '};')
(W / 'engine').mkdir(exist_ok=True)
(W / 'engine/backlog_ruby_map.h').write_text('\n'.join(h) + '\n', encoding='ascii')
old = OLDHDR.read_text('ascii').splitlines(); new = (W / 'engine/backlog_ruby_map.h').read_text('ascii').splitlines()
rowdiff = sum(1 for a, b in zip(old[3:-1], new[3:-1]) if a != b)
U = re.compile(r'\{(\d+),L"((?:\\x[0-9a-f]{4})*)",rubySpans\d+,\d+\}')
unitdiff = sum(1 for a, b in zip(U.findall(old[-1]), U.findall(new[-1])) if a != b)
rep = {'base_nss_sha256': sha(base), 'new_nss_sha256': sha(W / 'staging/nss.npa'), 'registry_sha256': sha(W / 'registry_1121.json'),
       'primary_units_changed': len(changed), 'primary_units_readback': rb, 'changed_scripts': sorted(over), 'unchanged_entries_identical': same,
       'derived_bindings': len(derived), 'derived_changed': [d for d in derived if d['changed']],
       'ruby_rows': len(rrows), 'ruby_span_lines_changed': rowdiff, 'ruby_unit_lines_changed': unitdiff,
       'header_sha256': sha(W / 'engine/backlog_ruby_map.h'), 'changed_ids': changed}
sv(W / 'qa/build.json', rep)
print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in rep.items()}, ensure_ascii=False))
