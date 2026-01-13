@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1

echo ========================================
echo  Javinizer Python - Installation Script
echo ========================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check Python version
echo [Check] Verifying Python installation...
python --version 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Verify Python version is 3.10+
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PYVER=%%v"
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set "PYMAJOR=%%a"
    set "PYMINOR=%%b"
)
if %PYMAJOR% LSS 3 (
    echo [ERROR] Python 3.10+ required. Found: %PYVER%
    pause
    exit /b 1
)
if %PYMAJOR%==3 if %PYMINOR% LSS 10 (
    echo [ERROR] Python 3.10+ required. Found: %PYVER%
    pause
    exit /b 1
)
echo   Python %PYVER% OK

:MENU
echo.
echo Choose installation type:
echo [1] Standard Install (Production)
echo [2] Development Install (+ ruff, mypy, pytest-cov)
echo [3] Clean Install (Delete env, cache, logs first)
echo [4] Exit
echo.
set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto INSTALL_STANDARD
if "%choice%"=="2" goto INSTALL_DEV
if "%choice%"=="3" goto CLEAN_INSTALL
if "%choice%"=="4" exit /b 0
echo Invalid choice.
goto MENU

:CLEAN_INSTALL
echo.
echo [!] WARNING: This will DELETE:
echo     - Virtual environment ('env', '.venv')
echo     - Cache files ('__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache')
echo     - Log files ('*.log')
echo     - Coverage data ('.coverage')
echo.
set /p confirm="Are you sure? (Y/N): "
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

echo [Clean] Removing cache directories...
for %%d in (.pytest_cache .mypy_cache .ruff_cache) do (
    if exist "%%d" (
        echo   Removing '%%d'...
        rmdir /s /q "%%d"
    )
)

REM Recursive delete __pycache__
echo   Removing '__pycache__' directories...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Delete log and coverage files
echo   Removing log and coverage files...
del /q *.log .coverage 2>nul

echo [Clean] Cleanup complete.
echo.
echo Choose install type:
echo [1] Standard Install
echo [2] Development Install
set /p postchoice="Enter choice (1-2): "
if "%postchoice%"=="2" goto INSTALL_DEV
goto INSTALL_STANDARD

:INSTALL_STANDARD
set "INSTALL_TYPE=standard"
goto INSTALL

:INSTALL_DEV
set "INSTALL_TYPE=dev"
goto INSTALL

:INSTALL
echo.
echo [1/5] Creating virtual environment...
if not exist "env" (
    python -m venv env
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo   Created 'env' directory.
) else (
    echo   Using existing 'env' directory.
)

echo [2/5] Activating virtual environment...
call env\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)

echo [3/5] Upgrading pip...
python -m pip install --upgrade pip --quiet

echo [4/5] Installing dependencies...
pip install -e . --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)

if "%INSTALL_TYPE%"=="dev" (
    echo   Installing development tools...
    pip install ruff mypy pytest-cov --quiet
    if errorlevel 1 (
        echo [WARNING] Some dev tools failed to install.
    )
)

echo [5/5] Installing optional Playwright (for dmm_new scraper)...
pip install playwright --quiet 2>nul
playwright install chromium 2>nul
if errorlevel 1 (
    echo   [INFO] Playwright installation skipped or failed (optional).
)

echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo Virtual Environment: env\Scripts\activate
echo.
echo Usage:
echo   .\javinizer.bat find IPX-486
echo   .\javinizer.ps1 find IPX-486 --source dmm,r18dev
echo   .\javinizer.bat sort "video.mp4" --dest "D:/Movies"
echo.
if "%INSTALL_TYPE%"=="dev" (
    echo Development Tools:
    echo   ruff check .          - Lint code
    echo   ruff format .         - Format code
    echo   pytest tests/ -v      - Run tests
    echo.
)
echo See GUIDE.md for full documentation.
echo ========================================
pause
