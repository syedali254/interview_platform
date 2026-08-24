@echo off
rem Delayed expansion is required: the branch check below reads a variable that
rem is set inside the same parenthesised block, which plain expansion resolves
rem at parse time and would therefore always see the previous value.
setlocal EnableExtensions EnableDelayedExpansion
title InterviewAI - Setup and Run

rem The branch this project is published on. Named once here rather than
rem repeated through the update routine, so it is changed in one place.
set "BRANCH_NAME=abdulwahab-dev"
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
call :update_code

if not exist "%~dp0InterviewAI\server.py" (
    echo.
    echo   ERROR: Could not find InterviewAI\server.py
    echo   Run this file from the folder that contains the
    echo   InterviewAI folder.
    echo.
    pause
    exit /b 1
)

rem  Windows caps a path at 260 characters unless long-path support is on.
rem  The deepest file pip creates here sits 136 characters below this folder,
rem  so a project folder beyond ~120 characters makes the install fail with an
rem  error that reads like a network problem. Warn before that happens.
call :strlen "%~dp0" PATHLEN
if !PATHLEN! GTR 120 (
    echo.
    echo   WARNING: this folder's path is !PATHLEN! characters long.
    echo   Windows limits paths to 260 characters, and installing here is
    echo   likely to fail partway through.
    echo.
    echo   Move the project somewhere shorter - for example C:\Projects -
    echo   and run this file again from there.
    echo.
    pause
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
rem  [4/7] Node.js  (installed or upgraded automatically via winget)
rem
rem  The version matters, not merely the presence. Vite 8 and rolldown
rem  require ^20.19.0 || >=22.12.0, and an older Node fails much later with
rem  "Cannot find native binding", which reads like a broken download rather
rem  than an unsupported runtime. Checking here turns a confusing build
rem  failure into an upgrade.
rem ---------------------------------------------------------------
echo [4/7] Checking Node.js...
call :check_node
if "%NODEOK%"=="1" goto :node_ready
if "%NODEFOUND%"=="1" (
    echo       Node.js !NODEVER! is too old for this project. Upgrading...
) else (
    echo       Node.js not found. Installing it for you...
)
call :winget_install "OpenJS.NodeJS.LTS" "Node.js LTS"
if errorlevel 1 (
    rem  Plenty of Windows installs have no winget - it ships with App
    rem  Installer, which Store-less and older builds lack. Falling straight
    rem  through to "install it yourself" made a one-click script stop being
    rem  one click, so fetch the official MSI instead.
    call :install_node_msi
    if errorlevel 1 goto :node_manual
)
call :refresh_path
call :check_node
if not "%NODEOK%"=="1" goto :node_restart
:node_ready
echo       Node.js OK (%NODEVER%).

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
    echo   ERROR: the Python packages did not install.
    echo.
    echo   The two usual causes are:
    echo     1. No internet, or a firewall blocking pypi.org.
    echo     2. This folder sits too deep. If the message above mentions
    echo        "No such file or directory" or long paths, move the project
    echo        somewhere shorter such as C:\Projects and try again.
    echo.
    echo   If neither applies, delete InterviewAI\venv and run this file again.
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
    rem  npm leaves the platform-specific binaries out of the tree after an
    rem  interrupted or upgraded install, and the build dies with "Cannot find
    rem  native binding" - npm/cli#4828. npm's own advice is to delete the lock
    rem  file too, but that is wrong here: the lock is committed, correct, and
    rem  pins the versions this project was tested against. Deleting it makes
    rem  npm re-resolve to newer packages and can replace one broken tree with
    rem  a differently broken one. npm ci wipes node_modules itself and
    rem  installs exactly what the lock pins, which is what we actually want.
    echo.
    echo       Build failed. Reinstalling the web packages from the lock file
    echo       and trying once more - this takes a few minutes...
    if exist "node_modules" rmdir /s /q "node_modules"
    call npm ci --no-audit --no-fund
    if errorlevel 1 (
        echo.
        echo   ERROR: npm install failed. Check your internet and rerun.
        echo.
        cd /d "%~dp0InterviewAI"
        pause
        exit /b 1
    )
    call npm run build
    if errorlevel 1 (
        echo.
        echo   ERROR: the web app failed to build, twice.
        echo.
        echo   Check the messages above. If they mention a Node version,
        echo   install the current LTS from https://nodejs.org, then run
        echo   this file again.
        echo.
        cd /d "%~dp0InterviewAI"
        pause
        exit /b 1
    )
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

rem --- Bring the checkout to the latest %BRANCH_NAME%, or say why not ---
rem The previous version piped the pull to nul and then announced "Code up to
rem date" whether or not it had worked. A failed pull therefore looked exactly
rem like a successful one, and the run continued on stale code. Every step
rem below is now checked, and anything that stops the update is reported.
:update_code
if not exist ".git" (
    echo       Not a git checkout - using the files as they are.
    exit /b 0
)
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo       Not a usable git checkout - using the files as they are.
    exit /b 0
)
set "BRANCH="
for /f "delims=" %%b in ('git branch --show-current 2^>nul') do set "BRANCH=%%b"
if not "!BRANCH!"=="!BRANCH_NAME!" (
    echo       Switching to branch !BRANCH_NAME!...
    git checkout !BRANCH_NAME! >nul 2>&1
    if errorlevel 1 (
        call :stale_warning "could not switch to the !BRANCH_NAME! branch"
        exit /b 0
    )
)
git fetch origin >nul 2>&1
if errorlevel 1 (
    call :stale_warning "could not reach GitHub - check your internet connection"
    exit /b 0
)
rem Fast-forward only. A merge commit created here would be a local edit that
rem blocks every future update, which is worse than stopping now.
git merge --ff-only origin/!BRANCH_NAME! >nul 2>&1
if errorlevel 1 (
    call :stale_warning "your copy has local changes that block the update"
    exit /b 0
)
echo       Code up to date.
exit /b 0

rem --- Say plainly that the code was NOT updated, and how to force it ---
:stale_warning
echo.
echo   ============================================================
echo   WARNING: %~1.
echo.
echo   The project was NOT updated. You may be running an older
echo   version. Setup will continue anyway.
echo.
echo   To force the latest code, open a terminal in this folder
echo   and run these three commands. Your .env keys are not
echo   touched by them:
echo.
echo       git fetch origin
echo       git checkout !BRANCH_NAME!
echo       git reset --hard origin/!BRANCH_NAME!
echo.
echo   Then double-click run.bat again.
echo   ============================================================
echo.
pause
exit /b 0

rem --- Length of %~1 into the variable named by %~2 ---
:strlen
set "_S=%~1"
set "_N=0"
:strlen_next
if defined _S (
    set "_S=!_S:~1!"
    set /a _N+=1
    goto :strlen_next
)
set "%~2=!_N!"
exit /b 0

rem --- Install Node LTS from the official MSI, for machines without winget ---
rem The version is resolved from nodejs.org rather than pinned here, so this
rem does not rot into pointing at an ancient release. msiexec needs elevation,
rem which raises the usual Windows prompt - the alternative is telling someone
rem to go and do it by hand, which is what this whole file exists to avoid.
:install_node_msi
echo       Downloading Node.js LTS from nodejs.org (about 30 MB)...
set "NODEMSI=%TEMP%\interviewai-node-lts.msi"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "try {" ^
  "  [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" ^
  "  $i=Invoke-RestMethod 'https://nodejs.org/dist/index.json';" ^
  "  $v=($i | Where-Object { $_.lts } | Select-Object -First 1).version;" ^
  "  $u=\"https://nodejs.org/dist/$v/node-$v-x64.msi\";" ^
  "  Write-Host ('      Version ' + $v);" ^
  "  Invoke-WebRequest -Uri $u -OutFile '%NODEMSI%' -UseBasicParsing;" ^
  "  exit 0" ^
  "} catch { Write-Host ('      Download failed: ' + $_.Exception.Message); exit 1 }"
if errorlevel 1 exit /b 1
if not exist "%NODEMSI%" exit /b 1
echo       Installing Node.js - approve the Windows prompt if one appears...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { $p=Start-Process msiexec.exe -ArgumentList '/i','%NODEMSI%','/qn','/norestart' -Verb RunAs -Wait -PassThru;" ^
  "      exit $p.ExitCode } catch { exit 1 }"
if errorlevel 1 (
    echo       The installer did not complete.
    del /q "%NODEMSI%" >nul 2>&1
    exit /b 1
)
del /q "%NODEMSI%" >nul 2>&1
echo       Node.js installed.
exit /b 0

rem --- Is Node present AND new enough? Sets NODEFOUND, NODEVER, NODEOK ---
rem The range is Vite's own: ^20.19.0 || >=22.12.0. Node itself does the
rem comparison, because batch cannot compare dotted versions without a mess.
:check_node
set "NODEOK="
set "NODEFOUND="
set "NODEVER="
for /f "delims=" %%v in ('node -v 2^>nul') do set "NODEVER=%%v"
if not defined NODEVER exit /b 0
set "NODEFOUND=1"
node -e "const [a,b]=process.versions.node.split('.').map(Number); process.exit(((a===20&&b>=19)||(a===22&&b>=12)||a>=23)?0:1)" >nul 2>&1
if not errorlevel 1 set "NODEOK=1"
exit /b 0

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
echo   ============================================================
echo   Could not install Node.js automatically.
echo.
echo   Install it by hand - it takes two minutes:
echo.
echo     1. Open this page:   https://nodejs.org/en/download
echo     2. Download the Windows Installer (.msi), 64-bit, LTS
echo     3. Run it and click Next until it finishes. Leave
echo        "Add to PATH" ticked - it is on by default.
echo     4. Close this window, then double-click run.bat again.
echo.
echo   This project needs Node 20.19 or newer. If yours is older,
echo   the installer above replaces it; nothing needs uninstalling.
echo   ============================================================
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
