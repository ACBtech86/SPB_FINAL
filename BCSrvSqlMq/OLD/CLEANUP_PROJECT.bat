@echo off
REM ============================================================================
REM BCSrvSqlMq Project Cleanup
REM Removes old files and organizes documentation after x64 migration
REM ============================================================================

color 0E
title Project Cleanup - x64 Migration Complete

cls
echo.
echo ============================================================================
echo BCSrvSqlMq Project Cleanup
echo ============================================================================
echo.
echo This will cleanup the project directory after successful x64 migration:
echo.
echo   [OLD BINARIES - Delete]
echo   - BCSrvSqlMq.exe (222KB, x86 - Feb 27)
echo   - CL32.dll (672KB, 32-bit library)
echo.
echo   [BACKUP FILES - Archive]
echo   - cmqc.h.STUB_BACKUP (stub header backup)
echo.
echo   [BUILD INTERMEDIATE - Clean]
echo   - 54 .obj, .tlog, .idb files (save space)
echo.
echo   [DOCUMENTATION - Organize]
echo   - Move old docs to DOCS/Archive/
echo   - Keep new comprehensive docs in root
echo.
echo WARNING: This will delete old x86 binaries!
echo Make sure you have the working x64 binary in build\Release\
echo.
pause

cd /d "%~dp0"

REM ============================================================================
REM Step 1: Create Archive directories
REM ============================================================================
echo.
echo [1/5] Creating Archive directories...

if not exist "Archive" mkdir Archive
if not exist "Archive\OldBinaries" mkdir "Archive\OldBinaries"
if not exist "Archive\BackupFiles" mkdir "Archive\BackupFiles"
if not exist "DOCS\Archive" mkdir "DOCS\Archive"

REM ============================================================================
REM Step 2: Archive old binaries (don't delete - keep for reference)
REM ============================================================================
echo.
echo [2/5] Archiving old x86 binaries...

if exist "BCSrvSqlMq.exe" (
    echo   Moving BCSrvSqlMq.exe ^(x86^) to Archive...
    move /Y "BCSrvSqlMq.exe" "Archive\OldBinaries\" >nul
)

if exist "CL32.dll" (
    echo   Moving CL32.dll ^(32-bit^) to Archive...
    move /Y "CL32.dll" "Archive\OldBinaries\" >nul
)

if exist "CL32.lib" (
    echo   Moving CL32.lib ^(32-bit^) to Archive...
    move /Y "CL32.lib" "Archive\OldBinaries\" >nul
)

REM ============================================================================
REM Step 3: Archive backup files
REM ============================================================================
echo.
echo [3/5] Archiving backup files...

if exist "cmqc.h.STUB_BACKUP" (
    echo   Moving cmqc.h.STUB_BACKUP to Archive...
    move /Y "cmqc.h.STUB_BACKUP" "Archive\BackupFiles\" >nul
)

REM ============================================================================
REM Step 4: Clean build intermediate files (keep binaries and DLLs)
REM ============================================================================
echo.
echo [4/5] Cleaning build intermediate files...

if exist "build\BCSrvSqlMq.dir\Release\*.obj" (
    echo   Deleting object files ^(.obj^)...
    del /Q "build\BCSrvSqlMq.dir\Release\*.obj" >nul 2>&1
)

if exist "build\BCSrvSqlMq.dir\Release\*.idb" (
    echo   Deleting debug files ^(.idb^)...
    del /Q "build\BCSrvSqlMq.dir\Release\*.idb" >nul 2>&1
)

if exist "build\BCSrvSqlMq.dir\Release\BCSrvSqlMq.tlog" (
    echo   Deleting build logs ^(.tlog^)...
    del /Q "build\BCSrvSqlMq.dir\Release\BCSrvSqlMq.tlog\*.*" >nul 2>&1
)

REM Keep PDB for debugging
echo   Keeping .pdb files for debugging

REM ============================================================================
REM Step 5: Organize documentation
REM ============================================================================
echo.
echo [5/5] Organizing documentation...

REM Move old/redundant docs to archive
if exist "CRYPTO_TEST_README.md" (
    echo   Moving CRYPTO_TEST_README.md to DOCS\Archive...
    move /Y "CRYPTO_TEST_README.md" "DOCS\Archive\" >nul
)

if exist "MQ_SETUP_GUIDE.md" (
    echo   Moving MQ_SETUP_GUIDE.md to DOCS\Archive...
    move /Y "MQ_SETUP_GUIDE.md" "DOCS\Archive\" >nul
)

if exist "REBUILD_INSTRUCTIONS.md" (
    echo   Moving REBUILD_INSTRUCTIONS.md to DOCS\Archive...
    move /Y "REBUILD_INSTRUCTIONS.md" "DOCS\Archive\" >nul
)

REM ============================================================================
REM Create Archive README files
REM ============================================================================
echo.
echo Creating Archive README files...

REM Old Binaries README
(
echo # Archived Old Binaries
echo.
echo **Archive Date**: %DATE% %TIME%
echo **Reason**: x64 migration completed
echo.
echo ## Files Archived
echo.
echo - **BCSrvSqlMq.exe** ^(222KB, x86^) - Old 32-bit binary from Feb 27
echo - **CL32.dll** ^(672KB^) - 32-bit library, not needed for x64
echo - **CL32.lib** - 32-bit import library
echo.
echo ## Current Working Binary
echo.
echo The current working x64 binary is:
echo - **Location**: `build\Release\BCSrvSqlMq.exe`
echo - **Size**: 240 KB
echo - **Architecture**: x64 ^(PE32+^)
echo - **Build Date**: March 1, 2026
echo - **Status**: Production ready, all 8 tasks working
echo.
echo ## Do Not Use These Files!
echo.
echo These archived binaries are x86 and will NOT work with:
echo - IBM MQ 9.4.5.0 x64
echo - OpenSSL 3.6.1 x64
echo - Current system configuration
echo.
echo They are kept only for reference and rollback purposes.
echo.
) > "Archive\OldBinaries\README.md"

REM Backup Files README
(
echo # Archived Backup Files
echo.
echo **Archive Date**: %DATE% %TIME%
echo.
echo ## Files Archived
echo.
echo - **cmqc.h.STUB_BACKUP** - Stub MQ header that caused structure mismatch
echo.
echo ## What Was Wrong
echo.
echo The stub header had:
echo - Simplified MQOD structure definition
echo - Different structure layout than real IBM MQ 9.4.5.0
echo - MQOD_DEFAULT with ObjectType = 0 ^(should be 1^)
echo.
echo This caused error 2043/2085 because ObjectType was written to wrong memory offset.
echo.
echo ## Resolution
echo.
echo - Removed stub header
echo - Rebuilt with real IBM MQ headers from C:\Program Files\IBM\MQ\tools\c\include\
echo - All 8 tasks now working correctly
echo.
echo ## Do Not Use This File!
echo.
echo This stub header is incompatible with IBM MQ 9.4.5.0 runtime.
echo It is kept only for reference to understand the issue.
echo.
) > "Archive\BackupFiles\README.md"

REM ============================================================================
REM Summary
REM ============================================================================
echo.
echo ============================================================================
echo Cleanup Complete!
echo ============================================================================
echo.
echo Archived:
echo   - Old x86 binaries ^(BCSrvSqlMq.exe, CL32.dll^)
echo   - Backup files ^(cmqc.h.STUB_BACKUP^)
echo   - Old documentation ^(3 files^)
echo.
echo Cleaned:
echo   - Build intermediate files ^(~50 files^)
echo.
echo Space saved: ~1.5 MB
echo.
echo Current project state:
echo   - Working binary: build\Release\BCSrvSqlMq.exe ^(240KB, x64^)
echo   - All 8 tasks: Operational
echo   - Documentation: Organized in root and DOCS\
echo   - Scripts: Ready for cleanup ^(run Scripts\CLEANUP_SCRIPTS.bat^)
echo.
echo ============================================================================
echo Archive locations:
echo   - Archive\OldBinaries\     - Old x86 binaries
echo   - Archive\BackupFiles\     - Stub header backup
echo   - DOCS\Archive\            - Old documentation
echo   - Scripts\Archive\         - ^(after running Scripts\CLEANUP_SCRIPTS.bat^)
echo ============================================================================
echo.
pause
