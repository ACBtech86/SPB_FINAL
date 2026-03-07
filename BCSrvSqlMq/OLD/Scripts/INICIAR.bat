@echo off
REM ============================================================================
REM Iniciar BCSrvSqlMq - Execute como Administrador
REM ============================================================================

REM Verificar Admin
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo.
    echo [ERRO] Execute como Administrador!
    echo Clique com BOTAO DIREITO e escolha "Executar como administrador"
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo Iniciando BCSrvSqlMq
echo ============================================================================
echo.

REM Verificar se servico existe
sc query BCSrvSqlMq >nul 2>&1
if %errorlevel% NEQ 0 (
    echo [ERRO] Servico nao instalado!
    echo Execute INSTALAR.bat primeiro
    echo.
    pause
    exit /b 1
)

echo Status atual:
sc query BCSrvSqlMq
echo.

echo Iniciando servico...
net start BCSrvSqlMq

if %errorlevel% EQU 0 (
    echo.
    echo [OK] Servico iniciado com sucesso!
    echo.
    echo Aguardando 3 segundos...
    timeout /t 3 /nobreak >nul
    echo.
    echo Status atualizado:
    sc query BCSrvSqlMq
    echo.
    echo Verificando logs...
    echo.
    if exist "C:\BCSrvSqlMq\Traces\*.log" (
        echo [OK] Logs encontrados:
        dir /b /o-d "C:\BCSrvSqlMq\Traces\*.log" | head -5
        echo.
        echo Ultimas linhas do log mais recente:
        for /f "delims=" %%f in ('dir /b /o-d "C:\BCSrvSqlMq\Traces\*.log" 2^>nul') do (
            echo Arquivo: C:\BCSrvSqlMq\Traces\%%f
            type "C:\BCSrvSqlMq\Traces\%%f" | tail -20
            goto :fim_log
        )
        :fim_log
    ) else (
        echo [AVISO] Nenhum log encontrado ainda em C:\BCSrvSqlMq\Traces\
        echo.
        echo Possivel causa: Servico pode ter falhado durante inicializacao
        echo.
        echo Verificando Event Viewer...
        powershell -Command "Get-EventLog -LogName Application -Newest 5 | Format-Table -AutoSize TimeGenerated, EntryType, Source" 2>nul
    )
) else (
    echo.
    echo [ERRO] Falha ao iniciar servico!
    echo.
    echo Codigo de erro: %errorlevel%
    echo.
    echo Verificando Event Viewer para detalhes...
    echo.
    powershell -Command "Get-EventLog -LogName Application -EntryType Error -Newest 10 | Format-Table -AutoSize TimeGenerated, Source, Message -Wrap" 2>nul
    echo.
    echo Verifique tambem:
    echo 1. PostgreSQL esta rodando? (porta 5432)
    echo 2. IBM MQ esta rodando? (QM.61377677.01)
    echo 3. Todas as DLLs estao presentes?
    echo.
)

echo.
pause
