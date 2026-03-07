@echo off
REM ========================================
REM IBM MQ Complete Setup for FINVEST ISPB 36266751
REM Deletes old QM.61377677.01 and creates QM.36266751.01
REM Creates 8 Bacen queues (4 local + 4 remote)
REM Run this script as Administrator!
REM ========================================

echo ========================================
echo IBM MQ Complete Setup for FINVEST (ISPB 36266751)
echo ========================================
echo.
echo Press any key to start...
pause
echo.

REM Note: This script requires Administrator privileges
REM If you get permission errors, right-click and select "Run as administrator"
echo.

REM Check if IBM MQ is installed
if not exist "C:\Program Files\IBM\MQ\bin\dspmq.exe" (
    echo ERROR: IBM MQ not found at C:\Program Files\IBM\MQ
    echo Please install IBM MQ first.
    echo.
    pause
    exit /b 1
)
echo IBM MQ installation found.
echo.

echo Starting IBM MQ service (MQ_FinvestDTVM)...
net start "MQ_FinvestDTVM"
if %errorlevel% neq 0 (
    echo Warning: Service may already be running or failed to start
    echo Trying to start it manually...
    sc start MQ_FinvestDTVM
)
echo.
timeout /t 3 /nobreak >nul

echo [1/6] Checking for old queue manager QM.61377677.01...
echo Running: dspmq -m QM.61377677.01
echo.
"C:\Program Files\IBM\MQ\bin\dspmq.exe" -m QM.61377677.01 2>&1
set DSPMQ_EXIT=%errorlevel%
echo.
echo Exit code from dspmq: %DSPMQ_EXIT%
echo.
if "%DSPMQ_EXIT%"=="0" (
    echo Found old queue manager QM.61377677.01
    echo.
    echo [2/6] Stopping old queue manager...
    "C:\Program Files\IBM\MQ\bin\endmqm.exe" -i QM.61377677.01
    if %errorlevel% neq 0 (
        echo ERROR: Failed to stop queue manager!
        pause
    )
    echo.
    echo Waiting 2 seconds...
    timeout /t 15 /nobreak >nul
    echo.
    echo [3/6] Deleting old queue manager...
    "C:\Program Files\IBM\MQ\bin\dltmqm.exe" QM.61377677.01
    if %errorlevel% neq 0 (
        echo ERROR: Failed to delete queue manager!
        echo Press any key to continue anyway...
        pause
    ) else (
        echo Deletion complete.
    )
) else (
    echo Old queue manager QM.61377677.01 not found - this is OK, will create new one.
)
echo.
echo Press any key to continue...
pause
echo.

echo [4/6] Creating Queue Manager QM.36266751.01...
"C:\Program Files\IBM\MQ\bin\crtmqm.exe" QM.36266751.01
if %errorlevel% equ 0 (
    echo Queue Manager created successfully.
) else (
    echo.
    echo ERROR: Failed to create queue manager! (error %errorlevel%)
    echo Press any key to see if you can continue...
    pause
)
echo.
echo Press any key to continue...
pause
echo.

echo [5/6] Starting Queue Manager QM.36266751.01...
"C:\Program Files\IBM\MQ\bin\strmqm.exe" QM.36266751.01
if %errorlevel% equ 0 (
    echo Queue Manager started successfully.
) else (
    echo.
    echo ERROR: Failed to start queue manager! (error %errorlevel%)
    echo Press any key to try queue creation anyway...
    pause
)
echo.
pause
echo.

echo [6/6] Creating MQSC queue definitions and running script...

REM Create MQSC script - 8 Bacen queues only
set MQSC_FILE=%~dp0mq_36266751.mqsc

echo Creating MQSC file at: %MQSC_FILE%
echo.

(
echo * ====================================================================
echo * FINVEST ISPB: 36266751
echo * BACEN ISPB:   00038166
echo * ====================================================================
echo(
echo * Local Queues - Messages FROM Bacen TO Finvest ^(4^)
echo DEFINE QLOCAL^('QL.REQ.00038166.36266751.01'^) DESCR^('Bacen Request to Finvest'^) DEFPSIST^(YES^) MAXDEPTH^(5000^) REPLACE
echo DEFINE QLOCAL^('QL.RSP.00038166.36266751.01'^) DESCR^('Bacen Response to Finvest'^) DEFPSIST^(YES^) MAXDEPTH^(5000^) REPLACE
echo DEFINE QLOCAL^('QL.REP.00038166.36266751.01'^) DESCR^('Bacen Report to Finvest'^) DEFPSIST^(YES^) MAXDEPTH^(5000^) REPLACE
echo DEFINE QLOCAL^('QL.SUP.00038166.36266751.01'^) DESCR^('Bacen Support to Finvest'^) DEFPSIST^(YES^) MAXDEPTH^(5000^) REPLACE
echo(
echo * Remote Queues - Messages FROM Finvest TO Bacen ^(4^)
echo DEFINE QREMOTE^('QR.REQ.36266751.00038166.01'^) DESCR^('Finvest Request to Bacen'^) RNAME^('QL.REQ.36266751.00038166.01'^) RQMNAME^('QM.BACEN'^) XMITQ^('QL.RSP.00038166.36266751.01'^) REPLACE
echo DEFINE QREMOTE^('QR.RSP.36266751.00038166.01'^) DESCR^('Finvest Response to Bacen'^) RNAME^('QL.RSP.36266751.00038166.01'^) RQMNAME^('QM.BACEN'^) XMITQ^('QL.RSP.00038166.36266751.01'^) REPLACE
echo DEFINE QREMOTE^('QR.REP.36266751.00038166.01'^) DESCR^('Finvest Report to Bacen'^) RNAME^('QL.REP.36266751.00038166.01'^) RQMNAME^('QM.BACEN'^) XMITQ^('QL.RSP.00038166.36266751.01'^) REPLACE
echo DEFINE QREMOTE^('QR.SUP.36266751.00038166.01'^) DESCR^('Finvest Support to Bacen'^) RNAME^('QL.SUP.36266751.00038166.01'^) RQMNAME^('QM.BACEN'^) XMITQ^('QL.RSP.00038166.36266751.01'^) REPLACE
echo(
echo * ====================================================================
echo * TCP Listener and SVRCONN Channel for pymqi client connectivity
echo * ====================================================================
echo(
echo * Listener on port 1414
echo DEFINE LISTENER^('FINVEST.LISTENER'^) TRPTYPE^(TCP^) PORT^(1414^) CONTROL^(QMGR^) REPLACE
echo START LISTENER^('FINVEST.LISTENER'^)
echo(
echo * Server-connection channel for pymqi
echo DEFINE CHANNEL^('FINVEST.SVRCONN'^) CHLTYPE^(SVRCONN^) TRPTYPE^(TCP^) MCAUSER^(''^) REPLACE
echo(
echo * Disable CHLAUTH blocking for local development
echo ALTER QMGR CHLAUTH^(DISABLED^)
echo(
echo * Allow connections without password check ^(local dev only^)
echo ALTER AUTHINFO^('SYSTEM.DEFAULT.AUTHINFO.IDPWOS'^) AUTHTYPE^(IDPWOS^) CHCKCLNT^(OPTIONAL^)
echo REFRESH SECURITY TYPE^(CONNAUTH^)
echo(
echo * Verification
echo DISPLAY LSSTATUS^('FINVEST.LISTENER'^) STATUS
echo DISPLAY CHANNEL^('FINVEST.SVRCONN'^) CHLTYPE TRPTYPE
echo DISPLAY QLOCAL^('QL.REQ.00038166.36266751.01'^) CURDEPTH MAXDEPTH DEFPSIST
echo DISPLAY QLOCAL^('QL.RSP.00038166.36266751.01'^) CURDEPTH MAXDEPTH DEFPSIST
echo DISPLAY QLOCAL^('QL.REP.00038166.36266751.01'^) CURDEPTH MAXDEPTH DEFPSIST
echo DISPLAY QLOCAL^('QL.SUP.00038166.36266751.01'^) CURDEPTH MAXDEPTH DEFPSIST
echo DISPLAY QREMOTE^('QR.REQ.36266751.00038166.01'^) RNAME RQMNAME
echo DISPLAY QREMOTE^('QR.RSP.36266751.00038166.01'^) RNAME RQMNAME
echo DISPLAY QREMOTE^('QR.REP.36266751.00038166.01'^) RNAME RQMNAME
echo DISPLAY QREMOTE^('QR.SUP.36266751.00038166.01'^) RNAME RQMNAME
echo END
) > "%MQSC_FILE%"

if not exist "%MQSC_FILE%" (
    echo ERROR: Failed to create MQSC file!
    echo.
    pause
    exit /b 1
)

echo.
echo MQSC script created successfully. Content:
echo ========================================
type "%MQSC_FILE%"
echo ========================================
echo.
echo Press any key to run MQSC script...
pause
echo.

echo Running MQSC script to create queues...
"C:\Program Files\IBM\MQ\bin\runmqsc.exe" QM.36266751.01 < "%MQSC_FILE%"
set MQSC_EXIT=%errorlevel%
echo.
echo Exit code from runmqsc: %MQSC_EXIT%
echo.
if %MQSC_EXIT% equ 0 (
    echo Queue creation complete! All commands successful.
) else if %MQSC_EXIT% equ 10 (
    echo Queue creation complete with warnings (exit code 10).
    echo This is normal if listener was already running.
) else (
    echo ERROR: Failed to create queues! (error %MQSC_EXIT%)
    echo Press any key to see results...
    pause
)

echo.
pause
echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Queue Manager: QM.36266751.01
echo Listener:      FINVEST.LISTENER (TCP port 1414)
echo Channel:       FINVEST.SVRCONN  (for pymqi client)
echo.
echo Local Queues (4) - FROM Bacen TO Finvest:
echo   - QL.REQ.00038166.36266751.01  (Request)
echo   - QL.RSP.00038166.36266751.01  (Response)
echo   - QL.REP.00038166.36266751.01  (Report)
echo   - QL.SUP.00038166.36266751.01  (Support)
echo.
echo Remote Queues (4) - FROM Finvest TO Bacen:
echo   - QR.REQ.36266751.00038166.01  (Request)
echo   - QR.RSP.36266751.00038166.01  (Response)
echo   - QR.REP.36266751.00038166.01  (Report)
echo   - QR.SUP.36266751.00038166.01  (Support)
echo.
echo Total: 8 queues + 1 listener + 1 SVRCONN channel
echo.

REM Clean up
if exist "%MQSC_FILE%" del "%MQSC_FILE%" 2>nul

echo Next step: Update BCSrvSqlMq.ini with queue names
echo.
pause
