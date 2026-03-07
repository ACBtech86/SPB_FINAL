@echo off
REM ============================================================================
REM BCSrvSqlMq - Restart Service and Check Logs
REM Final verification after MQ queue setup
REM ============================================================================

REM Check Admin
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
echo BCSrvSqlMq - Restart and Verification
echo ============================================================================
echo.

REM Step 1: Stop service
echo [1/4] Parando servico BCSrvSqlMq...
sc stop BCSrvSqlMq
timeout /t 5 /nobreak >nul
echo       OK
echo.

REM Step 2: Start service
echo [2/4] Iniciando servico BCSrvSqlMq...
sc start BCSrvSqlMq
if %errorlevel% NEQ 0 (
    echo       ERRO ao iniciar!
    echo.
    pause
    exit /b 1
)
echo       OK
echo.

REM Step 3: Wait for service to initialize
echo [3/4] Aguardando inicializacao (10 segundos)...
timeout /t 10 /nobreak >nul
echo       OK
echo.

REM Step 4: Check status
echo [4/4] Verificando status...
sc query BCSrvSqlMq
echo.

echo ============================================================================
echo PROXIMOS PASSOS:
echo ============================================================================
echo.
echo 1. Verificar log do servico:
echo    Scripts\VER-LOG.bat
echo.
echo 2. Procurar por:
echo    - Conexoes MQ bem-sucedidas (sem erros 2085/2092)
echo    - "Task RmtReq - Connected" ou similar
echo    - "ReadPublicKey" / "ReadPrivatKey" quando mensagens chegarem
echo.
echo 3. Se tudo OK, o servico esta pronto para producao!
echo.

pause
