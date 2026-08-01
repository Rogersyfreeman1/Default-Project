@echo off
echo ============================================
echo    ADSTUDIO PRO - Professional Video Studio
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed!
    echo Download from: https://python.org
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during install
    pause
    exit /b 1
)

REM Check FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo FFmpeg is not installed!
    echo Download from: https://www.gyan.dev/ffmpeg/builds/
    echo.
    echo After download, add ffmpeg.exe to this folder
    pause
    exit /b 1
)

REM Create folders if they don't exist
if not exist "music" mkdir music
if not exist "music\packs" mkdir music\packs
if not exist "output" mkdir output
if not exist "assets" mkdir assets

REM Install packages
echo Installing required packages...
pip install Pillow --quiet 2>nul

echo.
echo Starting AdStudio Pro...
echo.
python studio_cli.py

pause
