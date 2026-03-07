@echo off
REM ============================================================================
REM Iniciar BCSrvSqlMq - Versao Rapida (com timeout)
REM ============================================================================

net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [ERRO] Execute como Administrador!
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo Iniciando BCSrvSqlMq (com timeout de 10 segundos)
echo ============================================================================
echo.

echo [1] Status atual:
sc query BCSrvSqlMq | find "ESTADO"
echo.

echo [2] Tentando iniciar (aguarde 10 segundos)...
echo.

REM Usar sc start com timeout ao inves de net start
sc start BCSrvSqlMq

REM Aguardar 10 segundos para o servico iniciar
echo Aguardando 10 segundos...
timeout /t 10 /nobreak >nul

echo.
echo [3] Status apos 10 segundos:
sc query BCSrvSqlMq
echo.

REM Verificar se esta rodando
sc query BCSrvSqlMq | find "RUNNING" >nul
if %errorlevel% EQU 0 (
    echo [OK] Servico RODANDO!
    echo.
    echo Verificando logs...
    if exist "C:\BCSrvSqlMq\Traces\*.log" (
        dir /b /o-d "C:\BCSrvSqlMq\Traces\*.log"
    ) else (
        echo Nenhum log ainda. Aguarde mais alguns segundos.
    )
) else (
    echo [ERRO] Servico NAO esta rodando!
    echo.
    echo Verificando Event Viewer...
    echo.
    wevtutil qe Application /c:5 /rd:true /f:text /q:"*[System[Provider[@Name='BCSrvSqlMq']]]" 2>nul
    echo.
    echo Se nao houver eventos acima, verifique manualmente:
    echo   eventvwr.msc
)

echo.
pause
