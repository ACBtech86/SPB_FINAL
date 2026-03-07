@echo off
echo ============================================
echo Starting IBM MQ Queue Manager
echo ============================================
echo.
echo This script must be run as Administrator!
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script requires Administrator privileges!
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

echo Starting Queue Manager: QM.61377677.01
strmqm QM.61377677.01

if %errorLevel% equ 0 (
    echo.
    echo ✅ Queue Manager started successfully!
    echo.
) else (
    echo.
    echo ⚠️  Queue Manager might already be running or failed to start
    echo.
)

echo Checking status...
dspmq

pause
