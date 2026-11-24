"""번역 고침 목록(translation_fixes.json)을 nss.npa 에 반영한다. 마침표 탈출(escape_punct)보다 먼저 돌린다.

각 고침은 번역 단위 하나의 한국어 안에서 old 를 new 로 바꾼다. 단위 전체 문장이 그 스크립트에
정확히 한 번 있어야 하고, old 는 그 문장 안에 정확히 한 번 있어야 한다(아니면 멈춘다).

쓰는 법: python apply_translation_fixes.py <입력 nss.npa> <full_translation.json> <fixes.json> <출력 nss.npa> <보고 json>
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from npa_adapter import NPA, sha


def enc(text):
    return text.replace('\r\n', '\n').replace('\n', '\r\n').encode('cp949')


def main(src, translation, fixes, dst, report):
    arc = NPA(src); es = {e['name']: e for e in arc.entries}
    units = {u['id']: u for u in json.loads(Path(translation).read_text('utf-8-sig'))['units']}
    plan = json.loads(Path(fixes).read_text('utf-8'))['fixes']
    scripts = {}; done = []
    for f in plan:
        u = units[f['id']]; name = u['file']
        raw = scripts.get(name) or arc.read(es[name])
        assert u['target'].count(f['old']) == 1, ('old 가 문장 안에 한 번이 아님', f['id'])
        before = enc(u['target']); after = enc(u['target'].replace(f['old'], f['new']))
        assert raw.count(before) == 1, ('문장이 스크립트에 한 번이 아님', f['id'], raw.count(before))
        scripts[name] = raw.replace(before, after)
        done.append(dict(id=f['id'], file=name, old=f['old'], new=f['new'],
                         target_before=u['target'], target_after=u['target'].replace(f['old'], f['new'])))
    blob = arc.pack(scripts); Path(dst).write_bytes(blob)
    chk = NPA(dst)
    for e in chk.entries:
        if e['type'] != 2: continue
        if e['name'] in scripts: assert chk.read(e) == scripts[e['name']]
        else: assert chk.raw(e) == arc.raw(es[e['name']])
    Path(report).write_text(json.dumps(dict(source_sha256=sha(arc.blob), output_sha256=sha(blob), applied=len(done),
                                            changed_scripts=sorted(scripts), fixes=done), ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print('applied', len(done), 'scripts', len(scripts), 'sha', sha(blob)[:12])


if __name__ == '__main__':
    if len(sys.argv) != 6: raise SystemExit(__doc__)
    main(*sys.argv[1:])
