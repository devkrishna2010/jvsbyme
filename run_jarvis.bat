@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title J.A.R.V.I.S. V2 — Stark Tactical Assistant

echo [STARK INDUSTRIES] Booting J.A.R.V.I.S. V2...

REM Check for project venv Python
if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" "%~dp0main.py" %*
    goto :end
)

REM Fallback to system Python
python "%~dp0main.py" %*

:end
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [J.A.R.V.I.S. Launcher] Execution halted with error code %ERRORLEVEL%.
    pause
)
endlocal

