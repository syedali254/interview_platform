@echo off
echo ================================================
echo   InterviewAI - Starting Server
echo ================================================
echo.

if not exist venv\ (
    echo [ERROR] Not set up yet. Run setup.bat first!
    pause
    exit /b 1
)

if not exist .env (
    echo [ERROR] No .env file. Run setup.bat first!
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
echo Server: http://localhost:8000
echo Press Ctrl+C to stop
echo.
python server.py
