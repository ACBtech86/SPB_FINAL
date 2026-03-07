@echo off
REM ============================================================================
REM Check mqm Group Membership
REM ============================================================================

color 0B
title Check mqm Group

cls
echo.
echo ============================================================================
echo CHECK MQM GROUP MEMBERSHIP
echo ============================================================================
echo.

echo [1] Checking if 'mqm' group exists...
echo.
net localgroup mqm >nul 2>&1
if %errorlevel% EQU 0 (
    echo    Found: mqm group exists
    echo.
    echo [2] Members of 'mqm' group:
    echo ============================================================================
    net localgroup mqm
    echo ============================================================================
) else (
    echo    NOT FOUND: mqm group does not exist on this system
    echo.
    echo    This might be OK if MQ uses a different group name.
    echo    Common alternatives: Administrators, mqm, MQAdmins
)

echo.
echo.
echo [3] Checking BCSrvSqlMq service account:
echo ============================================================================
sc qc BCSrvSqlMq | findstr "SERVICE_START_NAME"
echo ============================================================================
echo.

echo.
echo [4] Checking if SYSTEM is in Administrators group:
echo ============================================================================
net localgroup Administrators | findstr /I "SYSTEM"
if %errorlevel% EQU 0 (
    echo    YES - SYSTEM is in Administrators group
) else (
    echo    NO - SYSTEM is NOT in Administrators group
)
echo ============================================================================
echo.

echo.
echo ============================================================================
echo RECOMMENDATION:
echo ============================================================================
echo.
echo If mqm group exists and SYSTEM is NOT a member:
echo    Run: Scripts\add_system_to_mqm.bat (as Administrator)
echo.
echo If mqm group does NOT exist:
echo    The service account needs to be in the Administrators group OR
echo    you need to create the mqm group and add the service account to it.
echo.

pause
