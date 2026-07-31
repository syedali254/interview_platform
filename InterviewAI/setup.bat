@echo off
setlocal enabledelayedexpansion

echo ================================================
echo   InterviewAI - Automated Setup
echo ================================================
echo.

:: Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.11+ from: https://www.python.org/downloads/
    echo Make sure to CHECK "Add Python to PATH" during installation!
    pause
    exit /b 1
)
python --version
echo.

:: Check Node.js
echo [2/5] Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found!
    echo Please install Node.js from: https://nodejs.org/
    pause
    exit /b 1
)
node --version
echo.

:: Create venv
echo [3/5] Setting up Python virtual environment...
if not exist venv\ (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
) else (
    echo Virtual environment already exists, skipping...
)
echo.

:: Install Python packages
echo [4/5] Installing Python packages...
echo This may take 2-3 minutes...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python packages!
    pause
    exit /b 1
)
echo Python packages installed successfully!
echo.

:: Build frontend
echo [5/5] Building frontend...
cd frontend

:: Check if node_modules exists
if not exist node_modules\ (
    echo Installing JavaScript packages...
    call npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install JavaScript packages!
        cd ..
        pause
        exit /b 1
    )
)

echo Building React app...
call npm run build
if %errorlevel% neq 0 (
    echo ERROR: Failed to build frontend!
    cd ..
    pause
    exit /b 1
)

cd ..
echo Frontend built successfully!
echo.

:: Check for .env
echo ================================================
echo   Setup Complete!
echo ================================================
echo.

if not exist .env (
    echo IMPORTANT: You need to configure API keys!
    echo.
    echo 1. Copy .env.example to .env:
    echo    copy .env.example .env
    echo.
    echo 2. Edit .env and add your API keys:
    echo    - GEMINI_API_KEY
    echo    - DEEPGRAM_API_KEY  
    echo    - ELEVENLABS_API_KEY
    echo.
    echo See SETUP.md for instructions on getting free API keys.
    echo.
) else (
    echo API keys file (.env) already exists.
    echo Make sure it contains your actual API keys!
    echo.
)

echo Next steps:
echo 1. Make sure .env file has your API keys
echo 2. Run: run.bat
echo 3. Open browser: http://localhost:8000
echo.
echo ================================================
pause
