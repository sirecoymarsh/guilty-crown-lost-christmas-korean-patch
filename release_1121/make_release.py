"""11-21 배포 묶음 두 개를 만든다(Y:\\AI\\gclx-release-1121\\out).
- 본 패치 zip: 한국어패치_설치.bat · 한국어패치_제거.bat · 읽어보기.txt · 한국어패치\\(files · delta · tools)
  files = 게임 폴더에 그대로 들어갈 파일(대본·DLL·대리 version.dll·실행기·글꼴·라이선스·한국어 영상 3개)
  delta = 원본 cg.npa·실행 파일 → 한국어판 차이(xdelta3, 앱 머리 없음) + cg.npa 되돌리기 차이
- 고화질 묶음 zip(압축 없이 담기): hires\\ · dx4k\\mv_op.mp4 · dx4k\\GC_eyecatch_E.mp4
  (dx4k\\mv_lx0201.mp4 는 지금 DLL 이 읽지 않으므로 넣지 않는다)
원본 게임 파일(그림·소리 묶음 등)은 넣지 않는다.
python -I -X utf8 make_release.py [--skip-hires]
"""
import hashlib, json, shutil, sys, zipfile
from pathlib import Path
W = Path(__file__).resolve().parent
R = Path(r'Y:\AI\gclx-release-1121'); T = R / 'work/text'; D = R / 'work/delta'; OUT = R / 'out'
GAME = Path(r'P:\AI\gclx-codexrun\game')          # 놀이 사본: 글꼴·라이선스·실행기·영상·고화질 원천
XD = Path(r'P:\AI\demonbane-ps2-kr\release\pkg\tools\xdelta3.exe')
VER = '1.0'
FILES = {
    'nss.npa': W / 'staging/nss_final.npa',
    'system.npa': GAME / 'system.npa',
    'n2hd_runtime.dll': W / 'engine/payload/n2hd_runtime.dll',
    'version.dll': W / 'proxy/version.dll',
    'Korean4K.exe': GAME / 'Korean4K.exe',
    'dx/mv_op.ngs': GAME / 'dx/mv_op.ngs',
    'dx/GC_eyecatch_E.ngs': GAME / 'dx/GC_eyecatch_E.ngs',
    'dx/mv_lx0201.ngs': W / 'movie/out/mv_lx0201.ngs',
}
for p in sorted((GAME / 'fonts').iterdir()):
    FILES['fonts/' + p.name] = p
for p in sorted((GAME / 'licenses').iterdir()):
    FILES['licenses/' + p.name] = p
DELTA = ['exe.vcdiff', 'cg.npa.vcdiff', 'cg.npa.restore.vcdiff']


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


OUT.mkdir(parents=True, exist_ok=True)
manifest = {'version': VER, 'main': {}, 'hires': {}}
if '--skip-hires' in sys.argv and (OUT / 'manifest.json').exists():   # 고화질 묶음은 그대로: 그 목록은 남긴다
    manifest['hires'] = json.loads((OUT / 'manifest.json').read_text('utf-8')).get('hires', {})
main = OUT / f'길티크라운_로스트크리스마스_한국어패치_{VER}_본패치.zip'
with zipfile.ZipFile(main, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for n in ('한국어패치_설치.bat', '한국어패치_제거.bat', '읽어보기.txt'):
        z.write(T / n, n); manifest['main'][n] = sha(T / n)
    for rel, src in FILES.items():
        arc = 'KoreanPatch/files/' + rel
        z.write(src, arc, compress_type=zipfile.ZIP_STORED if rel.endswith(('.ngs', '.ttf')) else zipfile.ZIP_DEFLATED)
        manifest['main'][arc] = sha(src)
    for n in DELTA:
        z.write(D / n, 'KoreanPatch/delta/' + n, compress_type=zipfile.ZIP_STORED); manifest['main']['KoreanPatch/delta/' + n] = sha(D / n)
    z.write(XD, 'KoreanPatch/tools/xdelta3.exe'); manifest['main']['KoreanPatch/tools/xdelta3.exe'] = sha(XD)
print('main', main.name, round(main.stat().st_size / 2**20, 1), 'MB')

if '--skip-hires' not in sys.argv:
    hz = OUT / f'길티크라운_로스트크리스마스_한국어패치_{VER}_고화질묶음.zip'
    with zipfile.ZipFile(hz, 'w', zipfile.ZIP_STORED, allowZip64=True) as z:
        for p in sorted((GAME / 'hires').rglob('*')):
            if p.is_file() and p.name != 'art.log':
                rel = p.relative_to(GAME).as_posix(); z.write(p, rel); manifest['hires'][rel] = p.stat().st_size
        for n in ('mv_op.mp4', 'GC_eyecatch_E.mp4'):
            z.write(GAME / 'dx4k' / n, 'dx4k/' + n); manifest['hires']['dx4k/' + n] = sha(GAME / 'dx4k' / n)
    print('hires', hz.name, round(hz.stat().st_size / 2**30, 2), 'GB', len(manifest['hires']), 'files')
(OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
