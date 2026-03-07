@echo off
color 0E
title MQ Permissions Diagnostics

cls
echo.
echo ============================================================================
echo MQ PERMISSIONS DIAGNOSTIC
echo ============================================================================
echo.

REM Step 1: Check service account
echo [STEP 1/4] Checking BCSrvSqlMq service account...
echo.
sc qc BCSrvSqlMq | findstr "SERVICE_START_NAME"
echo.
timeout /t 2 /nobreak >nul

REM Step 2: Check Queue Manager status
echo [STEP 2/4] Checking Queue Manager status...
echo.
set "PATH=%PATH%;C:\Program Files\IBM\MQ\bin;C:\Program Files\IBM\MQ\bin64"
dspmq -m QM.61377677.01
echo.
timeout /t 2 /nobreak >nul

REM Step 3: Check queue authorities for one queue
echo [STEP 3/4] Checking queue authorities for QL.61377677.01.ENTRADA.IF...
echo.
echo DISPLAY QLOCAL('QL.61377677.01.ENTRADA.IF') ALL > check_queue_auth.mqsc
runmqsc QM.61377677.01 < check_queue_auth.mqsc
del check_queue_auth.mqsc
echo.
timeout /t 2 /nobreak >nul

REM Step 4: Display authority records
echo [STEP 4/4] Checking MQ authority records...
echo.
echo Note: You may need to grant access using setmqaut command
echo.
echo Example command to grant access:
echo   setmqaut -m QM.61377677.01 -t qmgr -p [username] +connect +inq
echo   setmqaut -m QM.61377677.01 -t queue -n QL.61377677.01.* -p [username] +put +get +browse +inq
echo.

echo ============================================================================
echo RESULTS SUMMARY:
echo ============================================================================
echo.
echo 1. Check the SERVICE_START_NAME above - this is the user running the service
echo 2. Check if Queue Manager is running
echo 3. Look for any MQOPEN errors or authority failures
echo.
echo If you see permission errors, you need to grant the service user access
echo to the Queue Manager and queues.
echo.

echo Press ENTER to close...
pause >nul
exit /b 0
