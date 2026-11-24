"""음성 전사 채점용 정답 목록을 만든다: 원본 스크립트에 남은 일본어 대사(주석·SetBacklog)를 음성 파일과 짝짓는다.

- 주석: //<voice … src="voice/…"> 바로 뒤의 //「…」 또는 //《…》 (전각 공백으로 시작하는 다음 주석 줄까지 이어 붙임)
- SetBacklog("…", "voice/…", 화자) 와 그 바로 뒤 SetBacklog("…", NULL, NULL) 이어지는 줄
같은 음성에 두 꼴이 있으면 둘 다 남긴다(채점은 가까운 쪽).

쓰는 법: python build_stt_truth.py <원본 nss.npa> <출력 json>
"""
import sys, re, json, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from npa_adapter import NPA, sha

VOICE_C = re.compile(r'^\s*//\s*<voice\b[^>]*\bname="([^"]*)"[^>]*\bsrc="voice/([^"]+)"', re.I)
VOICE_C2 = re.compile(r'^\s*//\s*<voice\b[^>]*\bsrc="voice/([^"]+)"', re.I)
SPEAKER_C = re.compile(r'^\s*//\s*【([^】]+)】')
TEXT_C = re.compile(r'^\s*//\s*([「《].*)$')
CONT_C = re.compile(r'^\s*//\s*(　.*)$')
BACKLOG = re.compile(r'^\s*SetBacklog\s*\(\s*"([^"]*)"\s*,\s*("([^"]*)"|NULL|null)', re.I)


def voice_id(path):
    """'voice/LX02/0100010a02(.ogg)' → 'lx02/0100010a02'. 파일 이름은 장마다 겹칠 수 있어 폴더를 붙인다."""
    parts = path.replace('\\', '/').lower().rsplit('.ogg', 1)[0].split('/')
    return '/'.join(parts[-2:])


def closed(t):
    return t.rstrip().endswith(('」', '》'))


def main(src, dst):
    arc = NPA(src); truth = collections.defaultdict(list)
    for e in arc.entries:
        if e['type'] != 2 or not e['name'].endswith('.nss'): continue
        try: lines = arc.read(e).decode('cp932', 'replace').splitlines()
        except Exception: continue
        speaker = None; i = 0
        while i < len(lines):
            l = lines[i]
            m = SPEAKER_C.match(l)
            if m: speaker = m.group(1)
            m = VOICE_C2.match(l)
            if m:
                vpath = m.group(1); j = i + 1
                if j < len(lines) and TEXT_C.match(lines[j]):
                    text = TEXT_C.match(lines[j]).group(1); k = j + 1
                    while not closed(text) and k < len(lines) and CONT_C.match(lines[k]):
                        text += '\n' + CONT_C.match(lines[k]).group(1); k += 1
                    truth[voice_id(vpath)].append(dict(text=text, source='comment', file=e['name'], line=j + 1,
                                                        speaker=speaker, voice=vpath))
                i += 1; continue
            m = BACKLOG.match(l)
            if m and m.group(3) and m.group(3).lower() != 'null':
                text = m.group(1); vpath = m.group(3).replace('voice/', ''); k = i + 1
                while k < len(lines):
                    m2 = BACKLOG.match(lines[k])
                    if not (m2 and m2.group(3) is None): break
                    text += '\n' + m2.group(1); k += 1
                truth[voice_id(vpath)].append(dict(text=text, source='SetBacklog', file=e['name'], line=i + 1,
                                                    speaker=speaker, voice=vpath))
                i = k; continue
            i += 1
    rows = []
    for vid, vs in sorted(truth.items()):
        uniq = []
        for v in vs:
            if v['text'] not in [u['text'] for u in uniq]: uniq.append(v)
        rows.append(dict(voice_id=vid, variants=uniq))
    out = dict(source_npa=str(src), source_sha256=sha(arc.blob), voices=len(rows),
               by_source=collections.Counter(v['source'] for r in rows for v in r['variants']), rows=rows)
    Path(dst).write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print(json.dumps({k: v for k, v in out.items() if k != 'rows'}, ensure_ascii=False))


if __name__ == '__main__':
    if len(sys.argv) != 3: raise SystemExit(__doc__)
    main(*sys.argv[1:])
