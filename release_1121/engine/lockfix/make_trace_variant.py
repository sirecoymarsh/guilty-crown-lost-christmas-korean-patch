"""사운드 화면의 단계별 시간을 재는 시험 대본(Claude 11-24). 다른 세션의 새 대본(nss.test_seek.npa e609d7a9 사본)에
시각 표지를 심는다 - 표지는 DLL 의 시험 명령(그림 이름 nss/kr_cmd_trace*.png 을 읽으면 trace.log 에 GetTickCount 와 이름을 적음).
  s0 진입 직후 · s1 Wait(500) 뒤 · s2 KuCalc(열림 계산, Conquest) 뒤
  s3 KuList 시작 · s4 가림막·지우기·효과음 뒤 · s5 줄 19개 만든 뒤 · s6 막대·풀이 준비(Conquest 2번·프로세스) 뒤 · s7 가림막 걷힌 뒤(조작 가능)
  s8 곡 줄 누름(KuFade 시작) · s9 SoundPlay 뒤
만드는 것(lockfix\\nss): nss.test_trace_open.npa(모두 열기) · nss.test_trace_locked.npa(읽은 장면 없음 → Conquest 를 실제로 돎)
python -I -X utf8 make_trace_variant.py
"""
import hashlib, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NSS = HERE / 'nss'
sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_build import build
import npa_adapter as A

SRC = NSS / 'nss.test_seek_new.npa'
arc = A.NPA(SRC); ent = {e['name']: e for e in arc.entries}
snd = arc.read(ent['kr_sound.nss'])
boot = arc.read(ent['0_boot.nss'])
png = arc.read(ent['kr_cmd_q0.png'])          # 아무 작은 그림(읽히기만 하면 된다)


def sub(b, old, new, n=1):
    assert b.count(old) == n, (old, b.count(old))
    return b.replace(old, new)


snd = sub(snd, b'\tWait(500);\r\n\tKuCalc();\r\n', b'\tKuTr0();\r\n\tWait(500);\r\n\tKuTr1();\r\n\tKuCalc();\r\n\tKuTr2();\r\n')
snd = sub(snd, b'function KuList()\r\n{\r\n\tKuCover();\r\n\tKuClear();\r\n\tKuSounds();\r\n',
          b'function KuList()\r\n{\r\n\tKuTr3();\r\n\tKuCover();\r\n\tKuClear();\r\n\tKuSounds();\r\n\tKuTr4();\r\n')
snd = sub(snd, b'\tKuSeekRow();\r\n\tKuHintRow();\r\n', b'\tKuTr5();\r\n\tKuSeekRow();\r\n\tKuHintRow();\r\n\tKuTr6();\r\n')
snd = sub(snd, b'\tFade("ku_cover",200,0,null,true);\r\n\tDelete("ku_cover");\r\n', b'\tFade("ku_cover",200,0,null,true);\r\n\tDelete("ku_cover");\r\n\tKuTr7();\r\n')
snd = sub(snd, b'function KuFade()\r\n{\r\n', b'function KuFade()\r\n{\r\n\tKuTr8();\r\n')
snd = sub(snd, b'SoundPlay("@kubgm",300,1000,true);', b'SoundPlay("@kubgm",300,1000,true);KuTr9();', 19)
fns = b''.join(b'function KuTr%d()\r\n{\r\n\tCreateTexture("kutr%d",0,0,0,"nss/kr_cmd_trace_s%d.png");Delete("kutr%d");\r\n}\r\n\r\n' % (i, i, i, i) for i in range(10))
snd = sub(snd, b'function KuCover()\r\n', fns + b'function KuCover()\r\n')
add = {'kr_cmd_trace_s%d.png' % i: png for i in range(10)}

T = b'#N2Start=true;#SYSTEM_window_full=false;#KS_ALLOPEN=true;$KUS_DBG=true;'
assert boot.count(T) == 1
for tag, line in (('open', b'#N2Start=true;#SYSTEM_window_full=false;#KS_ALLOPEN=true;'),
                  ('locked', b'#N2Start=true;#SYSTEM_window_full=false;#KS_ALLOPEN=false;')):
    out = NSS / f'nss.test_trace_{tag}.npa'
    build(SRC, out, replace={'kr_sound.nss': snd, '0_boot.nss': boot.replace(T, line)}, add=add)
    print(out.name, hashlib.sha256(out.read_bytes()).hexdigest()[:8], out.stat().st_size)
# 같은 대본에서 디버그 글만 뺀 판(막대 프로세스가 0.5초마다 디버그 글을 만들지 않게): 켬/끔 비교용
plain = NSS / 'nss.test_new_open.npa'
build(SRC, plain, replace={'0_boot.nss': boot.replace(T, b'#N2Start=true;#SYSTEM_window_full=false;#KS_ALLOPEN=true;')})
print(plain.name, hashlib.sha256(plain.read_bytes()).hexdigest()[:8], plain.stat().st_size)
