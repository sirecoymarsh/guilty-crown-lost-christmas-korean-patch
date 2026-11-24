"""덮어쓰기 꼴 본 패치 ZIP 을 만든다(설치기·배치 파일 없음).
ZIP 뿌리 = 게임 폴더: stage 폴더의 파일 그대로 + 패치_사용방법.txt(UTF-8 BOM, CRLF).
python -I -X utf8 make_zip.py <stage 폴더> <디펜더 결과 한 줄>
"""
import sys, zipfile, hashlib, json
from pathlib import Path
stage, defender = Path(sys.argv[1]), sys.argv[2]
R = Path(r'Y:\AI\gclx-release-1121')
OUT = R / 'out'
VER = '1.0'
tpl = (R / 'work/overwrite/패치_사용방법.txt').read_text('utf-8')
assert tpl.count('{DEFENDER}') == 1
readme = ('\ufeff' + tpl.replace('{DEFENDER}', defender)).replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8')
assert b'\t' not in readme
z_path = OUT / f'길티크라운_로스트크리스마스_한국어패치_{VER}_본패치.zip'
man = {}
with zipfile.ZipFile(z_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    z.writestr('패치_사용방법.txt', readme); man['패치_사용방법.txt'] = hashlib.sha256(readme).hexdigest()
    for p in sorted(stage.rglob('*')):
        if not p.is_file():
            continue
        rel = p.relative_to(stage).as_posix()
        stored = p.suffix.lower() in ('.ngs', '.ttf', '.npa')
        z.write(p, rel, compress_type=zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED)
        man[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
with zipfile.ZipFile(z_path) as z:                  # 다 쓴 뒤 읽기로 열어 CRC 확인
    bad = z.testzip()
assert bad is None, bad
zsha = hashlib.sha256(z_path.read_bytes()).hexdigest()
m = json.loads((OUT / 'manifest.json').read_text('utf-8')) if (OUT / 'manifest.json').exists() else {}
m['version'] = VER; m['main_overwrite'] = man; m.pop('main', None); m['main_zip_sha256'] = zsha
(OUT / 'manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding='utf-8')
(z_path.with_suffix('.zip.sha256')).write_text(f'{zsha}  {z_path.name}\n', encoding='utf-8')
print(z_path.name, round(z_path.stat().st_size / 2**20, 1), 'MB', len(man), 'files', 'sha256', zsha[:8])
