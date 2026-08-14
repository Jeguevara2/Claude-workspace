@echo off
REM One-click launcher. Finds Python, builds the virtualenv on first run,
REM installs dependencies, then starts InkBridge.
REM
REM Every failure path below ends in `pause`, because this file is meant to be
REM double-clicked: without it the window closes instantly and takes the error
REM message with it.

chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "PYTHONIOENCODING=utf-8"
set "PYEXE="

REM 1. The py launcher is the most reliable entry point when it exists.
py -3 --version >nul 2>&1 && set "PYEXE=py -3"

REM 2. Otherwise a plain `python` on PATH.
if not defined PYEXE (
    python --version >nul 2>&1 && set "PYEXE=python"
)

REM 3. Otherwise look where the installer puts it when "Add to PATH" was
REM    skipped, which is the single most common setup mistake.
if not defined PYEXE (
    for %%D in (
        "%LOCALAPPDATA%\Programs\Python"
        "%ProgramFiles%\Python313" "%ProgramFiles%\Python312"
        "%ProgramFiles%\Python311" "%ProgramFiles%\Python310"
    ) do (
        if exist %%D (
            for /f "delims=" %%P in ('dir /b /s "%%~D\python.exe" 2^>nul') do (
                if not defined PYEXE set "PYEXE="%%P""
            )
        )
    )
)

if not defined PYEXE goto :nopython

echo.
echo   Python: !PYEXE!

if not exist ".venv\Scripts\python.exe" (
    if exist ".venv" (
        echo   기존 가상환경이 손상되어 다시 만듭니다  [rebuilding broken venv]
        rmdir /s /q ".venv"
    )
    echo   처음 실행이라 준비 중입니다. 1~2분 걸립니다.
    echo   [first run: creating environment, this takes a minute]
    echo.
    !PYEXE! -m venv .venv || goto :venvfail
    ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :depsfail
    echo.
    echo   준비 완료  [ready]
)

".venv\Scripts\python.exe" -m inkbridge %*
set "EXITCODE=%ERRORLEVEL%"

if not "%EXITCODE%"=="0" (
    echo.
    echo   프로그램이 오류로 종료되었습니다  [exited with an error]
    echo   위의 메시지를 그대로 알려주시면 도움이 됩니다.
    pause
)
exit /b %EXITCODE%

:nopython
echo.
echo   ============================================================
echo    Python이 설치되어 있지 않습니다.
echo    [Python was not found on this computer]
echo   ============================================================
echo.
echo    1. https://www.python.org/downloads/  에서 내려받으세요
echo    2. 설치 첫 화면 맨 아래
echo         [v] Add python.exe to PATH
echo       를 반드시 체크한 뒤 Install Now 를 누르세요
echo    3. 설치가 끝나면 이 파일을 다시 실행하세요
echo.
echo    이미 설치했는데 이 메시지가 보인다면, 2번 체크를 빠뜨린 것입니다.
echo    Python을 지우고 다시 설치하면 해결됩니다.
echo.
pause
exit /b 1

:venvfail
echo.
echo   가상환경을 만들지 못했습니다  [could not create the environment]
echo   Python은 찾았지만 실행에 실패했습니다. 재설치가 필요할 수 있습니다.
echo.
pause
exit /b 1

:depsfail
echo.
echo   필요한 구성 요소를 내려받지 못했습니다  [dependency install failed]
echo   인터넷 연결을 확인한 뒤 다시 실행해 보세요.
echo   회사 네트워크라면 방화벽이 막고 있을 수 있습니다.
echo.
pause
exit /b 1
