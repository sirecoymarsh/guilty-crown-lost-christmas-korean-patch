"""4배 리마스터 대상 목록. 한국어 통합본 cg.npa 의 그림 가운데
- 원본 영문판 cg.npa 와 내용이 같은 것만(한국어 패치·UI 가 바꾼 그림은 빼기 — 구운 글자를 AI가 바꾼다)
- sys/(UI, 코덱스가 4배로 따로 만듦)·data/(장면 전환 무늬)·mask/ 는 빼기
- 배율 = min(4, 4096/긴 변) — 32비트 게임(큰 주소 공간 없음)이라 4배 그림 긴 변을 4096으로 묶는다. 1.5 미만이면 빼기.
- 짧은 변 64 미만은 AI 없이 Lanczos
- 방식: 투명 그림(알파에 255 아닌 값) = 섞기(가장자리 메우기), JPEG = 섞기+JPEG 덩어리 다듬기, 그 밖 불투명 PNG = 섞기
python -X utf8 inventory.py -> F:\\AI\\gclx-4k\\inventory.json
"""
import hashlib, io, json, sys, collections
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

sys.stdout.reconfigure(encoding='utf-8')
KO = r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\outputs\korean-game-candidate\game\cg.npa'
EN = r'Y:\GAME\Guilty-Crown-Lost-Christmas_Win_EN_Full-rip\GUILTY CROWN LOST XMAS\cg.npa'
SKIP_TOP = {'sys', 'data', 'mask'}
CAP, MIN_FACTOR = 4096, 1.5


def main():
    ko, en = NPA(KO), NPA(EN)
    en_ent = {e['name']: e for e in en.entries if e['type'] == 2}
    rows, why = [], collections.Counter()
    for e in ko.entries:
        if e['type'] != 2:
            continue
        name = e['name'].replace('\\', '/')
        top = name.split('/')[0]
        if top in SKIP_TOP:
            why['UI·전환·마스크'] += 1; continue
        if not name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            why['그림 아님'] += 1; continue
        data = ko.read(e)
        o = en_ent.get(e['name'])
        if o is None or hashlib.sha256(en.read(o)).digest() != hashlib.sha256(data).digest():
            why['한국어판에서 바뀜'] += 1; continue
        im = Image.open(io.BytesIO(data))
        w, h = im.size
        factor = min(4.0, CAP / max(w, h))
        if factor < MIN_FACTOR:
            why['이미 큼'] += 1; continue
        alpha = False
        if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
            a = np.asarray(im.convert('RGBA'))[:, :, 3]
            alpha = bool((a != 255).any())
        jpeg = name.lower().endswith(('.jpg', '.jpeg'))
        method = 'lanczos' if min(w, h) < 64 else ('blend_alpha' if alpha else ('blend_deblock' if jpeg else 'blend'))
        out_w, out_h = round(w * factor), round(h * factor)
        rows.append({'name': name, 'w': w, 'h': h, 'factor': round(factor, 4), 'out': [out_w, out_h], 'alpha': alpha,
                     'jpeg': jpeg, 'method': method, 'sha256': hashlib.sha256(data).hexdigest()[:16]})
        why[method] += 1
    rows.sort(key=lambda r: (r['name'].split('/')[0] not in ('st', 'bu', 'fw', 'fu'), r['name']))   # 인물 먼저
    Path(r'F:\AI\gclx-4k\inventory.json').write_text(json.dumps({'cap': CAP, 'min_factor': MIN_FACTOR, 'counts': why, 'rows': rows},
                                                               ensure_ascii=False, indent=0), 'utf-8')
    print(dict(why))
    print('대상', len(rows), '4배', sum(r['factor'] == 4 for r in rows), '덜 키움', sum(r['factor'] < 4 for r in rows))
    print('무리별', collections.Counter(r['name'].split('/')[0] for r in rows))


if __name__ == '__main__':
    main()
