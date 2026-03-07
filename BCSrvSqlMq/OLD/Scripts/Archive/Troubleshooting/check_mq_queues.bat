@echo off
REM ============================================================================
REM BCSrvSqlMq - Check IBM MQ Queues
REM Verifies if all required queues exist
REM ============================================================================

echo.
echo ============================================================================
echo IBM MQ Queue Verification - BCSrvSqlMq
echo ============================================================================
echo.

set QMGR=QM.61377677.01

echo Queue Manager: %QMGR%
echo.
echo This script will check if the required queues exist.
echo Press any key to continue...
pause >nul
echo.

REM Check if runmqsc is available
where runmqsc >nul 2>&1
if %errorlevel% NEQ 0 (
    echo [WARNING] runmqsc command not found in PATH
    echo.
    echo Trying default IBM MQ location...
    set PATH=%PATH%;C:\Program Files\IBM\MQ\bin
    where runmqsc >nul 2>&1
    if %errorlevel% NEQ 0 (
        echo.
        echo [ERROR] runmqsc still not found!
        echo.
        echo Please run this from a command prompt with IBM MQ tools in PATH
        echo Or open: IBM MQ Command Prompt
        echo.
        pause
        exit /b 1
    )
)

echo Checking queues...
echo.

REM Create temporary MQSC script to display queues
echo DISPLAY QLOCAL('QL.61377677.01.*') > temp_check_queues.mqsc
echo DISPLAY QREMOTE('QR.61377677.01.*') >> temp_check_queues.mqsc

REM Execute MQSC script
runmqsc %QMGR% < temp_check_queues.mqsc

echo.
echo ============================================================================
echo.

if %errorlevel% EQU 0 (
    echo Check complete! Review the output above.
    echo.
    echo If you see "AMQ8147: WebSphere MQ queue not found":
    echo   Run: setup_mq_queues.bat to create the queues
    echo.
) else (
    echo [ERROR] Failed to connect to queue manager: %QMGR%
    echo.
    echo Possible issues:
    echo   - Queue manager not running
    echo   - Incorrect queue manager name
    echo   - Permission issues
    echo.
)

del temp_check_queues.mqsc >nul 2>&1

echo.
echo Press any key to close...
pause >nul
