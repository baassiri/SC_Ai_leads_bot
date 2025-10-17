@echo off
echo ============================================================
echo SC AI Lead Generation System - Windows Setup
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Upgrading pip...
python -m pip install --upgrade pip

echo [4/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [5/5] Initializing database...
python scripts\init_db.py
if errorlevel 1 (
    echo WARNING: Database initialization had issues
)

echo.
echo ============================================================
echo ✅ Setup Complete!
echo ============================================================
echo.
echo Next steps:
echo 1. Run: START_WINDOWS.bat
echo 2. Open browser: http://localhost:5000
echo 3. Go to Settings and add your credentials
echo 4. Start using the system!
echo.
echo ============================================================
pause
