@echo off
echo ============================================================
echo SC AI Lead Generation System - Starting Server
echo ============================================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if activation worked
where python | findstr venv >nul
if errorlevel 1 (
    echo ERROR: Virtual environment not activated
    echo Please run SETUP_WINDOWS.bat first
    pause
    exit /b 1
)

echo ✅ Virtual environment activated
echo.
echo Starting Flask server...
echo Open your browser to: http://localhost:5000
echo.
echo Press CTRL+C to stop the server
echo.
echo ============================================================

python backend\app.py

pause
