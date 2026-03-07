@echo off
REM ============================================================================
REM Check Latest Service Log for Errors
REM ============================================================================

color 0E
title Check Latest Service Log

cls
echo.
echo ============================================================================
echo CHECKING LATEST SERVICE LOG
echo ============================================================================
echo.

echo Looking for log file...
for /f %%i in ('dir /b /o-d "C:\BCSrvSqlMq\Traces\TRACE_SPB_*.log" 2^>nul ^| findstr /r ".*"') do (
    set LOGFILE=C:\BCSrvSqlMq\Traces\%%i
    goto :found
)

echo ERROR: No log files found!
pause
exit /b 1

:found
echo Found: %LOGFILE%
echo.

echo ============================================================================
echo LAST 50 LINES OF LOG:
echo ============================================================================
powershell -Command "Get-Content '%LOGFILE%' -Wait -Tail 50 | Select-Object -Last 50"
echo.

echo ============================================================================
echo CHECKING FOR ERROR 8019 (QUEUE OPEN FAILURE):
echo ============================================================================
powershell -Command "Get-Content '%LOGFILE%' -Tail 200 | Select-String '8019'"
if %errorLevel% equ 0 (
    echo.
    echo [ERROR] Found error 8019 - Queue opening failed!
    echo This means the ObjectType bug is still present.
) else (
    echo.
    echo [SUCCESS] No error 8019 found!
)
echo.

echo ============================================================================
echo CHECKING FOR "INICIADA" MESSAGES (TASKS STARTED):
echo ============================================================================
powershell -Command "Get-Content '%LOGFILE%' -Tail 200 | Select-String 'Task.*Iniciada' | Select-Object -Last 10"
echo.

echo ============================================================================
echo CHECKING FOR "TERMINADA" MESSAGES (TASKS STOPPED):
echo ============================================================================
powershell -Command "Get-Content '%LOGFILE%' -Tail 200 | Select-String '8012.*Terminada'"
if %errorLevel% equ 0 (
    echo.
    echo [WARNING] Found tasks terminating - check if they restarted successfully
) else (
    echo.
    echo [INFO] No recent task terminations found
)
echo.

pause
