@echo off
setlocal EnableExtensions
title InterviewAI - Setup and Run
color 0A

echo ============================================================
echo   InterviewAI - One-Click Setup and Run
echo.
echo   This checks, installs and starts everything for you.
echo   The FIRST run takes a few minutes (it downloads packages
echo   and the face/posture models). Later runs start in seconds.
echo.
echo   If Windows shows a SmartScreen warning, click "More info"
echo   then "Run anyway".
echo ============================================================
echo.

cd /d "%~dp0"

rem ---------------------------------------------------------------
rem  [1/7] Latest code
rem ---------------------------------------------------------------
echo [1/7] Checking project code...
if exist ".git" (
    for /f "delims=" %%b in ('git branch --show-current 2^>nul') do set "BRANCH=%%b"
    if not "%BRANCH%"=="sherali-dev2" (
        echo       Switching to branch sherali-dev2...
        git checkout sherali-dev2 >nul 2>&1
    )
    git pull >nul 2>&1
    echo       Code up to date.
) else (
    echo       Not a git checkout - using the files as they are.
)

if not exist "%~dp0InterviewAI\server.py" (
    echo.
    echo   ERROR: Could not find InterviewAI\server.py
    echo   Run this file from the folder that contains the
    echo   InterviewAI folder.
    echo.
    pause
    exit /b 1
)
cd /d "%~dp0InterviewAI"

rem ---------------------------------------------------------------
rem  [2/7] Python
rem ---------------------------------------------------------------
echo [2/7] Checking Python...
set "PYEXE=python"
call %PYEXE% -V >nul 2>&1
if errorlevel 1 set "PYEXE=py -3"
call %PYEXE% -V >nul 2>&1
if errorlevel 1 (
    echo.
    echo   ERROR: Python is not installed, or not on PATH.
    echo   Install Python 3.11 or newer from:
    echo       https://www.python.org/downloads/
    echo   IMPORTANT: tick "Add python.exe to PATH" during install.
    echo   Then run this file again.
    echo.
    pause
    exit /b 1
)
call %PYEXE% -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo   ERROR: Your Python is too old. Version 3.11 or newer is needed.
    echo   Get it from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
echo       Python OK.

rem ---------------------------------------------------------------
rem  [3/7] Node.js
rem ---------------------------------------------------------------
echo [3/7] Checking Node.js...
call node -v >nul 2>&1
if errorlevel 1 (
    echo.
    echo   ERROR: Node.js is not installed.
    echo   Install the LTS version from https://nodejs.org
    echo   Then run this file again.
    echo.
    pause
    exit /b 1
)
echo       Node.js OK.

rem ---------------------------------------------------------------
rem  [4/7] Python environment
rem ---------------------------------------------------------------
echo [4/7] Setting up the Python environment...
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
echo       Installing Python packages - this can take a few minutes...
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
venv\Scripts\python.exe -c "import fastapi, livekit, networkx, sklearn" >nul 2>&1
if errorlevel 1 (
    echo.
    echo   ERROR: Python packages did not install correctly.
    echo   Delete the InterviewAI\venv folder and run this file again.
    echo.
    pause
    exit /b 1
)
echo       Python packages OK.

rem ---------------------------------------------------------------
rem  [5/7] API keys
rem ---------------------------------------------------------------
:env_check
echo [5/7] Checking API keys...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo.
    echo   A new settings file was created:
    echo       %CD%\.env
    echo.
    echo   Notepad will open it now. Replace the placeholder values
    echo   with your own free API keys:
    echo.
    echo     GEMINI_API_KEY      https://aistudio.google.com/apikey
    echo     DEEPGRAM_API_KEY    https://console.deepgram.com
    echo     ELEVENLABS_API_KEY  https://elevenlabs.io
    echo.
    echo   Gemini and Deepgram are required.
    echo   ElevenLabs is optional - if it is missing or out of
    echo   credit, the interviewer uses the Deepgram voice instead.
    echo.
    echo   Save and close Notepad, then press any key here.
    echo   Press Ctrl+C if you do not have the keys yet.
    echo.
    notepad ".env"
    pause >nul
)
findstr /i "your_gemini_api_key_here your_deepgram_api_key_here" ".env" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo   Your .env file still has placeholder keys in it.
    echo   Open it, paste your real Gemini and Deepgram keys,
    echo   save, close, then press any key.
    echo.
    notepad ".env"
    pause >nul
    goto env_check
)
echo       API keys OK.

rem ---------------------------------------------------------------
rem  [6/7] Web app
rem ---------------------------------------------------------------
echo [6/7] Building the web app...
cd /d "%~dp0InterviewAI\frontend"
if not exist "node_modules" (
    echo       Installing web packages - first time takes a few minutes...
    call npm install --no-audit --no-fund
    if errorlevel 1 (
        echo.
        echo   ERROR: npm install failed. Check your internet and rerun.
        echo.
        cd /d "%~dp0InterviewAI"
        pause
        exit /b 1
    )
)
echo       Fetching face and posture models if needed...
echo       Compiling the interface...
call npm run build
if errorlevel 1 (
    echo.
    echo   ERROR: the web app failed to build.
    echo.
    cd /d "%~dp0InterviewAI"
    pause
    exit /b 1
)
cd /d "%~dp0InterviewAI"
if not exist "frontend\dist\index.html" (
    echo.
    echo   ERROR: build finished but produced no output.
    echo.
    pause
    exit /b 1
)
echo       Web app OK.

rem ---------------------------------------------------------------
rem  [7/7] Run
rem ---------------------------------------------------------------
echo [7/7] Starting InterviewAI...
echo.
echo ============================================================
echo   InterviewAI is starting.
echo.
echo   Your browser will open at:  http://localhost:8000
echo   If it does not, open that address yourself.
echo.
echo   Use Chrome or Edge, and allow camera and microphone
echo   access when the browser asks.
echo.
echo   Close this window to stop the application.
echo ============================================================
echo.

start "" /b cmd /c "ping -n 6 127.0.0.1 >nul & start http://localhost:8000"
venv\Scripts\python.exe server.py

echo.
echo   Server stopped.
pause
