# Compile and test cryptographic functions
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "===========================================

"
Write-Host "BCSrvSqlMq - Cryptographic Test"
Write-Host "OpenSSL 3.6.1 x64"
Write-Host "==========================================="
Write-Host ""

$ProjectDir = "C:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq"
Set-Location $ProjectDir

# Check for existing executable
if (Test-Path "build\Release\test_crypto_full.exe") {
    Write-Host "Test executable found, running..." -ForegroundColor Green
    Write-Host ""
    & "build\Release\test_crypto_full.exe"
    exit
}

# Otherwise, provide instructions
Write-Host "Test executable not found." -ForegroundColor Yellow
Write-Host ""
Write-Host "To compile and run the test:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Open 'x64 Native Tools Command Prompt for VS 2022'"
Write-Host "2. Navigate to: $ProjectDir"
Write-Host "3. Run these commands:"
Write-Host ""
Write-Host "   cl /std:c++17 /EHsc /O2 test_crypto_full.cpp \"
Write-Host "      /I\"C:\vcpkg\installed\x64-windows\include\" \"
Write-Host "      /link \"
Write-Host "      /LIBPATH:\"C:\vcpkg\installed\x64-windows\lib\" \"
Write-Host "      libcrypto.lib libssl.lib \"
Write-Host "      /OUT:build\Release\test_crypto_full.exe"
Write-Host ""
Write-Host "   build\Release\test_crypto_full.exe"
Write-Host ""
