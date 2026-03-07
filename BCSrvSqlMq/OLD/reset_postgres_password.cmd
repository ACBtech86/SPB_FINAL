@echo off
REM Reset PostgreSQL postgres user password
REM This script must be run as Administrator

echo ========================================
echo PostgreSQL Password Reset Script
echo ========================================
echo.
echo This will reset the 'postgres' user password.
echo.

set /p NEW_PASSWORD="Enter new password for postgres user: "

if "%NEW_PASSWORD%"=="" (
    echo Error: Password cannot be empty!
    pause
    exit /b 1
)

echo.
echo Resetting password...

"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -c "ALTER USER postgres WITH PASSWORD '%NEW_PASSWORD%';"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✅ Password reset successful!
    echo ========================================
    echo.
    echo New password: %NEW_PASSWORD%
    echo.
    echo IMPORTANT: Update BCSrvSqlMq.ini with this password:
    echo    [DataBase]
    echo    DBPassword=%NEW_PASSWORD%
    echo.
) else (
    echo.
    echo ❌ Password reset failed!
    echo.
    echo You may need to:
    echo 1. Run this script as Administrator
    echo 2. Or edit pg_hba.conf to allow trust authentication temporarily
    echo.
)

pause
