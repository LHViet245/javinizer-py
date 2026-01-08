@echo off
setlocal EnableDelayedExpansion
echo ========================================
echo  Javinizer Python - Installation Script
echo ========================================
echo.

REM Check Python version
python --version 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

:MENU
echo Choose installation type:
echo [1] Standard Install (Update existing or create new)
echo [2] Clean Install (Factory Reset: Delete env, cache, logs)
echo [3] Exit
echo.
set /p choice="Enter choice (1-3): "

if "%choice%"=="1" goto INSTALL
if "%choice%"=="2" goto CLEAN_INSTALL
if "%choice%"=="3" exit /b 0
echo Invalid choice.
goto MENU

:CLEAN_INSTALL
echo.
echo [!] WARNING: This will DELETE:
echo     - Virtual environment ('env', '.venv')
echo     - Cache files ('__pycache__', '.pytest_cache')
echo     - Log files ('*.log')
echo.
echo Are you sure? (Y/N)
set /p confirm="> "
if /i not "!confirm!"=="Y" goto MENU

echo.
echo [Clean] Removing virtual environments...
if exist "env" (
    echo   Removing 'env'...
    rmdir /s /q "env"
)
if exist ".venv" (
    echo   Removing '.venv'...
    rmdir /s /q ".venv"
)

echo [Clean] Removing cache and logs...
if exist ".pytest_cache" (
    echo   Removing '.pytest_cache'...
    rmdir /s /q ".pytest_cache"
)

REM Recursive delete __pycache__
echo   Removing '__pycache__' directories...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Delete log files
echo   Removing log files...
del /q *.log 2>nul

echo [Clean] Cleanup complete.
goto INSTALL

:INSTALL
echo.
echo [1/4] Creating virtual environment...
if not exist "env" (
    python -m venv env
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
) else (
    echo   Using existing 'env' directory.
)

echo [2/4] Activating virtual environment...
call env\Scripts\activate.bat

echo [3/4] Installing dependencies...
REM Upgrade pip first
python -m pip install --upgrade pip

REM Install packages
pip install -e .
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)

echo [4/4] Installing optional Playwright (for dmm_new scraper)...
pip install playwright
playwright install chromium

echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo Usage:
echo   .\javinizer.ps1 find IPX-486
echo   .\javinizer.ps1 sort "video.mp4" --dest "D:/Movies"
echo.
echo Run '.\javinizer.ps1 --help' for more commands.
echo.
echo See GUIDE.md for full documentation.
echo ========================================
pause
