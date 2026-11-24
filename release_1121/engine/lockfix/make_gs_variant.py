"""「먼저 끝내고 지우기」 시험 대본(Claude 11-24): 표지 대본(nss.test_trace_open.npa)에서 KuList 가 목록을 지우기 전에
풀이·막대 프로세스에 끝내라고 하고($KUH_ON=false) 고리가 끝난 것($KUH_RUN=false)을 본 뒤 지우게 한다.
돌고 있는 프로세스를 Delete 로 지우면 엔진 소멸자가 100+1500+1500ms 를 기다리는 일(잠금고침_기록.md 「둘째 고리」)을 대본 쪽에서 피하는 방법의 검증용.
다른 세션의 생성기(title_hints.py·patch_seek.py)에 같은 고침을 넣을 때의 견본이기도 하다.
python -I -X utf8 make_gs_variant.py   → nss\\nss.test_trace_gs.npa
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


def sub(b, old, new, n=1):
    assert b.count(old) == n, (old, b.count(old))
    return b.replace(old, new)


# 1) 프로세스가 스스로 「돌고 있음」을 알린다
snd = sub(snd, b'function KuHintLoop()\r\n{\r\n\tKuHintMake();\r\n', b'function KuHintLoop()\r\n{\r\n\t$KUH_RUN=true;\r\n\tKuHintMake();\r\n')
snd = sub(snd, b'\t\tif($KUS_ON){KuSeekTick();}\r\n\t\tWait(16);\r\n\t}\r\n}\r\n',
          b'\t\tif($KUS_ON){KuSeekTick();}\r\n\t\tWait(16);\r\n\t}\r\n\t$KUH_RUN=false;\r\n}\r\n')
# 2) 목록을 지우기 전에: 끝내라고 하고, 끝날 때까지(최대 0.5초) 기다린다
snd = sub(snd, b'\tKuTr3();\r\n\tKuCover();\r\n', b'\tKuTr3();\r\n\tKuProcStop();\r\n\tKuCover();\r\n')
snd = sub(snd, b'function KuCover()\r\n',
          b'function KuProcStop()\r\n{\r\n\t$KUH_ON=false;$KUS_ON=false;$kps_n=0;\r\n'
          b'\twhile($KUH_RUN){\r\n\t\tWait(4);\r\n\t\t$kps_n=$kps_n+1;\r\n\t\tif($kps_n>125){$KUH_RUN=false;}\r\n\t}\r\n}\r\n\r\n'
          b'function KuCover()\r\n')
out = NSS / 'nss.test_trace_gs.npa'
build(SRC, out, replace={'kr_sound.nss': snd})
print(out.name, hashlib.sha256(out.read_bytes()).hexdigest()[:8], out.stat().st_size)
