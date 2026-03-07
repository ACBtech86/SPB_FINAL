@echo off
REM ============================================================================
REM Check Current MQ Permissions for SYSTEM
REM ============================================================================

color 0E
title Check MQ Permissions

cls
echo.
echo ============================================================================
echo CHECK CURRENT MQ PERMISSIONS
echo ============================================================================
echo.

set "PATH=%PATH%;C:\Program Files\IBM\MQ\bin;C:\Program Files\IBM\MQ\bin64"

echo [1] Checking permissions for "SYSTEM":
echo ============================================================================
echo.
echo Queue Manager:
dspmqaut -m QM.61377677.01 -t qmgr -p "SYSTEM"
echo.

echo Sample Queue (QL.61377677.01.ENTRADA.BACEN):
dspmqaut -m QM.61377677.01 -t queue -n "QL.61377677.01.ENTRADA.BACEN" -p "SYSTEM"
echo.

echo ============================================================================
echo.
echo [2] Checking permissions for "NT AUTHORITY\SYSTEM":
echo ============================================================================
echo.
echo Queue Manager:
dspmqaut -m QM.61377677.01 -t qmgr -p "NT AUTHORITY\SYSTEM"
echo.

echo Sample Queue (QL.61377677.01.ENTRADA.BACEN):
dspmqaut -m QM.61377677.01 -t queue -n "QL.61377677.01.ENTRADA.BACEN" -p "NT AUTHORITY\SYSTEM"
echo.

echo ============================================================================
echo.

pause
