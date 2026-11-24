"""본문 대사 블록(<PRE @boxN>)의 반각 마침표·쉼표를 엔진 탈출 기호로 바꾼다.

원인: 대본 해석 함수(EXE 0x486da0·0x4895d0)는 대사 블록 안의 반각 '.'를 0.1초,
','를 0.5초 멈춤 명령으로 읽고 글자는 그리지 않는다(0x4874b5·0x4899fe).
같은 함수에 '&.' '&,'를 글자로 내보내는 탈출 처리가 있다(0x487593·0x489af0).
영문판은 이 때문에 전각 '．' '，'를 썼다.

쓰는 법: python escape_punct.py <입력 nss.npa> <출력 nss.npa> <보고 json>
- 대사 블록의 글자 부분만 바꾼다. 꺾쇠 태그 <...>, 중괄호 코드 {...}, 줄 안의 <PRE>...</PRE>,
  [text...] 표지 줄, // 주석 줄은 그대로 둔다.
- 이미 '&'가 앞에 있으면 건드리지 않는다(여러 번 돌려도 같다).
- CreateTextEX·SetBacklog·Message 같은 실행 중 문자열은 건드리지 않는다.
"""
import sys, re, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from npa_adapter import NPA, sha

BLOCK = re.compile(rb'(?m)^<PRE @box\d+>[^\n]*\n(.*?)^</PRE>', re.S)


def escape_body(body):
    """대사 블록 본문의 글자 부분에서 '.' ','를 '&.' '&,'로. (바뀐 본문, 바꾼 수) 반환.
    중괄호 코드는 여러 줄에 걸칠 수 있으므로 깊이를 블록 전체에서 이어 센다."""
    out = bytearray(); n = 0; depth_code = 0
    for line in body.split(b'\n'):
        if out: out.append(ord('\n'))
        if not depth_code and line.lstrip().startswith((b'//', b'[')):
            out += line; continue
        i = 0; depth_tag = 0; inline_pre = False
        while i < len(line):
            c = line[i]
            if c >= 0x81 and i + 1 < len(line):  # 2바이트 글자는 통째로 넘긴다
                out += line[i:i + 2]; i += 2; continue
            if depth_code and line.startswith(b'//', i):  # 코드 안 주석은 줄 끝까지
                out += line[i:]; break
            if not depth_code and line.startswith(b'<PRE>', i): inline_pre = True
            if inline_pre and line.startswith(b'</PRE>', i):
                out += b'</PRE>'; i += 6; inline_pre = False; continue
            if c == ord('<') and not depth_code: depth_tag += 1
            elif c == ord('>') and depth_tag: depth_tag -= 1
            elif c == ord('{') and not depth_tag: depth_code += 1
            elif c == ord('}') and depth_code: depth_code -= 1
            elif c in (0x2e, 0x2c) and not (depth_tag or depth_code or inline_pre):
                if not (out and out[-1] == ord('&')):
                    out.append(ord('&')); n += 1
            out.append(c); i += 1
    assert depth_code == 0, '대사 블록 안 중괄호가 닫히지 않음'
    return bytes(out), n


def escape_script(raw):
    total = 0; parts = []; last = 0
    for m in BLOCK.finditer(raw):
        new, n = escape_body(m.group(1)); total += n
        parts += [raw[last:m.start(1)], new]; last = m.end(1)
    parts.append(raw[last:])
    return b''.join(parts), total


def main(src, dst, report):
    arc = NPA(src); overrides = {}; counts = {}
    for e in arc.entries:
        if e['type'] != 2 or not e['name'].endswith('.nss'): continue
        try: raw = arc.read(e)
        except Exception: continue  # 원본에도 있던 빈 모듈(function_lc_wam.nss)
        new, n = escape_script(raw)
        if n:
            # 되돌림 검사: 넣은 '&'만 빼면 원본과 같아야 한다
            assert new.replace(b'&.', b'.').replace(b'&,', b',') == raw.replace(b'&.', b'.').replace(b'&,', b',')
            assert len(new) - len(raw) == n
            overrides[e['name']] = new; counts[e['name']] = n
    blob = arc.pack(overrides)
    Path(dst).write_bytes(blob)
    chk = NPA(dst); es = {e['name']: e for e in arc.entries}
    for e in chk.entries:
        if e['type'] != 2: continue
        if e['name'] in overrides: assert chk.read(e) == overrides[e['name']]
        else: assert chk.raw(e) == arc.raw(es[e['name']])
    rep = dict(source=str(src), source_sha256=sha(arc.blob), output=str(dst), output_sha256=sha(blob),
               escaped_total=sum(counts.values()), changed_scripts=len(counts), per_script=counts,
               untouched='실행 중 문자열(CreateTextEX·SetBacklog·Message 등)과 대사 블록 밖 바이트')
    Path(report).write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in rep.items() if k != 'per_script'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    if len(sys.argv) != 4: raise SystemExit(__doc__)
    main(*sys.argv[1:])
