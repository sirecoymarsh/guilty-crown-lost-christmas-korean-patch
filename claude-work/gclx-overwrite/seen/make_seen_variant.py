"""숨긴 시험용 대본: 시작하자마자 모든 장면(lx*.nss)에 대해 회상과 같은 판정(Conquest)을 묻고, 읽은 장면만 trace.log 에 적은 뒤 끝 표시.
사용자 common(읽음 기록)을 --seed-common 으로 넣고 돌리면 = 사용자 회상에 열린 장면 목록.
python -I -X utf8 make_seen_variant.py
"""
import sys, shutil
from pathlib import Path
sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_adapter import NPA
from npa_build import build
FINAL = Path(r'F:\AI\gclx-4k\release_1121\staging\nss_final.npa')
V = Path(r'Y:\AI\claude-work\gclx-overwrite\seen\nss_variants')
V.mkdir(parents=True, exist_ok=True)
arc = NPA(FINAL)
names = sorted(e['name'] for e in arc.entries if e['name'].startswith('lx') and e['name'].endswith('.nss'))
get = arc.read(next(e for e in arc.entries if e['name'] == 'kr_cmd_get.png'))
lines = ['\t$kq_r=false;',
         '\tif(#KS_ALLOPEN){$GameName="allopen";CreateTexture("kr_trace",0,0,0,"nss/kr_cmd_trace.png");Delete("kr_trace");}']   # 회상 「검수용 모두 열기」
for n in names:
    lines += [f'\t$kq_f="nss/{n}";', f'\t$kq_s="{n}";', '\t$kq_r=Conquest($kq_f,$kq_s,null);',
              f'\tif($kq_r){{$GameName="seen {n}";CreateTexture("kr_trace",0,0,0,"nss/kr_cmd_trace.png");Delete("kr_trace");}}']
lines += ['\t$GameName="done";', '\tCreateTexture("kr_trace",0,0,0,"nss/kr_cmd_tracetitle.png");Delete("kr_trace");',
          '\twhile(true){Wait(1000);}', '']
# 짧은 새 시작 대본은 엔진이 5초 만에 끝냈다(11-23 첫 시도) → 원래 0_boot 의 초기 설정 뒤(assemble.py 시험 대본과 같은 자리)에 끼운다
boot0 = arc.read(next(e for e in arc.entries if e['name'] == '0_boot.nss'))
A = '\tif(!#N2Start){'.encode('cp932')
assert boot0.count(A) == 1
boot = boot0.replace(A, '\r\n'.join(lines).encode('cp932') + A, 1)
shutil.copy2(FINAL, V / 'nss.normal.npa')
build(FINAL, V / 'nss.test_seen.npa', replace={'0_boot.nss': boot},
      add={'kr_cmd_trace.png': get, 'kr_cmd_tracetitle.png': get})
print('scenes', len(names), names[:3], names[-3:])
