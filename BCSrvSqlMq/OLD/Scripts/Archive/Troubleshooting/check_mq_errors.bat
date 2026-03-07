@echo off
REM ============================================================================
REM Check MQ Error Logs
REM ============================================================================

color 0E
title Check MQ Error Logs

cls
echo.
echo ============================================================================
echo MQ ERROR LOGS - Last 50 Lines
echo ============================================================================
echo.

REM Try common MQ error log locations (note: dots become ! in Windows paths)
set LOG1=C:\ProgramData\IBM\MQ\qmgrs\QM!61377677!01\errors\AMQERR01.LOG
set LOG2=C:\Program Files\IBM\MQ\qmgrs\QM!61377677!01\errors\AMQERR01.LOG
set LOG3=C:\ProgramData\IBM\MQ\errors\AMQERR01.LOG

if exist "%LOG1%" (
    echo Found: %LOG1%
    echo.
    echo Last 50 lines:
    echo ============================================================================
    powershell -Command "Get-Content '%LOG1%' -Tail 50"
    goto :found
)

if exist "%LOG2%" (
    echo Found: %LOG2%
    echo.
    echo Last 50 lines:
    echo ============================================================================
    powershell -Command "Get-Content '%LOG2%' -Tail 50"
    goto :found
)

if exist "%LOG3%" (
    echo Found: %LOG3%
    echo.
    echo Last 50 lines:
    echo ============================================================================
    powershell -Command "Get-Content '%LOG3%' -Tail 50"
    goto :found
)

echo ERROR: Could not find AMQERR01.LOG at expected locations:
echo   - %LOG1%
echo   - %LOG2%
echo   - %LOG3%
echo.
echo Try searching for it:
where /R C:\ AMQERR01.LOG 2>nul

:found
echo.
echo ============================================================================
echo.

pause
