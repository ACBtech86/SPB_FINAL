@echo off
REM ============================================================================
REM View Current Service Log
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

echo.
echo ============================================================================
echo Visualizando Log do Servico
echo ============================================================================
echo.

REM Stop service
echo Parando servico...
net stop BCSrvSqlMq
echo.

REM Wait for file to unlock
timeout /t 2 /nobreak >nul

REM Display log
echo ============================================================================
echo LOG TRACE:
echo ============================================================================
type "C:\BCSrvSqlMq\Traces\TRACE_SPB__20260301.log"
echo.
echo ============================================================================

REM Restart service
echo.
echo Reiniciando servico...
net start BCSrvSqlMq
echo.

pause
