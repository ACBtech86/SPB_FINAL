@echo off
setlocal enabledelayedexpansion
REM ============================================================================
REM Fix MQ Permissions for BCSrvSqlMq Service
REM MUST RUN AS ADMINISTRATOR with MQ admin rights
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
title Fix MQ Permissions

cls
echo.
echo ============================================================================
echo FIX MQ PERMISSIONS FOR BCSrvSqlMq
echo ============================================================================
echo.

REM Get service account
echo Checking service account...
echo.
sc qc BCSrvSqlMq | findstr "SERVICE_START_NAME"
echo.
echo.

REM Try to auto-detect
for /f "tokens=2* delims=: " %%a in ('sc qc BCSrvSqlMq ^| findstr "SERVICE_START_NAME"') do set SERVICE_USER=%%a

REM If auto-detect failed, ask user to specify
if "%SERVICE_USER%"=="" (
    echo Auto-detection failed!
    echo.
    echo Common values:
    echo   1 = LocalSystem
    echo   2 = NT AUTHORITY\NetworkService
    echo   3 = NT AUTHORITY\LocalService
    echo   4 = Specify custom user
    echo.
    set /p CHOICE="Choose option (1-4): "

    if "!CHOICE!"=="1" set MQ_USER=SYSTEM
    if "!CHOICE!"=="2" set MQ_USER=NT AUTHORITY\NetworkService
    if "!CHOICE!"=="3" set MQ_USER=NT AUTHORITY\LocalService
    if "!CHOICE!"=="4" (
        set /p MQ_USER="Enter username (e.g., DOMAIN\Username): "
    )
) else (
    REM Auto-detect worked, convert to MQ format
    if "%SERVICE_USER%"=="LocalSystem" (
        set MQ_USER=SYSTEM
    ) else if "%SERVICE_USER%"=="LocalService" (
        set MQ_USER=NT AUTHORITY\LocalService
    ) else if "%SERVICE_USER%"=="NetworkService" (
        set MQ_USER=NT AUTHORITY\NetworkService
    ) else (
        set MQ_USER=%SERVICE_USER%
    )
)

echo.
echo MQ User to grant permissions: %MQ_USER%
echo.
echo WARNING: This will grant the service user full access to:
echo   - Queue Manager: QM.61377677.01
echo   - All queues: QL.61377677.01.* and QR.61377677.01.*
echo.
echo Press ENTER to continue or CTRL+C to cancel...
pause

echo.
echo ============================================================================
echo GRANTING PERMISSIONS...
echo ============================================================================
echo.

set "PATH=%PATH%;C:\Program Files\IBM\MQ\bin;C:\Program Files\IBM\MQ\bin64"

echo [1/3] Granting Queue Manager access...
setmqaut -m QM.61377677.01 -t qmgr -p "%MQ_USER%" +connect +inq +alladm
if %errorlevel% EQU 0 (
    echo       OK - Queue Manager permissions granted
) else (
    echo       FAILED - Check if you have MQ admin rights
)
echo.

echo [2/3] Granting LOCAL queue access (QL.61377677.01.*)...
setmqaut -m QM.61377677.01 -t queue -n QL.61377677.01.** -p "%MQ_USER%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (
    echo       OK - Local queue permissions granted
) else (
    echo       FAILED - Check queue names and permissions
)
echo.

echo [3/3] Granting REMOTE queue access (QR.61377677.01.*)...
setmqaut -m QM.61377677.01 -t queue -n QR.61377677.01.** -p "%MQ_USER%" +put +get +browse +inq +dsp +set
if %errorlevel% EQU 0 (
    echo       OK - Remote queue permissions granted
) else (
    echo       FAILED - Check queue names and permissions
)
echo.

echo ============================================================================
echo COMPLETE!
echo ============================================================================
echo.
echo Permissions have been granted to: %MQ_USER%
echo.
echo NEXT STEPS:
echo   1. Restart the service: Scripts\RESTART-AND-CHECK.bat
echo   2. Check logs: Scripts\VER-LOG.bat
echo   3. Look for error 2085 to be gone
echo.

pause
exit /b 0
