"""게임이 꺼질 때까지 모든 스레드의 명령 주소를 기록(읽기만; 스레드를 수 마이크로초씩 멈췄다 놓음)하고, PresentMon 도 같이 돌린다.
끝나면 F:\\AI\\gclx-4k\\perf\\<이름>_eip.tsv(벽시계 ms, 스레드, 모듈, 오프셋), <이름>_pm.csv, <이름>_t0.txt(PresentMon 시작 벽시계).
python -X utf8 eip_record.py <이름> [간격ms=5]"""
import ctypes, ctypes.wintypes as wt, subprocess, sys, time
from pathlib import Path

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
psapi = ctypes.WinDLL('psapi', use_last_error=True)
EXE = 'GUILTY CROWN LOST XMAS.exe'
PM = Path(r'P:/AI/Codex/projects/guilty-crown-lost-christmas-ui-opening/work/revisions/frame-time-20261102/PresentMon-2.6.0-x64.exe')
OUT = Path(r'F:\AI\gclx-4k\perf')
name = sys.argv[1]
every = float(sys.argv[2]) / 1000 if len(sys.argv) > 2 else 0.005


class WOW64_CONTEXT(ctypes.Structure):
    _fields_ = [('ContextFlags', wt.DWORD), ('Dr', wt.DWORD * 6), ('FloatSave', ctypes.c_byte * 112),
                ('SegGs', wt.DWORD), ('SegFs', wt.DWORD), ('SegEs', wt.DWORD), ('SegDs', wt.DWORD),
                ('Edi', wt.DWORD), ('Esi', wt.DWORD), ('Ebx', wt.DWORD), ('Edx', wt.DWORD), ('Ecx', wt.DWORD), ('Eax', wt.DWORD),
                ('Ebp', wt.DWORD), ('Eip', wt.DWORD), ('SegCs', wt.DWORD), ('EFlags', wt.DWORD), ('Esp', wt.DWORD), ('SegSs', wt.DWORD),
                ('ExtendedRegisters', ctypes.c_byte * 512)]


class THREADENTRY32(ctypes.Structure):
    _fields_ = [('dwSize', wt.DWORD), ('cntUsage', wt.DWORD), ('th32ThreadID', wt.DWORD), ('th32OwnerProcessID', wt.DWORD),
                ('tpBasePri', wt.LONG), ('tpDeltaPri', wt.LONG), ('dwFlags', wt.DWORD)]


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [('dwSize', wt.DWORD), ('cntUsage', wt.DWORD), ('th32ProcessID', wt.DWORD), ('th32DefaultHeapID', ctypes.c_void_p),
                ('th32ModuleID', wt.DWORD), ('cntThreads', wt.DWORD), ('th32ParentProcessID', wt.DWORD), ('pcPriClassBase', wt.LONG),
                ('dwFlags', wt.DWORD), ('szExeFile', wt.WCHAR * 260)]


class MODINFO(ctypes.Structure):
    _fields_ = [('base', ctypes.c_void_p), ('size', wt.DWORD), ('entry', ctypes.c_void_p)]


WAIT_RET = {r + 5 for r in (0x8e16, 0x8e56, 0xf84b, 0xfcf2, 0xfdb3, 0xff71, 0x10097, 0x4a110, 0x4a3af, 0x4a404, 0x4d86a, 0x6c00a, 0x73326,
                             0x736ae, 0x738db, 0x73e60, 0x740a1, 0x740c1, 0x770a1, 0x79dab, 0x7a63e, 0x7b014, 0x7b170, 0x7b2d4, 0x7b3c4, 0x7b4c4,
                             0x7b5ba, 0x7ec3a, 0x7ec8e, 0x8078b, 0x90cf9)}   # call 0x484c00 자리 + 5
PERIOD_RET = {r + 5 for r in (0x4cd84, 0x721c4, 0x7227b, 0x7233a, 0x723b0)}   # call 0x490c80 자리 + 5


def find_pid():
    snap = k32.CreateToolhelp32Snapshot(0x2, 0)
    pe = PROCESSENTRY32W(); pe.dwSize = ctypes.sizeof(pe)
    ok = k32.Process32FirstW(snap, ctypes.byref(pe)); pid = None
    while ok:
        if pe.szExeFile.lower() == EXE.lower():
            pid = pe.th32ProcessID
        ok = k32.Process32NextW(snap, ctypes.byref(pe))
    k32.CloseHandle(snap); return pid


def threads_of(pid):
    snap = k32.CreateToolhelp32Snapshot(0x4, 0)
    te = THREADENTRY32(); te.dwSize = ctypes.sizeof(te); out = []
    ok = k32.Thread32First(snap, ctypes.byref(te))
    while ok:
        if te.th32OwnerProcessID == pid:
            out.append(te.th32ThreadID)
        ok = k32.Thread32Next(snap, ctypes.byref(te))
    k32.CloseHandle(snap); return out


def modules(hp):
    mods = (ctypes.c_void_p * 1024)(); need = wt.DWORD(); res = []
    psapi.EnumProcessModulesEx(hp, mods, ctypes.sizeof(mods), ctypes.byref(need), 0x03)
    for i in range(need.value // ctypes.sizeof(ctypes.c_void_p)):
        nm = ctypes.create_unicode_buffer(260)
        psapi.GetModuleBaseNameW(hp, ctypes.c_void_p(mods[i]), nm, 260)
        mi = MODINFO(); psapi.GetModuleInformation(hp, ctypes.c_void_p(mods[i]), ctypes.byref(mi), ctypes.sizeof(mi))
        res.append((mi.base or 0, (mi.base or 0) + mi.size, nm.value))
    return res


while not (pid := find_pid()):
    time.sleep(1)
print('pid', pid, flush=True)
time.sleep(3)
hp = k32.OpenProcess(0x0410 | 0x00100000, False, pid)
mods = modules(hp)
pm_csv = OUT / f'{name}_pm.csv'
pm_csv.unlink(missing_ok=True)
pm = subprocess.Popen([str(PM), '--process_name', EXE, '--output_file', str(pm_csv), '--terminate_on_proc_exit', '--no_console_stats',
                       '--stop_existing_session'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
(OUT / f'{name}_t0.txt').write_text(str(time.time()))
out = open(OUT / f'{name}_eip.tsv', 'w', encoding='utf-8')
handles, last_thr, last_mod = {}, 0, 0
# 코드(.text) 범위만: 스택의 자료 포인터를 돌아갈 주소로 잘못 세지 않게(EXE .text 0x1000~0x110d59, DLL .text 0x1000~0xe97c3)
exe_lo, exe_hi = next(((lo + 0x1000, lo + 0x110d59) for lo, hi, mn in mods if mn.lower() == EXE.lower()), (0, 0))
dll_lo, dll_hi = next(((lo + 0x1000, lo + 0xe97c3) for lo, hi, mn in mods if mn.lower() == 'n2hd_runtime.dll'), (0, 0))
ctx = WOW64_CONTEXT()
n = 0
while k32.WaitForSingleObject(hp, 0) == 0x102:   # 아직 살아 있음
    now = time.time()
    if now - last_thr > 2:
        for t in threads_of(pid):
            if t not in handles:
                handles[t] = k32.OpenThread(0x0002 | 0x0008 | 0x0040, False, t)
        last_thr = now
    if now - last_mod > 10:
        mods = modules(hp); last_mod = now
        # 모듈 목록이 늦게 차므로(DLL 은 시작 몇 초 뒤 올라옴) 코드 범위도 다시 잡는다
        exe_lo, exe_hi = next(((lo + 0x1000, lo + 0x110d59) for lo, hi, mn in mods if mn.lower() == EXE.lower()), (exe_lo, exe_hi))
        dll_lo, dll_hi = next(((lo + 0x1000, lo + 0xe97c3) for lo, hi, mn in mods if mn.lower() == 'n2hd_runtime.dll'), (dll_lo, dll_hi))
    for t, h in list(handles.items()):
        if not h or k32.Wow64SuspendThread(h) == 0xFFFFFFFF:
            continue
        ctx.ContextFlags = 0x10001
        got = k32.Wow64GetThreadContext(h, ctypes.byref(ctx))
        stack = b''; sp = ctx.Esp; fp = ctx.Ebp
        if got:   # 스택 16KB 를 읽어(스레드가 멈춘 동안) EBP 사슬을 따라 돌아갈 주소를 찾는다(스택에 남은 옛 값은 안 셈)
            buf = ctypes.create_string_buffer(16384); rd = ctypes.c_size_t()
            if k32.ReadProcessMemory(hp, ctypes.c_void_p(sp), buf, 16384, ctypes.byref(rd)):
                stack = buf.raw[:rd.value]
        k32.ResumeThread(h)
        if got:
            a = ctx.Eip; nm, off = '?', a
            for lo, hi, mn in mods:
                if lo <= a < hi:
                    nm, off = mn, a - lo; break
            callers = []
            for _ in range(24):
                i = fp - sp
                if i < 0 or i + 8 > len(stack):
                    break
                nfp = int.from_bytes(stack[i:i + 4], 'little'); ret = int.from_bytes(stack[i + 4:i + 8], 'little')
                if exe_lo <= ret < exe_hi:
                    callers.append(f'e{ret - exe_lo + 0x1000:x}')
                elif dll_lo <= ret < dll_hi:
                    callers.append(f'd{ret - dll_lo + 0x1000:x}')
                if len(callers) >= 4 or nfp <= fp:
                    break
                fp = nfp
            # EBP 를 안 쓰는 엔진 기다림 함수(0x484c00)와 프레임 주기 함수(0x490c80)에서는 사슬이 끊기므로, 스택 앞쪽에서 그 둘을 부른
            # 자리의 돌아갈 주소를 직접 찾는다(가장 가까운 것 = 지금 부른 자리)
            base = exe_lo - 0x1000; wsite = psite = ''
            for j in range(0, min(len(stack), 0x1000) - 3, 4):
                v = int.from_bytes(stack[j:j + 4], 'little') - base
                if not wsite and v in WAIT_RET:
                    wsite = f'w{v:x}'
                elif not psite and v in PERIOD_RET:
                    psite = f'p{v:x}'
                if wsite and psite:
                    break
            out.write(f'{now * 1000:.1f}\t{t}\t{nm}\t{off:x}\t{",".join(callers)}\t{wsite}\t{psite}\n'); n += 1
    time.sleep(every)
out.close()
try:
    pm.wait(timeout=90)
except subprocess.TimeoutExpired:
    pm.terminate()
print('done samples', n, flush=True)
