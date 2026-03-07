@echo off
REM ========================================
REM IBM MQ Full Setup for BCSrvSqlMq
REM Run this script as Administrator!
REM ========================================

echo ========================================
echo IBM MQ Full Setup for BCSrvSqlMq
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

REM Create MQSC script to define queues
(
echo * Local Queues - 4 filas locais
echo DEFINE QLOCAL('QL.61377677.01.ENTRADA.BACEN') DESCR('Entrada de mensagens do Bacen') DEFPSIST(YES) MAXDEPTH(5000) REPLACE
echo DEFINE QLOCAL('QL.61377677.01.SAIDA.BACEN') DESCR('Saida de mensagens para o Bacen') DEFPSIST(YES) MAXDEPTH(5000) REPLACE
echo DEFINE QLOCAL('QL.61377677.01.ENTRADA.IF') DESCR('Entrada de mensagens da IF') DEFPSIST(YES) MAXDEPTH(5000) REPLACE
echo DEFINE QLOCAL('QL.61377677.01.SAIDA.IF') DESCR('Saida de mensagens para a IF') DEFPSIST(YES) MAXDEPTH(5000) REPLACE
echo.
echo * Remote Queues - 4 filas remotas
echo DEFINE QREMOTE('QR.61377677.01.ENTRADA.BACEN') DESCR('Fila remota Bacen - Entrada') RNAME('BACEN.ENTRADA') RQMNAME('QM.BACEN') XMITQ('QL.61377677.01.SAIDA.BACEN') REPLACE
echo DEFINE QREMOTE('QR.61377677.01.SAIDA.BACEN') DESCR('Fila remota Bacen - Saida') RNAME('BACEN.SAIDA') RQMNAME('QM.BACEN') XMITQ('QL.61377677.01.SAIDA.BACEN') REPLACE
echo DEFINE QREMOTE('QR.61377677.01.ENTRADA.IF') DESCR('Fila remota IF - Entrada') RNAME('IF.ENTRADA') RQMNAME('QM.IF') XMITQ('QL.61377677.01.SAIDA.IF') REPLACE
echo DEFINE QREMOTE('QR.61377677.01.SAIDA.IF') DESCR('Fila remota IF - Saida') RNAME('IF.SAIDA') RQMNAME('QM.IF') XMITQ('QL.61377677.01.SAIDA.IF') REPLACE
echo.
echo * Verify queues
echo DISPLAY QLOCAL('QL.61377677.01.*') CURDEPTH MAXDEPTH DEFPSIST
echo DISPLAY QREMOTE('QR.61377677.01.*') RNAME RQMNAME XMITQ
echo END
) > "%TEMP%\mq_queues.mqsc"

echo [4/4] Running MQSC script to create and verify queues...
echo.
"C:\Program Files\IBM\MQ\bin\runmqsc.exe" QM.61377677.01 < "%TEMP%\mq_queues.mqsc"

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Queue Manager: QM.61377677.01
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

REM Clean up temporary script
del "%TEMP%\mq_queues.mqsc" 2>nul

echo To verify later, run: dspmq
echo.
echo Press any key to exit...
pause > nul
