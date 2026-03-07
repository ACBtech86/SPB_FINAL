@echo off
REM ============================================================================
REM BCSrvSqlMq - Instalacao ULTRA SIMPLES
REM ============================================================================

REM Vai para o diretorio do script
cd /d "%~dp0"

REM Verificar Admin
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo.
    echo [ERRO] Execute como Administrador!
    echo.
    echo Clique com BOTAO DIREITO neste arquivo e escolha:
    echo "Executar como administrador"
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo BCSrvSqlMq - Instalacao
echo ============================================================================
echo.
echo Diretorio: %CD%
echo.

REM Criar diretorios
if not exist "C:\BCSrvSqlMq" mkdir "C:\BCSrvSqlMq"
if not exist "C:\BCSrvSqlMq\Traces" mkdir "C:\BCSrvSqlMq\Traces"
if not exist "C:\BCSrvSqlMq\AuditFiles" mkdir "C:\BCSrvSqlMq\AuditFiles"

echo [1/5] Diretorios criados
echo.

REM Parar e remover servico existente
echo [2/5] Removendo servico antigo (se existir)...
net stop BCSrvSqlMq >nul 2>&1
sc delete BCSrvSqlMq >nul 2>&1
timeout /t 3 /nobreak >nul
echo       OK
echo.

REM Instalar
echo [3/5] Instalando servico...
BCSrvSqlMq.exe -i
if %errorlevel% NEQ 0 (
    echo.
    echo [ERRO] Falha na instalacao!
    echo.
    echo Verifique Event Viewer:
    echo   eventvwr.msc
    echo.
    pause
    exit /b 1
)
echo       OK
echo.

REM Aguardar
timeout /t 2 /nobreak >nul

REM Iniciar
echo [4/5] Iniciando servico...
net start BCSrvSqlMq
if %errorlevel% NEQ 0 (
    echo.
    echo [AVISO] Falha ao iniciar
    echo Verifique Event Viewer para detalhes
    echo.
)
echo.

REM Status
echo [5/5] Verificando status...
echo.
sc query BCSrvSqlMq
echo.

echo ============================================================================
echo CONCLUIDO!
echo ============================================================================
echo.
echo Logs: C:\BCSrvSqlMq\Traces\
echo Event Viewer: eventvwr.msc
echo.
pause
