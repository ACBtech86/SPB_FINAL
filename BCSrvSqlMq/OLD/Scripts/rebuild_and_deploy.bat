@echo off
REM ============================================================================
REM Rebuild and Deploy BCSrvSqlMq Service
REM Must run as Administrator!
REM ============================================================================

color 0E
title Rebuild and Deploy BCSrvSqlMq

cls
echo.
echo ============================================================================
echo REBUILD AND DEPLOY BCSrvSqlMq SERVICE
echo ============================================================================
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

echo [1/6] Stopping BCSrvSqlMq service...
echo ============================================================================
net stop BCSrvSqlMq
if %errorLevel% neq 0 (
    echo WARNING: Service stop failed or service was not running
)
echo.

echo [2/6] Deleting old object files...
echo ============================================================================
cd /d "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq"
del /Q build\BCSrvSqlMq.dir\Release\*.obj 2>nul
echo Done.
echo.

echo [3/6] Rebuilding project...
echo ============================================================================
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

echo [4/6] Build successful!
echo ============================================================================
dir build\Release\BCSrvSqlMq.exe
echo.

echo [5/6] Starting BCSrvSqlMq service...
echo ============================================================================
net start BCSrvSqlMq
if %errorLevel% neq 0 (
    echo.
    echo WARNING: Service failed to start! You can test in console mode with:
    echo   cd build\Release
    echo   BCSrvSqlMq.exe -d
    echo.
)
echo.

echo [6/6] Checking service status...
echo ============================================================================
sc query BCSrvSqlMq
echo.

echo ============================================================================
echo REBUILD AND DEPLOYMENT COMPLETE!
echo ============================================================================
echo.
echo Next steps:
echo   1. Check service logs: C:\BCSrvSqlMq\Traces\TRACE_SPB_*.log
echo   2. Look for "Task * Iniciada" messages for all 8 tasks
echo   3. Verify NO error 2043/2085 messages appear
echo.
pause
