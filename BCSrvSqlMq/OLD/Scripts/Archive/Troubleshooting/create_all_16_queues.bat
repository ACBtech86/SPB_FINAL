@echo off
REM ============================================================================
REM Create All 16 Required Queues for BCSrvSqlMq
REM MUST RUN AS ADMINISTRATOR
REM ============================================================================

REM Check Admin
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo.
    echo [ERRO] Execute como Administrador!
    echo.
    pause
    exit /b 1
)

color 0A
title Create 16 MQ Queues

cls
echo.
echo ============================================================================
echo CREATE 16 REQUIRED QUEUES FOR BCSrvSqlMq
echo ============================================================================
echo.
echo This will create:
echo   - 8 Local Queues  (QL.61377677.01.*)
echo   - 8 Remote Queues (QR.61377677.01.*)
echo.
echo Queue Manager: QM.61377677.01
echo.
echo Press ENTER to continue or CTRL+C to cancel...
pause

echo.
echo ============================================================================
echo CREATING QUEUES...
echo ============================================================================
echo.

set "PATH=%PATH%;C:\Program Files\IBM\MQ\bin;C:\Program Files\IBM\MQ\bin64"

REM Create MQSC script file
set MQSC_FILE=%TEMP%\create_queues.mqsc
echo Creating MQSC commands...

(
echo * ============================================================================
echo * LOCAL QUEUES - 8 queues
echo * ============================================================================
echo DEFINE QLOCAL^('QL.61377677.01.ENTRADA.BACEN'^) DEFPSIST^(YES^) MAXDEPTH^(5000^) REPLACE
echo DEFINE QLOCAL^('QL.61377677.01.SAIDA.BACEN'^) DEFPSIST^(YES^) MAXDEPTH^(5000^) REPLACE
echo DEFINE QLOCAL^('QL.61377677.01.REPORT.BACEN'^) DEFPSIST^(YES^) MAXDEPTH^(5000^) REPLACE
echo DEFINE QLOCAL^('QL.61377677.01.SUPORTE.BACEN'^) DEFPSIST^(YES^) MAXDEPTH^(5000^) REPLACE
echo DEFINE QLOCAL^('QL.61377677.01.ENTRADA.IF'^) DEFPSIST^(YES^) MAXDEPTH^(5000^) REPLACE
echo DEFINE QLOCAL^('QL.61377677.01.SAIDA.IF'^) DEFPSIST^(YES^) MAXDEPTH^(5000^) REPLACE
echo DEFINE QLOCAL^('QL.61377677.01.REPORT.IF'^) DEFPSIST^(YES^) MAXDEPTH^(5000^) REPLACE
echo DEFINE QLOCAL^('QL.61377677.01.SUPORTE.IF'^) DEFPSIST^(YES^) MAXDEPTH^(5000^) REPLACE
echo.
echo * ============================================================================
echo * REMOTE QUEUES - 8 queues ^(pointing to BACEN^)
echo * Note: RNAME and RQMNAME should be updated for production
echo * ============================================================================
echo DEFINE QREMOTE^('QR.61377677.01.ENTRADA.BACEN'^) RNAME^('QL.61377677.01.ENTRADA.BACEN'^) RQMNAME^('QM.61377677.01'^) REPLACE
echo DEFINE QREMOTE^('QR.61377677.01.SAIDA.BACEN'^) RNAME^('QL.61377677.01.SAIDA.BACEN'^) RQMNAME^('QM.61377677.01'^) REPLACE
echo DEFINE QREMOTE^('QR.61377677.01.REPORT.BACEN'^) RNAME^('QL.61377677.01.REPORT.BACEN'^) RQMNAME^('QM.61377677.01'^) REPLACE
echo DEFINE QREMOTE^('QR.61377677.01.SUPORTE.BACEN'^) RNAME^('QL.61377677.01.SUPORTE.BACEN'^) RQMNAME^('QM.61377677.01'^) REPLACE
echo DEFINE QREMOTE^('QR.61377677.01.ENTRADA.IF'^) RNAME^('QL.61377677.01.ENTRADA.IF'^) RQMNAME^('QM.61377677.01'^) REPLACE
echo DEFINE QREMOTE^('QR.61377677.01.SAIDA.IF'^) RNAME^('QL.61377677.01.SAIDA.IF'^) RQMNAME^('QM.61377677.01'^) REPLACE
echo DEFINE QREMOTE^('QR.61377677.01.REPORT.IF'^) RNAME^('QL.61377677.01.REPORT.IF'^) RQMNAME^('QM.61377677.01'^) REPLACE
echo DEFINE QREMOTE^('QR.61377677.01.SUPORTE.IF'^) RNAME^('QL.61377677.01.SUPORTE.IF'^) RQMNAME^('QM.61377677.01'^) REPLACE
echo.
echo END
) > "%MQSC_FILE%"

echo.
echo Executing MQSC commands...
echo.

type "%MQSC_FILE%" | runmqsc QM.61377677.01

echo.
echo.
echo ============================================================================
echo VERIFICATION - Listing Created Queues
echo ============================================================================
echo.

(
echo DISPLAY QUEUE^(QL*^)
echo DISPLAY QUEUE^(QR*^)
echo END
) | runmqsc QM.61377677.01 2>nul | findstr /C:"QUEUE("

echo.
echo ============================================================================
echo COMPLETE!
echo ============================================================================
echo.
echo Next steps:
echo   1. Run: Scripts\grant_permissions_each_queue.bat
echo   2. Run: Scripts\RESTART-AND-CHECK.bat
echo   3. Run: Scripts\VER-LOG.bat
echo   4. Error 2085 should be GONE!
echo.

del "%MQSC_FILE%" >nul 2>&1

pause
exit /b 0
