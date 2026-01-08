@echo off
setlocal

set "VENV_PYTHON="

rem Check for .venv (User's current environment)
if exist "%~dp0.venv\Scripts\python.exe" (
    set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"
) else if exist "%~dp0env\Scripts\python.exe" (
    rem Check for env (Created by install.bat)
    set "VENV_PYTHON=%~dp0env\Scripts\python.exe"
)

if not defined VENV_PYTHON (
    echo [ERROR] Virtual environment not found.
    echo Checked: .venv and env
    echo Please ensure you have a virtual environment set up.
    pause
    exit /b 1
)

"%VENV_PYTHON%" -m javinizer %*
