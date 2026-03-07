# BCSrvSqlMq - Full Cryptographic Test
# Compiles and runs OpenSSL 3.6.1 crypto tests

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "BCSrvSqlMq - Cryptographic Test" -ForegroundColor Cyan
Write-Host "OpenSSL 3.6.1 - x64 Architecture" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Change to project directory
$ProjectDir = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectDir

# Check if already compiled
$TestExe = "build\Release\test_crypto_full.exe"
if (Test-Path $TestExe) {
    Write-Host "✓ Test executable found!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "Compiling test..." -ForegroundColor Yellow
    Write-Host ""

    # Find vcpkg
    $VcpkgRoot = "C:\dev\vcpkg"
    if (-not (Test-Path $VcpkgRoot)) {
        Write-Host "[ERROR] vcpkg not found at $VcpkgRoot" -ForegroundColor Red
        Write-Host "Please install vcpkg first" -ForegroundColor Red
        pause
        exit 1
    }

    # Find Visual Studio
    $VSWhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $VSWhere) {
        $VSPath = & $VSWhere -latest -property installationPath
        if ($VSPath) {
            Write-Host "Found Visual Studio: $VSPath" -ForegroundColor Green

            # Import VS environment
            $VCVarsPath = Join-Path $VSPath "VC\Auxiliary\Build\vcvars64.bat"
            if (Test-Path $VCVarsPath) {
                Write-Host "Setting up Visual Studio environment..." -ForegroundColor Yellow

                # Run vcvars64 and capture environment
                $TempBat = [System.IO.Path]::GetTempFileName() + ".bat"
                "@echo off`n`"$VCVarsPath`"`nset" | Out-File -FilePath $TempBat -Encoding ASCII
                cmd /c $TempBat | ForEach-Object {
                    if ($_ -match "^(.*?)=(.*)$") {
                        Set-Item -Force -Path "ENV:\$($matches[1])" -Value $matches[2]
                    }
                }
                Remove-Item $TempBat -ErrorAction SilentlyContinue

                Write-Host "✓ Visual Studio environment ready" -ForegroundColor Green
                Write-Host ""
            }
        }
    }

    # Create output directory
    New-Item -ItemType Directory -Force -Path "build\Release" | Out-Null

    # Compile
    Write-Host "Compiling test_crypto_full.cpp..." -ForegroundColor Yellow

    $CompileCmd = @(
        "cl.exe",
        "/std:c++17",
        "/EHsc",
        "/O2",
        "/nologo",
        "test_crypto_full.cpp",
        "/I`"$VcpkgRoot\installed\x64-windows\include`"",
        "/link",
        "/LIBPATH:`"$VcpkgRoot\installed\x64-windows\lib`"",
        "libcrypto.lib",
        "libssl.lib",
        "/OUT:$TestExe"
    )

    & $CompileCmd[0] $CompileCmd[1..($CompileCmd.Length-1)]

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "[ERROR] Compilation failed!" -ForegroundColor Red
        Write-Host ""
        pause
        exit 1
    }

    Write-Host ""
    Write-Host "✓ Compilation successful!" -ForegroundColor Green
    Write-Host ""

    # Copy OpenSSL DLLs
    if (-not (Test-Path "build\Release\libcrypto-3-x64.dll")) {
        Copy-Item "$VcpkgRoot\installed\x64-windows\bin\libcrypto-3-x64.dll" "build\Release\" -ErrorAction SilentlyContinue
        Copy-Item "$VcpkgRoot\installed\x64-windows\bin\libssl-3-x64.dll" "build\Release\" -ErrorAction SilentlyContinue
    }

    # Clean up intermediate files
    Remove-Item "*.obj" -ErrorAction SilentlyContinue
}

# Run the test
Write-Host "Running cryptographic tests..." -ForegroundColor Cyan
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

& $TestExe

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

if ($LASTEXITCODE -eq 0) {
    Write-Host "[SUCCESS] All cryptographic tests passed!" -ForegroundColor Green
    Write-Host "The x64 OpenSSL migration is fully functional." -ForegroundColor Green
} else {
    Write-Host "[WARNING] Some tests failed - check output above" -ForegroundColor Yellow
}

Write-Host ""
pause
