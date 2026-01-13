@echo off
setlocal EnableDelayedExpansion

REM Javinizer Batch Launcher
REM Usage: javinizer.bat find IPX-486

REM Get script directory (handles spaces in path)
set "SCRIPT_DIR=%~dp0"

REM Check for virtual environments in order of preference
set "VENV_PYTHON="

if exist "%SCRIPT_DIR%env\Scripts\python.exe" (
    set "VENV_PYTHON=%SCRIPT_DIR%env\Scripts\python.exe"
) else if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    set "VENV_PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe"
)

if not defined VENV_PYTHON (
    echo [ERROR] Virtual environment not found.
    echo.
    echo Checked locations:
    echo   - %SCRIPT_DIR%env\Scripts\python.exe
    echo   - %SCRIPT_DIR%.venv\Scripts\python.exe
    echo.
    echo Please run install.bat first to create the virtual environment.
    echo.
    pause
    exit /b 1
)

REM Run javinizer with all arguments
"%VENV_PYTHON%" -m javinizer %*
