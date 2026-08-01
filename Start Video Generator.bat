@echo off
echo ========================================
echo    AI Video Generator - Quick Start
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed!
    echo Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Install required packages
echo Installing required packages...
pip install moviepy Pillow --quiet

REM Run the CLI
echo.
echo Starting Video Generator...
echo.
python video_cli.py

pause
