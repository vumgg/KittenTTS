@echo off
:: KittenTTS Web Interface Startup Script for Windows

echo ========================================
echo    KittenTTS Web Interface
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and add it to your PATH
    pause
    exit /b 1
)

echo Installing/updating dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ========================================
echo Starting KittenTTS Web Interface...
echo ========================================
echo.
echo Open your browser and go to:
echo   http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python app.py

pause
