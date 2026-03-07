@echo off
REM ============================================================================
REM BCSrvSqlMq - Full Cryptographic Test
REM Tests OpenSSL 3.6.1 integration with real certificates
REM ============================================================================

echo.
echo ============================================================================
echo BCSrvSqlMq - Cryptographic Test
echo OpenSSL 3.6.1 - x64 Architecture
echo ============================================================================
echo.

cd /d "%~dp0\.."

REM Check if already compiled
if exist "build\Release\test_crypto_full.exe" (
    echo Test executable found!
    echo.
    goto :run_test
)

echo Compiling test...
echo.

REM Find vcpkg
set VCPKG_ROOT=C:\vcpkg
if not exist "%VCPKG_ROOT%" (
    echo [ERROR] vcpkg not found at %VCPKG_ROOT%
    echo Please install vcpkg first
    pause
    exit /b 1
)

REM Setup Visual Studio environment
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if %errorlevel% NEQ 0 (
    call "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
)
if %errorlevel% NEQ 0 (
    call "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
)

REM Compile
cl /std:c++17 /EHsc /O2 ^
   test_crypto_full.cpp ^
   /I"%VCPKG_ROOT%\installed\x64-windows\include" ^
   /link ^
   /LIBPATH:"%VCPKG_ROOT%\installed\x64-windows\lib" ^
   libcrypto.lib libssl.lib ^
   /OUT:build\Release\test_crypto_full.exe

if %errorlevel% NEQ 0 (
    echo.
    echo [ERROR] Compilation failed!
    echo.
    pause
    exit /b 1
)

echo.
echo Compilation successful!
echo.

REM Copy OpenSSL DLLs if needed
if not exist "build\Release\libcrypto-3-x64.dll" (
    copy "%VCPKG_ROOT%\installed\x64-windows\bin\libcrypto-3-x64.dll" build\Release\ >nul 2>&1
    copy "%VCPKG_ROOT%\installed\x64-windows\bin\libssl-3-x64.dll" build\Release\ >nul 2>&1
)

:run_test
echo Running cryptographic tests...
echo.
echo ============================================================================
echo.

build\Release\test_crypto_full.exe

echo.
echo ============================================================================
echo.

if %errorlevel% EQU 0 (
    echo.
    echo [SUCCESS] All cryptographic tests passed!
    echo The x64 OpenSSL migration is fully functional.
    echo.
) else (
    echo.
    echo [WARNING] Some tests failed - check output above
    echo.
)

pause
