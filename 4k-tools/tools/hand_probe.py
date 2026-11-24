"""숨긴 시험용 손 모양 지도: run_test.py 가 띄운 게임(N2HD_TEST_CURSOR_FILE=1)에 가짜 커서를 격자로 옮기며
엔진이 정한 커서 모양([0x5b3114]+0x14, 0x7f89 = 손)을 읽는다. run_test 와 같이(이것은 앞에서) 돌린다.
python -X utf8 hand_probe.py <run 이름> [시작 대기초=50]
결과: 손이 뜬 엔진 좌표를 줄마다 출력 + testrun\\<run>\\hand.txt"""
import ctypes, ctypes.wintypes as wt, struct, sys, time
from pathlib import Path
sys.path.insert(0, r'P:\AI\touka-ps2-kr\work\codex_watch\host')
import hostlib as H  # noqa: E402

run = Path(r'F:\AI\gclx-4k\testrun') / sys.argv[1]; wait = float(sys.argv[2]) if len(sys.argv) > 2 else 50
GAME = Path(r'P:\AI\gclx-codexrun\game'); EXE = 'GUILTY CROWN LOST XMAS.exe'
K, U = ctypes.windll.kernel32, ctypes.windll.user32
t0 = time.time()
while time.time() - t0 < 60 and not H.pids_of(GAME, EXE):
    time.sleep(0.5)
pid = H.pids_of(GAME, EXE)[0]
hp = K.OpenProcess(0x0010 | 0x0400, False, pid)


def u32(a):
    b = ctypes.create_string_buffer(4); n = ctypes.c_size_t()
    return struct.unpack('<I', b.raw)[0] if K.ReadProcessMemory(hp, ctypes.c_void_p(a), b, 4, ctypes.byref(n)) else None


cur = run / 'profile' / 'cursor.txt'
time.sleep(max(0, t0 + wait - time.time()))
hwnd = H.window_of(pid)
hits, lines = [], []
for ey in range(280, 576, 8):
    row = []
    for ex in range(380, 1000, 24):
        cur.write_text(f'{ex},{ey}')
        for _ in range(2):
            U.PostMessageW(hwnd, 0x200, 0, (ey << 16) | ex); time.sleep(0.12)
        m = u32(0x5b3114)
        hand = m and u32(m + 0x14) == 0x7f89
        row.append('#' if hand else '.')
        if hand:
            hits.append((ex, ey))
    lines.append(f'{ey:3d} ' + ''.join(row))
    print(lines[-1], flush=True)
(run / 'hand.txt').write_text('x 380..1000 step 24\n' + '\n'.join(lines), 'utf-8')
print('hand points', len(hits))
