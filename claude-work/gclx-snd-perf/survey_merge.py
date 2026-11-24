"""병기 교차 글 전수 조사: 문장이 줄바꿈으로 이어지는 곳을 한 단위로 묶기 전(MERGE_LINES=False)과 뒤의 [mtext]·[ntext] 덩어리를 비교해
바뀐 덩어리를 모두 적는다(사용자 11-24 「일본어는 2줄인데 한국어는 1줄인 경우 … 해당 사례를 전수 조사해」).
python -I -X utf8 survey_merge.py → 병기_한문장묶기_조사.md·json (release_1121\sound_seek)
"""
import sys, re, json
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
from pathlib import Path
import io, contextlib
import patch_seek as ps, jp_twin, text_fixes
from npa_assets import NPA

W = Path(r'F:\AI\gclx-4k\release_1121')
arc = NPA(W / 'staging/nss_lyrics.npa'); ent = {e['name']: e for e in arc.entries}
rd = lambda a, e: text_fixes.apply(e['name'], ps.rd(a, e))
BLK = re.compile(rb'<PRE @\w+>\r\n\[([mn]text\d+)\]\r\n(.*?)</PRE>', re.S)


def run(flag):
    jp_twin.MERGE_LINES = flag
    with contextlib.redirect_stdout(io.StringIO()):
        res = jp_twin.patch_all(arc, ent, rd)
    out = {}
    for n, b in res.items():
        for m in BLK.finditer(b):
            out[(n, m.group(1).decode())] = m.group(2)
    return out


old, new = run(False), run(True)
changed = sorted(k for k in new if old.get(k) != new[k])
dec = lambda b: re.sub(r'<voice[^>]*>\r?\n?', '', b.decode('cp949', 'replace')).strip()
rows = []
for n, lab in changed:
    rows.append({'file': n, 'block': lab, 'mode': '일한' if lab.startswith('m') else '한일', 'before': dec(old[(n, lab)]), 'after': dec(new[(n, lab)])})
out = W / 'sound_seek'
(out / '병기_한문장묶기_조사.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), 'utf-8')
files = sorted({r['file'] for r in rows})
md = ['# 병기 교차 글: 줄바꿈으로 이어지는 문장을 한 단위로 묶은 곳 전수 조사', '',
      f'바뀐 덩어리 {len(rows)}개(일한 {sum(r["mode"] == "일한" for r in rows)} · 한일 {sum(r["mode"] == "한일" for r in rows)}), 장면 파일 {len(files)}개.', '']
for r in rows[:400]:
    md += [f'## {r["file"]} {r["block"]} ({r["mode"]})', '', '고치기 전:', '```', r['before'], '```', '고친 뒤:', '```', r['after'], '```', '']
(out / '병기_한문장묶기_조사.md').write_text('\n'.join(md), 'utf-8')
print('changed blocks', len(rows), 'files', len(files))
