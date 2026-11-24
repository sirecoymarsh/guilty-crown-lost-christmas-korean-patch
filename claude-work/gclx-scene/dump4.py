import sys
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
import patch_seek as ps
from npa_assets import NPA
arc = NPA(Path(r'P:\AI\gclx-codexrun\game\nss.npa')); ent = {e['name']: e for e in arc.entries}
def line(l):
    # 주석·명령 줄은 cp932, 대사는 cp949 가 맞을 때가 많다 — 둘 다 오류 없이 풀리면 한글 쪽
    try:
        k = l.decode('cp949')
        if any('\uac00' <= c <= '\ud7a3' for c in k):
            # 한글 음절이 실제 한국어 문장처럼 보이는지: 공백·조사 비율로 거칠게
            j = None
            try: j = l.decode('cp932')
            except: return k
            if any('\u3040' <= c <= '\u30ff' for c in j) and not any(c in k for c in '을를이가은는에의다요'):
                return j
            return k
        return l.decode('cp932', 'replace')
    except UnicodeDecodeError:
        return l.decode('cp932', 'replace')
for n in sys.argv[1:]:
    b = ps.rd(arc, ent[n])
    Path(n + '.mix.txt').write_text('\n'.join(line(l) for l in b.split(b'\r\n')), 'utf-8')
