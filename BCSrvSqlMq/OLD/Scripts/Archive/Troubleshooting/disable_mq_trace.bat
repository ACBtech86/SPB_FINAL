@echo off
REM ============================================================================
REM Disable MQ API Trace
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

color 0A
title Disable MQ Trace

cls
echo.
echo ============================================================================
echo DISABLE MQ API TRACE
echo ============================================================================
echo.

set MQCLIENT_INI=C:\ProgramData\IBM\MQ\mqclient.ini

if exist "%MQCLIENT_INI%" (
    echo Removing: %MQCLIENT_INI%
    del "%MQCLIENT_INI%"
    echo.
    echo MQ tracing disabled!
) else (
    echo MQ tracing was not enabled (mqclient.ini not found)
)

echo.
echo ============================================================================
echo.
echo Restart service to apply: net stop BCSrvSqlMQ ^&^& net start BCSrvSqlMQ
echo.

pause
