@echo off
setlocal enabledelayedexpansion

set SILENT=0
if "%1"=="--silent" set SILENT=1

if %SILENT%==0 echo [1/4] Checking for Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    if %SILENT%==0 (
        echo [ERROR] Python is not installed or not in PATH!
        echo Please install Python 3.11+ from https://www.python.org/downloads/
        pause
    )
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
if %SILENT%==0 echo [OK] Found Python %PYTHON_VERSION%

for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% LSS 3 (
    if %SILENT%==0 (
        echo [ERROR] Python 3.11+ is required. You have Python %PYTHON_VERSION%
        pause
    )
    exit /b 1
)

if %MAJOR% EQU 3 if %MINOR% LSS 11 (
    if %SILENT%==0 (
        echo [WARNING] Python 3.11+ is recommended. You have Python %PYTHON_VERSION%
        echo Continuing anyway...
    )
)

if %SILENT%==0 echo.

if %SILENT%==0 echo [2/4] Checking virtual environment...
if exist "venv\Scripts\activate.bat" (
    if %SILENT%==0 echo [OK] Virtual environment found
) else (
    if %SILENT%==0 echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        if %SILENT%==0 (
            echo [ERROR] Failed to create virtual environment!
            pause
        )
        exit /b 1
    )
    if %SILENT%==0 echo [OK] Virtual environment created
)

if %SILENT%==0 echo.

if %SILENT%==0 echo [3/4] Installing dependencies...
call venv\Scripts\activate.bat

python -c "import customtkinter, kasa, mss, numpy, watchfiles" >nul 2>&1
if errorlevel 1 (
    if %SILENT%==0 (
        echo [INFO] Installing packages from requirements.txt...
        echo This may take a few minutes on first run...
        echo.
    )

    if %SILENT%==0 (
        pip install -r requirements.txt
    ) else (
        pip install -r requirements.txt >nul 2>&1
    )

    if errorlevel 1 (
        if %SILENT%==0 (
            echo.
            echo [ERROR] Failed to install requirements!
            pause
        )
        exit /b 1
    )
    if %SILENT%==0 (
        echo.
        echo [OK] All packages installed
    )
) else (
    if %SILENT%==0 echo [OK] All packages already installed
)

if %SILENT%==0 echo.

if %SILENT%==0 (
    echo [4/4] Starting Smart Bulb Screen Sync...
    echo ================================================
    echo.
    echo Program is starting in the background...
    echo You can close this window - the program will keep running!
    echo Look for the light bulb icon in your system tray.
    echo.
)

start "" venv\Scripts\pythonw.exe main.py

if %SILENT%==0 (
    echo [OK] Program launched successfully!
    echo.
    timeout /t 3 /nobreak >nul
)

deactivate