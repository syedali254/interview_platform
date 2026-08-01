@echo off
setlocal enabledelayedexpansion
cls
echo ================================================
echo   InterviewAI - One-Click Setup and Launch
echo ================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Install Python 3.11+ from: https://www.python.org/downloads/
    echo CHECK "Add Python to PATH" during installation!
    pause
    exit /b 1
)
echo [OK] Python found

:: Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found!
    echo Install Node.js LTS from: https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js found
echo.

:: Create venv if missing
if not exist venv\ (
    echo [SETUP] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
    echo [SETUP] Installing Python packages (2-3 minutes)...
    call venv\Scripts\activate.bat
    pip install --quiet --disable-pip-version-check -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install packages
        pause
        exit /b 1
    )
    echo [OK] Python packages installed
) else (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
)
echo.

:: Build frontend if missing
if not exist frontend\dist\ (
    echo [SETUP] Building frontend...
    cd frontend
    if not exist node_modules\ (
        echo [SETUP] Installing JS packages...
        call npm install --silent 2>nul
    )
    call npm run build --silent 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Frontend build failed
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo [OK] Frontend built
) else (
    echo [OK] Frontend already built
)
echo.

:: Create .env if missing
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
    ) else (
        (
            echo GEMINI_API_KEY=your_gemini_api_key_here
            echo GEMINI_MODEL=gemini-2.0-flash
            echo DEEPGRAM_API_KEY=your_deepgram_api_key_here
            echo ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
            echo LIVEKIT_API_KEY=devkey
            echo LIVEKIT_API_SECRET=secret
            echo LIVEKIT_URL=ws://localhost:7880
        ) > .env
    )
    echo.
    echo ================================================
    echo   API KEYS NEEDED - Opening .env in Notepad
    echo ================================================
    echo.
    echo Get FREE keys from:
    echo   1. Gemini:     https://aistudio.google.com/apikey
    echo   2. Deepgram:   https://console.deepgram.com/signup
    echo   3. ElevenLabs: https://elevenlabs.io/
    echo.
    echo Paste your keys in Notepad, save, and close it.
    echo.
    start /wait notepad .env
)
echo [OK] Configuration ready
echo.

:: Start server
echo ================================================
echo   Starting InterviewAI Server
echo   Open browser: http://localhost:8000
echo   Press Ctrl+C to stop
echo ================================================
echo.
python server.py
