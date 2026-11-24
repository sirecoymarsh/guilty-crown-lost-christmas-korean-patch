"""켜져 있는 게임의 프레임 주기를 정하는 엔진 변수를 초당 20번 읽어(읽기만) 기록하고, PresentMon 도 같이 돌린다. 게임이 꺼질 때까지.
엔진 0x490c80: 주기 = int[0x6294b4 + 4*byte[0x629498]] / 배수, 배수 = [0x620540]==0x190 이면 double[0x620668],
[0x62057c]!=0 이면 double[0x6206b0], 아니면 double[0x620650 + 8*[0x620574](#SYSTEM_play_speed)]. (+ 코덱스 ×0.5)
결과 F:\\AI\\gclx-4k\\perf\\<이름>_pace.tsv(벽시계ms, 앞창여부, 540, 57c, 574, 498, 분자, 배수, 주기ms), <이름>_pm.csv, <이름>_t0.txt
python -X utf8 pace_watch.py <이름>"""
import ctypes, ctypes.wintypes as wt, struct, subprocess, sys, time
from pathlib import Path

k32 = ctypes.WinDLL('kernel32', use_last_error=True); u32 = ctypes.WinDLL('user32', use_last_error=True)
EXE = 'GUILTY CROWN LOST XMAS.exe'
PM = Path(r'P:/AI/Codex/projects/guilty-crown-lost-christmas-ui-opening/work/revisions/frame-time-20261102/PresentMon-2.6.0-x64.exe')
OUT = Path(r'F:\AI\gclx-4k\perf'); name = sys.argv[1]


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [('dwSize', wt.DWORD), ('cntUsage', wt.DWORD), ('th32ProcessID', wt.DWORD), ('th32DefaultHeapID', ctypes.c_void_p),
                ('th32ModuleID', wt.DWORD), ('cntThreads', wt.DWORD), ('th32ParentProcessID', wt.DWORD), ('pcPriClassBase', wt.LONG),
                ('dwFlags', wt.DWORD), ('szExeFile', wt.WCHAR * 260)]


def find_pid():
    snap = k32.CreateToolhelp32Snapshot(0x2, 0); pe = PROCESSENTRY32W(); pe.dwSize = ctypes.sizeof(pe); pid = None
    ok = k32.Process32FirstW(snap, ctypes.byref(pe))
    while ok:
        if pe.szExeFile.lower() == EXE.lower():
            pid = pe.th32ProcessID
        ok = k32.Process32NextW(snap, ctypes.byref(pe))
    k32.CloseHandle(snap); return pid


while not (pid := find_pid()):
    time.sleep(1)
time.sleep(3)
hp = k32.OpenProcess(0x0410 | 0x00100000, False, pid)


def rd(addr, n):
    buf = ctypes.create_string_buffer(n); got = ctypes.c_size_t()
    return buf.raw if k32.ReadProcessMemory(hp, ctypes.c_void_p(addr), buf, n, ctypes.byref(got)) else None


def fg_is_game():
    h = u32.GetForegroundWindow(); p = wt.DWORD(); u32.GetWindowThreadProcessId(h, ctypes.byref(p)); return int(p.value == pid)


pm_csv = OUT / f'{name}_pm.csv'; pm_csv.unlink(missing_ok=True)
nopm = len(sys.argv) > 2 and sys.argv[2] == 'nopm'   # eip_record 와 같이 돌릴 때(그쪽이 PresentMon 을 돌림)
pm = subprocess.Popen(['cmd', '/c', 'exit'], stdout=subprocess.DEVNULL) if nopm else subprocess.Popen([str(PM), '--process_name', EXE, '--output_file', str(pm_csv), '--terminate_on_proc_exit', '--no_console_stats',
                       '--stop_existing_session'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
(OUT / f'{name}_t0.txt').write_text(str(time.time()))
out = open(OUT / f'{name}_pace.tsv', 'w', encoding='utf-8')
n = 0
while k32.WaitForSingleObject(hp, 0) == 0x102:
    a = rd(0x620540, 0x180); b = rd(0x629498, 1)
    if a and b:
        v540 = struct.unpack_from('<I', a, 0)[0]; v57c = struct.unpack_from('<I', a, 0x3c)[0]; v574 = struct.unpack_from('<I', a, 0x34)[0]
        i498 = b[0]
        num = rd(0x6294b4 + 4 * i498, 4); num = struct.unpack('<i', num)[0] if num else 0
        if v540 == 0x190:
            fac = struct.unpack_from('<d', a, 0x620668 - 0x620540)[0]
        elif v57c:
            fac = struct.unpack_from('<d', a, 0x6206b0 - 0x620540)[0]
        else:
            f = rd(0x620650 + 8 * v574, 8); fac = struct.unpack('<d', f)[0] if f else 0
        per = num / fac if fac else 0
        out.write(f'{time.time() * 1000:.0f}\t{fg_is_game()}\t{v540:x}\t{v57c}\t{v574}\t{i498}\t{num}\t{fac:.4f}\t{per:.2f}\n'); n += 1
    time.sleep(0.05)
out.close()
try:
    pm.wait(timeout=90)
except subprocess.TimeoutExpired:
    pm.terminate()
print('done rows', n, flush=True)
