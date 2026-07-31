@echo off
echo ================================================
echo   InterviewAI - Starting Server
echo ================================================
echo.

:: Check if venv exists
if not exist venv\ (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

:: Check if .env exists
if not exist .env (
    echo WARNING: .env file not found!
    echo.
    echo You need to configure API keys:
    echo 1. Copy .env.example to .env
    echo 2. Edit .env and add your API keys
    echo.
    echo See SETUP.md for instructions.
    pause
    exit /b 1
)

:: Activate venv and run
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting server...
echo.
echo Server will be available at: http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
echo ================================================
echo.

python server.py
