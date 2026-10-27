# Pet Cursor — one-shot Windows build script (PowerShell)
#
# Creates a local .venv, installs deps, runs PyInstaller.
# Does NOT modify global Python/system state beyond the .venv.
#
# Usage:
#   pwsh -ExecutionPolicy Bypass -File build.ps1
#   .\build.ps1                       (if execution policy allows)
#
# Prereq: Python 3.11+ on PATH (or pass -Python <path>).

param(
    [string]$Python = "python",
    [switch]$Clean,
    [switch]$OneFile
)

# NOTE: Do not set $ErrorActionPreference = "Stop" — in Windows PowerShell 5.1
# any stderr line from a native command (even INFO logs) becomes a NativeCommandError
# and aborts the script. We check $LASTEXITCODE manually instead.
$Root = $PSScriptRoot

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Check($what) {
    if ($LASTEXITCODE -ne 0) { throw "$what failed (exit=$LASTEXITCODE)" }
}

if ($Clean) {
    Step "Cleaning build/dist/.venv"
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$Root\build", "$Root\dist", "$Root\.venv"
}

Step "Verifying Python"
& $Python --version
Check "python --version"

$Venv = Join-Path $Root ".venv"
if (-not (Test-Path $Venv)) {
    Step "Creating virtual environment at .venv"
    & $Python -m venv $Venv
    Check "python -m venv"
}

$PyVenv = Join-Path $Venv "Scripts\python.exe"

Step "Upgrading pip"
& $PyVenv -m pip install --upgrade pip
Check "pip upgrade"

Step "Installing project dependencies (PySide6, rembg, Pillow)"
& $PyVenv -m pip install -r (Join-Path $Root "requirements.txt")
Check "pip install requirements"

Step "Installing PyInstaller"
& $PyVenv -m pip install pyinstaller
Check "pip install pyinstaller"

# The spec reads this environment variable without changing tracked files.
$env:PET_CURSOR_ONEFILE = if ($OneFile) { "1" } else { "0" }

Step "Running PyInstaller"
& $PyVenv -m PyInstaller --noconfirm (Join-Path $Root "pet_cursor.spec")
Check "PyInstaller"

Step "Done"
if ($OneFile) {
    Write-Host "Output: $Root\dist\PetCursor.exe" -ForegroundColor Green
} else {
    Write-Host "Output: $Root\dist\PetCursor\PetCursor.exe" -ForegroundColor Green
    Write-Host "Distribute the entire 'PetCursor' folder." -ForegroundColor Yellow
}

