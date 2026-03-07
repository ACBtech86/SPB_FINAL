@echo off
REM ============================================================================
REM Check All Queue Managers on System
REM ============================================================================

color 0B
title Check Queue Managers

cls
echo.
echo ============================================================================
echo ALL QUEUE MANAGERS ON THIS SYSTEM
echo ============================================================================
echo.

set "PATH=%PATH%;C:\Program Files\IBM\MQ\bin;C:\Program Files\IBM\MQ\bin64"

echo Running: dspmq
echo.

dspmq

echo.
echo ============================================================================
echo.
echo Check BCSrvSqlMq.ini Queue Manager setting:
echo.
findstr /C:"QueueManager" "C:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\BCSrvSqlMq.ini"
echo.
echo ============================================================================
echo.
echo IMPORTANT: The Queue Manager name in BCSrvSqlMq.ini must EXACTLY match
echo one of the Queue Managers listed above (including case and spaces).
echo.

pause
