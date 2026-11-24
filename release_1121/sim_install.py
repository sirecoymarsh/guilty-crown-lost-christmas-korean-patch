"""설치기 시험: 원본 영문판에서 「새 게임 폴더」를 만들고(바뀌지 않는 큰 파일만 하드 링크, 설치기가 덮어쓰는 파일은 진짜 사본),
본 패치 zip 을 풀어 한국어패치_설치.bat 을 돌린 뒤 결과가 놀이 사본·최종 파일과 같은지, 제거.bat 뒤 원본과 같은지 본다.
cg.npa 는 설치기가 새 파일을 만들고 지운 뒤 이름을 바꾸므로 하드 링크여도 원본은 그대로다.
python -I -X utf8 sim_install.py
"""
import hashlib, os, shutil, subprocess, zipfile, json
from pathlib import Path
W = Path(__file__).resolve().parent
ORIG = Path(r'Y:\GAME\Guilty-Crown-Lost-Christmas_Win_EN_Full-rip\GUILTY CROWN LOST XMAS')
SIM = Path(r'Y:\AI\gclx-release-1121\work\simgame')
ZIP = Path(r'Y:\AI\gclx-release-1121\out\길티크라운_로스트크리스마스_한국어패치_1.0_본패치.zip')
PLAY = Path(r'P:\AI\gclx-codexrun\game')
LINK = {'cg.npa', 'cg1.npa', 'sound.npa', 'voice.npa'}
REPLACED_DX = {'mv_op.ngs', 'GC_eyecatch_E.ngs', 'mv_lx0201.ngs'}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def snapshot(root):
    return {p.relative_to(root).as_posix(): (p.stat().st_size, sha(p)) for p in sorted(root.rglob('*')) if p.is_file()}


if SIM.exists():
    shutil.rmtree(SIM)
SIM.mkdir(parents=True)
for p in ORIG.rglob('*'):
    rel = p.relative_to(ORIG); d = SIM / rel
    if p.is_dir():
        d.mkdir(parents=True, exist_ok=True); continue
    d.parent.mkdir(parents=True, exist_ok=True)
    if p.name in LINK or (rel.parts[0] == 'dx' and p.name not in REPLACED_DX):
        os.link(p, d)
    else:
        shutil.copy2(p, d)
before = snapshot(SIM)
with zipfile.ZipFile(ZIP) as z:
    z.extractall(SIM)


def run(bat, inp=''):
    r = subprocess.run(['cmd', '/c', str(SIM / bat)], cwd=SIM, input=inp.encode(), capture_output=True, timeout=1800,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    return r.returncode, r.stdout.decode('cp949', 'replace')[-1500:]


rep = {}
rep['install'] = run('한국어패치_설치.bat', '\r\n')
expect = {'cg.npa': sha(PLAY / 'cg.npa'), 'GUILTY CROWN LOST XMAS.exe': sha(PLAY / 'GUILTY CROWN LOST XMAS.exe'),
          'nss.npa': sha(W / 'staging/nss_final.npa'), 'system.npa': sha(PLAY / 'system.npa'), 'n2hd_runtime.dll': sha(W / 'engine/payload/n2hd_runtime.dll'),
          'version.dll': sha(W / 'proxy/version.dll'), 'dx/mv_op.ngs': sha(PLAY / 'dx/mv_op.ngs'), 'dx/mv_lx0201.ngs': sha(W / 'movie/out/mv_lx0201.ngs'),
          'dx/GC_eyecatch_E.ngs': sha(PLAY / 'dx/GC_eyecatch_E.ngs'), 'fonts/NotoSansKR-VF.ttf': sha(PLAY / 'fonts/NotoSansKR-VF.ttf')}
rep['installed_match'] = {k: (sha(SIM / k) == v) if (SIM / k).exists() else 'missing' for k, v in expect.items()}
rep['stray_npa'] = sorted(p.name for p in SIM.glob('*.npa') if p.name not in {'cg.npa', 'cg1.npa', 'nss.npa', 'sound.npa', 'system.npa', 'voice.npa'})
rep['tmp_left'] = sorted(p.name for p in SIM.glob('*tmp*'))
rep['uninstall'] = run('한국어패치_제거.bat', 'Y\r\n\r\n')
after = snapshot(SIM)
patchfiles = {k for k in after if k.startswith('KoreanPatch') or k in ('한국어패치_설치.bat', '한국어패치_제거.bat', '읽어보기.txt')}
rep['restored_identical'] = all(after.get(k) == v for k, v in before.items())
rep['restored_diff'] = [k for k, v in before.items() if after.get(k) != v][:20]
rep['extra_after_uninstall'] = sorted(k for k in after if k not in before and k not in patchfiles)[:20]
rep['orig_untouched'] = sha(ORIG / 'cg.npa')[:12]
(W / 'qa/sim_install.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps({k: v for k, v in rep.items() if k not in ('install', 'uninstall')}, ensure_ascii=False, indent=1))
print('INSTALL OUT:', rep['install'][1][-900:])
print('UNINSTALL OUT:', rep['uninstall'][1][-600:])
