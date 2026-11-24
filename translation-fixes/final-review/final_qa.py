"""최종 게임 nss.npa 를 Codex 번역 장부와 대조하고 엔진 규칙을 점검한다(읽기만 함).

  python -X utf8 final_qa.py
결과: report.json, 사람이 볼 목록은 표준 출력.
"""
import sys, re, json, collections
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA, sha
from escape_punct import BLOCK, escape_body

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
GAME = Path(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\outputs\korean-game-candidate\game')
LEDGER = Path(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\revisions\gemini-game-integration-20261026\full-translation-ruby-reviewed.json')
KANA = re.compile(r'[\u3040-\u30ff]')
rep = {}

arc = NPA(GAME / 'nss.npa'); rep['nss_sha256'] = sha(arc.blob)
scripts, bad_cp949 = {}, []
for e in arc.entries:
    if e['type'] != 2 or not e['name'].endswith('.nss'): continue
    try: raw = arc.read(e)
    except Exception: continue
    scripts[e['name']] = raw
    try: raw.decode('cp949')
    except UnicodeDecodeError as x: bad_cp949.append((e['name'], str(x)[:80]))
rep['scripts'] = len(scripts); rep['cp949_decode_fail'] = bad_cp949

# 1) 대사 블록 안 탈출 안 된 반각 . ,
unesc = collections.Counter()
for n, raw in scripts.items():
    for m in BLOCK.finditer(raw):
        _, k = escape_body(m.group(1))
        if k: unesc[n] += k
rep['unescaped_halfwidth_punct'] = dict(unesc)

# 2) 대사 블록 안 주석 아닌 줄의 가나
kana_lines = []
for n, raw in scripts.items():
    t = raw.decode('cp949', 'replace')
    for m in re.finditer(r'(?ms)^<PRE @box\d+>[^\n]*\n(.*?)^</PRE>', t):
        for line in m.group(1).split('\n'):
            s = line.strip()
            if not s or s.startswith('//') or s.startswith('['): continue
            if KANA.search(re.sub(r'<RUBY TEXT="[^"]*">', '', s)): kana_lines.append((n, s[:80]))
rep['kana_in_dialogue'] = kana_lines

# 3) 장부 2,422단위가 대본에 그대로 들어갔나
L = json.loads(LEDGER.read_text('utf-8-sig'))['units']
def norm(s): return re.sub(r'\s+', '', s.replace('&.', '.').replace('&,', ','))
normd = {n: norm(raw.decode('cp949', 'replace')) for n, raw in scripts.items()}
missing = []
for u in L:
    f = u['id'].split('::')[0]
    tgt = norm(u.get('target_with_controls') or u['target'])
    if f not in normd or tgt not in normd[f]: missing.append((u['id'], (u.get('target_with_controls') or u['target'])[:60]))
rep['ledger_units'] = len(L); rep['ledger_missing_in_nss'] = missing

# 4) 루비 뒤 조사 받침 (본문 글자 기준)
PART = {'은': '는', '는': '은', '이': '가', '가': '이', '을': '를', '를': '을', '과': '와', '와': '과'}
def jong(ch): return (ord(ch) - 0xAC00) % 28 if '가' <= ch <= '힣' else None
ruby_particle = []
for u in L:
    t = u.get('target_with_controls') or u['target']
    for m in re.finditer(r'<RUBY TEXT="([^"]*)">([^<]*)</RUBY>(으로|로|은|는|이|가|을|를|과|와)(?![가-힣])', t):
        base, p = m.group(2).strip(), m.group(3)
        j = jong(base[-1]) if base else None
        if j is None: continue
        if p in PART: ok = (p in '은이을과') == bool(j)
        else: ok = (p == '로') == (j in (0, 8))
        if not ok: ruby_particle.append((u['id'], m.group(0)))
rep['ruby_particle_mismatch'] = ruby_particle

# 5) 사용자 결정·용어
car = [u for u in L if (u.get('speaker') or '') in ('キャロル', '캐롤', 'carol')]
dlg = lambda u: (u.get('target_display') or u['target']).lstrip().startswith(('「', '《', '（', '('))
disp = lambda u: u.get('target_display') or u['target']
rep['carol_dangsin'] = [(u['id'], disp(u)[:60]) for u in car if '당신' in disp(u)]
rep['ousama_not_imgeumnim'] = [(u['id'], disp(u)[:60]) for u in L if '王さま' in u.get('source', '') and '임금님' not in disp(u)]
rep['dialogue_geu_geunyeo'] = [(u['id'], disp(u)[:70]) for u in L if dlg(u) and re.search(r'그녀|그들(?!이 없)|(?<![가-힣])그(는|가|를|의|에게) ', disp(u))]
rep['daath_saja'] = [disp(u)[:40] for u in L if u['id'] == 'lx0206.nss::text0050::p001']
allk = '\n'.join(disp(u) for u in L)
rep['term_counts'] = {k: allk.count(k) for k in ['패스트', '파스트', '프레젠트', '제이컵', '제이콥', '옛 투 컴', '임금님', '스크루지', '전신전령', '그녀']}
(HERE / 'report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), 'utf-8')
for k, v in rep.items():
    if isinstance(v, (list, dict)) and len(v) > 8: print(k, len(v), '예:', (list(v.items()) if isinstance(v, dict) else v)[:8])
    else: print(k, v)
