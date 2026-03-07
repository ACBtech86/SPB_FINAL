@echo off
REM ============================================================================
REM Add SYSTEM to mqm Group
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
title Add SYSTEM to mqm Group

cls
echo.
echo ============================================================================
echo ADD SYSTEM ACCOUNT TO MQM GROUP
echo ============================================================================
echo.

REM Check if mqm group exists
net localgroup mqm >nul 2>&1
if %errorlevel% NEQ 0 (
    echo [ERROR] The 'mqm' group does not exist!
    echo.
    echo Creating mqm group...
    net localgroup mqm /add /comment:"IBM MQ Administrators"
    if %errorlevel% EQU 0 (
        echo    OK - mqm group created
    ) else (
        echo    FAILED - Could not create mqm group
        pause
        exit /b 1
    )
)

echo Current mqm group members:
echo ============================================================================
net localgroup mqm
echo ============================================================================
echo.

echo.
echo Adding SYSTEM to mqm group...
net localgroup mqm "NT AUTHORITY\SYSTEM" /add

if %errorlevel% EQU 0 (
    echo.
    echo ============================================================================
    echo SUCCESS! SYSTEM added to mqm group
    echo ============================================================================
) else (
    echo.
    echo ============================================================================
    echo WARNING: May have failed or SYSTEM was already a member
    echo ============================================================================
)

echo.
echo.
echo Updated mqm group members:
echo ============================================================================
net localgroup mqm
echo ============================================================================
echo.

echo.
echo ============================================================================
echo NEXT STEPS:
echo ============================================================================
echo.
echo 1. Restart BCSrvSqlMq service: Scripts\RESTART-AND-CHECK.bat
echo 2. Check logs: Scripts\VER-LOG.bat
echo 3. Error 2085 should be GONE!
echo.
echo Note: Group membership changes may require a system restart to take effect.
echo       If error persists after service restart, try rebooting the system.
echo.

pause
exit /b 0
