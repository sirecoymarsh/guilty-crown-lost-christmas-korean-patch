"""다른 세션의 둘째 고침 대본(nss.test_seek.npa 65bdcd87: 풀이 그림을 본 대본이 만들고 SetAlias, 먼저 끝내고 지우기, 가림막 안 기다림,
Wait(300)은 재생 중일 때만)에 시각 표지를 심는다(Claude 11-24, 독립 확인용). 표지 뜻은 make_trace_variant.py·make_hint_trace_variant.py 와 같다:
  s0 진입 · s1 Wait(500) 뒤 · s2 KuCalc 뒤 · s3 KuList 시작 · s4 프로세스 끝내기·가림막·지우기 뒤 · s5 줄 만든 뒤 · s6 막대·풀이 준비 뒤 · s7 조작 가능
  s8 곡 누름(KuFade 시작) · s9 SoundPlay 뒤 · h0 프로세스 시작 · h2 프로세스 첫 틱 뒤
python -I -X utf8 make_trace_variant2.py   → nss\\nss.test_trace2_open.npa (원천 사본 nss\\nss.test_seek_new2.npa)
"""
import hashlib, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NSS = HERE / 'nss'
sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_build import build
import npa_adapter as A

SRC0 = Path(r'F:\AI\gclx-4k\release_1121\nss_variants\nss.test_seek.npa')
SRC = NSS / 'nss.test_seek_new2.npa'
shutil.copyfile(SRC0, SRC)
print('source', hashlib.sha256(SRC.read_bytes()).hexdigest()[:8])
arc = A.NPA(SRC); ent = {e['name']: e for e in arc.entries}
snd = arc.read(ent['kr_sound.nss'])
boot = arc.read(ent['0_boot.nss'])
png = arc.read(ent['kr_cmd_q0.png'])


def sub(b, old, new, n=1):
    assert b.count(old) == n, (old, b.count(old))
    return b.replace(old, new)


snd = sub(snd, b'\tWait(500);\r\n\tKuCalc();\r\n', b'\tKuTr0();\r\n\tWait(500);\r\n\tKuTr1();\r\n\tKuCalc();\r\n\tKuTr2();\r\n')
snd = sub(snd, b'function KuList()\r\n{\r\n', b'function KuList()\r\n{\r\n\tKuTr3();\r\n')
snd = sub(snd, b'\tKuCover();\r\n\tKuClear();\r\n\tKuSounds();\r\n', b'\tKuCover();\r\n\tKuClear();\r\n\tKuSounds();\r\n\tKuTr4();\r\n')
snd = sub(snd, b'\tKuSeekRow();\r\n\tKuHintRow();\r\n', b'\tKuTr5();\r\n\tKuSeekRow();\r\n\tKuHintRow();\r\n\tKuTr6();\r\n')
snd = sub(snd, b'\tFade("ku_cover",200,0,null,false);\r\n', b'\tFade("ku_cover",200,0,null,false);\r\n\tKuTr7();\r\n')
snd = sub(snd, b'function KuFade()\r\n{\r\n', b'function KuFade()\r\n{\r\n\tKuTr8();\r\n')
snd = sub(snd, b'SoundPlay("@kubgm",300,1000,true);', b'SoundPlay("@kubgm",300,1000,true);KuTr9();', 19)
snd = sub(snd, b'function KuHintLoop()\r\n{\r\n\t$KUH_RUN=true;\r\n\twhile($KUH_ON){\r\n\t\tKuHintTick();\r\n\t\tif($KUS_ON){KuSeekTick();}\r\n',
          b'function KuHintLoop()\r\n{\r\n\t$KUH_RUN=true;\r\n\tKuTh0();\r\n\t$kth_first=true;\r\n\twhile($KUH_ON){\r\n\t\tKuHintTick();\r\n\t\tif($KUS_ON){KuSeekTick();}\r\n'
          b'\t\tif($kth_first){$kth_first=false;KuTh2();}\r\n')
fns = b''.join(b'function KuTr%d()\r\n{\r\n\tCreateTexture("kutr%d",0,0,0,"nss/kr_cmd_trace_s%d.png");Delete("kutr%d");\r\n}\r\n\r\n' % (i, i, i, i) for i in range(10))
fns += b''.join(b'function KuTh%d()\r\n{\r\n\tCreateTexture("kuth%d",0,0,0,"nss/kr_cmd_trace_h%d.png");Delete("kuth%d");\r\n}\r\n\r\n' % (i, i, i, i) for i in (0, 2))
snd = sub(snd, b'function KuCover()\r\n', fns + b'function KuCover()\r\n')
add = {'kr_cmd_trace_s%d.png' % i: png for i in range(10)}
add.update({'kr_cmd_trace_h%d.png' % i: png for i in (0, 2)})
T = b'#N2Start=true;#SYSTEM_window_full=false;#KS_ALLOPEN=true;$KUS_DBG=true;'
assert boot.count(T) == 1
out = NSS / 'nss.test_trace2_open.npa'
build(SRC, out, replace={'kr_sound.nss': snd, '0_boot.nss': boot.replace(T, b'#N2Start=true;#SYSTEM_window_full=false;#KS_ALLOPEN=true;')}, add=add)
print(out.name, hashlib.sha256(out.read_bytes()).hexdigest()[:8], out.stat().st_size)
plain = NSS / 'nss.test_new2_open.npa'
build(SRC, plain, replace={'0_boot.nss': boot.replace(T, b'#N2Start=true;#SYSTEM_window_full=false;#KS_ALLOPEN=true;')})
print(plain.name, hashlib.sha256(plain.read_bytes()).hexdigest()[:8], plain.stat().st_size)
