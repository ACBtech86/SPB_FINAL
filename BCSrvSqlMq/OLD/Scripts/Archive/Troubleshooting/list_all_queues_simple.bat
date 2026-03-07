@echo off
REM ============================================================================
REM List ALL Queues - Simple Version
REM ============================================================================

color 0C
title List All Queues

cls
echo.
echo ============================================================================
echo ALL QUEUES IN QUEUE MANAGER QM.61377677.01
echo ============================================================================
echo.

set "PATH=%PATH%;C:\Program Files\IBM\MQ\bin;C:\Program Files\IBM\MQ\bin64"

echo Running: DISPLAY QUEUE(*)
echo.

REM Create temporary MQSC script
set MQSC_TEMP=%TEMP%\list_queues.mqsc
echo DISPLAY QUEUE(*) > "%MQSC_TEMP%"
echo END >> "%MQSC_TEMP%"

echo MQSC Commands:
type "%MQSC_TEMP%"
echo.
echo ============================================================================
echo.

runmqsc QM.61377677.01 < "%MQSC_TEMP%"

del "%MQSC_TEMP%" >nul 2>&1

echo.
echo ============================================================================
echo.

pause
