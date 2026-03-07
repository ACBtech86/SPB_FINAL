@echo off
REM ============================================================================
REM Test Rebuilt Binary in Console Mode
REM Must run as Administrator!
REM ============================================================================

color 0E
title Test Rebuilt Binary - Console Mode

cls
echo.
echo ============================================================================
echo TEST REBUILT BINARY IN CONSOLE MODE
echo ============================================================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click this .bat file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [1/3] Stopping service...
echo ============================================================================
net stop BCSrvSqlMq
echo.

echo [2/3] Starting in console mode...
echo ============================================================================
echo.
echo WATCH FOR:
echo   - All 8 tasks should show "Iniciada" message
echo   - NO error 8019 with reason code 2085 or 2043
echo   - Tasks should stay running (no "Terminada" immediately after)
echo.
echo Press Ctrl+C when you want to stop the console test.
echo ============================================================================
echo.

cd /d "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release"
BCSrvSqlMq.exe -d

echo.
echo ============================================================================
echo Console mode stopped.
echo.
echo [3/3] Restarting service...
echo ============================================================================
net start BCSrvSqlMq
echo.

echo ============================================================================
echo Test complete!
echo ============================================================================
echo.
echo If you saw:
echo   [X] All 8 tasks "Iniciada" without error 8019 = SUCCESS!
echo   [X] Error 8019 with code 2085/2043 = BUG STILL EXISTS
echo.
pause
