"""동봉 글꼴이 실제로 쓰이는지 가리는 시험 (이 PC엔 Noto KR 이 깔려 있어 그대로는 못 가림).
글꼴 이름을 「GCLX Test KR / GCLX Serif KR」로 바꾼 사본과, 대본의 글꼴 이름도 똑같이 바꾼 nss.npa 로
 fA: 바꾼 글꼴을 fonts\ 에 넣고 → 원래 Noto 와 똑같이 나와야 함
 fB: fonts\ 를 비우고         → 다른 글꼴(대체)로 나와야 함
끝나면 원래 fonts\ 와 nss.npa 를 되돌린다. python -X utf8 font_bundle_test.py
"""
import shutil, subprocess, sys
from pathlib import Path
from fontTools.ttLib import TTFont
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA
NAMES = sys.argv[1:3] or ['fA', 'fB']
G = Path(r'P:\AI\gclx-4k-test\game')
W = Path(r'F:\AI\gclx-4k\fonttest'); W.mkdir(exist_ok=True)
REN = {'Noto Sans KR': 'GCLX Test KR', 'Noto Serif KR': 'GCLX Serif KR', 'NotoSansKR': 'GCLXTestKR', 'NotoSerifKR': 'GCLXSerifKR'}
def rename(src, dst):
    f = TTFont(src)
    for r in f['name'].names:
        s = r.toUnicode()
        t = s
        for a, b in REN.items(): t = t.replace(a, b)
        if t != s: r.string = t
    f.save(dst)
for n in ('NotoSansKR-VF.ttf', 'NotoSerifKR-VF.ttf'):
    rename(G / 'fonts' / n, W / n.replace('Noto', 'GCLX'))
# 대본 사본: 글꼴 이름만 바꿈 (길이 같음)
nss = G / 'nss.npa'
shutil.copy2(nss, W / 'nss.orig.npa')
arc = NPA(nss)
ent = {e['name']: e for e in arc.entries}
rep = {}
for name in ('function_lc_toho.nss', 'lx0010.nss', 'sys_backlog.nss', 'sys_config.nss', 'sys_load.nss', 'sys_save.nss'):
    d = arc.read(ent[name])
    for a, b in (('Noto Sans KR', 'GCLX Test KR'), ('Noto Serif KR', 'GCLX Serif KR')):
        d = d.replace(a.encode(), b.encode())
    rep[name] = d
(W / 'nss.renamed.npa').write_bytes(arc.pack(rep))
fonts = G / 'fonts'; held = W / 'fonts_held'
shutil.move(str(fonts), str(held))
try:
    shutil.copy2(W / 'nss.renamed.npa', nss)
    fonts.mkdir()
    for p in W.glob('GCLX*.ttf'): shutil.copy2(p, fonts / p.name)
    subprocess.run([sys.executable, '-X', 'utf8', r'F:\AI\gclx-4k\tools\run_test.py', NAMES[0], '--art-off', '--seconds', '75', '--shot-ms', '3000', '--keys'], check=True)
    shutil.rmtree(fonts); fonts.mkdir()
    subprocess.run([sys.executable, '-X', 'utf8', r'F:\AI\gclx-4k\tools\run_test.py', NAMES[1], '--art-off', '--seconds', '75', '--shot-ms', '3000', '--keys'], check=True)
finally:
    if fonts.exists(): shutil.rmtree(fonts)
    shutil.move(str(held), str(fonts))
    shutil.copy2(W / 'nss.orig.npa', nss)
print('되돌림:', sorted(p.name for p in fonts.iterdir()), (nss.read_bytes() == (W / 'nss.orig.npa').read_bytes()))
