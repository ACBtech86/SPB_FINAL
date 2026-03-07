@echo off
REM ============================================================================
REM BCSrvSqlMq - Check IBM MQ Queues (Debug Version)
REM Shows detailed step-by-step execution
REM ============================================================================

echo.
echo ============================================================================
echo IBM MQ Queue Verification - BCSrvSqlMq (DEBUG)
echo ============================================================================
echo.

set QMGR=QM.61377677.01

echo Queue Manager: %QMGR%
echo.

REM Step 1: Find runmqsc
echo [STEP 1] Looking for IBM MQ command 'runmqsc'...
where runmqsc >nul 2>&1
if %errorlevel% EQU 0 (
    echo [OK] Found runmqsc in PATH
) else (
    echo [WARNING] runmqsc not in PATH, trying IBM MQ default location...
    set "PATH=%PATH%;C:\Program Files\IBM\MQ\bin"
    where runmqsc >nul 2>&1
    if %errorlevel% EQU 0 (
        echo [OK] Found runmqsc in IBM MQ bin directory
    ) else (
        echo [ERROR] Cannot find runmqsc command!
        echo.
        echo IBM MQ command-line tools are not available.
        echo.
        echo Possible solutions:
        echo 1. Open "IBM MQ Command Prompt" instead of regular Command Prompt
        echo 2. Add IBM MQ bin to PATH: C:\Program Files\IBM\MQ\bin
        echo 3. Run from IBM MQ installation directory
        echo.
        goto :end_with_pause
    )
)
echo.

REM Step 2: Create MQSC script
echo [STEP 2] Creating MQSC query script...
echo DISPLAY QLOCAL('QL.61377677.01.*') > temp_check_queues.mqsc
echo DISPLAY QREMOTE('QR.61377677.01.*') >> temp_check_queues.mqsc
echo [OK] Script created: temp_check_queues.mqsc
echo.

REM Step 3: Execute query
echo [STEP 3] Querying IBM MQ Queue Manager: %QMGR%
echo.
echo ============================================================================
echo MQ OUTPUT:
echo ============================================================================

runmqsc %QMGR% < temp_check_queues.mqsc

set RESULT=%errorlevel%
echo.
echo ============================================================================
echo END MQ OUTPUT
echo ============================================================================
echo.

REM Step 4: Analyze results
if %RESULT% EQU 0 (
    echo [STEP 4] Query completed successfully
    echo.
    echo Review the output above:
    echo - If you see "AMQ8147" errors: Queues do NOT exist
    echo - If you see queue details: Queues exist!
    echo.
) else (
    echo [STEP 4] Query FAILED with error code: %RESULT%
    echo.
    echo Possible causes:
    echo - Queue Manager '%QMGR%' is not running
    echo - Queue Manager does not exist
    echo - No permission to access queue manager
    echo.
    echo To check queue manager status:
    echo   dspmq
    echo.
    echo To start queue manager:
    echo   strmqm %QMGR%
    echo.
)

REM Cleanup
del temp_check_queues.mqsc >nul 2>&1

:end_with_pause
echo.
echo ============================================================================
echo.
echo Press any key to close this window...
pause >nul
exit /b 0
