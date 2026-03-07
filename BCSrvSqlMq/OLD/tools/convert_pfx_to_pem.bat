@echo off
REM convert_pfx_to_pem.bat
REM Convert .pfx file to separate .pem (certificate) and .key (private key) files
REM
REM Usage:
REM   convert_pfx_to_pem.bat input.pfx [password]
REM
REM Example:
REM   convert_pfx_to_pem.bat certificate.pfx mypassword
REM   convert_pfx_to_pem.bat certificate.pfx

setlocal

if "%~1"=="" (
    echo Usage: convert_pfx_to_pem.bat input.pfx [password]
    echo.
    echo Example:
    echo   convert_pfx_to_pem.bat certificate.pfx mypassword
    echo   convert_pfx_to_pem.bat certificate.pfx
    echo.
    echo This will create:
    echo   - public_cert.pem  ^(certificate^)
    echo   - private.key      ^(private key^)
    exit /b 1
)

set INPUT_FILE=%~1
set PASSWORD=%~2
set CERT_OUTPUT=public_cert.pem
set KEY_OUTPUT=private.key

echo =========================================
echo PFX to PEM/KEY Converter
echo =========================================
echo.
echo Input:  %INPUT_FILE%
echo Output: %CERT_OUTPUT% ^(certificate^)
echo         %KEY_OUTPUT% ^(private key^)
echo.

REM Check if input file exists
if not exist "%INPUT_FILE%" (
    echo ERROR: Input file not found: %INPUT_FILE%
    exit /b 1
)

REM Find OpenSSL
set OPENSSL_PATH=
if exist "C:\Program Files\OpenSSL-Win64\bin\openssl.exe" (
    set OPENSSL_PATH=C:\Program Files\OpenSSL-Win64\bin\openssl.exe
) else if exist "C:\OpenSSL-Win64\bin\openssl.exe" (
    set OPENSSL_PATH=C:\OpenSSL-Win64\bin\openssl.exe
) else (
    where openssl.exe >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set OPENSSL_PATH=openssl.exe
    ) else (
        echo ERROR: OpenSSL not found!
        echo.
        echo Please install OpenSSL:
        echo   winget install ShiningLight.OpenSSL
        echo.
        echo Or download from:
        echo   https://slproweb.com/products/Win32OpenSSL.html
        exit /b 1
    )
)

echo Using OpenSSL: %OPENSSL_PATH%
echo.

REM Extract certificate (public key)
echo Step 1: Extracting certificate...
if "%PASSWORD%"=="" (
    "%OPENSSL_PATH%" pkcs12 -in "%INPUT_FILE%" -clcerts -nokeys -out "%CERT_OUTPUT%"
) else (
    "%OPENSSL_PATH%" pkcs12 -in "%INPUT_FILE%" -clcerts -nokeys -out "%CERT_OUTPUT%" -password pass:%PASSWORD%
)

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to extract certificate
    echo.
    echo Common issues:
    echo   - Wrong password
    echo   - Corrupted PFX file
    echo   - Invalid PFX format
    exit /b 1
)
echo SUCCESS: Certificate saved to %CERT_OUTPUT%

REM Extract private key
echo.
echo Step 2: Extracting private key...
echo.
echo Choose private key format:
echo   1. Unencrypted ^(no password - easier to use^)
echo   2. Encrypted ^(with password - more secure^)
echo.
set /p KEY_FORMAT="Enter choice [1/2]: "

if "%KEY_FORMAT%"=="2" (
    echo.
    echo Private key will be encrypted
    if "%PASSWORD%"=="" (
        "%OPENSSL_PATH%" pkcs12 -in "%INPUT_FILE%" -nocerts -out "%KEY_OUTPUT%"
    ) else (
        "%OPENSSL_PATH%" pkcs12 -in "%INPUT_FILE%" -nocerts -out "%KEY_OUTPUT%" -password pass:%PASSWORD%
    )
) else (
    echo.
    echo Private key will be UNENCRYPTED ^(no password^)
    if "%PASSWORD%"=="" (
        "%OPENSSL_PATH%" pkcs12 -in "%INPUT_FILE%" -nocerts -nodes -out "%KEY_OUTPUT%"
    ) else (
        "%OPENSSL_PATH%" pkcs12 -in "%INPUT_FILE%" -nocerts -nodes -out "%KEY_OUTPUT%" -password pass:%PASSWORD%
    )
)

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to extract private key
    exit /b 1
)
echo SUCCESS: Private key saved to %KEY_OUTPUT%

REM Verify outputs
echo.
echo Step 3: Verifying outputs...
echo.

echo Certificate:
"%OPENSSL_PATH%" x509 -in "%CERT_OUTPUT%" -subject -issuer -dates -noout
echo.

echo Private Key:
"%OPENSSL_PATH%" rsa -in "%KEY_OUTPUT%" -check -noout
echo.

REM Check if certificate and key match
echo Step 4: Checking if certificate and key match...
"%OPENSSL_PATH%" x509 -noout -modulus -in "%CERT_OUTPUT%" > cert_modulus.tmp
"%OPENSSL_PATH%" rsa -noout -modulus -in "%KEY_OUTPUT%" > key_modulus.tmp

fc cert_modulus.tmp key_modulus.tmp >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo SUCCESS: Certificate and private key MATCH
) else (
    echo WARNING: Certificate and private key DO NOT MATCH
    echo This may cause issues with signing/encryption
)

del cert_modulus.tmp key_modulus.tmp >nul 2>&1

echo.
echo =========================================
echo Conversion Complete!
echo =========================================
echo.
echo Files created:
echo   - %CERT_OUTPUT%  ^(certificate for verification/encryption^)
echo   - %KEY_OUTPUT%    ^(private key for signing/decryption^)
echo.
echo Update BCSrvSqlMq.ini:
echo   [Security]
echo   CertificateFile=C:\BCSrvSqlMq\certificates\%CERT_OUTPUT%
echo   PrivateKeyFile=C:\BCSrvSqlMq\certificates\%KEY_OUTPUT%
echo.

endlocal
