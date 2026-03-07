@echo off
setlocal enabledelayedexpansion

echo ============================================
echo BCSrvSqlMq - Database Setup
echo ============================================
echo.
echo This script will:
echo 1. Create database 'bcspbstr'
echo 2. Create required tables
echo.
pause

set PGPASSWORD=Rama1248
set PSQL="C:\Program Files\PostgreSQL\18\bin\psql.exe"

echo.
echo Step 1: Creating database 'bcspbstr'...
%PSQL% -U postgres -h localhost -p 5432 -c "CREATE DATABASE bcspbstr;" 2>nul

if %errorlevel% equ 0 (
    echo ✅ Database created successfully!
) else (
    echo ⚠️  Database might already exist or creation failed
    echo    Checking if database exists...
    %PSQL% -U postgres -h localhost -p 5432 -c "SELECT 1 FROM pg_database WHERE datname='bcspbstr';" -t -A | findstr "1" >nul
    if !errorlevel! equ 0 (
        echo ✅ Database 'bcspbstr' already exists - continuing...
    ) else (
        echo ❌ Failed to create database!
        pause
        exit /b 1
    )
)

echo.
echo Step 2: Creating tables in database 'bcspbstr'...
if exist "create_tables_postgresql.sql" (
    %PSQL% -U postgres -h localhost -p 5432 -d bcspbstr -f "create_tables_postgresql.sql"
    if !errorlevel! equ 0 (
        echo ✅ Tables created successfully!
    ) else (
        echo ❌ Failed to create tables!
        pause
        exit /b 1
    )
) else (
    echo ❌ Error: create_tables_postgresql.sql not found!
    echo    Make sure the file exists in the current directory.
    pause
    exit /b 1
)

echo.
echo Step 3: Verifying tables...
%PSQL% -U postgres -h localhost -p 5432 -d bcspbstr -c "\dt"

echo.
echo ============================================
echo ✅ DATABASE SETUP COMPLETE!
echo ============================================
echo.
echo Database: bcspbstr
echo Tables created:
echo   - spb_log_bacen
echo   - spb_bacen_to_local
echo   - spb_local_to_bacen
echo   - spb_controle
echo.
echo Next step: Test BCSrvSqlMq.exe
echo.
pause
