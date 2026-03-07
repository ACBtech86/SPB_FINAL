@echo off
REM ============================================================================
REM BCSrvSqlMq - IBM MQ Queue Setup
REM Creates all required queues for the service
REM ============================================================================

echo.
echo ============================================================================
echo IBM MQ Queue Setup - BCSrvSqlMq
echo ============================================================================
echo.
echo This script will create 8 IBM MQ queues for BCSrvSqlMq
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul
echo.

REM Queue Manager name
set QMGR=QM.61377677.01

echo Queue Manager: %QMGR%
echo.

REM Check if runmqsc is available
where runmqsc >nul 2>&1
if %errorlevel% NEQ 0 (
    echo [ERROR] runmqsc command not found!
    echo.
    echo IBM MQ command-line tools not in PATH.
    echo Add IBM MQ bin directory to PATH, or run from:
    echo "C:\Program Files\IBM\MQ\bin"
    echo.
    pause
    exit /b 1
)

echo Creating MQ queues...
echo.

REM Create temporary MQSC script
echo * BCSrvSqlMq - Queue Creation Script > temp_create_queues.mqsc
echo * Generated: %date% %time% >> temp_create_queues.mqsc
echo. >> temp_create_queues.mqsc

REM Define LOCAL queues
echo * Local Queues (4) >> temp_create_queues.mqsc
echo DEFINE QLOCAL('QL.61377677.01.ENTRADA.BACEN') DEFPSIST(YES) MAXDEPTH(50000) REPLACE >> temp_create_queues.mqsc
echo DEFINE QLOCAL('QL.61377677.01.SAIDA.BACEN') DEFPSIST(YES) MAXDEPTH(50000) REPLACE >> temp_create_queues.mqsc
echo DEFINE QLOCAL('QL.61377677.01.ENTRADA.IF') DEFPSIST(YES) MAXDEPTH(50000) REPLACE >> temp_create_queues.mqsc
echo DEFINE QLOCAL('QL.61377677.01.SAIDA.IF') DEFPSIST(YES) MAXDEPTH(50000) REPLACE >> temp_create_queues.mqsc
echo. >> temp_create_queues.mqsc

REM Define REMOTE queues (pointing to external systems - using transmission queue)
echo * Remote Queues (4) - pointing to remote systems >> temp_create_queues.mqsc
echo DEFINE QREMOTE('QR.61377677.01.ENTRADA.BACEN') RNAME('QL.BACEN.ENTRADA') RQMNAME('QM.BACEN') XMITQ('SYSTEM.DEFAULT.XMITQ') REPLACE >> temp_create_queues.mqsc
echo DEFINE QREMOTE('QR.61377677.01.SAIDA.BACEN') RNAME('QL.BACEN.SAIDA') RQMNAME('QM.BACEN') XMITQ('SYSTEM.DEFAULT.XMITQ') REPLACE >> temp_create_queues.mqsc
echo DEFINE QREMOTE('QR.61377677.01.ENTRADA.IF') RNAME('QL.IF.ENTRADA') RQMNAME('QM.IF') XMITQ('SYSTEM.DEFAULT.XMITQ') REPLACE >> temp_create_queues.mqsc
echo DEFINE QREMOTE('QR.61377677.01.SAIDA.IF') RNAME('QL.IF.SAIDA') RQMNAME('QM.IF') XMITQ('SYSTEM.DEFAULT.XMITQ') REPLACE >> temp_create_queues.mqsc
echo. >> temp_create_queues.mqsc

REM Display queue information
echo * Display created queues >> temp_create_queues.mqsc
echo DISPLAY QLOCAL('QL.61377677.01.*') >> temp_create_queues.mqsc
echo DISPLAY QREMOTE('QR.61377677.01.*') >> temp_create_queues.mqsc

echo Created MQSC script: temp_create_queues.mqsc
echo.
echo Running queue creation...
echo.

REM Execute MQSC script
runmqsc %QMGR% < temp_create_queues.mqsc

if %errorlevel% EQU 0 (
    echo.
    echo ============================================================================
    echo [SUCCESS] Queues created successfully!
    echo ============================================================================
    echo.
    echo Local Queues (4):
    echo   - QL.61377677.01.ENTRADA.BACEN
    echo   - QL.61377677.01.SAIDA.BACEN
    echo   - QL.61377677.01.ENTRADA.IF
    echo   - QL.61377677.01.SAIDA.IF
    echo.
    echo Remote Queues (4):
    echo   - QR.61377677.01.ENTRADA.BACEN
    echo   - QR.61377677.01.SAIDA.BACEN
    echo   - QR.61377677.01.ENTRADA.IF
    echo   - QR.61377677.01.SAIDA.IF
    echo.
    echo Queue Manager: %QMGR%
    echo.
    echo Next step: Restart BCSrvSqlMq service to connect to queues
    echo   sc stop BCSrvSqlMq
    echo   sc start BCSrvSqlMq
    echo.
) else (
    echo.
    echo [ERROR] Queue creation failed!
    echo Check the output above for errors.
    echo.
)

REM Keep the MQSC script for reference
echo MQSC script saved as: temp_create_queues.mqsc
echo.

echo.
echo Press any key to close...
pause >nul
