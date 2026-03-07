@echo off
color 0B
title Service Account Info

cls
echo.
echo ============================================================================
echo BCSrvSqlMq SERVICE ACCOUNT
echo ============================================================================
echo.

echo Full service configuration:
echo.
sc qc BCSrvSqlMq
echo.

echo ============================================================================
echo.
echo Look for the line:
echo   SERVICE_START_NAME     : [username]
echo.
echo This shows which user account runs the service.
echo.
echo Common values:
echo   - LocalSystem          = Highest privileges, use "SYSTEM" for MQ
echo   - NT AUTHORITY\NetworkService
echo   - NT AUTHORITY\LocalService
echo   - [DOMAIN\Username]    = Specific user account
echo.
echo ============================================================================
echo.

pause
