@echo off
setlocal
title InterviewAI - One-Click Setup and Run
color 0A

echo ============================================================
echo   InterviewAI - One-Click Setup and Run
echo   This will check, install and start everything for you.
echo   First run takes a few minutes (downloads). Later runs
echo   are fast.
echo   If Windows shows a SmartScreen warning, click "More info"
echo   then "Run anyway".
echo ============================================================
echo.

cd /d "%~dp0"

rem ---- [1/6] Make sure we are on the latest fixed branch ----
echo [1/6] Checking project code...
if exist ".git" for /f "delims=" %%b in ('git branch --show-current') do set "BRANCH=%%b"
if not "%BRANCH%"=="sherali-dev2" (
    echo       Switching to branch 'sherali-dev2' - latest version...
    git checkout sherali-dev2 >nul 2>&1
    git pull >nul 2>&1
)

cd /d "%~dp0InterviewAI"

rem ---- [2/6] Check Python ----
echo [2/6] Checking Python...
set "PYEXE=python"
call %PYEXE% -V >nul 2>&1
if errorlevel 1 set "PYEXE=py -3"
call %PYEXE% -V >nul 2>&1
if errorlevel 1 (
    echo.
    echo   ERROR: Python 3.11 or newer is not installed or not in PATH.
    echo   Install it from https://www.python.org/downloads/
    echo   IMPORTANT: tick "Add python.exe to PATH" during install.
    echo   Then run this file again.
    echo.
    pause
    exit /b 1
)
call %PYEXE% -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo   ERROR: Python is too old. This project needs Python 3.11+.
    echo   Install it from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
echo       Python OK.

rem ---- [3/6] Check Node.js ----
echo [3/6] Checking Node.js...
node -v >nul 2>&1
if errorlevel 1 (
    echo.
    echo   ERROR: Node.js is not installed.
    echo   Install it from https://nodejs.org  - LTS version.
    echo   Then run this file again.
    echo.
    pause
    exit /b 1
)
echo       Node.js OK.

rem ---- [4/6] Python environment ----
echo [4/6] Setting up Python environment...
if not exist "venv\Scripts\python.exe" (
    echo       Creating virtual environment...
    call %PYEXE% -m venv venv
    if errorlevel 1 (
        echo.
        echo   ERROR: Could not create the virtual environment.
        echo.
        pause
        exit /b 1
    )
)
echo       Installing Python packages...
venv\Scripts\python.exe -m pip install --upgrade pip --quiet --disable-pip-version-check
venv\Scripts\python.exe -m pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo   ERROR: pip install failed. Check your internet connection
    echo   and run this file again.
    echo.
    pause
    exit /b 1
)
echo       Python packages OK.

rem ---- [5/6] API keys ----
:env_check
echo [5/6] Checking API keys...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo.
    echo   A new file was created:  %CD%\.env
    echo   Notepad will open it now. Replace these 3 lines with your
    echo   real API keys. Get them from the websites below:
    echo.
    echo     GEMINI_API_KEY=      https://aistudio.google.com/apikey
    echo     DEEPGRAM_API_KEY=    https://console.deepgram.com
    echo     ELEVENLABS_API_KEY=  https://elevenlabs.io
    echo.
    echo   Save and close Notepad, then press any key to continue.
    echo   Press Ctrl+C if you do not have the keys yet.
    echo.
    notepad ".env"
    pause >nul
)
findstr /i "your_gemini_api_key_here your_deepgram_api_key_here your_elevenlabs_api_key_here" ".env" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo   Your .env file still contains placeholder keys.
    echo   Open it, paste your real keys, save, close, then press any key.
    echo.
    notepad ".env"
    pause >nul
    goto env_check
)
echo       API keys OK.

rem ---- [6/6] Build the web app ----
echo [6/6] Building the web app...
if not exist "frontend\node_modules" (
    echo       Installing web app packages - first time takes a few minutes...
    call npm install --no-audit --no-fund
    if errorlevel 1 (
        echo.
        echo   ERROR: npm install failed. Check your internet and rerun.
        echo.
        pause
        exit /b 1
    )
)
if not exist "frontend\dist\index.html" (
    echo       Building the web app...
    cd /d "%~dp0InterviewAI\frontend"
    call npm run build
    if errorlevel 1 (
        echo.
        echo   ERROR: frontend build failed.
        echo.
        cd /d "%~dp0InterviewAI"
        pause
        exit /b 1
    )
    cd /d "%~dp0InterviewAI"
)
echo       Web app OK.

echo.
echo ============================================================
echo   Starting InterviewAI...
echo   Your browser will open http://localhost:8000 shortly.
echo   Close this window to stop the application.
echo ============================================================
echo.

start "" /b cmd /c "ping -n 7 127.0.0.1 >nul & start http://localhost:8000"
venv\Scripts\python.exe server.py

echo.
echo   Server stopped.
pause
