@echo off
setlocal enabledelayedexpansion

:: ================================================
::   InterviewAI - One-Click Launcher
::   First run: Full setup + server start
::   Next runs: Just start server
:: ================================================

cls
echo ================================================
echo   InterviewAI - Starting...
echo ================================================
echo.

:: ============================================
:: STEP 1: Check Prerequisites
:: ============================================

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo.
    echo Please install Python 3.11+ from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

:: Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found!
    echo.
    echo Please install Node.js (LTS) from:
    echo https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo [OK] Python and Node.js detected
echo.

:: ============================================
:: STEP 2: Setup Virtual Environment (if needed)
:: ============================================

if not exist venv\ (
    echo [SETUP] Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
    
    echo [SETUP] Installing Python packages...
    echo This will take 2-3 minutes...
    call venv\Scripts\activate.bat
    pip install --quiet -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install Python packages!
        pause
        exit /b 1
    )
    echo [OK] Python packages installed
    echo.
) else (
    echo [OK] Virtual environment exists
    call venv\Scripts\activate.bat
)

:: ============================================
:: STEP 3: Build Frontend (if needed)
:: ============================================

if not exist frontend\dist\ (
    echo [SETUP] Building frontend...
    cd frontend
    
    if not exist node_modules\ (
        echo [SETUP] Installing JavaScript packages...
        call npm install --silent
        if %errorlevel% neq 0 (
            echo ERROR: Failed to install JavaScript packages!
            cd ..
            pause
            exit /b 1
        )
    )
    
    echo [SETUP] Building React app...
    call npm run build --silent
    if %errorlevel% neq 0 (
        echo ERROR: Failed to build frontend!
        cd ..
        pause
        exit /b 1
    )
    
    cd ..
    echo [OK] Frontend built
    echo.
) else (
    echo [OK] Frontend already built
    echo.
)

:: ============================================
:: STEP 4: Configure API Keys (if needed)
:: ============================================

if not exist .env (
    echo ================================================
    echo   API KEYS REQUIRED
    echo ================================================
    echo.
    echo Creating .env file from template...
    copy .env.example .env >nul
    echo.
    echo You need 3 FREE API keys:
    echo.
    echo 1. GEMINI API KEY
    echo    - Go to: https://aistudio.google.com/apikey
    echo    - Click "Create API key"
    echo    - Copy the key
    echo.
    echo 2. DEEPGRAM API KEY
    echo    - Go to: https://console.deepgram.com/signup
    echo    - Sign up (get $200 free credit^)
    echo    - Go to API Keys -^> Create key
    echo    - Copy the key
    echo.
    echo 3. ELEVENLABS API KEY
    echo    - Go to: https://elevenlabs.io/
    echo    - Sign up (10k chars/month free^)
    echo    - Go to Profile -^> API Key
    echo    - Copy the key
    echo.
    echo ================================================
    echo.
    echo Opening .env file in Notepad...
    echo.
    echo INSTRUCTIONS:
    echo 1. Replace the placeholder values with your actual keys
    echo 2. Save the file (Ctrl+S^)
    echo 3. Close Notepad
    echo 4. Press any key here to continue...
    echo.
    
    start /wait notepad .env
    
    echo.
    echo Checking if API keys are configured...
    findstr /C:"your_gemini" .env >nul
    if %errorlevel% equ 0 (
        echo.
        echo WARNING: Looks like you didn't add your API keys!
        echo The app won't work without them.
        echo.
        echo Do you want to:
        echo   1. Edit .env again
        echo   2. Continue anyway (app will fail^)
        echo.
        choice /C 12 /N /M "Choice: "
        if !errorlevel! equ 1 (
            start /wait notepad .env
        )
    )
    echo.
)

:: ============================================
:: STEP 5: Start Server
:: ============================================

echo ================================================
echo   Starting InterviewAI Server
echo ================================================
echo.
echo Server will be available at:
echo   http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.
echo ================================================
echo.

python server.py
