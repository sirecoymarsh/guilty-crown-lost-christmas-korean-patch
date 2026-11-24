"""설치·제거 배치 파일을 cp949·CRLF 로 쓴다(한국어 윈도 cmd 의 기본 코드 페이지; UTF-8+chcp 는 블록 안 한글에서 줄이 갈렸다).
배치 안의 경로·이름은 모두 ASCII(KoreanPatch\\...)라 코드 페이지가 달라도 동작은 같고, 한글은 안내 문구에만 있다.
시스템 도구는 %SystemRoot%\\System32 에서 부른다(PATH 에 다른 find 가 있어도 되게).
python -I -X utf8 write_bats.py  -> Y:\\AI\\gclx-release-1121\\work\\text\\*.bat
"""
from pathlib import Path
T = Path(r'Y:\AI\gclx-release-1121\work\text')

INSTALL = r'''@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "P=%~dp0KoreanPatch"
set "XD=%P%\tools\xdelta3.exe"
set "BK=%P%\backup"
set "S32=%SystemRoot%\System32"
set "EXE=GUILTY CROWN LOST XMAS.exe"
set "FAILED="
echo ============================================================
echo  길티 크라운 로스트 크리스마스 한국어 패치 1.0 설치
echo ============================================================
echo.
if not exist "%EXE%" goto :notgame
if not exist "cg.npa" goto :notgame
if not exist "%XD%" goto :nopatch
"%S32%\tasklist.exe" /fi "imagename eq %EXE%" 2>nul | "%S32%\find.exe" /i "GUILTY CROWN" >nul
if not errorlevel 1 goto :running
if exist "%BK%\installed.txt" goto :already

for %%A in ("%EXE%") do set "S1=%%~zA"
for %%A in ("cg.npa") do set "S2=%%~zA"
if not "%S1%"=="1381888" echo [주의] 실행 파일 크기가 예상과 다릅니다: %S1% 바이트. 다른 판본일 수 있지만 그대로 시도합니다.
if not "%S2%"=="1929032617" echo [주의] cg.npa 크기가 예상과 다릅니다: %S2% 바이트. 다른 판본일 수 있지만 그대로 시도합니다.

if not exist "%BK%\dx" mkdir "%BK%\dx"
copy /y "%EXE%" "%BK%\%EXE%" >nul
for %%F in (nss.npa system.npa) do if exist "%%F" copy /y "%%F" "%BK%\%%F" >nul
for %%F in (mv_op.ngs GC_eyecatch_E.ngs mv_lx0201.ngs) do if exist "dx\%%F" copy /y "dx\%%F" "%BK%\dx\%%F" >nul

echo [1/3] 실행 파일을 바꾸는 중...
"%XD%" -d -f -s "%EXE%" "%P%\delta\exe.vcdiff" "%EXE%.kr_tmp"
if errorlevel 1 goto :exefail
move /y "%EXE%.kr_tmp" "%EXE%" >nul
goto :cg
:exefail
if exist "%EXE%.kr_tmp" del "%EXE%.kr_tmp"
set "FAILED=%FAILED% 실행파일"

:cg
echo [2/3] 그림 묶음 cg.npa 를 바꾸는 중... 몇 분 걸리고 빈 공간이 2GB 이상 필요합니다.
"%XD%" -d -f -s "cg.npa" "%P%\delta\cg.npa.vcdiff" "cg.npa.kr_tmp"
if errorlevel 1 goto :cgfail
del "cg.npa"
ren "cg.npa.kr_tmp" "cg.npa"
goto :files
:cgfail
if exist "cg.npa.kr_tmp" del "cg.npa.kr_tmp"
set "FAILED=%FAILED% cg.npa"

:files
echo [3/3] 한국어 파일을 넣는 중...
"%S32%\robocopy.exe" "%P%\files" "." /E /NJH /NJS /NFL /NDL /NP >nul
if errorlevel 8 set "FAILED=%FAILED% 한국어파일"

echo installed %DATE% %TIME%> "%BK%\installed.txt"
echo.
if defined FAILED goto :partial
echo 설치를 마쳤습니다.
goto :done
:partial
echo [알림] 다음은 적용하지 못했습니다:%FAILED%
echo        원본 파일이 이 패치가 기대하는 영문판과 다를 수 있습니다. 나머지는 설치되었습니다.
:done
echo 평소처럼 GUILTY CROWN LOST XMAS.exe 로 실행하면 됩니다.
echo 고화질 묶음은 이 폴더에 압축을 풀면 됩니다. 되돌리려면 한국어패치_제거.bat 을 실행하세요.
pause
exit /b 0

:notgame
echo [오류] 게임 폴더, 곧 GUILTY CROWN LOST XMAS.exe 와 cg.npa 가 있는 폴더에 압축을 풀어서 실행해야 합니다.
echo        지금 위치: %CD%
pause
exit /b 1
:nopatch
echo [오류] KoreanPatch 폴더가 없습니다. 압축을 통째로 게임 폴더에 풀어 주세요.
pause
exit /b 1
:running
echo [오류] 게임이 켜져 있습니다. 게임을 끄고 다시 실행해 주세요.
pause
exit /b 1
:already
echo 이미 설치되어 있습니다. 다시 설치하려면 먼저 한국어패치_제거.bat 을 실행해 주세요.
pause
exit /b 0
'''

UNINSTALL = r'''@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "P=%~dp0KoreanPatch"
set "XD=%P%\tools\xdelta3.exe"
set "BK=%P%\backup"
set "S32=%SystemRoot%\System32"
set "EXE=GUILTY CROWN LOST XMAS.exe"
set "FAILED="
echo ============================================================
echo  길티 크라운 로스트 크리스마스 한국어 패치 제거
echo ============================================================
echo.
if not exist "%BK%\installed.txt" goto :notinstalled
"%S32%\tasklist.exe" /fi "imagename eq %EXE%" 2>nul | "%S32%\find.exe" /i "GUILTY CROWN" >nul
if not errorlevel 1 goto :running
"%S32%\choice.exe" /c YN /m "한국어 패치와 고화질 묶음을 지우고 원래 게임으로 되돌릴까요"
if errorlevel 2 exit /b 0

echo [1/3] 그림 묶음 cg.npa 를 원래대로 되돌리는 중... 몇 분 걸립니다.
"%XD%" -d -f -s "cg.npa" "%P%\delta\cg.npa.restore.vcdiff" "cg.npa.orig_tmp"
if errorlevel 1 goto :cgfail
del "cg.npa"
ren "cg.npa.orig_tmp" "cg.npa"
goto :restore
:cgfail
if exist "cg.npa.orig_tmp" del "cg.npa.orig_tmp"
set "FAILED=%FAILED% cg.npa"

:restore
echo [2/3] 보관해 둔 원본 파일을 되돌리는 중...
"%S32%\robocopy.exe" "%BK%" "." /E /NJH /NJS /NFL /NDL /NP /XF installed.txt >nul
if errorlevel 8 set "FAILED=%FAILED% 원본파일"

echo [3/3] 패치가 더한 파일을 지우는 중...
for %%F in (version.dll n2hd_runtime.dll Korean4K.exe n2hd-options.ini) do if exist "%%F" del /q "%%F"
for %%F in (NotoSansKR-VF.ttf NotoSerifKR-VF.ttf OFL-notosanskr.txt OFL-notoserifkr.txt) do if exist "fonts\%%F" del /q "fonts\%%F"
rd "fonts" 2>nul
for %%F in (brotli-LICENSE.txt highway-LICENSE-BSD3.txt highway-LICENSE.txt libjxl-LICENSE.txt skcms-LICENSE.txt) do if exist "licenses\%%F" del /q "licenses\%%F"
rd "licenses" 2>nul
if exist "hires" rd /s /q "hires"
if exist "dx4k" rd /s /q "dx4k"
del "%BK%\installed.txt"
echo.
if defined FAILED goto :partial
echo 원래 게임으로 되돌렸습니다. 이제 KoreanPatch 폴더와 한국어패치 파일들은 지워도 됩니다.
goto :done
:partial
echo [알림] 다음은 되돌리지 못했습니다:%FAILED%
:done
pause
exit /b 0

:notinstalled
echo 설치 기록이 없습니다. 한국어패치_설치.bat 으로 설치한 폴더에서 실행해 주세요.
pause
exit /b 1
:running
echo [오류] 게임이 켜져 있습니다. 게임을 끄고 다시 실행해 주세요.
pause
exit /b 1
'''

for name, text in (('한국어패치_설치.bat', INSTALL), ('한국어패치_제거.bat', UNINSTALL)):
    (T / name).write_bytes(text.replace('\r\n', '\n').replace('\n', '\r\n').encode('cp949'))
    print(name, len(text))
