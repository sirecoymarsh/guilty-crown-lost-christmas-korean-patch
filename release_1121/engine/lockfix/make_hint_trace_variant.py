"""풀이·막대 프로세스 안의 시간을 재는 시험 대본(Claude 11-24): 표지 대본(nss.test_trace_open.npa)에 프로세스 쪽 표지를 더한다.
  h0 프로세스 시작(KuHintLoop 첫 줄) · h1 KuHintMake(풀이 그림 20장 만들기) 뒤 · h2 첫 틱 뒤
찍힌 화면(lk_mc_v3b)에서 다시 그린 지 4초 뒤에도 풀이 그림이 덜 만들어진 채 보인 일이 있어, 그 구간이 실제로 얼마나 걸리는지 본다.
python -I -X utf8 make_hint_trace_variant.py   → nss\\nss.test_trace_hint.npa
"""
import hashlib, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NSS = HERE / 'nss'
sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from npa_build import build
import npa_adapter as A

SRC = NSS / 'nss.test_trace_open.npa'
arc = A.NPA(SRC); ent = {e['name']: e for e in arc.entries}
snd = arc.read(ent['kr_sound.nss'])
png = arc.read(ent['kr_cmd_q0.png'])


def sub(b, old, new, n=1):
    assert b.count(old) == n, (old, b.count(old))
    return b.replace(old, new)


snd = sub(snd, b'function KuHintLoop()\r\n{\r\n\tKuHintMake();\r\n\twhile($KUH_ON){\r\n\t\tKuHintTick();\r\n\t\tif($KUS_ON){KuSeekTick();}\r\n',
          b'function KuHintLoop()\r\n{\r\n\tKuTh0();\r\n\tKuHintMake();\r\n\tKuTh1();\r\n\t$kth_first=true;\r\n\twhile($KUH_ON){\r\n\t\tKuHintTick();\r\n\t\tif($KUS_ON){KuSeekTick();}\r\n'
          b'\t\tif($kth_first){$kth_first=false;KuTh2();}\r\n')
fns = b''.join(b'function KuTh%d()\r\n{\r\n\tCreateTexture("kuth%d",0,0,0,"nss/kr_cmd_trace_h%d.png");Delete("kuth%d");\r\n}\r\n\r\n' % (i, i, i, i) for i in range(3))
snd = sub(snd, b'function KuCover()\r\n', fns + b'function KuCover()\r\n')
out = NSS / 'nss.test_trace_hint.npa'
build(SRC, out, replace={'kr_sound.nss': snd}, add={'kr_cmd_trace_h%d.png' % i: png for i in range(3)})
print(out.name, hashlib.sha256(out.read_bytes()).hexdigest()[:8], out.stat().st_size)
