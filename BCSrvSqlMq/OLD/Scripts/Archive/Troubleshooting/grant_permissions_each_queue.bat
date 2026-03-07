@echo off
REM ============================================================================
REM Grant MQ Permissions to SYSTEM for Each Queue Individually
REM Windows MQ doesn't support wildcards like Unix, need individual queues
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
title Grant MQ Permissions - Individual Queues

cls
echo.
echo ============================================================================
echo GRANT MQ PERMISSIONS TO EACH QUEUE INDIVIDUALLY
echo ============================================================================
echo.
echo This will grant SYSTEM account permissions to:
echo   - Queue Manager: QM.61377677.01
echo   - 8 Local Queues (QL.61377677.01.*)
echo   - 8 Remote Queues (QR.61377677.01.*)
echo.
echo Total: 16 individual queue permissions + Queue Manager
echo.
echo Press ENTER to continue or CTRL+C to cancel...
pause

echo.
echo ============================================================================
echo GRANTING PERMISSIONS...
echo ============================================================================
echo.

set "PATH=%PATH%;C:\Program Files\IBM\MQ\bin;C:\Program Files\IBM\MQ\bin64"
set QMgrName=QM.61377677.01
set Principal=SYSTEM

REM Queue Manager permissions
echo [1/17] Queue Manager: %QMgrName%
setmqaut -m %QMgrName% -t qmgr -p "%Principal%" +connect +inq +alladm
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

REM Local Queues
echo [2/17] QL.61377677.01.ENTRADA.BACEN
setmqaut -m %QMgrName% -t queue -n "QL.61377677.01.ENTRADA.BACEN" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [3/17] QL.61377677.01.ENTRADA.IF
setmqaut -m %QMgrName% -t queue -n "QL.61377677.01.ENTRADA.IF" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [4/17] QL.61377677.01.SAIDA.BACEN
setmqaut -m %QMgrName% -t queue -n "QL.61377677.01.SAIDA.BACEN" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [5/17] QL.61377677.01.SAIDA.IF
setmqaut -m %QMgrName% -t queue -n "QL.61377677.01.SAIDA.IF" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [6/17] QL.61377677.01.REPORT.BACEN
setmqaut -m %QMgrName% -t queue -n "QL.61377677.01.REPORT.BACEN" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [7/17] QL.61377677.01.REPORT.IF
setmqaut -m %QMgrName% -t queue -n "QL.61377677.01.REPORT.IF" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [8/17] QL.61377677.01.SUPORTE.BACEN
setmqaut -m %QMgrName% -t queue -n "QL.61377677.01.SUPORTE.BACEN" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [9/17] QL.61377677.01.SUPORTE.IF
setmqaut -m %QMgrName% -t queue -n "QL.61377677.01.SUPORTE.IF" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

REM Remote Queues
echo [10/17] QR.61377677.01.ENTRADA.BACEN
setmqaut -m %QMgrName% -t queue -n "QR.61377677.01.ENTRADA.BACEN" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [11/17] QR.61377677.01.ENTRADA.IF
setmqaut -m %QMgrName% -t queue -n "QR.61377677.01.ENTRADA.IF" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [12/17] QR.61377677.01.SAIDA.BACEN
setmqaut -m %QMgrName% -t queue -n "QR.61377677.01.SAIDA.BACEN" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [13/17] QR.61377677.01.SAIDA.IF
setmqaut -m %QMgrName% -t queue -n "QR.61377677.01.SAIDA.IF" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [14/17] QR.61377677.01.REPORT.BACEN
setmqaut -m %QMgrName% -t queue -n "QR.61377677.01.REPORT.BACEN" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [15/17] QR.61377677.01.REPORT.IF
setmqaut -m %QMgrName% -t queue -n "QR.61377677.01.REPORT.IF" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [16/17] QR.61377677.01.SUPORTE.BACEN
setmqaut -m %QMgrName% -t queue -n "QR.61377677.01.SUPORTE.BACEN" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [17/17] QR.61377677.01.SUPORTE.IF
setmqaut -m %QMgrName% -t queue -n "QR.61377677.01.SUPORTE.IF" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo.
echo ============================================================================
echo COMPLETE!
echo ============================================================================
echo.
echo All 16 queues + Queue Manager have been granted permissions.
echo.
echo NEXT STEPS:
echo   1. Restart service: Scripts\RESTART-AND-CHECK.bat
echo   2. Check logs: Scripts\VER-LOG.bat
echo   3. Error 2085 should NOW be gone!
echo.

pause
exit /b 0
