"""잠금 고침 시험 준비(Claude 11-24 「사운드 모드 성능」 세션). 다른 세션의 시험 사본(P:\\AI\\gclx-reltest)·대본 폴더는 건드리지 않는다.
1) 시험 사본 P:\\AI\\gclx-locktest\\game: 놀이 사본에서 큰 읽기 전용 묶음은 하드 링크, 작은 파일은 진짜 사본(make_reltest.py 와 같은 규칙).
   sound.npa 는 진짜 사본(사용자가 게임을 켜 두면 하드 링크는 엔진이 못 연다, 11-23). DLL 은 lockfix\\out 의 것.
2) 시험 대본 폴더 lockfix\\nss: 놀이 사본에 깔린 대본(사용자가 느리다고 한 판)을 바탕으로
   - nss.normal.npa   = run_test 가 시험 뒤 되돌려 놓는 기준(= 시험 사본에 처음 넣어 두는 것)
   - nss.test_inst_open.npa   = 설치판 + 창 모드·모두 열기(다른 세션의 nss.test_seek 와 같은 꼴)
   - nss.test_inst_locked.npa = 설치판 + 창 모드만(읽은 장면 없음 → Conquest 를 실제로 돈다; VOiD 만 열림)
python -I -X utf8 make_locktest.py
"""
import hashlib, os, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]                                   # release_1121
SRC = Path(r'P:\AI\gclx-codexrun\game')
DST = Path(r'P:\AI\gclx-locktest\game')
NSS = HERE / 'nss'
LINK = {'cg.npa', 'cg1.npa', 'voice.npa'}
LINK_DIRS = {'dx', 'dx4k', 'hires', 'hires_ui', 'fonts'}
SKIP = {'art.log', 'launcher-test.log', 'n2hd-options.ini'}
SKIP_DIRS = {'lyrics-resume'}                         # 코덱스의 세이브 보기 자료: 시험 프로필에는 세이브가 없다
INSTALL = {
    'n2hd_runtime.dll': HERE / 'out/n2hd_runtime.dll',
    'Korean4K_test.exe': W / 'launcher_test/Korean4K_test.exe',
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def make_copy():
    DST.mkdir(parents=True, exist_ok=True)
    n_link = n_copy = 0
    for p in SRC.rglob('*'):
        rel = p.relative_to(SRC); d = DST / rel
        if rel.parts[0] in SKIP_DIRS:
            continue
        if p.is_dir():
            d.mkdir(parents=True, exist_ok=True); continue
        if p.name in SKIP or rel.as_posix() in INSTALL or d.exists():
            continue
        d.parent.mkdir(parents=True, exist_ok=True)
        if p.name in LINK or rel.parts[0] in LINK_DIRS:
            os.link(p, d); n_link += 1
        else:
            shutil.copy2(p, d); n_copy += 1
    for rel, f in INSTALL.items():
        d = DST / rel
        if d.exists():
            d.unlink()
        shutil.copyfile(f, d)
        assert sha(d) == sha(f)
    print('copy: links', n_link, 'copies', n_copy, '->', DST, 'dll', sha(DST / 'n2hd_runtime.dll')[:8])


def make_variants():
    sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
    from npa_build import build
    import npa_adapter as A
    NSS.mkdir(exist_ok=True)
    inst = NSS / 'nss.installed.npa'
    shutil.copyfile(SRC / 'nss.npa', inst)
    arc = A.NPA(inst); ent = {e['name']: e for e in arc.entries}
    boot = arc.read(ent['0_boot.nss'])
    A = '\tif(!#N2Start){'.encode('cp932'); assert boot.count(A) == 1
    opened = boot.replace(A, '\t#N2Start=true;#SYSTEM_window_full=false;#KS_ALLOPEN=true;\r\n'.encode('cp932') + A, 1)
    locked = boot.replace(A, '\t#N2Start=true;#SYSTEM_window_full=false;#KS_ALLOPEN=false;\r\n'.encode('cp932') + A, 1)
    build(inst, NSS / 'nss.test_inst_open.npa', replace={'0_boot.nss': opened})
    build(inst, NSS / 'nss.test_inst_locked.npa', replace={'0_boot.nss': locked})
    shutil.copyfile(inst, NSS / 'nss.normal.npa')
    shutil.copyfile(inst, DST / 'nss.npa')
    for n in ('nss.installed.npa', 'nss.normal.npa', 'nss.test_inst_open.npa', 'nss.test_inst_locked.npa'):
        print(n, sha(NSS / n)[:8], (NSS / n).stat().st_size)


if __name__ == '__main__':
    make_copy()
    make_variants()
    print('play copy untouched: nss', sha(SRC / 'nss.npa')[:8], 'dll', sha(SRC / 'n2hd_runtime.dll')[:8])
