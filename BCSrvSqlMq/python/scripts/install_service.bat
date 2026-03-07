@echo off
REM ============================================================
REM  Install BCSrvSqlMq as a Windows Service
REM  Must be run as Administrator
REM ============================================================
echo Installing BCSrvSqlMq as Windows Service...
cd /d %~dp0..
python -m bcsrvsqlmq -i
echo.
echo To start the service: net start BCSrvSqlMq
echo To stop the service:  net stop BCSrvSqlMq
echo To uninstall:         python -m bcsrvsqlmq -u
