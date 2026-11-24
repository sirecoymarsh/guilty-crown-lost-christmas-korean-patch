"""길티 크라운 대본 전체에서 「글 없이 그림만 움직이는 연출」 구간을 찾는다(11-24 사용자 「영상이 아닌 CG 연출 같은게 여럿 있을거 같아 모두 찾아줘」).
구간 = 한 대사(TypeBegin) 끝에서 다음 대사(<PRE) 시작까지. 그 사이의 기다림(Wait·막는 애니메이션)을 더해 길이를 어림하고,
움직임 명령 수·쓰인 그림(ev·ef)·영상(.ngs)·개발 주석을 모은다.
python -I -X utf8 stage_scan.py → stage_scan.json
"""
import sys, re, json
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
import patch_seek as ps
from npa_assets import NPA

arc = NPA(Path(r'P:\AI\gclx-codexrun\game\nss.npa')); ent = {e['name']: e for e in arc.entries}
rec = ps.rd(arc, ent['kr_scenario.nss']).decode('cp949', 'replace')
ks = {}
for m in re.finditer(r'\$KS_FILE\[(\d+)\]="([^"]+)";.*?\$KS_TT\[\d+\]="([^"]*)"', rec):
    ks[m.group(2)] = (int(m.group(1)) + 1, m.group(3))


def dec(l):
    if l.lstrip().startswith(b'//'):
        try: return l.decode('cp932')
        except UnicodeDecodeError: pass
    try:
        k = l.decode('cp949')
        if any('\uac00' <= c <= '\ud7a3' for c in k):
            try:
                j = l.decode('cp932')
                if any('\u3040' <= c <= '\u30ff' for c in j) and not any(c in k for c in '을를이가은는에의다요'):
                    return j
            except UnicodeDecodeError:
                pass
            return k
        return l.decode('cp932', 'replace')
    except UnicodeDecodeError:
        return l.decode('cp932', 'replace')


ANIM = re.compile(r'\b(Move|Zoom|Rotate|Shake|BezierMove|MoveCamera|Fade|FadeDelete|SetBlur|DrawTransition|ClearFadeAll|SetVolumeEX|MusicStart)\s*\((.*)\)\s*;')
WAIT = re.compile(r'\bWait\s*\(\s*([^)]+)\)')
ASSIGN = re.compile(r'\$(\w+)\s*=\s*(\d+)\s*;')
DUR_ARG = {'Move': 1, 'Zoom': 1, 'Rotate': 1, 'Shake': 1, 'BezierMove': 1, 'MoveCamera': 1, 'Fade': 1, 'FadeDelete': 1,
           'SetBlur': None, 'DrawTransition': 1, 'ClearFadeAll': 0, 'SetVolumeEX': None, 'MusicStart': None}
VISUAL = {'Move', 'Zoom', 'Rotate', 'Shake', 'BezierMove', 'MoveCamera', 'Fade', 'FadeDelete', 'DrawTransition', 'SetBlur'}


def split_args(s):
    out, d, cur = [], 0, ''
    for c in s:
        if c in '({[': d += 1
        if c in ')}]': d -= 1
        if c == ',' and d == 0:
            out.append(cur.strip()); cur = ''
        else:
            cur += c
    out.append(cur.strip())
    return out


def num(x, vars_):
    x = x.strip()
    if re.fullmatch(r'-?\d+', x): return int(x)
    m = re.fullmatch(r'\$(\w+)', x)
    if m and m.group(1) in vars_: return vars_[m.group(1)]
    return None


res = []
for n in sorted(ent):
    if not re.fullmatch(r'lx\d.*\.nss', n): continue
    lines = [dec(l) for l in ps.rd(arc, ent[n]).split(b'\r\n')]
    vars_ = {}
    seg = None
    last_text = ''
    in_pre = False
    pre_tag = ''
    cur_pre = []

    def close(seg, end):
        if seg:
            seg['end'] = end
            res.append(seg)

    for i, l in enumerate(lines, 1):
        s = l.strip()
        if s.startswith('<PRE'):
            in_pre = True; cur_pre = []; continue
        if in_pre:
            if s.startswith('</PRE>'):
                in_pre = False
                if pre_tag.startswith('[text'):
                    ko = [x for x in cur_pre if x and not x.startswith(('<voice', '//', '{', '}', '[')) and any('\uac00' <= c <= '\ud7a3' for c in x)]
                    if ko: last_text = ko[-1].strip()
                continue
            if s.startswith('['): pre_tag = s
            cur_pre.append(s)
            continue
        if 'TypeBegin(' in s:
            close(seg, i)
            seg = {'file': n, 'start': i, 'after': last_text, 'ms': 0, 'anim': 0, 'blockers': 0, 'ev': [], 'ef': [], 'movies': [], 'notes': [], 'skipmovie': []}
            continue
        if seg is None:
            seg = {'file': n, 'start': i, 'after': '(장면 첫머리)', 'ms': 0, 'anim': 0, 'blockers': 0, 'ev': [], 'ef': [], 'movies': [], 'notes': [], 'skipmovie': []}
        for m in ASSIGN.finditer(s):
            vars_[m.group(1)] = int(m.group(2))
        if s.startswith('//'):
            t = s.lstrip('/').strip()
            if re.search(r'\w+\(.*\);|^\$\w+\s*=|^<|^\}|^\{', t): continue
            if t and not re.fullmatch(r'[―\-=＝─━/\s]*', t) and not t.startswith(('【', '（', '■', '▽', '[', '定義', '◆◆')) and len(t) > 2:
                seg['notes'].append(t[:80])
            continue
        for m in re.finditer(r'"((?:cg/ev|cg/ef)/[^"]+)"', s):
            k = 'ev' if '/ev/' in m.group(1) else 'ef'
            v = m.group(1).rsplit('/', 1)[-1]
            if v not in seg[k]: seg[k].append(v)
        for m in re.finditer(r'"(dx/[^"]+\.ngs)"', s):
            v = m.group(1)[3:]
            if v not in seg['movies']: seg['movies'].append(v)
        m = re.search(r'MovieSkipPlay\("[^"]+","([^"]+)"\)', s)
        if m: seg['skipmovie'].append(m.group(1))
        for m in WAIT.finditer(s):
            v = num(m.group(1), vars_)
            if v: seg['ms'] += v
        m = ANIM.search(s)
        if m:
            f, a = m.group(1), split_args(m.group(2))
            di = DUR_ARG[f]
            d = num(a[di], vars_) if di is not None and di < len(a) else None
            if f in VISUAL and d and d > 0:
                seg['anim'] += 1
            if a and a[-1] == 'true' and d:
                seg['ms'] += d; seg['blockers'] += 1
            elif a and d and re.fullmatch(r'\d+', a[-1]) and f in VISUAL and len(a) >= 5:
                seg['ms'] += int(a[-1])
    close(seg, len(lines))

for r in res:
    r['ks'] = ks.get(r['file'], (None, ''))
Path('stage_scan.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), 'utf-8')
big = [r for r in res if r['ms'] >= 6000 and r['anim'] >= 12 or r['skipmovie']]
print('segments>=3s', len(res), 'big', len(big))
for r in big:
    print(f"{r['file']:<18}{r['start']:>5}-{r['end']:<5} {r['ms']/1000:5.1f}s anim{r['anim']:>4} ev{len(r['ev'])} mv{r['movies'][:3]} notes:{' / '.join(r['notes'][:2])[:90]}")
