"""CG 연출 다시 보기 대본 만들기(11-24 사용자 「CG 연출도 영상실에서 다시 볼 수 있게 해줘 … 스크루지가 캐롤에게서 처음으로 검을 꺼내는 장면 같은게 어디에도 없어」).
연출 하나 = 새 장면 모듈 kr_sp_NN.nss 하나:
  1) 앞부분(장면 첫머리 → 연출 첫 대사 직전): 원래 장면 대본을 그대로 옮기되 기다림·글·일회성 효과음을 빼고 움직임 시간을 0 으로
     → 화면·배경음 상태를 그 자리까지 한순간에 만든다(엔진 건너뛰기는 창이 뒤로 가면 꺼져서 쓰지 않음).
  2) 연출 본문(첫 대사 → 끝 대사의 TypeBegin): 원래 대본 그대로(대사·음성·한국어/일본어 병기 블록 포함).
  3) 닫기: 대사 상자 지우기. 남은 정리는 영상실(KmStagePlay)이 한다.
원래 장면 모듈·공용 함수는 건드리지 않는다(세이브·코덱스 세이브 호환과 무관한 새 모듈만).
python -I -X utf8 stage_replay.py <nss_play.npa> <출력 폴더>
"""
import sys, re, json
from pathlib import Path
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_assets import NPA
import patch_seek as ps

HERE = Path(__file__).resolve().parent
L1 = 'latin-1'   # 바이트를 그대로 글자로(cp932·cp949 가 섞인 대본을 깨뜨리지 않고 ASCII 명령만 고친다)

DROP = r'Wait|WaitKey|WaitPlay|WaitAction|WaitText|MovieSkipPlay|TypeBegin\w*|SetText\w*|KrAlt\w*|SetBacklog|TextBoxDelete|Fw|SkipOut'
CALL = r'\b(%s)\s*\(((?:[^()"]|"[^"]*"|\((?:[^()"]|"[^"]*")*\))*)\)\s*;'
DROP_RE = re.compile(CALL % DROP)
ANIM = {'Fade': 1, 'FadeDelete': 1, 'Move': 1, 'Zoom': 1, 'Rotate': 1, 'Shake': 1, 'BezierMove': 1, 'MoveCamera': 1,
        'DrawTransition': 1, 'DrawDelete': 1, 'SetVolumeEX': 1, 'SetVolume': 1, 'SetVolume_Loop': 1, 'ClearFadeAll': 0, 'FadeSt': 1}
ANIM_RE = re.compile(CALL % '|'.join(ANIM))
SND_RE = re.compile(CALL % 'MusicStart|SoundPlay')
REQ_PLAY = re.compile(r'\bRequest\s*\(\s*"[^"]*"\s*,\s*Play\s*\)\s*;')


def split_args(s):
    out, d, cur, q = [], 0, '', False
    for c in s:
        if c == '"': q = not q
        if not q:
            if c in '({[': d += 1
            if c in ')}]': d -= 1
            if c == ',' and d == 0:
                out.append(cur); cur = ''; continue
        cur += c
    out.append(cur)
    return out


def fast(line):
    """앞부분 한 줄: 기다림·글 명령은 지우고, 움직임은 시간 0, 한 번 울리는 소리는 지운다."""
    line = DROP_RE.sub('', line)
    line = REQ_PLAY.sub('', line)

    def anim(m):
        a = split_args(m.group(2)); i = ANIM[m.group(1)]
        if i < len(a) and a[i].strip():
            a[i] = ' 0'
        if len(a) >= 5 and re.fullmatch(r'\s*\d+\s*', a[-1]):
            a[-1] = ' false'
        return f'{m.group(1)}({",".join(a)});'
    line = ANIM_RE.sub(anim, line)

    def snd(m):
        a = split_args(m.group(2))
        return m.group(0) if a and a[-1].strip() == 'true' else ''   # 되풀이(배경음·고리 효과음)만 남김
    return SND_RE.sub(snd, line)


def code_only(line):
    """괄호 세기용: 주석·문자열 뺀 코드. 먼저 글자로 푼다 — cp932 두 바이트 글자의 둘째 바이트가 { } 일 수 있다(六本木 = 98 5A 96 7B)."""
    raw = line.encode(L1)
    for enc in ('cp932', 'cp949'):
        try:
            line = raw.decode(enc); break
        except UnicodeDecodeError:
            pass
    out, q = '', False
    i = 0
    while i < len(line):
        c = line[i]
        if c == '"': q = not q; i += 1; continue
        if not q and line.startswith('//', i): break
        if not q: out += c
        i += 1
    return out


def tb_of(lines, label):
    """대사 이름표([text0520] - 한국어 기본 블록)의 TypeBegin 줄(1부터)."""
    i = next(i for i, l in enumerate(lines, 1) if l.strip() == f'[{label}]')
    return next(j for j in range(i, len(lines) + 1) if re.match(r'\s*TypeBegin\w*\(', lines[j - 1]))


def build_module(src: bytes, name: str, start, end_label, cut_choice=True):
    """start/end_label: 대사 이름표(문자열) 또는 TypeBegin 줄 번호. start=None 이면 장면 첫머리부터, end=None 이면 장면 끝까지.
    cut_choice=False(회상 「이 장면의 연출」): 선택지도 그대로 두고 장면 끝까지 이어 간다(회상 「재생」과 같게)."""
    lines = src.decode(L1).split('\r\n')
    tb = [i for i, l in enumerate(lines, 1) if re.match(r'\s*TypeBegin\w*\(', l)]
    scene_hdr = [i for i, l in enumerate(lines, 1) if re.match(r'scene \S+\.nss\s*$', l)]
    body0 = scene_hdr[-1] + 2   # 'scene X' 다음 '{' 다음 줄
    assert lines[body0 - 2].strip() == '{'
    last_close = max(i for i, l in enumerate(lines, 1) if l.strip() == '}')
    if start is None:
        gs = body0
    else:
        start_tb = tb_of(lines, start) if isinstance(start, str) else start
        assert start_tb in tb, ('start', start_tb)
        prev = max([t for t in tb if t < start_tb] + [body0 - 1])
        gs = next(i for i in range(prev + 1, start_tb) if re.match(r'\s*(\$KR_IA|<PRE)', lines[i - 1]))
    end_tb = tb_of(lines, end_label) if isinstance(end_label, str) else end_label
    end = end_tb if end_tb else last_close - 1
    if end_tb is None:   # 장면 끝까지 옮길 때: 장면 뒤에 함수가 붙어 있으면 그것까지 장면 안에 들어가 버린다
        assert not any(re.match(r'\s*function\s', l) for l in lines[body0:]), name
    # 선택지가 들면 그 앞 마지막 대사에서 끝낸다(다시 보기가 선택지에서 서지 않게 — 숨긴 시험 stage_all: lx0010 끝 「속죄를/응보를」)
    ch = [i for i in range(gs, end + 1) if re.match(r'\s*(SetChoice|WaitChoice)\w*\(', lines[i - 1])] if cut_choice else []
    if ch:
        end = max(t for t in tb if gs <= t < ch[0])
    out = [f'// Claude 11-24: CG 연출 다시 보기 - 원래 대본 {name} 줄 {gs}~{end} (앞 {body0}~{gs - 1} 줄은 한순간에)'.encode('cp949').decode(L1),
           f'scene kr_sp.nss', '{']
    if 'LProcAK_' in src.decode(L1):   # 11-24: 같은 세션에서 두 번째 보면 정리 블록이 빠지지 않게(원작은 true 로만 바꿈 — recall_sp.LPROC)
        import recall_sp
        out.append('\t' + recall_sp.lproc_reset())
    pre = False
    for i in range(body0, gs):
        l = lines[i - 1]; s = l.strip()
        if s.startswith('<PRE'): pre = True; continue
        if pre:
            if s.startswith('</PRE>'): pre = False
            continue
        if s.startswith('//'): continue
        out.append(fast(l))
    # 시간 0·기다림 없음(false)으로 바꾼 움직임은 다음 그림에서야 붙으므로 몇 그림 기다렸다 걷는다(숨긴 시험 stage2: 앞 배경이 한 번 비침)
    out.append('\tWait(150);Fade("@kz_spv",400,0,null,true);Delete("@kz_spv");   // 앞부분을 덮던 검은 판(KmStagePlay 가 만든 것이라 별칭으로)'.encode('cp949').decode(L1))
    out += lines[gs - 1:end]
    out.append('\tTextBoxDelete(0);')
    depth = 0; pre = False
    for l in out[3:]:
        s = l.strip()
        if s.startswith('<PRE'): pre = True; continue
        if pre:
            if s.startswith('</PRE>'): pre = False
            continue
        c = code_only(l); depth += c.count('{') - c.count('}')
    assert depth >= 0, depth
    out += ['}'] * depth
    out.append('}')
    return ('\r\n'.join(out) + '\r\n').encode(L1), {'group_start': gs, 'end': end, 'prologue_lines': gs - body0, 'closing_braces': depth}


if __name__ == '__main__':
    arc = NPA(Path(sys.argv[1])); ent = {e['name']: e for e in arc.entries}
    outdir = Path(sys.argv[2]); outdir.mkdir(exist_ok=True)
    items = json.loads((HERE / 'stage_items.json').read_text('utf-8'))
    rep = []
    for k, it in enumerate(items, 1):
        src = ps.rd(arc, ent[it['file']])
        b, info = build_module(src, it['file'], it['start'], it['end'])
        mod = f'kr_sp{k:02d}.nss'
        b = b.replace(b'scene kr_sp.nss', f'scene {mod}'.encode())
        (outdir / mod).write_bytes(b)
        rep.append({'mod': mod, **it, **info, 'bytes': len(b)})
    (outdir / 'report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), 'utf-8')
    print(json.dumps(rep, ensure_ascii=False)[:2000])
