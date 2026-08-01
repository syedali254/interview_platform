@echo off
echo ================================================
echo   InterviewAI - Updating Dependencies
echo ================================================
echo.

if not exist venv\ (
    echo [ERROR] Not set up yet. Run setup.bat first!
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo [1/3] Updating Python packages...
pip install --quiet --disable-pip-version-check --upgrade -r requirements.txt
echo [OK] Python packages updated
echo.

echo [2/3] Updating JS packages...
cd frontend
call npm install --silent 2>nul
echo [OK] JS packages updated
echo.

echo [3/3] Rebuilding frontend...
call npm run build --silent 2>nul
cd ..
echo [OK] Frontend rebuilt
echo.

echo ================================================
echo   Update complete! Run: run.bat
echo ================================================
pause
