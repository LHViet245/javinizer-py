#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Javinizer PowerShell Launcher
.DESCRIPTION
    Runs the Javinizer CLI using the project's virtual environment.
.EXAMPLE
    .\javinizer.ps1 find IPX-486
    .\javinizer.ps1 sort "video.mp4" --dest "D:/Movies"
    .\javinizer.ps1 find START-469 --source r18dev,dmm
#>

# Get script directory
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

# Check for virtual environments in order of preference
$VenvPaths = @(
    Join-Path $ScriptDir ".venv\Scripts\python.exe"
    Join-Path $ScriptDir "env\Scripts\python.exe"
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
    Write-Host ""
    Write-Host "Checked locations:" -ForegroundColor Yellow
    foreach ($Path in $VenvPaths) {
        Write-Host "  - $Path"
    }
    Write-Host ""
    Write-Host "Please run install.bat first to create the virtual environment."
    exit 1
}

# Fix PowerShell array handling for comma-separated values
# PowerShell converts "a,b,c" to array when passed as argument
$FixedArgs = @()
foreach ($Arg in $args) {
    if ($Arg -is [System.Array]) {
        # Join array back to comma-separated string
        $FixedArgs += ($Arg -join ',')
    } else {
        $FixedArgs += $Arg
    }
}

# Run javinizer
& $PythonExe -m javinizer $FixedArgs
