@echo off
color 0B
title Checking MQ Queues - Ultra Simple Version

cls
echo.
echo ============================================================================
echo CHECKING MQ QUEUES - ULTRA SIMPLE VERSION
echo ============================================================================
echo.
echo Queue Manager: QM.61377677.01
echo.
echo Step-by-step execution - you will see EVERYTHING
echo.
echo Press ENTER to start...
pause

cls
echo.
echo [STEP 1/5] Setting up paths...
set "PATH=%PATH%;C:\Program Files\IBM\MQ\bin;C:\Program Files\IBM\MQ\bin64"
echo OK - PATH updated
echo.
timeout /t 2 /nobreak >nul

echo [STEP 2/5] Creating MQSC query script...
echo DISPLAY QLOCAL('QL.61377677.01.*') > check_temp.mqsc
echo DISPLAY QREMOTE('QR.61377677.01.*') >> check_temp.mqsc
echo OK - Script created: check_temp.mqsc
echo.
timeout /t 2 /nobreak >nul

echo [STEP 3/5] Running IBM MQ query...
echo Command: runmqsc QM.61377677.01 ^< check_temp.mqsc
echo.
echo ============================================================================
echo MQ OUTPUT START:
echo ============================================================================
echo.

runmqsc QM.61377677.01 < check_temp.mqsc

echo.
echo ============================================================================
echo MQ OUTPUT END
echo ============================================================================
echo.
timeout /t 2 /nobreak >nul

echo [STEP 4/5] Cleaning up...
del check_temp.mqsc
echo OK - Temporary files deleted
echo.

echo [STEP 5/5] COMPLETE!
echo.
echo ============================================================================
echo RESULTS:
echo ============================================================================
echo.
echo Look at the MQ OUTPUT above.
echo.
echo - If you see "AMQ8147" errors: Queues DO NOT exist (need to create them)
echo - If you see queue details: Queues EXIST (ready to use)
echo.
echo ============================================================================
echo.
echo This window will stay open until you close it.
echo.
echo Press ENTER to close...
pause
exit /b 0
