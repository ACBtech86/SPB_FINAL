@echo off
REM ============================================================================
REM Grant MQ Permissions Using Full NT AUTHORITY\SYSTEM Principal
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
title Grant Permissions - NT AUTHORITY\SYSTEM

cls
echo.
echo ============================================================================
echo GRANT PERMISSIONS USING FULL PRINCIPAL NAME
echo ============================================================================
echo.
echo Using: "NT AUTHORITY\SYSTEM" instead of just "SYSTEM"
echo.
echo This will grant permissions to:
echo   - Queue Manager: QM.61377677.01
echo   - All 16 queues
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
set Principal=NT AUTHORITY\SYSTEM

echo [1/17] Queue Manager: %QMgrName%
setmqaut -m %QMgrName% -t qmgr -p "%Principal%" +connect +inq +alladm
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [2/17] QL.61377677.01.ENTRADA.BACEN
setmqaut -m %QMgrName% -t queue -n "QL.61377677.01.ENTRADA.BACEN" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [3/17] QL.61377677.01.SAIDA.BACEN
setmqaut -m %QMgrName% -t queue -n "QL.61377677.01.SAIDA.BACEN" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [4/17] QL.61377677.01.REPORT.BACEN
setmqaut -m %QMgrName% -t queue -n "QL.61377677.01.REPORT.BACEN" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [5/17] QL.61377677.01.SUPORTE.BACEN
setmqaut -m %QMgrName% -t queue -n "QL.61377677.01.SUPORTE.BACEN" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [6/17] QL.61377677.01.ENTRADA.IF
setmqaut -m %QMgrName% -t queue -n "QL.61377677.01.ENTRADA.IF" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [7/17] QL.61377677.01.SAIDA.IF
setmqaut -m %QMgrName% -t queue -n "QL.61377677.01.SAIDA.IF" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [8/17] QL.61377677.01.REPORT.IF
setmqaut -m %QMgrName% -t queue -n "QL.61377677.01.REPORT.IF" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [9/17] QL.61377677.01.SUPORTE.IF
setmqaut -m %QMgrName% -t queue -n "QL.61377677.01.SUPORTE.IF" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [10/17] QR.61377677.01.ENTRADA.BACEN
setmqaut -m %QMgrName% -t queue -n "QR.61377677.01.ENTRADA.BACEN" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [11/17] QR.61377677.01.SAIDA.BACEN
setmqaut -m %QMgrName% -t queue -n "QR.61377677.01.SAIDA.BACEN" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [12/17] QR.61377677.01.REPORT.BACEN
setmqaut -m %QMgrName% -t queue -n "QR.61377677.01.REPORT.BACEN" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [13/17] QR.61377677.01.SUPORTE.BACEN
setmqaut -m %QMgrName% -t queue -n "QR.61377677.01.SUPORTE.BACEN" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [14/17] QR.61377677.01.ENTRADA.IF
setmqaut -m %QMgrName% -t queue -n "QR.61377677.01.ENTRADA.IF" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [15/17] QR.61377677.01.SAIDA.IF
setmqaut -m %QMgrName% -t queue -n "QR.61377677.01.SAIDA.IF" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [16/17] QR.61377677.01.REPORT.IF
setmqaut -m %QMgrName% -t queue -n "QR.61377677.01.REPORT.IF" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo [17/17] QR.61377677.01.SUPORTE.IF
setmqaut -m %QMgrName% -t queue -n "QR.61377677.01.SUPORTE.IF" -p "%Principal%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (echo       OK) else (echo       FAILED)

echo.
echo ============================================================================
echo COMPLETE!
echo ============================================================================
echo.
echo NEXT STEPS:
echo   1. Restart service: Scripts\RESTART-AND-CHECK.bat
echo   2. Check logs: Scripts\VER-LOG.bat
echo.

pause
exit /b 0
