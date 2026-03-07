@echo off
REM ============================================================================
REM BCSrvSqlMq - Instalacao Simples (SEM testes complexos)
REM ============================================================================
REM Execute como Administrador
REM ============================================================================

REM Ir para o diretorio do script
cd /d "%~dp0"

echo.
echo ============================================================================
echo BCSrvSqlMq - Instalacao Simples
echo ============================================================================
echo.
echo Diretorio: %CD%
echo.

REM Verificar Admin
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [ERRO] Execute como Administrador!
    echo Clique com botao direito e selecione "Executar como Administrador"
    echo.
    pause
    exit /b 1
)

echo [OK] Executando como Administrador
echo.

REM ============================================================================
echo Passo 1: Criando Diretorios
REM ============================================================================
echo.

if not exist "C:\BCSrvSqlMq" mkdir "C:\BCSrvSqlMq"
if not exist "C:\BCSrvSqlMq\Traces" mkdir "C:\BCSrvSqlMq\Traces"
if not exist "C:\BCSrvSqlMq\AuditFiles" mkdir "C:\BCSrvSqlMq\AuditFiles"
if not exist "C:\BCSrvSqlMq\certificates" mkdir "C:\BCSrvSqlMq\certificates"

echo [OK] Diretorios criados
echo.

REM ============================================================================
echo Passo 2: Verificando Arquivos
REM ============================================================================
echo.

if not exist "BCSrvSqlMq.exe" (
    echo [ERRO] BCSrvSqlMq.exe nao encontrado!
    pause
    exit /b 1
)
echo [OK] BCSrvSqlMq.exe

if not exist "BCSrvSqlMq.ini" (
    echo [ERRO] BCSrvSqlMq.ini nao encontrado!
    pause
    exit /b 1
)
echo [OK] BCSrvSqlMq.ini

echo.

REM ============================================================================
echo Passo 3: Verificando Status Atual
REM ============================================================================
echo.

BCSrvSqlMq.exe -v
echo.

REM ============================================================================
echo Passo 4: Instalacao
REM ============================================================================
echo.

set /p continuar="Deseja instalar o servico? (S/N): "
if /i not "%continuar%"=="S" goto :fim

echo.
echo Instalando servico...
BCSrvSqlMq.exe -i

if %errorlevel% EQU 0 (
    echo.
    echo [OK] Servico instalado com sucesso!
) else (
    echo.
    echo [AVISO] Verifique se o servico ja existe
)

echo.

REM ============================================================================
echo Passo 5: Iniciando Servico
REM ============================================================================
echo.

set /p iniciar="Deseja iniciar o servico agora? (S/N): "
if /i not "%iniciar%"=="S" goto :verificar

echo.
echo Iniciando servico...
net start BCSrvSqlMq

if %errorlevel% EQU 0 (
    echo.
    echo [OK] Servico iniciado!
) else (
    echo.
    echo [ERRO] Falha ao iniciar
    echo Verifique Event Viewer para detalhes
)

echo.

:verificar
REM ============================================================================
echo Passo 6: Verificando Status Final
REM ============================================================================
echo.

sc query BCSrvSqlMq
echo.

echo ============================================================================
echo Instalacao Concluida!
echo ============================================================================
echo.
echo Proximos passos:
echo 1. Verificar logs em: C:\BCSrvSqlMq\Traces\
echo 2. Event Viewer: eventvwr.msc
echo 3. Status: sc query BCSrvSqlMq
echo.

:fim
pause
