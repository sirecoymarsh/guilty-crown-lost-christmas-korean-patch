"""덮어쓰기 배포에 들어갈 파일을 게임 폴더 꼴 그대로 stage 폴더에 모은다(ZIP 은 이 폴더를 그대로 담는다).
- 놀이 사본(손 확인하는 판)과 같은 파일: 대본·system.npa·DLL·대리 version.dll·실행기·영상 3개·글꼴·라이선스
- 한국어판 실행 파일(대용량 주소·한국어 글자 처리 고침) — DLL 이 이 파일의 SHA256 을 확인한다
- 한국어 그림 묶음(make_cgko.py): 원본 cg.npa 는 그대로 두고 바뀐·더한 그림 545장만
python -I -X utf8 make_stage.py <stage 폴더> <그림 묶음 이름.npa>
"""
import shutil, sys, hashlib, json
from pathlib import Path
R = Path(r'F:\AI\gclx-4k\release_1121')
GAME = Path(r'P:\AI\gclx-codexrun\game')
W = Path(r'Y:\AI\claude-work\gclx-overwrite')
stage, cgname = Path(sys.argv[1]), sys.argv[2]
FILES = {
    'GUILTY CROWN LOST XMAS.exe': GAME / 'GUILTY CROWN LOST XMAS.exe',
    'nss.npa': R / 'staging/nss_play.npa',   # 11-24 가사판 + sound_seek/patch_seek.py   # 11-24 코덱스 노래 가사판(nss_final 위에 build_lyrics.py)
    'system.npa': GAME / 'system.npa',
    cgname: W / 'cgko_build.npa',
    'n2hd_runtime.dll': R / 'engine/payload/n2hd_runtime.dll',
    'version.dll': R / 'proxy/version.dll',
    'Korean4K.exe': GAME / 'Korean4K.exe',
    'dx/mv_op.ngs': GAME / 'dx/mv_op.ngs',
    'dx/GC_eyecatch_E.ngs': GAME / 'dx/GC_eyecatch_E.ngs',
    'dx/mv_lx0201.ngs': R / 'movie_room/fixed/mv_lx0201.ngs',   # 11-23 MPEG-1(엔진이 MPEG-2 를 멈춤)
}
for sub in ('fonts', 'licenses', 'hires_ui'):   # 11-24 hires_ui = 문장 끝 아이콘 4배(본 패치)
    for p in sorted((GAME / sub).iterdir()):
        FILES[f'{sub}/{p.name}'] = p
if stage.exists():
    shutil.rmtree(stage)
man = {}
for rel, src in FILES.items():
    d = stage / rel
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, d)
    man[rel] = hashlib.sha256(d.read_bytes()).hexdigest()
    # 놀이 사본과 같은지(그림 묶음은 놀이 사본에 없다)
    g = GAME / rel
    if g.exists() and hashlib.sha256(g.read_bytes()).hexdigest() != man[rel]:
        print('놀이 사본과 다름:', rel)
(W / f'stage_manifest_{cgname}.json').write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding='utf-8')
print('stage', stage, len(man), 'files', round(sum((stage / r).stat().st_size for r in man) / 2**20, 1), 'MB')
