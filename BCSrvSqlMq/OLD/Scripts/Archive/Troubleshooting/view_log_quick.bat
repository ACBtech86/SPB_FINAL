@echo off
REM ============================================================================
REM View Service Log (stops service briefly)
REM Must run as Administrator!
REM ============================================================================

color 0E
title View Service Log

cls
echo.
echo ============================================================================
echo VIEW SERVICE LOG
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

echo Stopping service to unlock log file...
net stop BCSrvSqlMq >nul 2>&1
timeout /t 2 /nobreak >nul

echo.
echo ============================================================================
echo LAST 100 LINES OF LOG:
echo ============================================================================
powershell -Command "Get-Content 'C:\BCSrvSqlMq\Traces\TRACE_SPB_*.log' -Tail 100"
echo.

echo ============================================================================
echo CHECKING FOR ERROR 8019:
echo ============================================================================
powershell -Command "Get-Content 'C:\BCSrvSqlMq\Traces\TRACE_SPB_*.log' -Tail 200 | Select-String '8019'"
if %errorLevel% equ 0 (
    echo.
    echo [ERROR] Found error 8019 - Queue opening failed!
    echo The ObjectType bug is still present.
) else (
    echo.
    echo [SUCCESS] No error 8019 found in last 200 lines!
)
echo.

echo ============================================================================
echo TASK STATUS:
echo ============================================================================
echo.
echo Tasks that started:
powershell -Command "Get-Content 'C:\BCSrvSqlMq\Traces\TRACE_SPB_*.log' -Tail 200 | Select-String 'Iniciada' | Select-Object -Last 10"
echo.
echo Tasks that terminated:
powershell -Command "Get-Content 'C:\BCSrvSqlMq\Traces\TRACE_SPB_*.log' -Tail 200 | Select-String '8012.*Task' | Select-Object -Last 10"
echo.

echo ============================================================================
echo Restarting service...
net start BCSrvSqlMq
echo.

pause
