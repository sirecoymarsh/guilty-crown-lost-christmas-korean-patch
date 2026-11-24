"""놀이 사본 DLL 이 바뀌면 알리고 끝난다(Claude 11-24). 읽기만 한다.
코덱스가 세이브 호환 DLL 을 놀이 사본에 넣을 때, 잠금 고침이 그대로 들었는지 바로 보려고.
python -X utf8 watch_play_dll.py [기다릴 시간(시간 단위)=8]"""
import hashlib, sys, time
from pathlib import Path

DLL = Path(r'P:\AI\gclx-codexrun\game\n2hd_runtime.dll')
MARKS = [b'N2HD_TEST_LOCKFIX_OFF', b'N2HD_TEST_LOCKFIX_NOSTOP', b'locks.log', b'stepped-aside', b'delete-stopped']
hours = float(sys.argv[1]) if len(sys.argv) > 1 else 8


def state():
    st = DLL.stat()
    return st.st_size, st.st_mtime_ns


def sha():
    return hashlib.sha256(DLL.read_bytes()).hexdigest()


first = sha()
seen = state()
print(time.strftime('%H:%M:%S'), 'watching', first[:8], flush=True)
t0 = time.time()
while time.time() - t0 < hours * 3600:
    time.sleep(20)
    try:
        now = state()
    except OSError:
        continue                      # 바꾸는 중
    if now == seen:
        continue
    time.sleep(3)                     # 쓰기가 끝나길
    try:
        h = sha(); data = DLL.read_bytes(); seen = state()
    except OSError:
        continue
    if h == first:
        continue
    print(time.strftime('%H:%M:%S'), 'CHANGED', first[:8], '->', h, len(data), 'bytes')
    print('lock fix markers:', {m.decode(): (m in data) for m in MARKS})
    sys.exit(0)
print(time.strftime('%H:%M:%S'), 'no change in', hours, 'hours')
