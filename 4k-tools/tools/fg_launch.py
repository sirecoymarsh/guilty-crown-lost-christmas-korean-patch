"""앞 창 시험용 실행(사용자가 조작을 맡겼을 때만): 4K 실행기를 환경 변수와 함께 WMI 로 띄운다. 세이브는 사용자 평소 자리.
python -X utf8 fg_launch.py [NAME=VALUE ...]"""
import subprocess, sys
from pathlib import Path

GAME = Path(r'P:\AI\gclx-codexrun\game')
cmd = Path(r'F:\AI\gclx-4k\testrun\fg\launch.cmd')
lines = ['@echo off'] + [f'set {kv}' for kv in sys.argv[1:]] + [f'"{GAME / "Korean4K.exe"}"']
cmd.write_text('\r\n'.join(lines) + '\r\n', 'cp949')
ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments "
      "@{CommandLine='cmd /c \"%s\"'; CurrentDirectory='%s'; ProcessStartupInformation=(New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ShowWindow=[uint16]0})}; $r.ReturnValue" % (cmd, GAME))
print('WMI', subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, text=True).stdout.strip())
