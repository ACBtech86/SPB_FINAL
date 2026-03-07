@echo off
REM ========================================
REM IBM MQ Complete Setup for Python BCSrvSqlMq
REM Creates 16 queues (8 local + 8 remote)
REM Run this script as Administrator!
REM ========================================

echo ========================================
echo IBM MQ Complete Setup for BCSrvSqlMq
echo Python Project Compatible Configuration
echo ========================================
echo.

REM Check Administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [1/4] Creating Queue Manager QM.61377677.01...
"C:\Program Files\IBM\MQ\bin\crtmqm.exe" QM.61377677.01
if %errorlevel% equ 0 (
    echo Queue Manager created successfully.
) else (
    echo Warning: Queue Manager may already exist (error %errorlevel%).
)
echo.

echo [2/4] Starting Queue Manager QM.61377677.01...
"C:\Program Files\IBM\MQ\bin\strmqm.exe" QM.61377677.01
if %errorlevel% equ 0 (
    echo Queue Manager started successfully.
) else (
    echo Warning: Queue Manager may already be running (error %errorlevel%).
)
echo.

echo [3/4] Creating MQSC queue definitions...

REM Create MQSC script to define ALL 16 queues
(
echo * ====================================================================
echo * Local Queues - 8 filas locais (BACEN + IF)
echo * ====================================================================
echo.
echo * BACEN Local Queues (4)
echo DEFINE QLOCAL('QL.61377677.01.ENTRADA.BACEN') DESCR('Bacen - Entrada/Request') DEFPSIST(YES) MAXDEPTH(5000) REPLACE
echo DEFINE QLOCAL('QL.61377677.01.SAIDA.BACEN') DESCR('Bacen - Saida/Response') DEFPSIST(YES) MAXDEPTH(5000) REPLACE
echo DEFINE QLOCAL('QL.61377677.01.REPORT.BACEN') DESCR('Bacen - Report') DEFPSIST(YES) MAXDEPTH(5000) REPLACE
echo DEFINE QLOCAL('QL.61377677.01.SUPORTE.BACEN') DESCR('Bacen - Suporte') DEFPSIST(YES) MAXDEPTH(5000) REPLACE
echo.
echo * IF Local Queues (4)
echo DEFINE QLOCAL('QL.61377677.01.ENTRADA.IF') DESCR('IF - Entrada/Request') DEFPSIST(YES) MAXDEPTH(5000) REPLACE
echo DEFINE QLOCAL('QL.61377677.01.SAIDA.IF') DESCR('IF - Saida/Response') DEFPSIST(YES) MAXDEPTH(5000) REPLACE
echo DEFINE QLOCAL('QL.61377677.01.REPORT.IF') DESCR('IF - Report') DEFPSIST(YES) MAXDEPTH(5000) REPLACE
echo DEFINE QLOCAL('QL.61377677.01.SUPORTE.IF') DESCR('IF - Suporte') DEFPSIST(YES) MAXDEPTH(5000) REPLACE
echo.
echo * ====================================================================
echo * Remote Queues - 8 filas remotas (BACEN + IF)
echo * ====================================================================
echo.
echo * BACEN Remote Queues (4)
echo DEFINE QREMOTE('QR.61377677.01.ENTRADA.BACEN') DESCR('Bacen Remote - Entrada') RNAME('BACEN.ENTRADA') RQMNAME('QM.BACEN') XMITQ('QL.61377677.01.SAIDA.BACEN') REPLACE
echo DEFINE QREMOTE('QR.61377677.01.SAIDA.BACEN') DESCR('Bacen Remote - Saida') RNAME('BACEN.SAIDA') RQMNAME('QM.BACEN') XMITQ('QL.61377677.01.SAIDA.BACEN') REPLACE
echo DEFINE QREMOTE('QR.61377677.01.REPORT.BACEN') DESCR('Bacen Remote - Report') RNAME('BACEN.REPORT') RQMNAME('QM.BACEN') XMITQ('QL.61377677.01.SAIDA.BACEN') REPLACE
echo DEFINE QREMOTE('QR.61377677.01.SUPORTE.BACEN') DESCR('Bacen Remote - Suporte') RNAME('BACEN.SUPORTE') RQMNAME('QM.BACEN') XMITQ('QL.61377677.01.SAIDA.BACEN') REPLACE
echo.
echo * IF Remote Queues (4)
echo DEFINE QREMOTE('QR.61377677.01.ENTRADA.IF') DESCR('IF Remote - Entrada') RNAME('IF.ENTRADA') RQMNAME('QM.IF') XMITQ('QL.61377677.01.SAIDA.IF') REPLACE
echo DEFINE QREMOTE('QR.61377677.01.SAIDA.IF') DESCR('IF Remote - Saida') RNAME('IF.SAIDA') RQMNAME('QM.IF') XMITQ('QL.61377677.01.SAIDA.IF') REPLACE
echo DEFINE QREMOTE('QR.61377677.01.REPORT.IF') DESCR('IF Remote - Report') RNAME('IF.REPORT') RQMNAME('QM.IF') XMITQ('QL.61377677.01.SAIDA.IF') REPLACE
echo DEFINE QREMOTE('QR.61377677.01.SUPORTE.IF') DESCR('IF Remote - Suporte') RNAME('IF.SUPORTE') RQMNAME('QM.IF') XMITQ('QL.61377677.01.SAIDA.IF') REPLACE
echo.
echo * ====================================================================
echo * Verification
echo * ====================================================================
echo DISPLAY QLOCAL('QL.61377677.01.*') CURDEPTH MAXDEPTH DEFPSIST
echo DISPLAY QREMOTE('QR.61377677.01.*') RNAME RQMNAME XMITQ
echo END
) > "%TEMP%\mq_queues_complete.mqsc"

echo [4/4] Running MQSC script to create and verify queues...
echo.
"C:\Program Files\IBM\MQ\bin\runmqsc.exe" QM.61377677.01 < "%TEMP%\mq_queues_complete.mqsc"

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Queue Manager: QM.61377677.01
echo.
echo BACEN Local Queues (4):
echo   - QL.61377677.01.ENTRADA.BACEN  (Request/Req)
echo   - QL.61377677.01.SAIDA.BACEN    (Response/Rsp)
echo   - QL.61377677.01.REPORT.BACEN   (Report/Rep)
echo   - QL.61377677.01.SUPORTE.BACEN  (Support/Sup)
echo.
echo IF Local Queues (4):
echo   - QL.61377677.01.ENTRADA.IF     (Request/Req)
echo   - QL.61377677.01.SAIDA.IF       (Response/Rsp)
echo   - QL.61377677.01.REPORT.IF      (Report/Rep)
echo   - QL.61377677.01.SUPORTE.IF     (Support/Sup)
echo.
echo BACEN Remote Queues (4):
echo   - QR.61377677.01.ENTRADA.BACEN  (Request)
echo   - QR.61377677.01.SAIDA.BACEN    (Response)
echo   - QR.61377677.01.REPORT.BACEN   (Report)
echo   - QR.61377677.01.SUPORTE.BACEN  (Support)
echo.
echo IF Remote Queues (4):
echo   - QR.61377677.01.ENTRADA.IF     (Request)
echo   - QR.61377677.01.SAIDA.IF       (Response)
echo   - QR.61377677.01.REPORT.IF      (Report)
echo   - QR.61377677.01.SUPORTE.IF     (Support)
echo.
echo Total: 16 queues (8 local + 8 remote)
echo.

REM Clean up temporary script
del "%TEMP%\mq_queues_complete.mqsc" 2>nul

echo Compatible with BCSrvSqlMq.ini configuration
echo To verify later, run: dspmq
echo.
echo Press any key to exit...
pause > nul
