@echo off
setlocal EnableExtensions
title InterviewAI - Setup and Run
color 0A

echo ============================================================
echo   InterviewAI - One-Click Setup and Run
echo.
echo   This installs and starts everything for you, including
echo   Python and Node.js if they are missing.
echo.
echo   The FIRST run takes about 5-10 minutes. Later runs start
echo   in seconds.
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
rem  [2/7] Settings file
rem
rem  Created silently with placeholders. Nothing opens and nothing is
rem  asked here: the whole setup runs unattended, and the keys are
rem  checked once at the end.
rem ---------------------------------------------------------------
echo [2/7] Preparing the settings file...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo       Created: %CD%\.env
) else (
    echo       Already present.
)

rem ---------------------------------------------------------------
rem  [3/7] Python  (installed automatically via winget if missing)
rem ---------------------------------------------------------------
echo [3/7] Checking Python...
call :find_python
if not "%PYOK%"=="1" (
    echo       Python 3.11+ not found. Installing it for you...
    call :winget_install "Python.Python.3.12" "Python 3.12"
    if errorlevel 1 goto :python_manual
    call :refresh_path
    call :find_python
)
if not "%PYOK%"=="1" goto :python_restart
echo       Python OK.

rem ---------------------------------------------------------------
rem  [4/7] Node.js  (installed automatically via winget if missing)
rem ---------------------------------------------------------------
echo [4/7] Checking Node.js...
call node -v >nul 2>&1
if errorlevel 1 (
    echo       Node.js not found. Installing it for you...
    call :winget_install "OpenJS.NodeJS.LTS" "Node.js LTS"
    if errorlevel 1 goto :node_manual
    call :refresh_path
    call node -v >nul 2>&1
    if errorlevel 1 goto :node_restart
)
echo       Node.js OK.

rem ---------------------------------------------------------------
rem  [5/7] Python environment
rem ---------------------------------------------------------------
echo [5/7] Setting up the Python environment...
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
rem  [7/7] Launch, or stop and explain what is still needed
rem
rem  Setup is complete either way by this point. The only thing that
rem  can be missing is the two API keys, which arrive separately.
rem ---------------------------------------------------------------
echo [7/7] Checking API keys...
call :check_keys
if not "%KEYSOK%"=="1" goto :keys_needed
echo       API keys OK.
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
exit /b 0


rem ---------------------------------------------------------------
:keys_needed
echo.
echo ============================================================
echo   SETUP IS COMPLETE
echo ============================================================
echo.
echo   Everything is installed and ready. Only the API keys are
echo   still missing.
echo.
echo   1. Open this file in Notepad:
echo.
echo        %CD%\.env
echo.
echo   2. Paste the keys you were sent after the equals sign,
echo      with no spaces and no quotes:
echo.
echo        GEMINI_API_KEY=paste-here
echo        DEEPGRAM_API_KEY=paste-here
echo.
echo      Leave every other line exactly as it is.
echo.
echo   3. Save the file, then double-click run.bat again.
echo      It will start straight away this time.
echo.
echo ============================================================
echo.
pause
exit /b 0


rem ===============================================================
rem  Helpers
rem ===============================================================

rem --- Locate a Python 3.11+ interpreter, setting PYEXE and PYOK ---
:find_python
set "PYOK="
for %%C in ("python" "py -3.12" "py -3.11" "py -3") do (
    if not defined PYOK (
        call %%~C -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
        if not errorlevel 1 (
            set "PYEXE=%%~C"
            set "PYOK=1"
        )
    )
)
exit /b 0

rem --- Are the two required keys filled in? Sets KEYSOK=1 when yes. ---
rem Rejects both the shipped placeholders and an empty value, so a half-edited
rem file is caught rather than failing later with a confusing API error.
:check_keys
set "KEYSOK=1"
if not exist ".env" (
    set "KEYSOK="
    exit /b 0
)
findstr /i /c:"your_gemini_api_key_here" ".env" >nul 2>&1 && set "KEYSOK="
findstr /i /c:"your_deepgram_api_key_here" ".env" >nul 2>&1 && set "KEYSOK="
findstr /r /c:"^GEMINI_API_KEY= *$" ".env" >nul 2>&1 && set "KEYSOK="
findstr /r /c:"^DEEPGRAM_API_KEY= *$" ".env" >nul 2>&1 && set "KEYSOK="
findstr /r /c:"^GEMINI_API_KEY=" ".env" >nul 2>&1 || set "KEYSOK="
findstr /r /c:"^DEEPGRAM_API_KEY=" ".env" >nul 2>&1 || set "KEYSOK="
exit /b 0

rem --- Install a winget package. Returns errorlevel 1 if it cannot. ---
:winget_install
call winget --version >nul 2>&1
if errorlevel 1 (
    echo       Automatic install needs winget, which this Windows does not have.
    exit /b 1
)
echo       Installing %~2 - this takes a few minutes, please wait...
call winget install --id %~1 --exact --silent ^
    --accept-package-agreements --accept-source-agreements ^
    --disable-interactivity
if errorlevel 1 (
    echo       Automatic install of %~2 did not succeed.
    exit /b 1
)
echo       %~2 installed.
exit /b 0

rem --- Pick up a fresh install without needing a new window ---
rem Deliberately ADDS the standard install locations rather than rebuilding
rem PATH from the registry. Registry Path values are REG_EXPAND_SZ and hold
rem unexpanded %VAR% references that do not survive being assigned here, so
rem rebuilding silently corrupts PATH - including the WindowsApps folder that
rem winget itself lives in. Appending can only ever help.
:refresh_path
set "PATH=%PATH%;%LOCALAPPDATA%\Microsoft\WindowsApps"
for %%V in (313 312 311) do (
    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python%%V;%LOCALAPPDATA%\Programs\Python\Python%%V\Scripts"
    set "PATH=%PATH%;%ProgramFiles%\Python%%V;%ProgramFiles%\Python%%V\Scripts"
)
set "PATH=%PATH%;%ProgramFiles%\nodejs"
if defined ProgramFiles(x86) set "PATH=%PATH%;%ProgramFiles(x86)%\nodejs"
exit /b 0


rem ===============================================================
rem  Failure paths
rem ===============================================================

:python_manual
echo.
echo   Could not install Python automatically.
echo   Please install it yourself, then run this file again:
echo       https://www.python.org/downloads/
echo   IMPORTANT: tick "Add python.exe to PATH" during install.
echo.
pause
exit /b 1

:python_restart
echo.
echo   Python was installed, but this window cannot see it yet.
echo   Close this window and double-click run.bat again - that is all.
echo.
pause
exit /b 1

:node_manual
echo.
echo   Could not install Node.js automatically.
echo   Please install the LTS version yourself, then run this file again:
echo       https://nodejs.org
echo.
pause
exit /b 1

:node_restart
echo.
echo   Node.js was installed, but this window cannot see it yet.
echo   Close this window and double-click run.bat again - that is all.
echo.
pause
exit /b 1
