@echo off
REM ============================================================================
REM Enable MQ API Trace for BCSrvSqlMq Service
REM This will show EXACTLY what the service is doing with MQ
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

color 0E
title Enable MQ Trace

cls
echo.
echo ============================================================================
echo ENABLE MQ API TRACE FOR BCSrvSqlMq
echo ============================================================================
echo.
echo This will create detailed trace files showing exactly what MQ calls
echo the service is making, including the queue names it's trying to open.
echo.
echo Trace files will be in: C:\ProgramData\IBM\MQ\trace
echo.
echo WARNING: Trace files can grow large quickly. Remember to disable after
echo collecting enough data!
echo.
echo Press ENTER to enable tracing or CTRL+C to cancel...
pause

echo.
echo Creating MQ trace configuration...
echo.

set "MQ_TRACE_DIR=C:\ProgramData\IBM\MQ\trace"

REM Create trace directory if it doesn't exist
if not exist "%MQ_TRACE_DIR%" mkdir "%MQ_TRACE_DIR%"

REM Create mqclient.ini for tracing
set MQCLIENT_INI=C:\ProgramData\IBM\MQ\mqclient.ini

echo [Trace] > "%MQCLIENT_INI%"
echo TraceLevel=6 >> "%MQCLIENT_INI%"
echo TraceFile=C:\ProgramData\IBM\MQ\trace\BCSrvSqlMq_%%p.TRC >> "%MQCLIENT_INI%"

echo.
echo Created: %MQCLIENT_INI%
echo.
type "%MQCLIENT_INI%"
echo.

echo.
echo ============================================================================
echo NEXT STEPS:
echo ============================================================================
echo.
echo 1. Restart BCSrvSqlMq service: net stop BCSrvSqlMQ ^&^& net start BCSrvSqlMQ
echo 2. Wait 30 seconds for errors to occur
echo 3. Check trace files: dir C:\ProgramData\IBM\MQ\trace
echo 4. Send trace file for analysis
echo 5. DISABLE tracing: Scripts\disable_mq_trace.bat
echo.

pause
