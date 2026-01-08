@echo off
echo ========================================
echo  Javinizer Python - Installation Script
echo ========================================
echo.

REM Check Python version
python --version 2>nul
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
python -m venv env
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment!
    pause
    exit /b 1
)

echo [2/4] Activating virtual environment...
call env\Scripts\activate.bat

echo [3/4] Installing dependencies...
pip install -e .
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
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
