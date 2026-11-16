@echo off
title WILDFIRE GUARD Command Center Launcher
echo ========================================================
echo        WILDFIRE GUARD Command Center & API Server
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] Python detected. Starting Backend API ^& SQLite Database...
    python wildfire_backend.py
) else (
    echo [INFO] Python executable not in PATH.
    echo Launching standalone dashboard directly in your browser...
    start "" "index.html"
)
pause
