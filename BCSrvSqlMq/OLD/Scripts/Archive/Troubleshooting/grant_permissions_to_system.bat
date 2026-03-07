@echo off
REM ============================================================================
REM Grant MQ Permissions to SYSTEM (LocalSystem service account)
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
title Grant MQ Permissions to SYSTEM

cls
echo.
echo ============================================================================
echo GRANT MQ PERMISSIONS TO SYSTEM
echo ============================================================================
echo.
echo This will grant the SYSTEM account (LocalSystem) access to:
echo   - Queue Manager: QM.61377677.01
echo   - All local queues: QL.61377677.01.**
echo   - All remote queues: QR.61377677.01.**
echo.
echo Press ENTER to continue or CTRL+C to cancel...
pause

echo.
echo ============================================================================
echo GRANTING PERMISSIONS...
echo ============================================================================
echo.

set "PATH=%PATH%;C:\Program Files\IBM\MQ\bin;C:\Program Files\IBM\MQ\bin64"

echo [1/3] Granting Queue Manager access to SYSTEM...
setmqaut -m QM.61377677.01 -t qmgr -p "SYSTEM" +connect +inq +alladm
if %errorlevel% EQU 0 (
    echo       OK - Queue Manager permissions granted
) else (
    echo       WARNING - May have failed, but continuing...
)
echo.

echo [2/3] Granting LOCAL queue access to SYSTEM...
setmqaut -m QM.61377677.01 -t queue -n "QL.61377677.01.**" -p "SYSTEM" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (
    echo       OK - Local queue permissions granted
) else (
    echo       WARNING - May have failed, but continuing...
)
echo.

echo [3/3] Granting REMOTE queue access to SYSTEM...
setmqaut -m QM.61377677.01 -t queue -n "QR.61377677.01.**" -p "SYSTEM" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (
    echo       OK - Remote queue permissions granted
) else (
    echo       WARNING - May have failed, but continuing...
)
echo.

echo ============================================================================
echo CHECKING PERMISSIONS...
echo ============================================================================
echo.

echo Checking permissions for SYSTEM on Queue Manager...
dspmqaut -m QM.61377677.01 -t qmgr -p "SYSTEM"
echo.

echo ============================================================================
echo COMPLETE!
echo ============================================================================
echo.
echo NEXT STEPS:
echo   1. Restart the service: Scripts\RESTART-AND-CHECK.bat
echo   2. Check logs: Scripts\VER-LOG.bat
echo   3. Error 2085 should be gone!
echo.

pause
exit /b 0
