@echo off
setlocal
cd /d "%~dp0"
title CS2 Sub-Tick Replay Studio // Control Center
color 0B

echo ==============================================================================
echo   COUNTER-STRIKE 2: SUB-TICK REPLAY STUDIO // CONTROL CENTER
echo ==============================================================================
echo.
echo Starting Desktop GUI Control Center...
echo.

python "%~dp0launcher.py" %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with error code %ERRORLEVEL%.
    pause
)
