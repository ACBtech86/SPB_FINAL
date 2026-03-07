@echo off
REM ============================================================================
REM Rebuild with REAL IBM MQ Headers (Fix for Structure Mismatch)
REM Must run as Administrator!
REM ============================================================================

color 0E
title Rebuild with Real IBM MQ Headers

cls
echo.
echo ============================================================================
echo REBUILD WITH REAL IBM MQ HEADERS
echo ============================================================================
echo.
echo CRITICAL FIX: The stub cmqc.h has been removed!
echo Now using real IBM MQ headers from:
echo   C:\Program Files\IBM\MQ\tools\c\include\
echo.
echo This fixes the MQOD structure layout mismatch that was causing
echo ObjectType to be set at the wrong memory offset!
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click this .bat file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [1/5] Stopping BCSrvSqlMq service...
echo ============================================================================
net stop BCSrvSqlMq
if %errorLevel% neq 0 (
    echo WARNING: Service stop failed or service was not running
)
timeout /t 2 /nobreak >nul
echo.

echo [2/5] Verifying stub header is removed...
echo ============================================================================
if exist "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\cmqc.h" (
    echo ERROR: Stub cmqc.h still exists!
    echo Please delete or rename it first.
    pause
    exit /b 1
)
echo Good - stub header not found.
echo.

echo [3/5] Clean rebuild with REAL IBM MQ headers...
echo ============================================================================
cd /d "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq"
del /Q build\BCSrvSqlMq.dir\Release\*.obj 2>nul
cmake --build build --config Release
if %errorLevel% neq 0 (
    echo.
    echo ============================================================================
    echo ERROR: Build failed!
    echo ============================================================================
    echo.
    pause
    exit /b 1
)
echo.

echo [4/5] Build successful! Checking binary size...
echo ============================================================================
dir build\Release\BCSrvSqlMq.exe
echo.
echo NOTE: Binary should be DIFFERENT size than before (structure layout changed)!
echo.

echo [5/5] Starting BCSrvSqlMq service...
echo ============================================================================
net start BCSrvSqlMq
if %errorLevel% neq 0 (
    echo.
    echo WARNING: Service failed to start!
    echo Test in console mode: cd build\Release ^&^& BCSrvSqlMq.exe -d
    echo.
)
echo.

echo ============================================================================
echo REBUILD COMPLETE WITH REAL IBM MQ HEADERS!
echo ============================================================================
echo.
echo What changed:
echo   [X] Removed stub cmqc.h (backup: cmqc.h.STUB_BACKUP)
echo   [X] Now using real IBM MQ 9.4.5.0 headers
echo   [X] MQOD structure now has CORRECT layout
echo   [X] ObjectType field at CORRECT offset
echo.
echo Next: Test the service!
echo   1. Check logs for NO error 8019
echo   2. All 8 tasks should stay running
echo   3. This SHOULD fix the ObjectType bug!
echo.
pause
