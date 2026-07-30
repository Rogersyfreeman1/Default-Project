@echo off
title Identity Protection Tool
echo.
echo ============================================
echo   IDENTITY PROTECTION TOOL
echo ============================================
echo.
echo   Starting...
echo.
python "%~dp0identity_protector.py" scan
echo.
echo ============================================
echo   Press any key to exit
echo ============================================
pause >nul
