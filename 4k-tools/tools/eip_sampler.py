"""켜져 있는 게임(32비트)의 주 스레드를 잠깐씩 멈춰 명령 주소를 모아, 어느 모듈·함수 근처에서 시간을 쓰는지 본다(읽기만).
python -X utf8 eip_sampler.py <초> [<간격ms>=5] [--all-threads]
결과: 모듈별 비율, 게임 EXE·n2hd_runtime 안의 주소 상위(4KB 묶음). 대기 중(커널 안)인 표본은 그 스레드의 마지막 사용자 주소로 잡힌다."""
import collections, ctypes, ctypes.wintypes as wt, sys, time

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
psapi = ctypes.WinDLL('psapi', use_last_error=True)
EXE = 'GUILTY CROWN LOST XMAS.exe'
secs = float(sys.argv[1]) if len(sys.argv) > 1 else 10
every = float(sys.argv[2]) / 1000 if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else 0.005
ALL = '--all-threads' in sys.argv


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


snap = k32.CreateToolhelp32Snapshot(0x2 | 0x4, 0)
pe = PROCESSENTRY32W(); pe.dwSize = ctypes.sizeof(pe)
pid = None
ok = k32.Process32FirstW(snap, ctypes.byref(pe))
while ok:
    if pe.szExeFile.lower() == EXE.lower():
        pid = pe.th32ProcessID
    ok = k32.Process32NextW(snap, ctypes.byref(pe))
if not pid:
    raise SystemExit('게임이 안 떠 있음')
threads = []
te = THREADENTRY32(); te.dwSize = ctypes.sizeof(te)
ok = k32.Thread32First(snap, ctypes.byref(te))
while ok:
    if te.th32OwnerProcessID == pid:
        threads.append(te.th32ThreadID)
    ok = k32.Thread32Next(snap, ctypes.byref(te))
hp = k32.OpenProcess(0x0410, False, pid)
# 모듈 목록(32비트 모듈 포함)
mods = (ctypes.c_void_p * 1024)(); need = wt.DWORD()
psapi.EnumProcessModulesEx(hp, mods, ctypes.sizeof(mods), ctypes.byref(need), 0x03)
modlist = []


class MODINFO(ctypes.Structure):
    _fields_ = [('base', ctypes.c_void_p), ('size', wt.DWORD), ('entry', ctypes.c_void_p)]


for i in range(need.value // ctypes.sizeof(ctypes.c_void_p)):
    nm = ctypes.create_unicode_buffer(260)
    psapi.GetModuleBaseNameW(hp, ctypes.c_void_p(mods[i]), nm, 260)
    mi = MODINFO(); psapi.GetModuleInformation(hp, ctypes.c_void_p(mods[i]), ctypes.byref(mi), ctypes.sizeof(mi))
    modlist.append((mi.base or 0, (mi.base or 0) + mi.size, nm.value))


def mod_of(a):
    for lo, hi, nm in modlist:
        if lo <= a < hi:
            return nm, a - lo
    return '?', a


# 주 스레드 = 가장 먼저 생긴 스레드(목록 첫째)로 본다. --all-threads 면 모두
targets = threads if ALL else threads[:1]
hts = {t: k32.OpenThread(0x0002 | 0x0008 | 0x0040, False, t) for t in targets}   # SUSPEND_RESUME|GET_CONTEXT|QUERY_INFORMATION
by_mod, by_addr = collections.Counter(), collections.Counter()
n = 0
t_end = time.time() + secs
ctx = WOW64_CONTEXT();
while time.time() < t_end:
    for t, h in hts.items():
        if k32.Wow64SuspendThread(h) == 0xFFFFFFFF:
            continue
        ctx.ContextFlags = 0x10001   # WOW64_CONTEXT_CONTROL
        if k32.Wow64GetThreadContext(h, ctypes.byref(ctx)):
            nm, off = mod_of(ctx.Eip)
            by_mod[nm] += 1
            by_addr[(nm, ctx.Eip & ~0xfff if nm == '?' else off & ~0xfff)] += 1
            n += 1
        k32.ResumeThread(h)
    time.sleep(every)
print(f'pid {pid}, threads {len(threads)}, sampled {len(targets)}, samples {n}')
for nm, c in by_mod.most_common(15):
    print(f'  {100 * c / n:5.1f}%  {nm}')
print('주소 상위(모듈+오프셋 4KB 묶음):')
for (nm, off), c in by_addr.most_common(20):
    print(f'  {100 * c / n:5.1f}%  {nm}+0x{off:x}')
