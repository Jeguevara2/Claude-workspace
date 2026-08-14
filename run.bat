@echo off
REM One-click launcher. Creates the virtualenv on first run, then starts InkBridge.
setlocal

cd /d "%~dp0"

if not exist ".venv" (
    echo Creating virtual environment...
    py -3 -m venv .venv || goto :fail
    call .venv\Scripts\activate.bat
    echo Installing dependencies, this takes a minute the first time...
    python -m pip install --upgrade pip >nul
    python -m pip install -r requirements.txt || goto :fail
) else (
    call .venv\Scripts\activate.bat
)

python -m inkbridge %*
goto :eof

:fail
echo.
echo Setup failed. Make sure Python 3.10 or newer is installed and on PATH.
pause
exit /b 1
