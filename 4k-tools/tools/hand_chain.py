"""앞 손 모양 지도 시험이 끝나길 기다렸다가, 새 DLL 을 넣고 숨긴 창으로 원래 1배 → 4K(고침) 손 모양 지도를 차례로 잰다.
python -X utf8 hand_chain.py <새 DLL> <이름 앞머리>"""
import shutil, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, r'P:\AI\touka-ps2-kr\work\codex_watch\host')
import hostlib as H  # noqa: E402

GAME = Path(r'P:\AI\gclx-codexrun\game'); EXE = 'GUILTY CROWN LOST XMAS.exe'
dll, pre = Path(sys.argv[1]), sys.argv[2]
while H.pids_of(GAME, EXE):
    time.sleep(2)
time.sleep(3)
shutil.copyfile(dll, GAME / 'n2hd_runtime.dll')
tools = Path(r'F:\AI\gclx-4k\tools')
env = dict(__import__('os').environ, GCLX_GAME=str(GAME), GCLX_NSS_DIR=r'F:\AI\gclx-4k\nss_variants_codex')
for name, extra in ((f'{pre}_native', ['--native']), (f'{pre}_4kfix', [])):
    rt = subprocess.Popen([sys.executable, '-X', 'utf8', str(tools / 'run_test.py'), name, '--nss', 'nss.normal.npa', '--seconds', '330',
                           '--shot-ms', '30000', '--env', 'N2HD_TEST_CURSOR_FILE=1', *extra], env=env, cwd=str(tools),
                          stdout=open(rf'F:\AI\gclx-4k\testrun\{name}.out', 'w'), stderr=subprocess.STDOUT)
    time.sleep(2)
    out = subprocess.run([sys.executable, '-X', 'utf8', str(tools / 'hand_probe.py'), name, '50'], capture_output=True, text=True, encoding='utf-8')
    print('=====', name); print(out.stdout[-3500:], out.stderr[-800:], flush=True)
    rt.wait(); time.sleep(3)
