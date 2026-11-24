"""코덱스 배포 후보를 숨긴 시험용 사본으로 꾸린다(코덱스 폴더는 읽기만).
- 큰 읽기 전용 묶음(cg·cg1·sound·voice.npa, dx·dx4k·hires·fonts)은 하드 링크, 엔진·실행기·대본 등 작은 파일은 진짜 사본.
  run_test.py 가 nss.npa 를 copyfile 로 덮어쓰므로 nss.npa 가 하드 링크면 코덱스 원본이 바뀐다 — 반드시 사본.
- 시험 실행기 Korean4K_test.exe 는 Claude 시험 사본에서 가져옴(창을 활성화하지 않음).
- 대본 변형은 nss_variants_codex\\: nss.normal.npa(코덱스 원본 그대로) · nss.test.npa(타이틀 없이 lx0010·자동 진행).
  python -X utf8 make_codex_run.py
"""
import hashlib, os, shutil, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA

SRC = Path(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\outputs\korean-game-candidate\game')
DST = Path(r'P:\AI\gclx-codexrun\game')
NSS = Path(r'F:\AI\gclx-4k\nss_variants_codex')
LINK = {'cg.npa', 'cg1.npa', 'sound.npa', 'voice.npa'}
LINK_DIRS = {'dx', 'dx4k', 'hires', 'fonts'}
SKIP = {'art.log'}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


DST.mkdir(parents=True, exist_ok=True)
for p in SRC.iterdir():
    q = DST / p.name
    if p.is_dir():
        if p.name in LINK_DIRS:
            for f in p.rglob('*'):
                if f.is_file() and f.name not in SKIP:
                    t = q / f.relative_to(p)
                    if not t.exists():
                        t.parent.mkdir(parents=True, exist_ok=True)
                        os.link(f, t)
        else:
            shutil.copytree(p, q, dirs_exist_ok=True)
    elif p.name in LINK:
        if not q.exists():
            os.link(p, q)
    else:
        shutil.copyfile(p, q)
shutil.copyfile(r'P:\AI\gclx-4k-test\game\Korean4K_test.exe', DST / 'Korean4K_test.exe')

NSS.mkdir(parents=True, exist_ok=True)
shutil.copyfile(SRC / 'nss.npa', NSS / 'nss.normal.npa')
arc = NPA(SRC / 'nss.npa')
ent = {e['name']: e for e in arc.entries}
boot = arc.read(ent['0_boot.nss'])
a = '\tif(!#N2Start){'.encode('cp932')
assert boot.count(a) == 1
boot = boot.replace(a, '\t#N2Start=true;#SYSTEM_window_full=false;\r\n'.encode('cp932') + a, 1)
b = '\twhile(1)\r\n\t{\r\n\t\t$スクリプトバージョン'.encode('cp932')
assert boot.count(b) == 1, boot.count(b)
boot = boot.replace(b, '\t$GameContiune=1;$GameName="lx0010.nss";\r\n'.encode('cp932') + b, 1)
start = arc.read(ent['0_boot_開始スクリプト.nss'])
c = '$SYSTEM_text_auto=false;'.encode('cp932')
assert start.count(c) >= 1
start = start.replace(c, '$SYSTEM_text_auto=true;'.encode('cp932'))
(NSS / 'nss.test.npa').write_bytes(arc.pack({'0_boot.nss': boot, '0_boot_開始スクリプト.nss': start}))
chk = NPA(NSS / 'nss.test.npa')
ce = {e['name']: e for e in chk.entries}
assert chk.read(ce['0_boot.nss']) == boot and chk.read(ce['0_boot_開始スクリプト.nss']) == start

for n in ('n2hd_runtime.dll', 'nss.npa', 'GUILTY CROWN LOST XMAS.exe'):
    assert sha(SRC / n) == sha(DST / n), n
for n in LINK:
    assert os.stat(SRC / n).st_ino == os.stat(DST / n).st_ino, n
print('사본 →', DST)
print('대본 →', NSS, sha(NSS / 'nss.normal.npa')[:16], sha(NSS / 'nss.test.npa')[:16])
