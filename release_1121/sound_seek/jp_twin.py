"""J(본문 일본어↔한국어, 사용자 11-24 「J키를 누르면 인게임에서 일본어와 한국어를 교체 가능하게」 → 「Story text」).
장면 대본(lx*.nss)의 한국어 글 덩어리마다 바로 뒤에
    if(#KR_JP){ <PRE @상자> [jtextNNNN] 일본어 원문 </PRE> }
를 붙인다(실험 jp1~3: 장면 끝에 둔 덩어리는 등록이 안 되고, 조건 안에서 지나간 덩어리가 '지금 글'이 된다).
- 원문: 코덱스 japanese-original-source-20261025/extracted/nss-original 의 같은 이름 파일, 같은 [textNNNN] 이름표(라벨 일치 확인).
- 음성 태그는 한국어 덩어리의 것을 바이트 그대로(같은 src 로 짝지음): class 가 음성 설정(인물별 끄기)에 쓰인다.
- // 주석 줄은 뺀다. 글 안 반각 . , 는 엔진 멈춤 명령이라 &. &, 로(한국어와 같음).
- 글자: cp949 에 있으면 그대로, 없으면(ー 気 体 … 222자) 한국어 대본이 한 번도 안 쓰는 UHC 확장 한글 자리를 빌린다.
  그 표는 engine/src/jp_map.h 로 내보내 DLL 이 그 자리를 해당 일본 글자로 그린다(글자 모양은 일본어 글꼴).
"""
import re, json
from pathlib import Path
W = Path(__file__).resolve().parents[1]
JDIR = Path(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\revisions\japanese-original-source-20261025\extracted\nss-original')
BLOCK = re.compile(rb'<PRE @(\w+)>\r\n\[(text\d+)\]\r\n(.*?)</PRE>\r\n', re.S)
JBLOCK = re.compile(r'<PRE @\w+>\r?\n\[(text\d+)\]\r?\n(.*?)</PRE>', re.S)
VOICE_K = re.compile(rb'<voice [^>]*src="([^"]+)"[^>]*>')
VOICE_J = re.compile(r'<voice [^>]*src="([^"]+)"[^>]*>')


def _trail_ok(t):
    return 0x41 <= t <= 0x5a or 0x61 <= t <= 0x7a or 0x81 <= t <= 0xfe


def free_codes(korean_texts, need):
    used = set()
    for b in korean_texts:
        used.update(b.decode('cp949', 'replace'))
    out = []
    for lead in range(0x81, 0xa1):
        for trail in range(0x41, 0xff):
            if not _trail_ok(trail):
                continue
            try:
                ch = bytes([lead, trail]).decode('cp949')
            except UnicodeDecodeError:
                continue
            if ch not in used:
                out.append((lead << 8) | trail)
                if len(out) >= need:
                    return out
    raise SystemExit('free codes short')


def text_segments(s):
    """(is_tag, piece) — tags kept as they are."""
    return [(p.startswith('<'), p) for p in re.split(r'(<[^>]*>)', s) if p]


def build_twins(arc, ent, rd):
    jp_files = {p.name.lower(): p for p in JDIR.glob('*.nss')}
    names = [n for n in ent if n.lower().startswith('lx') and n.lower().endswith('.nss')]
    kor = {n: rd(arc, ent[n]) for n in names}
    # pass 1: Japanese bodies, characters
    jp_blocks = {}
    chars = set()
    for n in names:
        jf = jp_files.get(n.lower())
        if not jf:
            continue
        jt = jf.read_bytes().decode('cp932')
        jb = {}
        for m in JBLOCK.finditer(jt):
            body = '\n'.join(l for l in m.group(2).replace('\r\n', '\n').split('\n') if not l.lstrip().startswith('//'))
            jb[m.group(1)] = body
            for is_code, chunk in split_code_s(body):
                if is_code:
                    continue          # 덩어리 안 대본 코드는 한국어 덩어리의 것을 바이트 그대로 쓴다(아래)
                for is_tag, piece in text_segments(chunk):
                    if is_tag:
                        mm = re.match(r'<RUBY TEXT="([^"]*)">', piece)
                        if mm: chars.update(mm.group(1))
                    else:
                        chars.update(piece)
        jp_blocks[n] = jb
    missing = sorted(c for c in chars if c not in '\n' and not _enc_ok(c))
    codes = free_codes([rd(arc, e) for nm, e in ent.items() if nm.endswith('.nss')], len(missing))
    cmap = {c: bytes([code >> 8, code & 0xff]) for c, code in zip(missing, codes)}

    def enc(s, escape):
        out = bytearray()
        for ch in s:
            if escape and ch in '.,':
                out += b'&' + ch.encode()
            elif ch in cmap:
                out += cmap[ch]
            else:
                out += ch.encode('cp949')
        return bytes(out)

    stats = {'files': 0, 'blocks': 0, 'twins': 0, 'no_jp_label': 0, 'voice_unmatched': 0}
    # 11-24 사용자 「한글은 상단 루비의 강조가 약하게 찍혀있다 … 일본어처럼 진하게」: 한국어 대본의 강조점 루비는 가운뎃점
    # 「·」(U+00B7, cp949 A1A4 — 작은 점), 일본어는 「・」(U+30FB, 굵은 점). 「・」 는 cp949 에 없지만 일본어 쌍둥이가 빌려 쓰는
    # UHC 자리(cmap)가 있어 DLL 이 일본어 글꼴로 그린다 → 점만으로 된 한국어 루비(70곳)를 그 자리로.
    dot = cmap.get('・')
    def fix_dots(bb):
        if not dot:
            return bb
        def rep(m):
            stats['ruby_dots'] = stats.get('ruby_dots', 0) + 1
            return b'RUBY TEXT="' + dot * (len(m.group(1)) // 2) + b'"'
        return re.sub(rb'RUBY TEXT="((?:\xa1\xa4)+)"', rep, bb)
    result = {}
    for n in names:
        b = fix_dots(kor[n])
        jb = jp_blocks.get(n)
        if jb is None:
            continue
        stats['files'] += 1
        out = bytearray(); last = 0; changed = False
        for m in BLOCK.finditer(b):
            stats['blocks'] += 1
            box, label, kbody = m.group(1), m.group(2).decode(), m.group(3)
            body = jb.get(label)
            if body is None:
                out += b[last:m.end()]; last = m.end()
                stats['no_jp_label'] += 1
                continue
            # 11-24 「해당 구역 로딩된건 바뀌지 않네」: SetText(); TypeBegin(0); 이 바로 따르는 덩어리는 두 말을 다 싣는다.
            # 지금 상태의 말이 주(타이핑·음성·대사 기록), 다른 말은 KrPassText() 로 숨겨 실어 J·K 를 누르면 그 자리에서 바꾼다
            # (jp_swap.py KrJLayout: 한쪽만 또는 둘 다 위아래로).
            # 11-24 덩어리 안 대본 코드 { … }(배경·얼굴 창·페이드, 240덩어리): 일본어 쪽 코드 자리에 한국어 덩어리의 코드를 바이트
            # 그대로 넣는다(전에는 일본어 원문을 cp949 로 다시 적고 . , 까지 &. &, 로 바꿔 코드가 깨졌다). 개수가 다른 6덩어리
            # (한국어 패치가 코드를 더한 곳)는 쌍둥이를 만들지 않는다(그 대사만 J·K 와 상관없이 한국어).
            kcode = [kbody[s:e] for s, e in code_spans_b(kbody)]
            chunks = split_code_s(body)
            if len(kcode) != sum(1 for c, _ in chunks if c):
                out += b[last:m.end()]; last = m.end()
                stats['code_mismatch'] = stats.get('code_mismatch', 0) + 1
                continue
            stats['with_code'] = stats.get('with_code', 0) + (1 if kcode else 0)
            std = b[m.end():m.end() + 40].startswith(b'\tSetText();\r\n\tTypeBegin(0);')
            if not std:
                out += b[last:m.end()]; last = m.end()
            else:
                out += b[last:m.start()]; last = m.end()
            kvoice = {mm.group(1).decode('ascii', 'replace'): mm.group(0) for mm in VOICE_K.finditer(kbody)}
            jbytes = bytearray(); ci = 0
            for is_code, chunk in chunks:
                if is_code:
                    jbytes += kcode[ci]; ci += 1
                    continue
                for li, line in enumerate(chunk.split('\n')):
                    if li:
                        jbytes += b'\r\n'
                    for is_tag, piece in text_segments(line):
                        if is_tag:
                            vm = VOICE_J.match(piece)
                            if vm:
                                kv = kvoice.get(vm.group(1))
                                if kv is None:
                                    stats['voice_unmatched'] += 1
                                    jbytes += enc(piece, False)
                                else:
                                    jbytes += kv
                            else:
                                jbytes += enc(piece, False)
                        else:
                            jbytes += enc(piece, True)
            jtext = bytes(jbytes).rstrip(b'\r\n') + b'\r\n\r\n'
            pre = lambda lab, txt: b'<PRE @' + box + b'>\r\n[' + lab.encode() + b']\r\n' + txt + b'</PRE>\r\n'
            if std:
                # 11-24 J·K 네 상태(#KR_JP 0 한국어·1 일본어·2 일한 병기·3 한일 병기). 한 대사에 온전한 글 넷을 싣고 하나만 타이핑한다
                # (jp_swap.py KrJBegin). 둘이 같이 타이핑되면 쪽 기다림마다 클릭을 나눠 가져 어긋났다(숨긴 시험 js4).
                #   [mtext] 일한 · [ntext] 한일 — 사용자 「가능하면 한 문장씩 교차하는 형식으로」: 앞 말의 음성·코드·쪽 나눔·<K> 그대로,
                #   다른 말 문장을 바로 아래에 끼운다(interleave). [ptext]/[qtext] 다른 말, [jtext]/[text] 대사 시작 때 상태의 말(지금 글).
                ia = interleave(jtext, kbody, 'ja', 'ko', stats)
                ib = interleave(kbody, jtext, 'ko', 'ja', stats)
                pa = page_max(_jp_str(strip_code_b(ia), cmap), 'mix')
                pb = page_max(_jp_str(strip_code_b(ib), cmap), 'mix')
                stats['bi_max'] = max(stats.get('bi_max', 0), pa, pb)
                # 11-24 엔진은 장면 하나에 <PRE> 덩어리 512개까지(장면 개체의 표 두 개, 범위 검사 없음 — 넘으면 해석 중 튕김:
                # 회상 진입 때 lx0506 546개로 꺼짐, Forest 세션 조사). 그래서 대사당 4벌만: 교차 둘 + 일본어 + 한국어(늘 지금 글).
                # 대사 도중 바꾸기는 그 대사를 다시 불러와 KrJBegin 이 고르므로 시작 때 어느 말이 지금 글인지는 상관없다.
                # 11-24 교차 글 줄 간격 28px 은 루비가 윗줄에 얹혀 버려(js9) 루비가 있는 덩어리만 40px — $KR_IRB
                irb = 1 if (b'<RUBY' in kbody or b'<RUBY' in jtext) else 0
                stats['ruby_blocks'] = stats.get('ruby_blocks', 0) + irb
                out += (b'$KR_IA=%d;$KR_IB=%d;$KR_IRB=%d;\r\n' % (pa, pb, irb)
                        + pre('m' + label, ia) + b'\tKrAltIJ();\r\n' + pre('n' + label, ib) + b'\tKrAltIK();\r\n'
                        + pre('j' + label, jtext) + b'\tKrAltFJ();\r\n' + pre(label, kbody))
                stats['dual'] = stats.get('dual', 0) + 1
            else:
                # 11-24 사용자 「일부 문자는 한 일 동시병기가 작동하지 않는다」: SetText 와 TypeBegin 사이에 다른 명령이 있거나 가운데 글
                # (SetTextM) 인 덩어리(25)도 병기 — 덩어리를 지날 때 상태대로 고른다(대사 도중 바꾸기는 없음, 알림은 「다음 대사부터」).
                # 대사창 글 칸은 높이 150(줄 40 → 3줄)이라 교차 글이 한 쪽 3줄을 넘으면 앞 말만(넘치면 쪽이 갈릴 수 있어서).
                ia = interleave(jtext, kbody, 'ja', 'ko', stats)
                ib = interleave(kbody, jtext, 'ko', 'ja', stats)
                pa = page_max(_jp_str(strip_code_b(ia), cmap), 'mix')
                pb = page_max(_jp_str(strip_code_b(ib), cmap), 'mix')
                tail = b''
                if pa <= 3 and pb <= 3:
                    tail = (b'else if(#KR_JP==2){\r\n' + pre('m' + label, ia) + b'}\r\n'
                            + b'else if(#KR_JP==3){\r\n' + pre('n' + label, ib) + b'}\r\n')
                    stats['nonstd_bi'] = stats.get('nonstd_bi', 0) + 1
                elif pa <= 6 and pb <= 6:
                    # 11-24 4~6줄(가운데 날짜 글 lx0010 text0100 등 5덩어리): 줄 간격을 교차 글처럼 28px(루비 40)로 좁히고 글 칸 높이를
                    # 줄 수에 맞춘다 — jp_swap.TALL 이 SetTextBase 에서 $KR_TALL(줄 수)·$KR_TRB(루비)를 한 번 쓰고 지운다.
                    irb = 1 if (b'<RUBY' in kbody or b'<RUBY' in jtext) else 0
                    tall = lambda p: b'$KR_TALL=%d;$KR_TRB=%d;\r\n' % (p, irb)
                    tail = (b'else if(#KR_JP==2){\r\n' + tall(pa) + pre('m' + label, ia) + b'}\r\n'
                            + b'else if(#KR_JP==3){\r\n' + tall(pb) + pre('n' + label, ib) + b'}\r\n')
                    stats['nonstd_tall'] = stats.get('nonstd_tall', 0) + 1
                else:
                    tail = b'else if(#KR_JP==2){\r\n' + pre('m' + label, jtext) + b'}\r\n'   # 너무 길면 일한 = 일본어만
                    stats['nonstd_front_only'] = stats.get('nonstd_front_only', 0) + 1
                    stats.setdefault('front_only_list', []).append((n, label, pa, pb, b[m.end():m.end() + 70].decode('cp949', 'replace')))
                out += b'if(#KR_JP==1){\r\n' + pre('j' + label, jtext) + b'}\r\n' + tail
            changed = True; stats['twins'] += 1
        out += b[last:]
        if changed:
            result[n] = bytes(out)
    return result, cmap, stats


JPMAIN = b'if(#KR_JP==1||#KR_JP==2){\r\n'
VOICE_LINE = re.compile(rb'^[ \t]*<voice [^>]*>[ \t]*\r\n', re.M)
VOICE_ANY = re.compile(rb'<voice [^>]*>')


def _cp932_lead(c):
    return 0x81 <= c <= 0x9f or 0xe0 <= c <= 0xfc


def code_spans_b(b: bytes):
    """덩어리 바이트 안 맨 바깥 { … } 코드 자리들. 글 부분은 cp949(뒤 바이트가 { } 일 수 없음), 코드 안은 cp932
    (뒤 바이트가 { } 일 수 있음 — ボ 0x837B 등)로 읽고, 코드 안 "문자열"과 // 주석은 건너뛴다. // 로 시작하는 글 줄도 건너뛴다."""
    spans = []; i = 0; n = len(b); depth = 0; start = 0; bol = True
    while i < n:
        c = b[i]
        if depth == 0:
            if bol:
                j = i
                while j < n and b[j] in (0x20, 0x09):
                    j += 1
                if b[j:j + 2] == b'//':
                    k = b.find(b'\n', j); i = n if k < 0 else k + 1; continue
            bol = c == 0x0a
            if c == 0x7b:
                depth = 1; start = i; i += 1
            elif c >= 0x81:
                i += 2
            else:
                i += 1
        else:
            if c == 0x22:
                k = i + 1
                while k < n and b[k] != 0x22:
                    k += 2 if _cp932_lead(b[k]) else 1
                i = k + 1
            elif c == 0x2f and b[i + 1:i + 2] == b'/':
                k = b.find(b'\n', i); i = n if k < 0 else k
            elif c == 0x7b:
                depth += 1; i += 1
            elif c == 0x7d:
                depth -= 1; i += 1
                if depth == 0:
                    spans.append((start, i)); bol = False
            elif _cp932_lead(c):
                i += 2
            else:
                i += 1
    return spans


def split_code_s(s: str):
    """일본어 원문(유니코드) 덩어리를 [(코드인가, 조각)] 으로. 규칙은 code_spans_b 와 같다."""
    out = []; i = 0; n = len(s); depth = 0; start = 0; last = 0; bol = True
    while i < n:
        c = s[i]
        if depth == 0:
            if bol and s[i:].lstrip(' \t').startswith('//'):
                k = s.find('\n', i); i = n if k < 0 else k + 1; continue
            bol = c == '\n'
            if c == '{':
                depth = 1; start = i
            i += 1
        else:
            if c == '"':
                k = s.find('"', i + 1); i = n if k < 0 else k + 1; continue
            if s.startswith('//', i):
                k = s.find('\n', i); i = n if k < 0 else k; continue
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    if start > last: out.append((False, s[last:start]))
                    out.append((True, s[start:i + 1])); last = i + 1; bol = False
            i += 1
    if last < n: out.append((False, s[last:]))
    return out


def strip_code_b(b: bytes) -> bytes:
    """코드 자리를 빼고, 그래서 빈 줄이 된 줄은 줄째 뺀다."""
    spans = code_spans_b(b)
    if not spans:
        return b
    out = bytearray(); last = 0
    for s, e in spans:
        ls = b.rfind(b'\n', 0, s) + 1
        le = b.find(b'\n', e); le = len(b) if le < 0 else le + 1
        head, tail = b[ls:s], b[e:le]
        if not head.strip() and not tail.strip() and ls >= last:
            out += b[last:ls]; last = le          # 코드만 있던 줄(들): 줄째
        else:
            out += b[last:s]; last = e
    out += b[last:]
    return bytes(out)


# ---- 11-24 병기 = 한 문장씩 교차(사용자 「가능하면 한 문장씩 교차하는 형식으로 만들어주겠어」)
_TAGS = re.compile(rb'<[^>]*>')


def _items(b: bytes):
    """덩어리 → 쪽 목록. 쪽 = [(종류, 바이트)]; 종류 'raw'(코드가 든 줄·주석·태그만 있는 줄) / 'text'(보이는 글 줄).
    빈 줄(쪽 나눔)에서 쪽을 가른다. 여러 줄에 걸친 코드 { … } 는 한 줄로 묶는다."""
    spans = code_spans_b(b)
    pages, cur = [], []
    i, n = 0, len(b)
    while i < n:
        ls = i
        j = b.find(b'\n', i); j = n if j < 0 else j
        grow = True
        while grow:
            grow = False
            for s_, e_ in spans:
                if ls <= s_ < j and e_ > j:
                    j2 = b.find(b'\n', e_); j = n if j2 < 0 else j2; grow = True
        line = b[ls:j].rstrip(b'\r'); i = j + 1
        has_code = any(ls <= s_ < j for s_, e_ in spans)
        txt = _TAGS.sub(b'', line).strip()
        if not line.strip():
            if cur: pages.append(cur); cur = []
        elif has_code or line.lstrip().startswith(b'//') or not txt:
            cur.append(('raw', line))
        else:
            cur.append(('text', line))
    if cur: pages.append(cur)
    return pages


def _units(line: bytes):
    """글 줄 → [(글, 뒤에 <K> 기다림)] (<K> 에서 가름)."""
    parts = line.split(b'<K>')
    out = []
    for k, p in enumerate(parts):
        p = p.strip(b' ') if k else p.rstrip(b' ')
        if not _TAGS.sub(b'', p).strip():
            if out and k < len(parts) - 1: out[-1] = (out[-1][0], True)
            continue
        out.append((p, k < len(parts) - 1))
    return out


_SENT_KO = re.compile(r'(?:(?<=&\.)|(?<=[?!？！…]))\s+(?=\S)')
_SENT_JA = re.compile(r'(?<=[。！？])(?=[^」』）\s])')


def _sent_split(units, lang):
    """문장 끝에서 더 가른다(태그 안은 안 가름). 글은 cp949 로 풀 수 있어야 한다(아니면 그대로)."""
    out = []
    pat = _SENT_KO if lang == 'ko' else _SENT_JA
    for txt, wait in units:
        try:
            s = txt.decode('cp949')
        except UnicodeDecodeError:
            out.append((txt, wait)); continue
        tags = [(m.start(), m.end()) for m in re.finditer(r'<[^>]*>', s)]
        cuts = [m.start() for m in pat.finditer(s) if not any(a < m.start() < b for a, b in tags)]
        pieces, last = [], 0
        for c in cuts:
            pieces.append(s[last:c].strip()); last = c
        pieces.append(s[last:].strip())
        pieces = [p for p in pieces if p]
        for k, p in enumerate(pieces):
            out.append((p.encode('cp949'), wait and k == len(pieces) - 1))
    return out


# 11-24 사용자 「병기 모드에서 일본어는 2줄인데 한국어는 1줄인 경우 … 일본어가 완성된 후 한국어 문장은 마지막에」:
# 한 문장이 줄바꿈으로 두 줄에 걸치면(줄 끝이 문장 끝 부호가 아니고 다음 줄이 새 「 로 시작하지 않으면) 한 단위로 묶는다 — 두 말 모두.
_END_JA = set('。！？!?」』）)…‥♪')
_END_KO = set('.!?！？」』)）…~♪')
_OPEN_Q = ('「', '『', '（', '(')
MERGE_LINES = True   # 조사용 끄기 스위치(survey_merge.py)


def _vis(txt: bytes) -> str:
    try:
        return _TAGS.sub(b'', txt).decode('cp949').strip()
    except UnicodeDecodeError:
        return ''


def _is_open(txt: bytes, lang: str) -> bool:
    s = _vis(txt)
    if not s:
        return False
    return s[-1] not in (_END_KO if lang == 'ko' else _END_JA)


def _merge_lines(lines, lang, stats):
    """lines = [(종류, [(글, <K>)] 또는 None)] 차례 그대로. 이어지는 줄의 첫 단위를 앞 줄 마지막 단위에 줄바꿈째 붙인다(코드·태그 줄은 넘지 않음)."""
    if not MERGE_LINES:
        return lines
    holder = None
    for idx, (kind, units) in enumerate(lines):
        if kind != 'text' or not units:
            holder = None; continue
        if holder is not None and not _vis(units[0][0]).startswith(_OPEN_Q):
            t, w = units.pop(0)
            hl = lines[holder][1]; ht, _hw = hl[-1]
            hl[-1] = (ht + b'\r\n' + t, w)
            stats['merged_' + lang] = stats.get('merged_' + lang, 0) + 1
            stats['_merged_here'] = True
            if not units:
                holder = holder if (not w and _is_open(t, lang)) else None
                continue
        holder = idx if (not units[-1][1] and _is_open(units[-1][0], lang)) else None
    return lines


def interleave(front: bytes, other: bytes, flang: str, olang: str, stats) -> bytes:
    """앞 말 덩어리(음성·코드·쪽 나눔·<K> 그대로)에 다른 말을 한 문장씩 끼운다: 앞 문장, 그 아래 다른 말 문장, 그다음 <K>.
    쪽은 둘이 늘 같다(1,432덩어리 확인). 줄 수가 다르면 문장 끝에서 더 갈라 맞추고, 그래도 다르면 차례대로 짝짓고 남는 것은 끝에."""
    fp, op = _items(front), _items(strip_code_b(other))     # 다른 말: 코드는 빼고 <K> 는 남겨 단위를 가른다
    # 글이 있는 쪽끼리 짝짓는다(코드만 있는 쪽은 앞 말에서 제자리에 그대로). 개수가 다르면 남는 다른 말 쪽은 마지막 쪽에.
    has_text = lambda pg: any(kind == 'text' for kind, _ in pg)
    # 이어지는 줄 묶기(_merge_lines)는 줄 수가 안 맞을 때만 — 두 말이 같은 자리에서 줄을 바꾼 곳(lx0205 등)은 줄마다 짝짓는 편이 낫다.
    def _ounits(pg, merge):
        ls = [(kind, _units(VOICE_ANY.sub(b'', l)) if kind == 'text' else None) for kind, l in pg]
        if merge:
            ls = _merge_lines(ls, olang, stats)
        return [u for kind, us in ls if kind == 'text' and us for u in us]
    def _fit(ot):
        if nft != len(ot) and nft and len(ot) > nft:
            ot = ot[:nft - 1] + [[u for pg in ot[nft - 1:] for u in pg]]
        return ot
    nft = sum(1 for pg in fp if has_text(pg))
    otext = [_ounits(pg, False) for pg in op if has_text(pg)]
    if nft != len(otext):
        stats['page_mismatch'] = stats.get('page_mismatch', 0) + 1
    otext = _fit(otext)
    otext_m = _fit([_ounits(pg, True) for pg in op if has_text(pg)])
    out_pages = []; ti = -1
    for fpage in fp:
        if not has_text(fpage):
            out_pages.append(b'\r\n'.join(l for _, l in fpage)); continue
        fl = [(_units(l) if kind == 'text' else None) for kind, l in fpage]       # 앞 말 줄마다 단위
        ti += 1
        oun = otext[ti] if ti < len(otext) else []
        nf = sum(len(u) for u in fl if u)
        if nf != len(oun):
            # 11-24 먼저 줄바꿈으로 이어진 문장을 묶어 본다(앞 말만 / 다른 말만 / 둘 다). 맞으면 그것으로, 안 맞아도 묶은 것을 바탕으로
            flm = [us for _k, us in _merge_lines([(kind, (_units(l) if kind == 'text' else None)) for kind, l in fpage], flang, stats)]
            ounm = otext_m[ti] if ti < len(otext_m) else []
            cnt = lambda f: sum(len(u) for u in f if u)
            for cf, co in ((flm, oun), (fl, ounm), (flm, ounm)):
                if cnt(cf) == len(co):
                    fl, oun = cf, co; break
            else:
                fl, oun = flm, ounm
            nf = cnt(fl)
        if nf != len(oun):
            fl2 = [(_sent_split(u, flang) if u else None) for u in fl]
            oun2 = _sent_split(oun, olang)
            nf2 = sum(len(u) for u in fl2 if u)
            for cand_f, cand_o in ((fl2, oun), (fl, oun2), (fl2, oun2)):
                if sum(len(u) for u in cand_f if u) == len(cand_o):
                    fl, oun = cand_f, cand_o; break
            nf = sum(len(u) for u in fl if u)
        key = 'pair_same' if nf == len(oun) else 'pair_loose'
        stats[key] = stats.get(key, 0) + 1
        lines, k = [], 0
        for (kind, l), units in zip(fpage, fl):
            if kind == 'raw':
                lines.append(l); continue
            for ftxt, fwait in units:
                lines.append(ftxt)
                extra = [oun[k]] if k < len(oun) else []
                if k == nf - 1: extra += oun[nf:]
                lines += [t for t, _w in extra]
                if fwait: lines[-1] = lines[-1] + b'<K>'
                k += 1
        out_pages.append(b'\r\n'.join(lines))
    return b'\r\n\r\n'.join(out_pages) + b'\r\n\r\n'


def strip_all(txt: bytes) -> bytes:
    """병기의 둘째 말(정지 화면): 코드·음성 태그·<K> 를 빼고, 빈 줄(이 게임의 쪽 나눔 = 클릭 기다림)은 끝의 것까지 모두 뺀다
    — 끝 빈 줄이 남으면 다 쓴 뒤 그 자리에서 클릭을 기다려 보석 아이콘을 가져가고 클릭 하나를 삼켰다(숨긴 시험 js5)."""
    t = passive(txt).replace(b'\r\n', b'\n')
    lines = [l for l in t.split(b'\n') if l.strip(b' \t')]
    return b'\r\n'.join(lines) + b'\r\n'


def _jp_str(b: bytes, cmap) -> str:
    """일본어 쌍둥이 바이트 → 글(빌린 UHC 자리는 일본 글자로; 줄 수 세기용)."""
    rev = {v: k for k, v in cmap.items()}
    out = []; i = 0
    while i < len(b):
        c = b[i]
        if c >= 0x81 and i + 1 < len(b):
            two = b[i:i + 2]
            out.append(rev.get(two) or two.decode('cp949', 'replace')); i += 2
        else:
            out.append(chr(c)); i += 1
    return ''.join(out)


def page_max(s: str, lang: str) -> int:
    """온전한 판의 한 쪽(빈 줄로 나뉨)에 오는 가장 많은 줄 수. 코드·음성 태그·주석 줄은 세지 않는다."""
    s = s.replace('\r\n', '\n')
    pages, cur = [], []
    for raw in s.split('\n'):
        if raw.lstrip().startswith('//'):
            continue
        t = re.sub(r'<[^>]*>', '', raw)
        if not t.strip():
            if raw.strip():
                continue          # 태그만 있는 줄
            if cur: pages.append('\n'.join(cur)); cur = []
            continue
        cur.append(raw)
    if cur: pages.append('\n'.join(cur))
    return max([count_lines(p, lang) for p in pages] or [1])


def passive(txt: bytes) -> bytes:
    """숨긴 글: 음성 태그를 뺀다(태그만 있는 줄은 줄째) — 주 글이 음성을 낸다. <K>(클릭 기다림)도 뺀다 — 둘 다 Enter 된 글이
    <K> 에서 기다리면 Enter 에 게임이 멈췄다(숨긴 시험 js2). 그래서 <K> 가 든 29덩어리는 숨긴 글이 덩어리 전체를 한 번에 보인다.
    덩어리 안 대본 코드 { … } 도 뺀다 — 주 글이 이미 한 번 돌린다."""
    return VOICE_ANY.sub(b'', VOICE_LINE.sub(b'', strip_code_b(txt))).replace(b'<K>', b'')


_FONTS = {}


def _font(lang):
    from PIL import ImageFont
    if lang not in _FONTS:
        path = r'C:\Windows\Fonts\malgun.ttf' if lang == 'ko' else str(Path(__file__).with_name('NotoSansCJKjp-Medium.otf'))
        _FONTS[lang] = ImageFont.truetype(path, 26)
    return _FONTS[lang]


def count_lines(s: str, lang: str, width=790) -> int:
    """엔진 글자 칸(폭 800, 26px, 줄 40px)에서 몇 줄이 될지. 주석 줄·태그만 있는 줄은 세지 않고, 빈 줄은 한 줄."""
    lines = []
    for raw in s.replace('\r\n', '\n').split('\n'):
        if raw.lstrip().startswith('//'):
            continue
        t = re.sub(r'<[^>]*>', '', raw).replace('&.', '.').replace('&,', ',')
        if not t.strip() and raw.strip():
            continue          # 태그만 있는 줄
        lines.append(t)
    while lines and not lines[-1].strip():
        lines.pop()
    while lines and not lines[0].strip():
        lines.pop(0)
    n = 0
    for t in lines:
        f = _font(('ja' if re.search('[぀-ヿ一-鿿]', t) else 'ko') if lang == 'mix' else lang)
        w = f.getlength(t) if t else 0
        n += max(1, -(-int(w) // width))
    return max(1, n)


def _enc_ok(c):
    try:
        c.encode('cp949'); return True
    except UnicodeEncodeError:
        return False


def write_map(cmap, path):
    rows = sorted(((b[0] << 8) | b[1], c) for c, b in cmap.items())
    lines = ['// generated by sound_seek/jp_twin.py (11-24): UHC codes the Korean scripts never use -> Japanese characters for J mode',
             'static const struct {unsigned short code;wchar_t ch;} kJpMap[]={']
    lines += [f'{{0x{code:04x},0x{ord(c):04x}}},' for code, c in rows]
    lines += ['};', f'static const int kJpMapN={len(rows)};', '']
    Path(path).write_text('\n'.join(lines), encoding='ascii')


PRE_LIMIT = 480   # 엔진 한도 512(장면 개체 +0xf14·+0x1714 표), 여유를 둔다


def patch_all(arc, ent, rd):
    result, cmap, stats = build_twins(arc, ent, rd)
    counts = {n: len(re.findall(rb'(?i)<PRE', b)) for n, b in result.items()}
    worst = sorted(counts.items(), key=lambda kv: -kv[1])[:4]
    stats['pre_max'] = worst
    assert worst[0][1] <= PRE_LIMIT, ('장면 하나의 <PRE> 덩어리가 엔진 한도(512) 가까이', worst)
    write_map(cmap, W / 'engine/src/jp_map.h')
    (W / 'sound_seek/jp_twin_stats.json').write_text(json.dumps({'stats': stats, 'mapped': {c: b.hex() for c, b in cmap.items()}}, ensure_ascii=False, indent=1), 'utf-8')
    print('jp twins', stats, 'mapped chars', len(cmap))
    return result
