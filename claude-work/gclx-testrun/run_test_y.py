import sys as _s; _s.path.insert(0, r'F:\AI\gclx-4k\tools')
"""시험 사본(P:\\AI\\gclx-4k-test\\game)을 소리 끄고 화면 밖 창으로 띄워 4K 화면을 몇 초마다 저장한다(사용자 허락 10-26).
- 시험용 실행기 Korean4K_test.exe(창을 활성화하지 않음)를 WMI 로 띄운 cmd 가 환경 변수와 함께 실행 — Claude 앱 밖.
- 저장 위치는 DLL 시험 스위치(N2HD_PROFILE_DIR)로 이 시험 폴더에만. 4K 화면은 DLL 이 N2HD_TEST_SHOT_MS 마다 BMP 로.
- 창은 뜨자마자 모든 모니터 바깥(주 모니터 오른쪽)·맨 뒤·작업 표시줄에서 빼고, 소리 세션은 음소거.
- 시험 대본(타이틀 없이 바로 시작·자동 진행)은 시작 때 nss.npa 자리에 넣고 끝나면 원래 대본으로 되돌린다. 사본은
  게임 폴더 밖 NSS_DIR 에만: 엔진은 폴더의 .npa 를 이름과 상관없이 전부 읽어, 10-27 nss.normal.npa 가 시험 대본을
  덮고 첫 실행 질문 창이 사용자 화면에 떴다.
- 그래서 게임의 다른 창(질문 창 등)도 0.02초마다 찾아 화면 밖으로 옮기고 「아니요」로 닫는다.
  python -X utf8 run_test.py <이름> [--art-off] [--seconds 150] [--shot-ms 3000]
"""
import argparse, ctypes, ctypes.wintypes as wt, hashlib, json, os, shutil, subprocess, sys, threading, time
from pathlib import Path

sys.path.insert(0, r'P:\AI\touka-ps2-kr\work\codex_watch\host')
import hostlib as H  # noqa: E402

GAME = Path(os.environ.get('GCLX_GAME', r'P:\AI\gclx-4k-test\game'))          # 코덱스 후보 사본: P:\AI\gclx-codexrun\game
RUNS = Path(r'Y:\AI\claude-work\gclx-testrun')   # 11-24 F: 가득 참 → Y: 로 쓰는 사본
NSS_DIR = Path(os.environ.get('GCLX_NSS_DIR', r'F:\AI\gclx-4k\nss_variants'))  # 그때는 F:\AI\gclx-4k\nss_variants_codex
ARCHIVES = {'cg.npa', 'cg1.npa', 'nss.npa', 'sound.npa', 'system.npa', 'voice.npa'}
# 11-23 덮어쓰기 배포 시험: 한국어 그림 묶음(예 cg.kor.npa)처럼 일부러 둔 .npa 는 GCLX_EXTRA_NPA=이름,이름 으로 허용
ARCHIVES |= {n.strip().lower() for n in os.environ.get('GCLX_EXTRA_NPA', '').split(',') if n.strip()}
EXE = 'GUILTY CROWN LOST XMAS.exe'
U = H.U


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


MonitorFromRect = ctypes.windll.user32.MonitorFromRect
MonitorFromRect.restype = ctypes.c_void_p


def guard_dialogs(stop, main_hwnd, log):
    """게임 프로세스의 다른 보이는 창(질문 창 등)을 곧바로 화면 밖으로 옮기고 「아니요」(IDNO)로 닫는다."""
    w = U.GetSystemMetrics(0)
    while not stop.is_set():
        pids = set(H.pids_of(GAME, EXE))
        if pids:
            def cb(h, _):
                p = wt.DWORD()
                U.GetWindowThreadProcessId(h, ctypes.byref(p))
                if p.value in pids and h != main_hwnd[0] and U.IsWindowVisible(h):
                    c = ctypes.create_unicode_buffer(64); t = ctypes.create_unicode_buffer(256)
                    U.GetClassNameW(h, c, 64); U.GetWindowTextW(h, t, 256)
                    if c.value == '#32770':
                        U.SetWindowPos(h, 1, w + 60, 200, 0, 0, 0x0001 | 0x0010)
                        # 11-24: 질문·오류 창의 본문(Static)도 적는다(부팅 멈춤 진단)
                        body = []
                        def ccb(ch, _):
                            cc = ctypes.create_unicode_buffer(64); ct = ctypes.create_unicode_buffer(1024)
                            U.GetClassNameW(ch, cc, 64); U.GetWindowTextW(ch, ct, 1024)
                            if ct.value: body.append(f'{cc.value}:{ct.value}')
                            return True
                        U.EnumChildWindows(h, H.EnumProc(ccb), 0)
                        U.PostMessageW(h, 0x0111, 7, 0)       # WM_COMMAND IDNO
                        log.append([time.strftime('%H:%M:%S'), t.value, ' | '.join(body)])
                return True
            U.EnumWindows(H.EnumProc(cb), 0)
        # 11-23: 시험 창이 어느 모니터에라도 걸치면 곧바로 밖으로 되돌린다. 화면 밖 창이 다시 보일 때 윈도가 창의 1/3 을
        # 화면 안으로 끌어온다(창 크기 자유 조절 시험에서 큰 창이 주 모니터 오른쪽 아래에 걸쳤다).
        if main_hwnd[0] and not os.environ.get('RUN_TEST_WINDOW'):
            r = wt.RECT()
            if U.GetWindowRect(main_hwnd[0], ctypes.byref(r)) and MonitorFromRect(ctypes.byref(r), 0):
                U.SetWindowPos(main_hwnd[0], 1, w + 40, 120, 0, 0, 0x0001 | 0x0010)
                log.append([time.strftime('%H:%M:%S'), f'main window was on screen at {r.left},{r.top} -> moved off'])
        time.sleep(0.02)


def offscreen(hwnd):
    ctypes.windll.user32.SetProcessDPIAware()
    w = U.GetSystemMetrics(0)
    ex = U.GetWindowLongW(hwnd, -20)
    if not ex & 0x80:                                   # WS_EX_TOOLWINDOW: out of the taskbar and Alt+Tab
        U.ShowWindow(hwnd, 0)
        U.SetWindowLongW(hwnd, -20, (ex | 0x80) & ~0x40000)
        U.ShowWindow(hwnd, 4)                           # SW_SHOWNOACTIVATE
    big = os.environ.get('RUN_TEST_WINDOW')   # 예 4096x2160: 사용자 TV 전체 화면과 같은 크기의 창을 모든 모니터 밖에 둔다(속도 재현용)
    if big:
        bw, bh = map(int, big.lower().split('x'))
        U.SetWindowPos(hwnd, 1, -bw - 30000, -bh - 30000, bw, bh, 0x0010)   # HWND_BOTTOM, SWP_NOACTIVATE
    else:
        U.SetWindowPos(hwnd, 1, w + 40, 120, 0, 0, 0x0001 | 0x0010)   # HWND_BOTTOM, SWP_NOSIZE|SWP_NOACTIVATE
    r = wt.RECT()
    U.GetWindowRect(hwnd, ctypes.byref(r))
    return [r.left, r.top, r.right, r.bottom], w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('name')
    ap.add_argument('--art-off', action='store_true')
    ap.add_argument('--seconds', type=int, default=150)
    ap.add_argument('--shot-ms', type=int, default=3000)
    ap.add_argument('--keys', action='store_true', help='Enter 를 1.5초마다 보냄')
    ap.add_argument('--profile', action='store_true', help='엔진 주 스레드 표본 측정(profile.log)')
    ap.add_argument('--native', action='store_true', help='4K 없이 원래 1024x576 렌더러(프레임 간격만 native.log)')
    ap.add_argument('--no-jump', action='store_true', help='대사 기록 점프 지점 저장 끄기(비교용)')
    ap.add_argument('--wheel-at', type=int, default=0, help='이 초부터 휠 올리기(대사 기록 열기)를 0.7초마다 10번')
    ap.add_argument('--wheel-down-at', type=int, default=0, help='이 초부터 휠 내리기(대사 기록 닫기)를 0.7초마다 10번')
    ap.add_argument('--rclick-at', action='append', default=[], help='초 — 그 초에 오른쪽 클릭 한 번(11-24)')
    ap.add_argument('--wheel1', action='append', default=[], help='초:up|down — 그 초에 휠 한 칸(11-24 회상 쪽 넘기기)')
    ap.add_argument('--click-at', type=int, default=0, help='이 초에 왼쪽 단추 누르기(대사 기록 점프 시험; DLL 이 N2HD_TEST_JUMP_BACK 지점으로)')
    ap.add_argument('--jump-back', type=int, default=0, help='N2HD_TEST_JUMP_BACK')
    ap.add_argument('--nss', default='nss.test.npa', help='nss_variants 안 시험 대본 이름')
    ap.add_argument('--env', action='append', default=[], help='추가 환경 변수 NAME=VALUE (시험 스위치)')
    ap.add_argument('--keys-until', type=int, default=0, help='이 초 뒤로는 Enter 를 안 보냄')
    ap.add_argument('--keys-from', type=int, default=0, help='이 초부터 Enter 를 보냄(그 전 화면에서 Enter 가 단추를 누르지 않게)')
    ap.add_argument('--seed-common', default='', help='이 폴더의 파일(사용자 val.npf·cqst.npf 사본 등)을 시험 프로필 common 에 미리 넣음 — 사용자 설정으로 시험')
    ap.add_argument('--keep-throttle', action='store_true', help='DLL 의 윈도 절전 제한 끄기를 하지 않음(비교용)')
    ap.add_argument('--key-at', action='append', default=[], help='초:가상키 — 그 초에 키 한 번(예 45:0x53 = S, 세이브 메뉴)')
    ap.add_argument('--hover-xy', action='append', default=[], help='초:x:y — 그 초에 엔진 좌표로 커서만 올림(누르지 않음)')
    ap.add_argument('--click-xy', action='append', default=[], help='초:x:y — 그 초에 엔진 좌표(1024x576)로 올린 뒤 왼쪽 클릭(타이틀 단추 등)')
    ap.add_argument('--stop-trace', default='', help='11-21 완주 시험: 시험 폴더 trace.log 에 이 글이 나오면 30초 뒤 끝냄')
    ap.add_argument('--stall-min', type=float, default=0, help='trace.log 가 이 분 동안 안 늘면 멈춤으로 적고 끝냄')
    ap.add_argument('--wheel-at2', type=int, default=0, help='두 번째 휠 올리기(다시 열기) 시각')
    ap.add_argument('--stop-delay', type=float, default=30, help='--stop-trace 를 본 뒤 이 초 뒤 끝냄')
    ap.add_argument('--key-every', type=float, default=0, help='Enter 를 이 초마다(완주 시험: 숨긴 창에서는 엔진이 건너뛰기를 끔)')
    a = ap.parse_args()
    run = RUNS / a.name
    prof = run / 'profile'
    prof.mkdir(parents=True, exist_ok=False)
    if a.seed_common:
        com = prof / 'Nitroplus' / 'GUILTY CROWN LOST XMAS' / '1.00' / 'common'
        com.mkdir(parents=True)
        for f in Path(a.seed_common).iterdir():
            shutil.copyfile(f, com / f.name)
    if H.pids_of(GAME, EXE):
        raise SystemExit('시험 사본이 이미 돌고 있음')
    extra = sorted(p.name for p in GAME.glob('*.npa') if p.name.lower() not in ARCHIVES)
    if extra:
        raise SystemExit(f'게임 폴더에 엔진이 읽을 다른 .npa 가 있음: {extra}')
    if sha(GAME / 'nss.npa') != sha(NSS_DIR / 'nss.normal.npa'):
        raise SystemExit('게임 폴더 nss.npa 가 원래 대본(nss_variants\\nss.normal.npa)과 다름 — 먼저 확인할 것')
    shutil.copyfile(NSS_DIR / a.nss, GAME / 'nss.npa')
    try:
        run_game(a, run, prof)
    finally:
        shutil.copyfile(NSS_DIR / 'nss.normal.npa', GAME / 'nss.npa')


def run_game(a, run, prof):
    (GAME / 'launcher-test.log').unlink(missing_ok=True)
    cmd = run / 'run.cmd'
    lines = ['@echo off', f'set N2HD_PROFILE_DIR={prof}', 'set N2HD_ART_LOG=1', f'set N2HD_TEST_SHOT_MS={a.shot_ms}']
    if a.art_off:
        lines.append('set N2HD_ART_OFF=1')
    if a.profile:
        lines.append('set N2HD_TEST_PROFILE=1')
    if a.native:
        lines.append('set N2HD_TEST_NATIVE=1')
    if a.no_jump:
        lines.append('set N2HD_TEST_NO_JUMP=1')
    if a.jump_back:
        lines.append(f'set N2HD_TEST_JUMP_BACK={a.jump_back}')
    for kv in a.env:
        lines.append(f'set {kv}')
    if a.keep_throttle:
        lines.append('set N2HD_TEST_KEEP_THROTTLE=1')
    lines.append(f'"{GAME / "Korean4K_test.exe"}"')
    cmd.write_text('\r\n'.join(lines) + '\r\n', 'cp949')
    prev_fg = U.GetForegroundWindow()
    ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments "
          "@{CommandLine='cmd /c \"%s\"'; CurrentDirectory='%s'; ProcessStartupInformation=(New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ShowWindow=[uint16]0})}; $r.ReturnValue" % (cmd, GAME))
    rc = subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, text=True).stdout.strip()
    rep = {'run': str(run), 'art_off': a.art_off, 'wmi_rc': rc, 'started': time.strftime('%H:%M:%S'), 'events': []}
    t0 = time.time()
    rep['t0_epoch'] = t0
    pid = hwnd = None
    muted = set()
    stop, main_hwnd, dialogs = threading.Event(), [None], []
    threading.Thread(target=guard_dialogs, args=(stop, main_hwnd, dialogs), daemon=True).start()
    try:
        run_body(a, run, prof, rep, t0, prev_fg, muted, main_hwnd)
    finally:
        stop.set()
        rep['dialogs_closed'] = dialogs
        (run / 'report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), 'utf-8')


def run_body(a, run, prof, rep, t0, prev_fg, muted, main_hwnd):
    pid = hwnd = None
    while time.time() - t0 < 40 and not hwnd:
        pids = H.pids_of(GAME, EXE)
        if pids:
            pid = pids[0]
            hwnd = H.window_of(pid)
        time.sleep(0.02)
    main_hwnd[0] = hwnd
    if not hwnd:
        rep['error'] = '창이 안 뜸'
        (run / 'report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), 'utf-8')
        for p in H.pids_of(GAME, EXE):
            subprocess.run(['taskkill', '/PID', str(p), '/F'], capture_output=True)
        raise SystemExit(json.dumps(rep, ensure_ascii=False))
    rep['window_rect'], rep['primary_width'] = offscreen(hwnd)
    rep['focus_returned'] = H.give_focus_back(hwnd, prev_fg)
    rep['window_seconds'] = round(time.time() - t0, 2)
    last_act = 0
    while time.time() - t0 < a.seconds:
        if time.time() - last_act > 1.5:              # the engine may pause while it thinks it is inactive
            H.activate(hwnd)
            if a.keys and time.time() - t0 > max(6, a.keys_from) and not (a.keys_until and time.time() - t0 > a.keys_until):
                H.key(hwnd, 0x0D)                      # Enter: past a "press any key" or a waiting line
            last_act = time.time()
        pk = 0.0
        for vol, meter in H.sessions_of(pid):
            if not H.get_mute(vol):
                H.set_mute(vol, True)
                muted.add(time.strftime('%H:%M:%S'))
            pk = max(pk, H.peak(meter))                # 음소거해도 값이 나온다: 소리가 실제로 나는지(사운드 모드 시험)
        sec_ = int(time.time() - t0)
        au = rep.setdefault('audio_peak', {})
        au[str(sec_)] = round(max(au.get(str(sec_), 0.0), pk), 3)
        for i, ka in enumerate(a.key_at):
            sec, vk = ka.split(':')
            if float(sec) <= time.time() - t0 and i not in rep.setdefault('_keys_sent', []):
                H.key(hwnd, int(vk, 0)); rep['_keys_sent'].append(i); rep.setdefault('keys_at', []).append([ka, round(time.time() - t0, 1)])
        for i, cx in enumerate(a.click_xy):
            sec, x, y = cx.split(':')
            if float(sec) <= time.time() - t0 and i not in rep.setdefault('_clicks_sent', []):
                rep['_clicks_sent'].append(i)
                if any(kv.startswith('N2HD_TEST_CURSOR_FILE') for kv in a.env):   # the DLL's test cursor (engine coordinates)
                    (prof / 'cursor.txt').write_text(f'{x},{y}')
                for _ in range(3):                                   # hover first (the engine highlights, then takes the click)
                    U.PostMessageW(hwnd, 0x200, 0, (int(y) << 16) | int(x)); time.sleep(0.1)
                H.click(hwnd, int(x), int(y)); rep.setdefault('clicks_xy', []).append([cx, round(time.time() - t0, 1)])
        for i, hx in enumerate(a.hover_xy):                         # 11-23: 누르지 않고 커서만 올림(대사 기록 밑줄 찍기 등)
            sec, x, y = hx.split(':')
            if float(sec) <= time.time() - t0 and i not in rep.setdefault('_hovers_sent', []):
                rep['_hovers_sent'].append(i)
                if any(kv.startswith('N2HD_TEST_CURSOR_FILE') for kv in a.env):
                    (prof / 'cursor.txt').write_text(f'{x},{y}')
                for _ in range(3):
                    U.PostMessageW(hwnd, 0x200, 0, (int(y) << 16) | int(x)); time.sleep(0.1)
                rep.setdefault('hovers_xy', []).append([hx, round(time.time() - t0, 1)])
        for i, rx in enumerate(a.rclick_at):                       # 11-24: 오른쪽 클릭(사운드 화면 「재생 중이면 멈춤」 시험)
            if float(rx) <= time.time() - t0 and i not in rep.setdefault('_rclicks_sent', []):
                rep['_rclicks_sent'].append(i)
                U.PostMessageW(hwnd, 0x0204, 2, (300 << 16) | 500); time.sleep(0.2); U.PostMessageW(hwnd, 0x0205, 0, (300 << 16) | 500)
                rep.setdefault('rclicks', []).append([rx, round(time.time() - t0, 1)])
        if a.click_at and a.click_at <= time.time() - t0 < a.click_at + 3 and not rep.get('clicked'):
            U.PostMessageW(hwnd, 0x0201, 1, (200 << 16) | 300); time.sleep(0.25); U.PostMessageW(hwnd, 0x0202, 0, (200 << 16) | 300)
            rep['clicked'] = round(time.time() - t0, 1); rep['events'].append(['click', time.time()])
        for i, wa in enumerate(a.wheel1):                        # 11-24: one wheel notch at a given second (sec:up|down)
            sec, dirn = wa.split(':')
            if float(sec) <= time.time() - t0 and i not in rep.setdefault('_w1_sent', []):
                rep['_w1_sent'].append(i); r_ = wt.RECT(); U.GetWindowRect(hwnd, ctypes.byref(r_))
                U.PostMessageW(hwnd, 0x020A, ((120 if dirn == 'up' else -120) & 0xffff) << 16, ((r_.top + 200) << 16) | ((r_.left + 300) & 0xffff))
                rep.setdefault('wheel1_at', []).append([wa, round(time.time() - t0, 1)])
        if a.wheel_down_at and a.wheel_down_at <= time.time() - t0 < a.wheel_down_at + 7 and time.time() - rep.get('_ld', 0) > 0.7:
            r_ = wt.RECT(); U.GetWindowRect(hwnd, ctypes.byref(r_))
            U.PostMessageW(hwnd, 0x020A, ((-120) & 0xffff) << 16, ((r_.top + 200) << 16) | ((r_.left + 300) & 0xffff))
            rep['_ld'] = time.time(); rep['wheels_down'] = rep.get('wheels_down', 0) + 1; rep['events'].append(['wheel_down', time.time()])
        if ((a.wheel_at and a.wheel_at <= time.time() - t0 < a.wheel_at + 7) or (a.wheel_at2 and a.wheel_at2 <= time.time() - t0 < a.wheel_at2 + 2)) and time.time() - rep.get('_lw', 0) > 0.7:
            r_ = wt.RECT(); U.GetWindowRect(hwnd, ctypes.byref(r_))
            U.PostMessageW(hwnd, 0x020A, 120 << 16, ((r_.top + 200) << 16) | ((r_.left + 300) & 0xffff))
            rep['_lw'] = time.time(); rep['wheels'] = rep.get('wheels', 0) + 1; rep['events'].append(['wheel_up', time.time()])
        if U.GetForegroundWindow() == hwnd:
            H.give_focus_back(hwnd, prev_fg)
        if not H.pids_of(GAME, EXE):
            rep['exited_early'] = round(time.time() - t0, 1)
            break
        if a.key_every and time.time() - t0 > max(6, a.keys_from) and time.time() - rep.get('_lk', 0) > a.key_every and not rep.get('stop_seen') and not (a.keys_until and time.time() - t0 > a.keys_until):
            H.key(hwnd, 0x0D); rep['_lk'] = time.time(); rep['keys_sent'] = rep.get('keys_sent', 0) + 1
        tr = prof / 'trace.log'
        if a.stop_trace or a.stall_min:
            if tr.exists():
                st = tr.stat()
                if st.st_size != rep.get('_trace_size'):
                    rep['_trace_size'] = st.st_size; rep['_trace_t'] = time.time()
                if a.stop_trace and not rep.get('stop_seen') and a.stop_trace in tr.read_text(errors='replace'):
                    rep['stop_seen'] = round(time.time() - t0, 1)
                if rep.get('stop_seen') and time.time() - t0 > rep['stop_seen'] + a.stop_delay:
                    break
            if a.stall_min and time.time() - rep.get('_trace_t', t0) > a.stall_min * 60:
                rep['stalled_at'] = round(time.time() - t0, 1)
                break
        time.sleep(0.25)
    rep['muted_at'] = sorted(muted)
    seen = []                                          # every window of the game (dialogs included), for stalls

    def cb(h, _):
        p = wt.DWORD()
        U.GetWindowThreadProcessId(h, ctypes.byref(p))
        if p.value == pid:
            c = ctypes.create_unicode_buffer(256); t = ctypes.create_unicode_buffer(256)
            U.GetClassNameW(h, c, 256); U.GetWindowTextW(h, t, 256)
            seen.append([c.value, t.value, bool(U.IsWindowVisible(h))])
        return True
    U.EnumWindows(H.EnumProc(cb), 0)
    rep['windows_at_end'] = seen
    alive = H.pids_of(GAME, EXE)
    if alive:
        U.PostMessageW(hwnd, 0x0010, 0, 0)            # WM_CLOSE
        time.sleep(4)
        alive = H.pids_of(GAME, EXE)
        rep['closed_by'] = 'WM_CLOSE' if not alive else 'terminate'
        for p in alive:
            subprocess.run(['taskkill', '/PID', str(p), '/F'], capture_output=True)
    rep['shots'] = len(list(prof.glob('shot-*.bmp')))
    rep['launcher_log'] = (GAME / 'launcher-test.log').read_text(errors='replace') if (GAME / 'launcher-test.log').exists() else None
    fl = prof / 'fonts.log'
    rep['fonts_log'] = fl.read_text(errors='replace') if fl.exists() else None
    (run / 'report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), 'utf-8')
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
