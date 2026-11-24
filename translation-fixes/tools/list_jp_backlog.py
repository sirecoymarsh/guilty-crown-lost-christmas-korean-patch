"""대사 기록·이어 보기용 일본어 문자열(SetBacklog·$SYSTEM_last_text) 목록을 뽑는다.

쓰는 법: python list_jp_backlog.py <nss.npa> <출력 json>
"""
import sys, re, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from npa_adapter import NPA, sha

PAT = re.compile(rb'^(\s*)(SetBacklog\s*\(|\$SYSTEM_last_text\s*=\s*)"([^"\r\n]*)"')


def japanese(b):
    """2바이트 글자가 모두 KS X 1001 범위(두 바이트 다 0xA1~0xFE)면 한국어, 하나라도 벗어나면
    CP932 일본어 바이트로 본다(가나·「」·…·全角空白은 리드 0x81~0x83이라 여기서 걸린다)."""
    i = 0; outside = False; multi = False
    while i < len(b):
        if b[i] < 0x80: i += 1; continue
        multi = True
        if i + 1 >= len(b) or not (0xA1 <= b[i] <= 0xFE and 0xA1 <= b[i + 1] <= 0xFE): outside = True
        i += 2
    if not (multi and outside): return None
    try: return b.decode('cp932')
    except UnicodeDecodeError: return None


def main(src, dst):
    arc = NPA(src); rows = []
    for e in arc.entries:
        if e['type'] != 2 or not e['name'].endswith('.nss'): continue
        try: raw = arc.read(e)
        except Exception: continue
        for i, ln in enumerate(raw.split(b'\n')):
            m = PAT.match(ln)
            if not m: continue
            s = japanese(m.group(3))
            if s is None: continue
            kind = 'SetBacklog' if m.group(2).startswith(b'SetBacklog') else '$SYSTEM_last_text'
            voice = re.search(rb'"\s*,\s*"(voice/[^"]+)"', ln)
            rows.append(dict(file=e['name'], line=i + 1, kind=kind, source_ja=s,
                             voice=voice.group(1).decode() if voice else None,
                             line_cp932=ln.rstrip(b'\r').decode('cp932', 'replace')))
    out = dict(source_npa=str(src), source_sha256=sha(arc.blob), count=len(rows),
               by_kind={k: sum(r['kind'] == k for r in rows) for k in ('SetBacklog', '$SYSTEM_last_text')},
               rows=rows)
    Path(dst).write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in out.items() if k != 'rows'}, ensure_ascii=False))


if __name__ == '__main__':
    if len(sys.argv) != 3: raise SystemExit(__doc__)
    main(*sys.argv[1:])
