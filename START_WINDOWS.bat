@echo off
echo ========================================
echo  Quant Analytics App - Quick Start
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found!
    echo.
    echo Please make sure you're running this from:
    echo C:\Users\Pranav\Downloads\quant-analytics-app\
    echo.
    pause
    exit /b 1
)

echo [1/3] Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK - Python is installed
echo.

echo [2/3] Installing dependencies...
echo This may take 2-3 minutes...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Try running: pip install -r requirements.txt
    pause
    exit /b 1
)
echo OK - Dependencies installed
echo.

echo [3/3] Starting application...
echo.
echo ========================================
echo  Dashboard will open at:
echo  http://localhost:8501
echo.
echo  Wait 1-2 minutes for data collection
echo.
echo  Press Ctrl+C to stop the application
echo ========================================
echo.

streamlit run app.py

pause
