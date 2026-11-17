@echo off
setlocal
cd /d "%~dp0"
title CS2 Replay Studio
color 0B

echo ==============================================================================
echo   COUNTER-STRIKE 2: REPLAY STUDIO
echo ==============================================================================
echo.

if "%~1"=="" (
    echo [PROMPT] Drag and drop ANY CS2 match recording .dem file onto this icon.
    echo.
    set /p "TARGET_DEMO=Or paste full path to a demo file: "
) else (
    set "TARGET_DEMO=%~1"
)

if defined TARGET_DEMO (
    set "TARGET_DEMO=%TARGET_DEMO:"=%"
)

if "%TARGET_DEMO%"=="" (
    python "%~dp0launcher.py"
    exit /b 0
)

if not exist "%TARGET_DEMO%" (
    echo [ERROR] File does not exist: "%TARGET_DEMO%"
    pause
    exit /b 1
)

python "%~dp0launcher.py" "%TARGET_DEMO%"
