@echo off
REM Simple compilation script for crypto test
REM Run this from "x64 Native Tools Command Prompt for VS 2022"

cd /d "%~dp0"

echo.
echo ============================================================================
echo Compiling Cryptographic Test
echo ============================================================================
echo.

if not exist "build\Release" mkdir "build\Release"

cl /std:c++17 /EHsc /O2 /nologo test_crypto_full.cpp ^
   /I"C:\dev\vcpkg\installed\x64-windows\include" ^
   /link ^
   /LIBPATH:"C:\dev\vcpkg\installed\x64-windows\lib" ^
   libcrypto.lib libssl.lib ^
   /OUT:build\Release\test_crypto_full.exe

if %errorlevel% NEQ 0 (
    echo.
    echo [ERROR] Compilation failed!
    echo.
    echo Make sure you run this from:
    echo "x64 Native Tools Command Prompt for VS 2022"
    echo.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Compilation complete!
echo.

REM Copy OpenSSL DLLs if needed
if not exist "build\Release\libcrypto-3-x64.dll" (
    copy "C:\dev\vcpkg\installed\x64-windows\bin\libcrypto-3-x64.dll" build\Release\ >nul 2>&1
    copy "C:\dev\vcpkg\installed\x64-windows\bin\libssl-3-x64.dll" build\Release\ >nul 2>&1
)

REM Clean up intermediate files
del *.obj >nul 2>&1

echo Running test...
echo.
echo ============================================================================
echo.

build\Release\test_crypto_full.exe

echo.
echo ============================================================================
echo.
pause
