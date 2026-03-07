@echo off
REM ============================================================================
REM Test BCSrvSqlMq in Console Mode
REM Must run as Administrator!
REM ============================================================================

color 0E
title Test BCSrvSqlMq - Console Mode

cls
echo.
echo ============================================================================
echo TEST BCSrvSqlMq IN CONSOLE MODE
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

echo Stopping service if running...
net stop BCSrvSqlMq 2>nul
echo.

echo ============================================================================
echo Starting BCSrvSqlMq in Console Mode
echo ============================================================================
echo.
echo Expected output:
echo   - "BCSrvSqlMq esta rodando em modo console."
echo   - "Task MainSrv Iniciada"
echo   - "Task Monitor Iniciada"
echo   - "Task BacenREQ Iniciada"  (and 7 more tasks)
echo.
echo CRITICAL: Should see NO error 2043 or 2085!
echo.
echo Press Ctrl+C to stop the service when testing is complete.
echo ============================================================================
echo.

cd /d "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release"
BCSrvSqlMq.exe -d

echo.
echo ============================================================================
echo Console mode stopped.
echo.
echo Check the trace log to verify all tasks started successfully:
type C:\BCSrvSqlMq\Traces\TRACE_SPB_*.log | findstr /C:"Iniciada" /C:"8019"
echo.
echo If you saw error 8019, the ObjectType bug is still present!
echo ============================================================================
echo.
pause
