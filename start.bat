@echo off
title Phone As PC Speaker Launcher
cd /d "%~dp0"

echo ====================================================
echo        PHONE AS PC SPEAKER - AUDIO STREAMER
echo ====================================================
echo.

:: 1. Check local virtual environment first
if exist ".venv\Scripts\python.exe" (
    echo Using Virtual Environment (.venv)...
    ".venv\Scripts\python.exe" app.py
    goto end
)

:: 2. Check standard Windows Python 3.12
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" (
    echo Using Windows Python 3.12...
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" app.py
    goto end
)

:: 3. Check Windows py launcher
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Using Windows py launcher...
    py app.py
    goto end
)

:: 4. Fallback to python
python app.py

:end
pause
