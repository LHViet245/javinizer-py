#!/usr/bin/env pwsh
# Javinizer PowerShell Launcher
# Usage: .\javinizer.ps1 find IPX-486

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check for virtual environments
$VenvPaths = @(
    "$ScriptDir\.venv\Scripts\python.exe",
    "$ScriptDir\env\Scripts\python.exe"
)

$PythonExe = $null
foreach ($Path in $VenvPaths) {
    if (Test-Path $Path) {
        $PythonExe = $Path
        break
    }
}

if (-not $PythonExe) {
    Write-Host "[ERROR] Virtual environment not found." -ForegroundColor Red
    Write-Host "Checked: .venv and env"
    Write-Host "Please run install.bat first or create a virtual environment."
    exit 1
}

# Run javinizer with all arguments
# Note: In PowerShell, comma-separated values become arrays.
# We need to join them back for Python.
$fixedArgs = @()
foreach ($arg in $args) {
    if ($arg -is [System.Array]) {
        $fixedArgs += ($arg -join ',')
    } else {
        $fixedArgs += $arg
    }
}

& $PythonExe -m javinizer $fixedArgs
