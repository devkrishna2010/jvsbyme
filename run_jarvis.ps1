# J.A.R.V.I.S. V2 — PowerShell Native Launcher
$ErrorActionPreference = "Continue"
Set-Location -Path $PSScriptRoot
$Host.UI.RawUI.WindowTitle = "J.A.R.V.I.S. V2 — Stark Tactical Assistant"

Write-Host "[STARK INDUSTRIES] Initializing J.A.R.V.I.S. V2..." -ForegroundColor Cyan

$VenvPython = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
$MainScript = Join-Path $PSScriptRoot "main.py"

if (Test-Path $VenvPython) {
    & $VenvPython $MainScript @args
} else {
    python $MainScript @args
}
