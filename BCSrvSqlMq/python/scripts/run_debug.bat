@echo off
REM ============================================================
REM  Start BCSrvSqlMq in debug (console) mode
REM  This runs the service directly without Windows SCM
REM ============================================================
echo Starting BCSrvSqlMq in debug mode...
echo Press Ctrl+C to stop.
echo.

cd /d %~dp0..
python -m bcsrvsqlmq -d
